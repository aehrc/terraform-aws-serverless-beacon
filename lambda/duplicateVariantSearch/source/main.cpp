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



static aws::lambda_runtime::invocation_response lambdaHandler(aws::lambda_runtime::invocation_request const& req, Aws::S3::S3Client &s3Client)
{
    Aws::String messageString = awsutils::getMessageString(req);
    std::cout << "Message is: " << messageString << std::endl;
    Aws::Utils::Json::JsonValue message(messageString);
    Aws::Utils::Json::JsonView messageView = message.View();

    Aws::String bucket = messageView.GetString("bucket");
    uint64_t rangeStart = messageView.GetInt64("rangeStart");
    uint64_t rangeEnd = messageView.GetInt64("rangeEnd");
    uint16_t chrom = messageView.GetInteger("chrom");
    Aws::Utils::Array<Aws::Utils::Json::JsonView> targetFilepaths = messageView.GetArray("targetFilepaths");

    DuplicateVariantSearch(s3Client, bucket, rangeStart, rangeEnd, chrom, targetFilepaths).searchForDuplicates();

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
        auto handlerFunction = [&s3Client](aws::lambda_runtime::invocation_request const& req) {
            std::cout << "Event Received: " << req.payload << std::endl;
            return lambdaHandler(req, s3Client);
            std::cout.flush();
        };
        aws::lambda_runtime::run_handler(handlerFunction);
    }
    Aws::ShutdownAPI(options);
    return 0;
}
