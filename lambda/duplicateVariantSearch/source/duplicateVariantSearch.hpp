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
    deque<deque<generalutils::vcfData>> _fileLookup;
    map<string, deque<size_t>> _duplicates = {};
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
    vector<generalutils::vcfData> streamS3Outcome(Aws::S3::Model::GetObjectOutcome &response);
    static bool comparePos(generalutils::vcfData const &i, uint64_t j);
    std::deque<generalutils::vcfData>::iterator searchForPosition(uint64_t pos, deque<generalutils::vcfData> &fileData, size_t offset);
    static bool isADuplicate(generalutils::vcfData &a, generalutils::vcfData &b);
    static bool containsExistingFilepath(deque<size_t> &existingFilepaths, size_t filepath);
    static string to_zero_lead(const uint64_t value, const unsigned precision);
    size_t searchForDuplicates();
    void compareFiles(size_t j, size_t m);
};