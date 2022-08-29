#pragma once

#include <iostream>
#include <string>
#include <sstream>
#include <algorithm>
#include <iterator>
#include <iostream>

#include <aws/core/Aws.h>
#include <aws/core/auth/AWSCredentialsProvider.h>
#include <aws/core/client/ClientConfiguration.h>
#include <aws/core/platform/Environment.h>
#include <aws/core/utils/json/JsonSerializer.h>
#include <aws/lambda-runtime/runtime.h>
#include <aws/s3/S3Client.h>
#include <aws/s3/model/ListObjectsV2Request.h>
#include <aws/s3/model/GetObjectRequest.h>
#include <aws/sns/SNSClient.h>
#include <aws/sns/model/PublishRequest.h>

using namespace std;

class awsutils {
    public:
    // S3 utils
    static Aws::S3::S3Client getNewClient();
    static vector<string> retrieveBucketObjectKeys(Aws::String bucket);
    static Aws::S3::Model::GetObjectOutcome getS3Object(Aws::String bucket, Aws::String key);
    // JSON utils
    static Aws::String getMessageString(aws::lambda_runtime::invocation_request const& req);
    static Aws::String getMessageString(string const &req);
    // SNS utils
    static void publishSnsRequest(Aws::SNS::SNSClient const& snsClient, const char * topicArn,  Aws::Utils::Json::JsonValue message);
};
