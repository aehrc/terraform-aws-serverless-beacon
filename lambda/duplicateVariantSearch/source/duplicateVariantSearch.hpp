#pragma once

#include <iostream>
#include <queue>
#include <stdint.h>
#include <math.h>
#include <algorithm>
#include <iomanip>
#include <aws/dynamodb/DynamoDBClient.h>
#include <aws/dynamodb/model/UpdateItemRequest.h>

#include "readVcfData.hpp"

struct range {
    uint64_t start;
    uint64_t end;
};

class DuplicateVariantSearch {
    private:
    Aws::S3::S3Client &_s3Client;
    Aws::DynamoDB::DynamoDBClient &_dynamodbClient;
    Aws::String _bucket;
    uint64_t _rangeStart;
    uint64_t _rangeEnd;
    Aws::String _contig;
    Aws::Utils::Array<Aws::Utils::Json::JsonView> _targetFilepaths;
    Aws::String _dataset;

    vector<string> retrieveS3Objects();
    vcfRegionData getFileNameInfo(string s);
    // void createContigRegionsMap(map<uint16_t, range> &chromLookup, vcfRegionData &insertItem);
    // void filterChromAndRange(
    //     vector<vcfRegionData> &currentSearchTargets,
    //     vector<vcfRegionData> &regionData,
    //     uint16_t contig,
    //     uint64_t start,
    //     uint64_t end
    // );
    bool updateVariantDuplicates(int64_t totalCount);

    public:
    DuplicateVariantSearch(
        Aws::S3::S3Client &client,
        Aws::DynamoDB::DynamoDBClient &dynamodbClient,
        Aws::String bucket,
        uint64_t rangeStart,
        uint64_t rangeEnd,
        Aws::String contig,
        Aws::Utils::Array<Aws::Utils::Json::JsonView> targetFilepaths,
        Aws::String dataset
    );
    vector<generalutils::vcfData> streamS3Outcome(Aws::S3::Model::GetObjectOutcome &response);
    static bool comparePos(generalutils::vcfData const &i, uint64_t j);
    std::vector<generalutils::vcfData>::iterator searchForPosition(uint64_t pos, vector<generalutils::vcfData> &fileData);
    static bool isADuplicate(generalutils::vcfData *a, generalutils::vcfData *b);
    static bool containsExistingFilepath(vector<string> &existingFilepaths, string filepath);
    static string to_zero_lead(const uint64_t value, const unsigned precision);
    size_t searchForDuplicates();

};