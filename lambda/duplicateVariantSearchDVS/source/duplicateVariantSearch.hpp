#pragma once

#include <iostream>
#include <stdint.h>
#include <math.h>
#include <algorithm>
#include <iomanip>
#include <aws/dynamodb/DynamoDBClient.h>
#include <aws/dynamodb/model/UpdateItemRequest.h>
#include <aws/dynamodb/model/GetItemRequest.h>

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

    void updateVariantCounts(int64_t finalTally);
    int64_t updateVariantDuplicates(size_t totalCount);

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
    void searchForDuplicates();
};