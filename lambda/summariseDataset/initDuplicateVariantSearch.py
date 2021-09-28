from dataclasses import dataclass, field
import os
import json
import math
import boto3
from botocore.exceptions import ClientError

MAX_BASE_PAIR_DIGITS: int = 15
MIN_DATA_SPLIT: int = os.environ['MIN_DATA_SPLIT']
ABS_MAX_DATA_SPLIT: int = os.environ['ABS_MAX_DATA_SPLIT']

DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN = os.environ['DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN']
VCF_DUPLICATES_TABLE_NAME = os.environ['VCF_DUPLICATES_TABLE']
S3_SUMMARIES_BUCKET = os.environ['S3_SUMMARIES_BUCKET']

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.client('dynamodb')

@dataclass
class vcfRegionData:
    filepath: str
    filename: str
    filesize: int
    chrom: str
    startRange: int
    endRange: int

@dataclass
class basePairRange:
    start: int
    end: int
    filePaths: 'list[str]' = field(default_factory=list)

def retrieveS3Objects(bucket: str) -> 'list[str]':
    """Get a list of all keys in an S3 bucket."""
    keys = []

    kwargs = {'Bucket': bucket, 'Prefix': 'vcf-summaries/'}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            keys.append(obj['Key'])

        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break

    return keys

def getFileNameInfo(filepath: str) -> vcfRegionData:
    # Array looks like [ 'vcf-summaries', 'filename' , 'chromosomes', '1', 'regions', '43400310-43749862-125506']
    splitArray : list[str] = filepath.split('/')
    chrom: str = splitArray[-3]
    filename: str = splitArray[-5]

    splitRange : list[str] = splitArray[-1].split('-')
    startRange: int = int(splitRange[0])
    endRange: int = int(splitRange[1])
    fileSize: int = int(splitRange[2])
    
    return vcfRegionData(filepath, filename, fileSize, chrom, startRange, endRange)

def filterChromAndRange(regionData: 'list[vcfRegionData]', chrom: int, start: int, end: int) -> 'tuple[int, list[vcfRegionData]]':
    searchFiles: list[vcfRegionData] = []
    rangeSize: int = 0
    for rd in regionData:
        isSameChrom: bool = rd.chrom == chrom
        isInRange: bool = (
            (rd.startRange <= start and start <= rd.endRange) or # If the start point lies within the range
            (rd.startRange <= end and end <= rd.endRange) or # If the end point lies within the range
            (start < rd.startRange and rd.endRange < end) # If the start and end point encompass the range
        )

        if (isSameChrom and isInRange):
            searchFiles.append(rd)
            rangeSize = rangeSize + rd.filesize
    return rangeSize, searchFiles

# Add a range to the rangeSlices array, return the starting point for the next loop
def addRange(regionData: 'list[vcfRegionData]', chrom: str, startRange: int, endRange: int, rangeSlices : 'dict[str, list[basePairRange]]') -> 'tuple[int, int]':
    rangeSize, fileList = filterChromAndRange(regionData, chrom, startRange, endRange)

    while rangeSize > ABS_MAX_DATA_SPLIT:
        # catch issue where there could be no more items in the list, return the minimum list if this happens
        try:
            # Keep all files less than than the endRange
            # Take the maximum of this result to be the new end
            newEnd = max(file.endRange for file in fileList if file.endRange < endRange)
            rangeSize, fileList = filterChromAndRange(fileList, chrom, startRange, newEnd)
        except ValueError:
            print("Issue with reducing the dataset, Max value exceeded")
            newEnd = endRange
        
        if endRange == newEnd:
            break
        endRange = newEnd
    
    rangeSlices[chrom].append(basePairRange(startRange, endRange, [file.filepath for file in fileList]))
    # print("Start R:", startRange, "End R:", endRange, f"({MIN_DATA_SPLIT} <= {rangeSize} <= {ABS_MAX_DATA_SPLIT}) =", MIN_DATA_SPLIT <= rangeSize <= ABS_MAX_DATA_SPLIT, [file.filepath for file in fileList])

    return endRange + 1, (regionData.index(fileList[-1]) + 1)


# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Limits.html
# DynamoDB transactional API operations have the following constraints:
# A transaction cannot contain more than 25 unique items.
# A transaction cannot contain more than 4 MB of data.
# There is no limit on the number of values in a List, a Map, or a Set, as long as the item containing the values fits within the 400 KB (409600 bytes) item size limit.
# The size of a List or Map is (length of attribute name) + sum (size of nested elements) + (3 bytes)

def mark_updating(chrom: str, slices : 'list[basePairRange]'):
    slice_strings = [f'{s.start}-{s.end}' for s in slices]
    kwargs = {
        'TableName': VCF_DUPLICATES_TABLE_NAME,
        'Key': {
            'vcfDuplicates': {
                'S': chrom,
            },
        },
        'UpdateExpression': 'SET toUpdate=:toUpdate',
        'ExpressionAttributeValues': {
            ':toUpdate': {
                'SS': slice_strings,
            },
        },
        'ConditionExpression': 'attribute_not_exists(toUpdate)',
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

def sortVcfRegion(elem: vcfRegionData):
    return elem.chrom + str(elem.startRange).zfill(MAX_BASE_PAIR_DIGITS)

def calcRangeSplits(regionData: 'list[vcfRegionData]' ) -> 'dict[str, list[basePairRange]]':
    rangeSlices : 'dict[str, list[basePairRange]]' = {} # This is the data structure we are trying to fill in
    runningTotal: int = 0
    chromEndTracker: int = 0
    chrom: str = regionData[0].chrom
    startRange: int = regionData[0].startRange
    itemInc: int = 0

    while startRange - 1 != regionData[-1].endRange:
        element = regionData[itemInc]
        # Init the range slice with a new chrom if needed
        if chrom not in rangeSlices:
            rangeSlices[chrom] = []

        # If we are switching chrom, finish the other range first
        if chrom != element.chrom:
            # Check to see if the range is valid, it could have just been added
            if runningTotal != 0:
                addRange(regionData, chrom, startRange, chromEndTracker, rangeSlices)
            # Reset variables ready for this chrom
            runningTotal = 0
            chrom = element.chrom
            startRange = element.startRange

        chromEndTracker = element.endRange
        if runningTotal < MIN_DATA_SPLIT:
            runningTotal = runningTotal + element.filesize
            itemInc = itemInc + 1 if itemInc + 1 < len(regionData) else itemInc
        else:
            # We have hit the minimum amount required, gather other files and return the next starting point
            startRange, itemInc = addRange(regionData, chrom, startRange, element.endRange, rangeSlices)
            runningTotal = 0

    if runningTotal != 0:
        addRange(regionData, chrom, startRange, chromEndTracker, rangeSlices)
    
    return rangeSlices

def insertDatabaseAndCallSNS(rangeSlices : 'dict[str, list[basePairRange]]') -> None:
    for chrom, baseRange in rangeSlices.items():
        # Only send the SNS if the database update succeeds
        if mark_updating(chrom, baseRange):
            for br in baseRange: 
                message = {
                    'bucket': S3_SUMMARIES_BUCKET,
                    'rangeStart': br.start,
                    'rangeEnd': br.end,
                    'chrom': chrom,
                    'targetFilepaths': br.filePaths
                }

                kwargs = {
                    'TopicArn': DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN,
                    'Message': json.dumps(message),
                }
                print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
                # continue # TODO
                response = sns.publish(**kwargs)
                print('Received Response: {}'.format(json.dumps(response)))

def initDuplicateVariantSearch(filepaths: 'list[str]') -> None:
    print('filepaths:', filepaths)
    filenames: list[str] = [fn.split('/')[-1].split('.')[0] for fn in filepaths]
    print('filenames:', filenames)
    s3Objects: list[str] = retrieveS3Objects(S3_SUMMARIES_BUCKET)
    # print('s3Objects:', s3Objects)

    regionData: list[vcfRegionData] = []
    for filepath in s3Objects:
        splitfilepath: vcfRegionData = getFileNameInfo(filepath)
        if splitfilepath.filename in filenames:
            regionData.append(splitfilepath)
    regionData.sort(key=sortVcfRegion)

    rangeSlices : 'dict[str, list[basePairRange]]' = calcRangeSplits(regionData)
    print(rangeSlices)
    insertDatabaseAndCallSNS(rangeSlices)
