#include "duplicateVariantSearch.hpp"

#include <aws/core/Aws.h>
#include <aws/core/auth/AWSCredentialsProvider.h>
#include <aws/core/platform/Environment.h>

using namespace std;

constexpr const char* TAG = "LAMBDA_ALLOC";
constexpr int VCF_SEARCH_BASE_PAIR_RANGE = 5000;

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



// static aws::lambda_runtime::invocation_response lambdaHandler(aws::lambda_runtime::invocation_request const& req, Aws::S3::S3Client &s3Client, Aws::DynamoDB::DynamoDBClient &dynamodbClient)
// {
//     Aws::String messageString = awsutils::getMessageString(req);
//     std::cout << "Message is: " << messageString << std::endl;
//     Aws::Utils::Json::JsonValue message(messageString);
//     Aws::Utils::Json::JsonView messageView = message.View();

//     Aws::String bucket = messageView.GetString("bucket");
//     uint64_t rangeStart = messageView.GetInt64("rangeStart");
//     uint64_t rangeEnd = messageView.GetInt64("rangeEnd");
//     Aws::String contig = messageView.GetString("contig");
//     Aws::Utils::Array<Aws::Utils::Json::JsonView> targetFilepaths = messageView.GetArray("targetFilepaths");
//     Aws::String dataset = messageView.GetString("dataset");

//     DuplicateVariantSearch(s3Client, dynamodbClient, bucket, rangeStart, rangeEnd, contig, targetFilepaths, dataset).searchForDuplicates();

//     return aws::lambda_runtime::invocation_response::success(bundleResponse("Success", 200), "application/json");
// }

// int main()
// {
//     Aws::SDKOptions options;
//     Aws::InitAPI(options);
//     {
//         Aws::Client::ClientConfiguration config;
//         config.region = Aws::Environment::GetEnv("AWS_REGION");
//         config.caFile = "/etc/pki/tls/certs/ca-bundle.crt";

//         auto credentialsProvider = Aws::MakeShared<Aws::Auth::EnvironmentAWSCredentialsProvider>(TAG);

//         auto handlerFunction = [&credentialsProvider, &config](aws::lambda_runtime::invocation_request const& req) {
//             std::cout << "Event Received: " << req.payload << std::endl;
//             Aws::S3::S3Client s3Client(credentialsProvider, config);
//             Aws::DynamoDB::DynamoDBClient dynamodbClient(credentialsProvider, config);
//             return lambdaHandler(req, s3Client, dynamodbClient);
//             std::cout.flush();
//         };
//         aws::lambda_runtime::run_handler(handlerFunction);
//     }
//     Aws::ShutdownAPI(options);
//     return 0;
// }

static aws::lambda_runtime::invocation_response lambdaHandler(Aws::S3::S3Client &s3Client, Aws::DynamoDB::DynamoDBClient &dynamodbClient)
{
    Aws::String messageString = "{\n    \"bucket\": \"sbeacon20220803055006699700000001\",\n    \"rangeStart\": 182026241,\n    \"rangeEnd\": 198311936,\n    \"contig\": \"2\",\n    \"targetFilepaths\": [\n        \"vcf-summaries/contig/2/vcf-simulations%population-1-chr2-100-samples-seed-0-2-full/regions/182026241-190169088-317571072\",\n        \"vcf-summaries/contig/2/vcf-simulations%population-1-chr2-100-samples-seed-0-2-full/regions/190169089-198311936-317571072\"\n    ],\n    \"dataset\": \"pop-1-wic\"\n}";
    std::cout << "Message is: " << messageString << std::endl;
    Aws::Utils::Json::JsonValue message(messageString);
    Aws::Utils::Json::JsonView messageView = message.View();

    Aws::String bucket = messageView.GetString("bucket");
    uint64_t rangeStart = messageView.GetInt64("rangeStart");
    uint64_t rangeEnd = messageView.GetInt64("rangeEnd");
    Aws::String contig = messageView.GetString("contig");
    Aws::Utils::Array<Aws::Utils::Json::JsonView> targetFilepaths = messageView.GetArray("targetFilepaths");
    Aws::String dataset = messageView.GetString("dataset");

    DuplicateVariantSearch(s3Client, dynamodbClient, bucket, rangeStart, rangeEnd, contig, targetFilepaths, dataset).searchForDuplicates();

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
        Aws::S3::S3Client s3Client(credentialsProvider, config);
        Aws::DynamoDB::DynamoDBClient dynamodbClient(credentialsProvider, config);
        lambdaHandler(s3Client, dynamodbClient);
    }
    Aws::ShutdownAPI(options);
    return 0;
}
