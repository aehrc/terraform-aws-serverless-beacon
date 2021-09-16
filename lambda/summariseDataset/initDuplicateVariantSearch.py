from dataclasses import dataclass
import boto3
import os
import json

VCF_SEARCH_BASE_PAIR_RANGE: int = 5000
DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN = os.environ['DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN']

s3 = boto3.client('s3')
sns = boto3.client('sns')

@dataclass
class vcfRegionData:
    filepath: str
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

def getFileNameInfo(filePath: str) -> vcfRegionData:
    # Array looks like [ 'vcf-summaries', .. , 'chromosomes', '1', 'regions', '10000-13333']
    splitArray : list[str] = filePath.split('/')
    chrom: str = splitArray[-3]

    splitRange : list[str] = splitArray[-1].split('-')
    startRange: int = int(splitRange[0])
    endRange: int = int(splitRange[1])
    
    return vcfRegionData(filePath, chrom, startRange, endRange)

def createChromRegionsMap(chromLookup: 'dict[int, basePairRange]', insertItem: vcfRegionData) -> None:
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

def initDuplicateVariantSearch(bucket: str) -> None:
    s3Objects: list[str] = retrieveS3Objects(bucket)
    chromLookup: dict[int, basePairRange] = {}

    regionData: list[vcfRegionData] = []
    for filepath in s3Objects:
        regionData.append(getFileNameInfo(filepath))
        createChromRegionsMap(chromLookup, regionData[-1])
    
    for chrom, reg in chromLookup.items():
        if (reg.end < reg.start):
            raise Exception("logic error: region end is greater than region start")

        for rangeStart in range(reg.start, reg.end, VCF_SEARCH_BASE_PAIR_RANGE):
            rangeEnd: int = reg.end if rangeStart + VCF_SEARCH_BASE_PAIR_RANGE > reg.end else rangeStart + VCF_SEARCH_BASE_PAIR_RANGE - 1
            print(rangeStart, rangeEnd)

            currentSearchTargets: list[vcfRegionData] = []
            filterChromAndRange(
                currentSearchTargets,
                regionData,
                chrom,
                rangeStart,
                rangeEnd
            )

            targetFilepaths: list[str] = []
            for cst in currentSearchTargets:
                targetFilepaths.append(cst.filepath)

            message = {
                'bucket': bucket,
                'rangeStart': rangeStart,
                'rangeEnd': rangeEnd,
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
