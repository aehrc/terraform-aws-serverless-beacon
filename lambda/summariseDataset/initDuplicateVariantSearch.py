from dataclasses import dataclass, field
import os
import json
import struct
import boto3
from botocore.exceptions import ClientError

MAX_BASE_PAIR_DIGITS: int = 15
ABS_MAX_DATA_SPLIT: int = int(os.environ['ABS_MAX_DATA_SPLIT'])

DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN = os.environ['DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN']
VARIANT_DUPLICATES_TABLE_NAME = os.environ['DYNAMO_VARIANT_DUPLICATES_TABLE']
VARIANTS_BUCKET = os.environ['VARIANTS_BUCKET']
DATASETS_TABLE_NAME = os.environ['DYNAMO_DATASETS_TABLE']

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.client('dynamodb')


@dataclass
class vcfRegionData:
    filepath: str
    filename: str
    filesize: int
    startRange: int
    endRange: int


@dataclass
class basePairRange:
    start: int
    end: int
    filePaths: 'list[str]' = field(default_factory=list)


def retrieveS3Objects(bucket: str, contig: str) -> 'list[str]':
    """Get a list of all keys in a contig."""
    keys = []

    kwargs = {'Bucket': bucket, 'Prefix': f"vcf-summaries/contig/{contig}/"}
    objects_left = True

    while objects_left:
        response = s3.list_objects_v2(**kwargs)
        if response['KeyCount'] == 0:
            return []
        for obj in response['Contents']:
            keys.append(obj['Key'])
        objects_left = response['IsTruncated']
        if objects_left:
            kwargs['ContinuationToken'] = response['NextContinuationToken']

    return keys


def getContigs() -> 'list[str]':
    """Get a list of all contigs for which variants are available."""
    contigs = []
    kwargs = {
        'Bucket': VARIANTS_BUCKET,
        'Delimiter': '/',
        'Prefix': f'vcf-summaries/contig/',
    }
    objects_left = True

    while objects_left:
        response = s3.list_objects_v2(**kwargs)
        contigs += [
            prefix['Prefix'].split('/')[-2]
            for prefix in response.get('CommonPrefixes', [])
        ]
        objects_left = response['IsTruncated']
        if objects_left:
            kwargs['ContinuationToken'] = response['NextContinuationToken']

    return contigs


def getFileNameInfo(filepath: str) -> vcfRegionData:
    # Array looks like [ 'vcf-summaries', 'contig', '1', 'filename', 'regions', '43400310-43749862-125506']
    splitArray : list[str] = filepath.split('/')
    filename: str = splitArray[-3]

    splitRange : list[str] = splitArray[-1].split('-')
    startRange: int = int(splitRange[0])
    endRange: int = int(splitRange[1])
    fileSize: int = int(splitRange[2])
    
    return vcfRegionData(filepath, filename, fileSize, startRange, endRange)


def filterRange(regionData: 'list[vcfRegionData]', start: int, end: int) -> 'tuple[int, list[vcfRegionData]]':
    searchFiles: list[vcfRegionData] = []
    rangeSize: int = 0
    for rd in regionData:
        if rd.startRange <= end and rd.endRange >= start: # If the two regions overlap
            searchFiles.append(rd)
            rangeSize = rangeSize + rd.filesize
    return rangeSize, searchFiles


# Add a range to the rangeSlices array, return the starting point for the next loop
def addRange(regionData: 'list[vcfRegionData]', startRange: int, endRange: int, rangeSlices : 'dict[str, list[basePairRange]]') -> 'tuple[int, int]':
    rangeSize, fileList = filterRange(regionData, startRange, endRange)

    while rangeSize > ABS_MAX_DATA_SPLIT:
        # catch issue where there could be no more items in the list, return the minimum list if this happens
        try:
            # Keep all files less than than the endRange
            # Take the maximum of this result to be the new end
            newEnd = max(file.endRange for file in fileList if file.endRange < endRange)
            rangeSize, fileList = filterRange(fileList, startRange, newEnd)
        except ValueError:
            print("Issue with reducing the dataset, Max value exceeded")
            newEnd = endRange
        
        if endRange == newEnd:
            break
        endRange = newEnd
    
    rangeSlices.append(basePairRange(startRange, endRange, [file.filepath for file in fileList]))
    # print("Start R:", startRange, "End R:", endRange, f"({MIN_DATA_SPLIT} <= {rangeSize} <= {ABS_MAX_DATA_SPLIT}) =", MIN_DATA_SPLIT <= rangeSize <= ABS_MAX_DATA_SPLIT, [file.filepath for file in fileList])

    return endRange + 1, (regionData.index(fileList[-1]) + 1)


# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Limits.html
# DynamoDB transactional API operations have the following constraints:
# A transaction cannot contain more than 25 unique items.
# A transaction cannot contain more than 4 MB of data.
# There is no limit on the number of values in a List, a Map, or a Set, as long as the item containing the values fits within the 400 KB (409600 bytes) item size limit.
# An attribute of type List or Map requires 3 bytes of overhead, regardless of its contents
# The size of a List or Map is (length of attribute name) + sum (size of nested elements) + (3 bytes)

# length of attribute name = sizeof("toUpdate") = 8
# size of nested elements = 8*2 = 16
# + 3
# ( (409600 - 8 - 3) / 16 ) = 25,598 items in the array
def mark_updating(contig: str, slices : 'list[basePairRange]', dataset: str):
    slice_strings = [struct.pack('QQ', s.start, s.end) for s in slices]

    kwargs = {
        'TableName': VARIANT_DUPLICATES_TABLE_NAME,
        'Key': {
            "contig": {"S":contig}, 
            "datasetKey": {"S":dataset},
        },
        'UpdateExpression': 'ADD toUpdate :toUpdate SET variantCount = :variantCount',
        'ExpressionAttributeValues': {
            ':toUpdate': {
                'BS': slice_strings,
            },
            ':variantCount': {
                'N': '0',
            },
        },
    }
    print('Updating table: ', kwargs)
    try:
        dynamodb.update_item(**kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("VCF duplicates is already updated, aborting.")
            return False
        else:
            raise e
    return True


def calcRangeSplits(regionData: 'list[vcfRegionData]' ) -> 'list[basePairRange]':
    rangeSlices : 'list[basePairRange]' = [] # This is the data structure we are trying to fill in
    runningTotal: int = 0
    startRange: int = regionData[0].startRange
    itemInc: int = 0
    minDataSplit: int = ABS_MAX_DATA_SPLIT - (regionData[0].filesize * 2)

    while startRange - 1 != regionData[-1].endRange:
        element = regionData[itemInc]
        if runningTotal < minDataSplit:
            runningTotal = runningTotal + element.filesize
            itemInc = itemInc + 1 if itemInc + 1 < len(regionData) else itemInc
        else:
            # We have hit the minimum amount required, gather other files and return the next starting point
            startRange, itemInc = addRange(regionData, startRange, element.endRange, rangeSlices)
            runningTotal = 0

    if runningTotal != 0:
        addRange(regionData, startRange, max(r.endRange for r in regionData), rangeSlices)
    
    return rangeSlices


def publishVariantSearch(contig, baseRanges : 'list[basePairRange]', dataset: str) -> None:
    for baseRange in baseRanges:
        message = {
            'bucket': VARIANTS_BUCKET,
            'rangeStart': baseRange.start,
            'rangeEnd': baseRange.end,
            'contig': contig,
            'targetFilepaths': baseRange.filePaths,
            'dataset': dataset,
        }

        kwargs = {
            'TopicArn': DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN,
            'Message': json.dumps(message),
        }
        print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
        # continue # TODO
        response = sns.publish(**kwargs)
        print('Received Response: {}'.format(json.dumps(response)))


def clearDatasetVariantCount(dataset: str) -> None:
    kwargs = {
        'TableName': DATASETS_TABLE_NAME,
        'Key': {
            "id": {"S": dataset}, 
        },
        'UpdateExpression': 'SET variantCount = :variantCount',
        'ExpressionAttributeValues': {
            ':variantCount': {
                'N': '0',
            },
        },
    }
    print('Updating table: ', kwargs)
    try:
        dynamodb.update_item(**kwargs)
    except ClientError as e:
        raise e


def initDuplicateVariantSearch(dataset: str, filepaths: 'list[str]') -> None:
    print('filepaths:', filepaths)
    filenames: list[str] = ['/'+ fn[5:-7].replace('/', '%')+'/' for fn in filepaths]
    # mark dataset variantCount as zero
    clearDatasetVariantCount(dataset)
    contigs: list[str] = getContigs()

    for contig in contigs:
        s3Objects: list[str] = retrieveS3Objects(VARIANTS_BUCKET, contig)

        regionData: list[vcfRegionData] = []
        for filepath in s3Objects:
            if any([fn in filepath for fn in filenames]):
                splitfilepath: vcfRegionData = getFileNameInfo(filepath)
                regionData.append(splitfilepath)
        if (len(regionData) > 0):
            regionData.sort(key=lambda x: x.startRange)
            rangeSlices : 'list[basePairRange]' = calcRangeSplits(regionData)
            # Only send the SNS if the database update succeeds
            if mark_updating(contig, rangeSlices, dataset):
                publishVariantSearch(contig, rangeSlices, dataset)
