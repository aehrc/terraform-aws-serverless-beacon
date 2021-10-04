#pragma once

#include <iostream>
#include <deque>
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
    static size_t compareFiles(
        uint64_t rangeStart,
        uint64_t rangeEnd,
        uint64_t targetFilepathsLength,
        deque<deque<generalutils::vcfData>> &fileLookup
    );
    inline static deque<generalutils::vcfData>::iterator searchForPosition(uint64_t pos, deque<generalutils::vcfData> &fileData, size_t offset);
    inline static bool comparePos(generalutils::vcfData const &i, uint64_t j);
    inline static bool isADuplicate(generalutils::vcfData &a, generalutils::vcfData &b);
    inline static bool containsExistingFilepath(deque<size_t> &existingFilepaths, size_t filepath);
    inline static string to_zero_lead(const uint64_t value, const unsigned precision);
    vector<generalutils::vcfData> streamS3Outcome(Aws::S3::Model::GetObjectOutcome &response);
    size_t searchForDuplicates();
};