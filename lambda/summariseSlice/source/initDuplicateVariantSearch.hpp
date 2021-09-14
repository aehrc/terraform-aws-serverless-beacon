#pragma once

#include <stdint.h>
#include <string>
#include <awsutils.hpp>
#include <aws/s3/S3Client.h>
#include <generalutils.hpp>

#define VCF_SEARCH_BASE_PAIR_RANGE 5000

struct vcfRegionData  { 
    string filepath; 
    uint16_t chrom;
    uint64_t startRange;
    uint64_t endRange;
};

struct range {
    uint64_t start;
    uint64_t end;
};

class InitDuplicateVariantSearch {
    private:
    Aws::S3::S3Client s3Client;
    Aws::SNS::SNSClient const& snsClient;

    vector<string> retrieveS3Objects(string bucket, Aws::S3::S3Client const& s3Client);
    static int nthLastIndexOf(int nth, string str);
    vcfRegionData getFileNameInfo(string s);
    void createChromRegionsMap(map<uint16_t, range> &chromLookup, vcfRegionData &insertItem);
    void filterChromAndRange(
        vector<vcfRegionData> &currentSearchTargets,
        vector<vcfRegionData> &regionData,
        uint16_t chrom,
        uint64_t start,
        uint64_t end
    );

    public:
    InitDuplicateVariantSearch(Aws::S3::S3Client s3C, Aws::SNS::SNSClient const& snsC);
    void initDuplicateVariantSearch(string bucket);
};
