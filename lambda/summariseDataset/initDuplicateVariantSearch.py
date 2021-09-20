from dataclasses import dataclass
import os
import json
import boto3
from botocore.exceptions import ClientError

VCF_SEARCH_BASE_PAIR_RANGE: int = 5000
DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN = os.environ['DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN']
VCF_DUPLICATES_TABLE_NAME = os.environ['VCF_DUPLICATES_TABLE']

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.client('dynamodb')

@dataclass
class vcfRegionData:
    filepath: str
    filename: str
    chrom: str
    startRange: int
    endRange: int

@dataclass
class basePairRange:
    start: int
    end: int

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
    # Array looks like [ 'vcf-summaries', 'filename' , 'chromosomes', '1', 'regions', '10000-13333']
    splitArray : list[str] = filepath.split('/')
    chrom: str = splitArray[-3]
    filename: str = splitArray[-5]

    splitRange : list[str] = splitArray[-1].split('-')
    startRange: int = int(splitRange[0])
    endRange: int = int(splitRange[1])
    
    return vcfRegionData(filepath, filename, chrom, startRange, endRange)

def createChromRegionsMap(chromLookup: 'dict[str, basePairRange]', insertItem: vcfRegionData) -> None:
    if insertItem.chrom not in chromLookup: # If we haven't seen this chrom before, add a record.
        chromLookup[insertItem.chrom] = basePairRange(insertItem.startRange, insertItem.endRange)
    else:
        if (chromLookup[insertItem.chrom].start > insertItem.startRange):
            chromLookup[insertItem.chrom].start = insertItem.startRange
        
        if (chromLookup[insertItem.chrom].end < insertItem.endRange):
            chromLookup[insertItem.chrom].end = insertItem.endRange

def filterChromAndRange(currentSearchTargets: 'list[vcfRegionData]', regionData: 'list[vcfRegionData]', chrom: int, start: int, end: int) -> None:
    for rd in regionData:
        isSameChrom: bool = rd.chrom == chrom
        isInRange: bool = (
            (rd.startRange <= start and start <= rd.endRange) or # If the start point lies within the range
            (rd.startRange <= end and end <= rd.endRange) or # If the end point lies within the range
            (start < rd.startRange and rd.endRange < end) # If the start and end point encompass the range
        )

        if (isSameChrom and isInRange):
            currentSearchTargets.append(rd)

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

def initDuplicateVariantSearch(filepaths: 'list[str]') -> None:
    print('filepaths:', filepaths)
    filenames: list[str] = [fn.split('/')[-1].split('.')[0] for fn in filepaths]
    print('filenames:', filenames)
    s3Objects: list[str] = retrieveS3Objects("large-test-vcfs")
    # print('s3Objects:', s3Objects)

    chromLookup: dict[str, basePairRange] = {}

    regionData: list[vcfRegionData] = []
    for filepath in s3Objects:
        splitfilepath: vcfRegionData = getFileNameInfo(filepath)
        if splitfilepath.filename in filenames:
            regionData.append(splitfilepath)
            createChromRegionsMap(chromLookup, regionData[-1])

    # print('regionData: ', [out.filename for out in regionData])
    rangeSlices : dict[str, list[basePairRange]] = {}
    
    for chrom, reg in chromLookup.items():
        if (reg.end < reg.start):
            raise Exception("logic error: region end is greater than region start")
        rangeSlices[chrom] = []

        for rangeStart in range(reg.start, reg.end, VCF_SEARCH_BASE_PAIR_RANGE):
            rangeEnd: int = reg.end if rangeStart + VCF_SEARCH_BASE_PAIR_RANGE > reg.end else rangeStart + VCF_SEARCH_BASE_PAIR_RANGE - 1
            rangeSlices[chrom].append(basePairRange(rangeStart, rangeEnd))
            # print(rangeStart, rangeEnd)

    for chrom, baseRange in rangeSlices.items():
        # Only send the SNS if the database update succeeds
        if mark_updating(chrom, baseRange):
            for br in baseRange: 
                currentSearchTargets: list[vcfRegionData] = []
                filterChromAndRange(
                    currentSearchTargets,
                    regionData,
                    chrom,
                    br.start,
                    br.end
                )

                targetFilepaths: list[str] = []
                for cst in currentSearchTargets:
                    targetFilepaths.append(cst.filepath)

                message = {
                    'bucket': "large-test-vcfs", # TODO
                    'rangeStart': br.start,
                    'rangeEnd': br.end,
                    'chrom': chrom,
                    'targetFilepaths': targetFilepaths
                }

                kwargs = {
                    'TopicArn': DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN,
                    'Message': json.dumps(message),
                }
                print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
                response = sns.publish(**kwargs)
                print('Received Response: {}'.format(json.dumps(response)))
