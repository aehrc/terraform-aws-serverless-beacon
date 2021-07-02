#include <array>
#include <fstream>
#include <iostream>
#include <vector>

#include <aws/core/Aws.h>
#include <aws/core/auth/AWSCredentialsProvider.h>
#include <aws/core/client/ClientConfiguration.h>
#include <aws/core/platform/Environment.h>
#include <aws/core/utils/json/JsonSerializer.h>
#include <aws/dynamodb/DynamoDBClient.h>
#include <aws/dynamodb/model/UpdateItemRequest.h>
#include <aws/lambda-runtime/runtime.h>
#include <aws/s3/S3Client.h>
#include <aws/s3/model/GetObjectRequest.h>

#include "fast_atoi.h"
#include "GzipReader.h"


constexpr const char* TAG = "LAMBDA_ALLOC";
constexpr uint_fast32_t BGZIP_MAX_BLOCKSIZE = 65536;
constexpr const char* CHUNK_FILENAME = "/tmp/vcf_chunk.gz";
constexpr unsigned READER_CHUNK_SIZE = 1048576;

struct VcfChunk
{
    const uint_fast64_t startCompressed;
    const uint_fast16_t startUncompressed;
    const uint_fast64_t endCompressed;
    const uint_fast16_t endUncompressed;
    VcfChunk(uint64_t virtualStart, uint64_t virtualEnd)
    :startCompressed(virtualStart >> 16), startUncompressed(virtualStart & 0xffff), endCompressed(virtualEnd >> 16), endUncompressed(virtualEnd & 0xffff) {}
};


void add_counts(GzipReader& reader, uint_fast64_t& numCalls, uint_fast64_t& numVariants)
{
    constexpr const char* acTag = "AC=";
    constexpr const char* anTag = "AN=";
    bool foundAc = false;
    bool foundAn = false;
    // Skip to info section, we want AC and AN
    reader.skipPast<7>('\t');
    do
    {
        const char lastChar = reader.readPastDifferentChars(';', '\t');
        if (lastChar == '\0')
        {
            // EOF in the middle of INFO, don't include this
            break;
        }
        const size_t numChars = reader.getCharactersInRead();
        if (numChars >= 4)
        {
            // Could be AC=x or AN=x
            const char* firstChar_p = reader.getStartOfRead();
            if (memcmp(firstChar_p, acTag, 3) == 0)
            {
                foundAc = true;
                numVariants += 1;
                for (size_t j = 3; j < numChars; ++j)
                {
                    // Number of variants should be 1 more than the number of commas
                    if (*(firstChar_p + j) == ',')
                    {
                        numVariants += 1;
                    }
                }
            } else if (memcmp(firstChar_p, anTag, 3) == 0) {
                foundAn = true;
                numCalls += atoui64(firstChar_p+3, numChars-3);
            }
        }
        if (lastChar == '\t' && !(foundAc && foundAn))
        {
            std::cout << "Did not find either AC or AN. AC found: " << foundAc << ". AN found: " << foundAn << std::endl;
            break;
        }
    } while (!(foundAc && foundAn));
}

Aws::String bundle_response(Aws::String const& body, int statusCode)
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


Aws::String get_chunk(Aws::String bucket, Aws::String key, Aws::S3::S3Client const& s3Client, VcfChunk chunk)
{
    Aws::String byteRange = "bytes=" + std::to_string(chunk.startCompressed) + "-" + std::to_string(chunk.endCompressed + BGZIP_MAX_BLOCKSIZE);
    Aws::S3::Model::GetObjectRequest request;
    request.WithBucket(bucket).WithKey(key).WithRange(byteRange);
    request.SetResponseStreamFactory([](){
        return Aws::New<Aws::FStream>(
            TAG, CHUNK_FILENAME, std::ios_base::out | std::ios_base::binary | std::ios_base::trunc
        );
    });
    std::cout << "Attempting to download s3://" << bucket << "/" << key << " with byterange: \"" << byteRange << "\"" << std::endl;
    Aws::S3::Model::GetObjectOutcome response = s3Client.GetObject(request);
    if (response.IsSuccess()) {
        std::cout << "Chunk download complete." << std::endl;
        GzipReader gzipReader(READER_CHUNK_SIZE);
        std::cout << "Opening reader..." << std::endl;
        gzipReader.open(CHUNK_FILENAME);
        if (!gzipReader.isGood())
        {
            std::cout << "reader isn't good, exiting..." << std::endl;
            return "";
        }
        std::cout << "offset: " << gzoffset(gzipReader.inFile_gz) << std::endl;
        std::cout << "Seeking to " << chunk.startUncompressed << std::endl;
        gzipReader.seek(chunk.startUncompressed);
        std::cout << "offset: " << gzoffset(gzipReader.inFile_gz) << std::endl;
        uint_fast64_t numCalls = 0;
        uint_fast64_t numVariants = 0;
        add_counts(gzipReader, numCalls, numVariants);
        uint_fast64_t numRecords = 1;
        const uint_fast64_t charsToSkip = gzipReader.readPastAndCountChars('\n');
        std::cout << "charsToSkip: " << charsToSkip << std::endl;
        while (gzipReader.isGood())
        {
            add_counts(gzipReader, numCalls, numVariants);
            ++numRecords;
            gzipReader.seek(charsToSkip);
            gzipReader.skipPast<1>('\n');
        }
        std::cout << "offset: " << gzoffset(gzipReader.inFile_gz) << std::endl;
        int close_response = gzipReader.close();
        std::cout << "Closed file with code " << close_response << std::endl;
        return "numCalls: " + std::to_string(numCalls) + ", numRecords: " + std::to_string(numRecords) + ", numVariants: " + std::to_string(numVariants);
    }
    return "";
}


Aws::String get_message_string(aws::lambda_runtime::invocation_request const& req)
{
    Aws::Utils::Json::JsonValue json(req.payload);
    return json.View().GetArray("Records").GetItem(0).GetObject("Sns").GetString("Message");
}

static aws::lambda_runtime::invocation_response my_handler(aws::lambda_runtime::invocation_request const& req,
    Aws::S3::S3Client const& s3Client)
{
    Aws::String messageString = get_message_string(req);
    std::cout << "Message is: " << messageString << std::endl;
    Aws::Utils::Json::JsonValue message(messageString);
    Aws::Utils::Json::JsonView messageView = message.View();
    Aws::String location = messageView.GetString("location");
    int64_t virtualStart = messageView.GetInt64("virtual_start");
    int64_t virtualEnd = messageView.GetInt64("virtual_end");
    VcfChunk chunk(virtualStart, virtualEnd);

    // Get bucket and key from location
    Aws::String bucket = "";
    Aws::String key = "";
    for (size_t j = 5; j < location.length(); ++j)
    {
        if (location[j] == '/')
        {
            bucket = location.substr(5, j-5);
            key = location.substr(j+1);
            break;
        }
    }
    Aws::String output = get_chunk(bucket, key, s3Client, chunk);
    std::cout << "get_chunk output:" << std::endl << output << std::endl;

    return aws::lambda_runtime::invocation_response::success(bundle_response("Success", 200), "application/json");
    
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
        auto handler_fn = [&s3Client](aws::lambda_runtime::invocation_request const& req) {
            std::cout << "Event Recived: " << req.payload << std::endl;
            return my_handler(req, s3Client);
            std::cout.flush();
        };
        aws::lambda_runtime::run_handler(handler_fn);
    }
    Aws::ShutdownAPI(options);
    return 0;
}
