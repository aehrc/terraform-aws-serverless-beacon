#include "initDuplicateVariantSearch.hpp"

vector<string> InitDuplicateVariantSearch::retrieveS3Objects(string bucket, Aws::S3::S3Client const& s3Client) {
    vector<string> objectKeys;
    vector<string> bucketObjectKeys = awsutils::retrieveBucketObjectKeys(bucket, s3Client);
    copy_if(bucketObjectKeys.begin(), bucketObjectKeys.end(), back_inserter(objectKeys), [](string s) { return s.find("vcf-summaries") != std::string::npos; });
    return objectKeys;
}

int InitDuplicateVariantSearch::nthLastIndexOf(int nth, string str) {
    if (nth <= 0) return str.length();
    return nthLastIndexOf(--nth, str.substr(0, str.find_last_of("/")));
}

vcfRegionData InitDuplicateVariantSearch::getFileNameInfo(string s) {
    vcfRegionData regions;
    regions.filepath = s;

    int rangePos = nthLastIndexOf(1, s);
    string range = s.substr(rangePos + 1, s.length() - rangePos);
    int chromPos = nthLastIndexOf(3, s) + 1;
    string chrom = s.substr(chromPos, nthLastIndexOf(2, s) - chromPos);
    
    // This will convert chromosome 0-23 to a number and
    // chromosome 'X'and 'Y' to an ASCII integer representave
    if (chrom.length() == 1 && chrom.c_str()[0] > '9') {
        regions.chrom = chrom.c_str()[0];
    } else {
        regions.chrom = generalutils::fast_atoi<uint16_t>(chrom.c_str(), chrom.length());
    }

    string startRange = range.substr(0, range.find('-'));
    string endRange = range.substr(range.find('-') + 1, range.size());
    
    regions.startRange = generalutils::fast_atoi<uint64_t>(startRange.c_str(), startRange.length());
    regions.endRange = generalutils::fast_atoi<uint64_t>(endRange.c_str(), endRange.length());
    return regions;
}

void InitDuplicateVariantSearch::createChromRegionsMap(map<uint16_t, range> &chromLookup, vcfRegionData &insertItem) {
    if (chromLookup.count(insertItem.chrom) == 0) {  // If we havent seen this chrom before, add a record.
        chromLookup[insertItem.chrom] = range{ insertItem.startRange, insertItem.endRange };
    } else {
        if (chromLookup[insertItem.chrom].start > insertItem.startRange) {
            chromLookup[insertItem.chrom].start = insertItem.startRange;
        }
        if (chromLookup[insertItem.chrom].end < insertItem.endRange) {
            chromLookup[insertItem.chrom].end = insertItem.endRange;
        }
    }
    // cout << insertItem.filepath << " Chrom: " << (int)(insertItem.chrom) << " Start: " << (int)(insertItem.startRange) << " End: " << (int)(insertItem.endRange) << endl;
}

void InitDuplicateVariantSearch::filterChromAndRange(
    vector<vcfRegionData> &currentSearchTargets,
    vector<vcfRegionData> &regionData,
    uint16_t chrom,
    uint64_t start,
    uint64_t end
) {
    for (vcfRegionData rd : regionData) {
        bool isSameChrom = rd.chrom == chrom;
        bool isInRange = (
            (rd.startRange <= start && start <= rd.endRange) || // If the start point lies withn the range
            (rd.startRange <= end && end <= rd.endRange) || // If the end point lies withn the range
            (start < rd.startRange && rd.endRange < end) // If the start and end point encompass the range
        );

        if (isSameChrom && isInRange) {
            currentSearchTargets.push_back(rd);
        }
    }
};

    
InitDuplicateVariantSearch::InitDuplicateVariantSearch(Aws::S3::S3Client s3C, Aws::SNS::SNSClient const& snsC):
    s3Client(s3C),
    snsClient(snsC)
{}

void InitDuplicateVariantSearch::initDuplicateVariantSearch(string bucket) {
    vector<string> s3Objects = retrieveS3Objects(bucket, s3Client);
    map<uint16_t, range> chromLookup;
    map<string, size_t> duplicatesCount;

    vector<vcfRegionData> regionData;
    for (Aws::String filepath : s3Objects) {
        regionData.push_back(getFileNameInfo(filepath));
        createChromRegionsMap(chromLookup, regionData.back());
    }

    for (auto const& [chrom, reg]: chromLookup) {
        if (reg.end < reg.start) {
            throw runtime_error("logic error: region end is greater than region start");
        }

        for (uint64_t rangeStart = reg.start; rangeStart <= reg.end; rangeStart+=VCF_SEARCH_BASE_PAIR_RANGE) {
            uint64_t rangeEnd = rangeStart + VCF_SEARCH_BASE_PAIR_RANGE > reg.end ? reg.end : rangeStart + VCF_SEARCH_BASE_PAIR_RANGE - 1;
            cout << rangeStart << " " << rangeEnd << endl;
        
            Aws::Utils::Json::JsonValue vcfWindow;
            vcfWindow.WithString("bucket", bucket);
            vcfWindow.WithInt64("rangeStart", rangeStart);
            vcfWindow.WithInt64("rangeEnd", rangeEnd);
            vcfWindow.WithInteger("chrom", chrom);
            awsutils::publishSnsRequest(snsClient, "DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN", vcfWindow);
        }
    }
}
