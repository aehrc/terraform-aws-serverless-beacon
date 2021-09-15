#pragma once

#include <iostream>
#include <queue>
#include <stdint.h>
#include <math.h>
#include <algorithm>
#include <iomanip>

#include "readVcfData.hpp"

struct range {
    uint64_t start;
    uint64_t end;
};

class DuplicateVariantSearch {
    private:
    Aws::S3::S3Client _s3Client;
    Aws::String _bucket;
    uint64_t _rangeStart;
    uint64_t _rangeEnd;
    uint16_t _chrom;
    Aws::Utils::Array<Aws::Utils::Json::JsonView> _targetFilepaths;

    vector<string> retrieveS3Objects();
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
    DuplicateVariantSearch(
        Aws::S3::S3Client client,
        Aws::String bucket,
        uint64_t rangeStart,
        uint64_t rangeEnd,
        uint16_t chrom,
        Aws::Utils::Array<Aws::Utils::Json::JsonView> targetFilepaths
    );
    vector<generalutils::vcfData> streamS3Outcome(Aws::S3::Model::GetObjectOutcome &response);
    static bool comparePos(generalutils::vcfData const &i, uint64_t j);
    std::vector<generalutils::vcfData>::iterator searchForPosition(uint64_t pos, vector<generalutils::vcfData> &fileData);
    static bool isADuplicate(generalutils::vcfData *a, generalutils::vcfData *b);
    static bool containsExistingFilepath(vector<string> &existingFilepaths, string filepath);
    static string to_zero_lead(const uint64_t value, const unsigned precision);
    int searchForDuplicates();

};