#include <iostream>
#include <queue>
#include <stdint.h>
#include <zlib.h>
#include <awsutils.hpp>

#include <aws/core/Aws.h>
#include <aws/core/auth/AWSCredentialsProvider.h>
#include <aws/core/client/ClientConfiguration.h>
#include <aws/core/platform/Environment.h>
#include <aws/core/utils/json/JsonSerializer.h>
#include <aws/core/utils/memory/stl/AWSVector.h>
#include <aws/core/utils/stream/PreallocatedStreamBuf.h>
#include <aws/dynamodb/DynamoDBClient.h>
#include <aws/dynamodb/model/ScanRequest.h>
#include <aws/dynamodb/model/UpdateItemRequest.h>
#include <aws/lambda-runtime/runtime.h>
#include <aws/s3/S3Client.h>
#include <aws/s3/model/GetObjectRequest.h>
#include <aws/sns/SNSClient.h>
#include <aws/sns/model/PublishRequest.h>
#include <aws/s3/model/PutObjectRequest.h>

using namespace std;

constexpr const char* TAG = "LAMBDA_ALLOC";
constexpr uint_fast32_t BGZIP_MAX_BLOCKSIZE = 65536;
constexpr uint_fast8_t BGZIP_BLOCK_START_LENGTH = 4;
constexpr const uint8_t BGZIP_BLOCK_START[BGZIP_BLOCK_START_LENGTH] = {0x1f, 0x8b, 0x08, 0x04};
constexpr uint_fast8_t BGZIP_FIELD_START_LENGTH = 4;
constexpr const uint8_t BGZIP_FIELD_START[BGZIP_FIELD_START_LENGTH] = {'B', 'C', 0x02, 0x00};
constexpr uint_fast16_t DOWNLOAD_SLICE_NUM = 4;  // Maximum number of concurrent downloads
constexpr uint_fast64_t MAX_DOWNLOAD_SLICE_SIZE = 100000000;
constexpr uint_fast8_t XLEN_OFFSET = 10;
constexpr uint VCF_S3_OUTPUT_SIZE_LIMIT = 10000000;

Aws::String bundleResponse(Aws::String const& body, int statusCode)
{
    Aws::String outputString = "{\"headers\": {\"Access-Control-Allow-Origin\": \"*\"}, \"statusCode\": ";
    outputString.append(std::to_string(statusCode));
    outputString.append(", \"body\": \"");
    for (char c : body)
    {
        if (c == '"' || c == '\\')
        {
            outputString.push_back('\\');
        }
        outputString.push_back(c);
    }
    outputString.append("\"}");
    return outputString;
}



static aws::lambda_runtime::invocation_response lambdaHandler(aws::lambda_runtime::invocation_request const& req,
    Aws::S3::S3Client const& s3Client, Aws::DynamoDB::DynamoDBClient const& dynamodbClient, Aws::SNS::SNSClient const& snsClient)
{
    Aws::String messageString = awsutils::getMessageString(req);
    std::cout << "Message is: " << messageString << std::endl;
    Aws::Utils::Json::JsonValue message(messageString);
    Aws::Utils::Json::JsonView messageView = message.View();

    return aws::lambda_runtime::invocation_response::success(bundleResponse("Success", 200), "application/json");
}

int main()
{
    Aws::SDKOptions options;
    Aws::InitAPI(options);
    {
        Aws::Client::ClientConfiguration config;
        config.region = Aws::Environment::GetEnv("AWS_REGION");
        config.caFile = "/etc/pki/tls/certs/ca-bundle.crt";

        auto credentialsProvider = Aws::MakeShared<Aws::Auth::EnvironmentAWSCredentialsProvider>(TAG);
        Aws::DynamoDB::DynamoDBClient dynamodbClient(credentialsProvider, config);
        Aws::S3::S3Client s3Client(credentialsProvider, config);
        Aws::SNS::SNSClient snsClient(credentialsProvider, config);
        auto handlerFunction = [&s3Client, &dynamodbClient, &snsClient](aws::lambda_runtime::invocation_request const& req) {
            std::cout << "Event Recived: " << req.payload << std::endl;
            return lambdaHandler(req, s3Client, dynamodbClient, snsClient);
            std::cout.flush();
        };
        aws::lambda_runtime::run_handler(handlerFunction);
    }
    Aws::ShutdownAPI(options);
    return 0;
}
