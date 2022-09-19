#include <iostream>
#include <queue>
#include <stdint.h>
#include <stdlib.h>
#include <zlib.h>
#include <regex>
#include <generalutils.hpp>
#include <gzip.hpp>
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

#include "fast_atoi.h"
#include "stopwatch.h"
#include "vcf_chunk_reader.h"
#include "constants.h"
#include "write_data_to_s3.h"

// #define INCLUDE_STOP_WATCH
// #define DEBUG_ON

const char *DATASETS_TABLE = getenv("DYNAMO_DATASETS_TABLE");
const char *ASSEMBLY_GSI = getenv("ASSEMBLY_GSI");
const char *SUMMARISE_DATASET_SNS_TOPIC_ARN = getenv("SUMMARISE_DATASET_SNS_TOPIC_ARN");
const char *VCF_SUMMARIES_TABLE = getenv("DYNAMO_VCF_SUMMARIES_TABLE");

using namespace std;

struct RegionStats
{
    uint_fast64_t numVariants;
    uint_fast64_t numCalls;
    RegionStats()
        : numVariants(0), numCalls(0) {}
};

// Function assumes reader is at the INFO part of the header
void addCounts(VcfChunkReader &reader, RegionStats &regionStats)
{
    constexpr const char *acTag = "AC=";
    constexpr const char *anTag = "AN=";
    bool foundAc = false;
    bool foundAn = false;

    do
    {
        const char lastChar = reader.readPastChars<';', '\t'>();
        if (lastChar == '\0')
        {
            // EOF in the middle of INFO, don't include this
            break;
        }
        const size_t numChars = reader.getReadLength();
        if (numChars >= 4)
        {
            // Could be AC=x or AN=x
            const char *firstChar_p = reader.getReadStart();
            if (memcmp(firstChar_p, acTag, 3) == 0)
            {
                foundAc = true;
                regionStats.numVariants += 1;
                for (size_t j = 3; j < numChars; ++j)
                {
                    // Number of variants should be 1 more than the number of commas
                    if (*(firstChar_p + j) == ',')
                    {
                        regionStats.numVariants += 1;
                    }
                }
            }
            else if (memcmp(firstChar_p, anTag, 3) == 0)
            {
                foundAn = true;
                regionStats.numCalls += atoui64(firstChar_p + 3, (uint8_t)(numChars)-3);
            }
#ifdef DEBUG_ON
            else
            {
                std::cout << "Found unrecognised INFO field: \"" << Aws::String(firstChar_p, numChars) << "\" with lastChar: \"" << lastChar << "\" and charPos: " << reader.charPos << std::endl;
            }
#endif
        }
#ifdef DEBUG_ON
        else
        {
            std::cout << "Found short unrecognised INFO field: \"" << Aws::String(reader.getReadStart(), numChars) << "\" with lastChar: \"" << lastChar << "\" and charPos: " << reader.charPos << std::endl;
        }
#endif
        if (lastChar == '\t' && !(foundAc && foundAn))
        {
            std::cout << "Did not find either AC or AN. AC found: " << foundAc << ". AN found: " << foundAn << std::endl;
            break;
        }
    } while (!(foundAc && foundAn));
}

Aws::String bundleResponse(Aws::String const &body, int statusCode)
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

Aws::Vector<Aws::String> getAffectedDatasets(Aws::DynamoDB::DynamoDBClient const &dynamodbClient, Aws::String location)
{
    Aws::DynamoDB::Model::ScanRequest request;
    request.SetTableName(DATASETS_TABLE);
    request.SetIndexName(ASSEMBLY_GSI);
    request.SetProjectionExpression("id");
    request.SetFilterExpression("contains(vcfLocations, :location)");
    Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> expressionAttributeValues;
    Aws::DynamoDB::Model::AttributeValue locationValue;
    locationValue.SetS(location);
    expressionAttributeValues[":location"] = locationValue;
    request.SetExpressionAttributeValues(expressionAttributeValues);
    Aws::Vector<Aws::String> datasetIds;
    do
    {
        std::cout << "Calling dynamodb::Scan with vcfLocations contains \"" << location << "\"" << std::endl;
        const Aws::DynamoDB::Model::ScanOutcome &result = dynamodbClient.Scan(request);
        if (result.IsSuccess())
        {
            std::cout << "Got ids [";
            for (const Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> &item : result.GetResult().GetItems())
            {
                auto datasetIdItr = item.find("id");
                if (datasetIdItr != item.end())
                {
                    datasetIds.push_back(datasetIdItr->second.GetS());
                    std::cout << "\"" << datasetIds.back() << "\", ";
                }
                else
                {
                    // Why is there a dataset with no id here? Let's not let it ruin the others updating.
                    std::cout << "None (ignored), ";
                }
            }
            std::cout << "]" << std::endl;
            const Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> &lastEvaluatedKey = result.GetResult().GetLastEvaluatedKey();
            if (lastEvaluatedKey.empty())
            {
                std::cout << "No more ids to find" << std::endl;
                return datasetIds;
            }
            else
            {
                std::cout << "More ids to find, querying for the rest..." << std::endl;
                request.SetExclusiveStartKey(lastEvaluatedKey);
                continue;
            }
        }
        else
        {
            const Aws::DynamoDB::DynamoDBError error = result.GetError();
            std::cout << "Scan was not successful, received error: " << error.GetMessage() << std::endl;
            if (error.ShouldRetry())
            {
                std::cout << "Retrying after 1 second..." << std::endl;
                std::this_thread::sleep_for(std::chrono::seconds(1));
                continue;
            }
            else
            {
                std::cout << "Not Retrying." << std::endl;
                return datasetIds;
            }
        }
    } while (true);
}

const RegionStats getRegionStats(Aws::String location, int64_t virtualStart, int64_t virtualEnd)
{
    VcfChunk chunk(virtualStart, virtualEnd);

    // Get bucket and key from location
    Aws::String bucket = "";
    Aws::String key = "";
    for (size_t j = 5; j < location.length(); ++j)
    {
        if (location[j] == '/')
        {
            bucket = location.substr(5, j - 5);
            key = location.substr(j + 1);
            break;
        }
    }
#ifdef INCLUDE_STOP_WATCH
    stop_watch s = stop_watch();
    s.start();
#endif
    VcfChunkReader vcfChunkReader(bucket, key, chunk);
    std::cout << "Loaded Reader" << std::endl << std::flush;
    writeDataToS3 s3Data = writeDataToS3(location);
    vcfChunkReader.readBlock<true>();
    std::cout << "Read block with " << vcfChunkReader.zStream.total_out << " bytes output." << std::endl;
    RegionStats regionStats = RegionStats();
    s3Data.recordHeader(vcfChunkReader);
    addCounts(vcfChunkReader, regionStats);
    // Count delimiters and use to calculate theoretical minimum line length.
    // Successive lines in the same chunk (and therefore contig) will not have less than this minimum,
    // unless the VCF is very contrived. But what if they do? How do we know, and what do we do in that case?
    uint_fast64_t skipSize = 2 * vcfChunkReader.skipPastAndCountChars('\n');
    std::cout << "vcfChunkReader skipSize: " << skipSize << std::endl;
    std::cout << "First record numVariants: " << regionStats.numVariants << " numCalls: " << regionStats.numCalls << std::endl;
    uint_fast32_t records = 1;
    while (vcfChunkReader.keepReading())
    {
        s3Data.recordHeader(vcfChunkReader);
        addCounts(vcfChunkReader, regionStats);
        vcfChunkReader.seek(skipSize);
        vcfChunkReader.skipPast<1, '\n'>();
        records += 1;
    }
#ifdef INCLUDE_STOP_WATCH
    s.stop();
    std::cout << "Finished processing " << vcfChunkReader.totalBytes << " bytes in " << s << " (" << 1000 * vcfChunkReader.totalBytes / s.nanoseconds << "MB/s)" << std::endl;
#endif
    std::cout << "vcfChunkReader read " << vcfChunkReader.reads << " blocks completely, found compressed size: " << vcfChunkReader.totalCSize << " and uncompressed size: " << vcfChunkReader.totalUSize << " with records: " << records << std::endl;
    std::cout << "numVariants: " << regionStats.numVariants << ", numCalls: " << regionStats.numCalls << std::endl;
    return regionStats;
}

void summariseDatasets(Aws::SNS::SNSClient const &snsClient, Aws::Vector<Aws::String> datasetIds)
{
    // TODO use the util here
    Aws::SNS::Model::PublishRequest request;
    request.SetTopicArn(SUMMARISE_DATASET_SNS_TOPIC_ARN);
    for (Aws::String &datasetId : datasetIds)
    {
        do
        {
            request.SetMessage(datasetId);
            std::cout << "Calling sns::Publish with TopicArn=\"" << request.GetTopicArn() << "\" and message=\"" << request.GetMessage() << "\"" << std::endl;
            Aws::SNS::Model::PublishOutcome result = snsClient.Publish(request);
            if (result.IsSuccess())
            {
                std::cout << "Successfully published" << std::endl;
                break;
            }
            else
            {
                const Aws::SNS::SNSError error = result.GetError();
                std::cout << "Publish was not successful, received error: " << error.GetMessage() << std::endl;
                if (error.ShouldRetry())
                {
                    std::cout << "Retrying after 1 second..." << std::endl;
                    std::this_thread::sleep_for(std::chrono::seconds(1));
                    continue;
                }
                else
                {
                    std::cout << "Not Retrying." << std::endl;
                    break;
                }
            }
        } while (true);
    }
}

bool updateFileInDataset(Aws::DynamoDB::DynamoDBClient const &dynamodbClient, Aws::String vcfLocation, Aws::String datasetId)
{
    Aws::DynamoDB::Model::UpdateItemRequest request;
    request.SetTableName(DATASETS_TABLE);
    Aws::DynamoDB::Model::AttributeValue keyValue;
    keyValue.SetS(datasetId);
    request.AddKey("id", keyValue);
    request.SetUpdateExpression("DELETE toUpdateFiles :vcfLocationSet");
    request.SetConditionExpression("contains(toUpdateFiles, :vcfLocation)");

    Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> expressionAttributeValues;

    Aws::DynamoDB::Model::AttributeValue vcfLocationSetValue;
    vcfLocationSetValue.SetSS(Aws::Vector<Aws::String>{vcfLocation});
    expressionAttributeValues[":vcfLocationSet"] = vcfLocationSetValue;

    Aws::DynamoDB::Model::AttributeValue vcfLocationValue;
    vcfLocationValue.SetS(vcfLocation);
    expressionAttributeValues[":vcfLocation"] = vcfLocationValue;

    request.SetExpressionAttributeValues(expressionAttributeValues);
    request.SetReturnValues(Aws::DynamoDB::Model::ReturnValue::UPDATED_NEW);
    do
    {
        std::cout << "Calling dynamodb::UpdateItem with key=\"" << datasetId << "\" and vcfLocation=\"" << vcfLocation << "\"" << std::endl;
        const Aws::DynamoDB::Model::UpdateItemOutcome &result = dynamodbClient.UpdateItem(request);
        if (result.IsSuccess())
        {
            const Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> newAttributes = result.GetResult().GetAttributes();
            std::cout << ", toUpdateFiles=";
            auto toUpdateItr = newAttributes.find("toUpdateFiles");
            if (toUpdateItr != newAttributes.end())
            {
                std::cout << "{";
                Aws::Vector<Aws::String> toUpdateNew = toUpdateItr->second.GetSS();
                for (Aws::String vcfLocationRemaining : toUpdateNew)
                {
                    std::cout << "\"" << vcfLocationRemaining << "\", ";
                }
                std::cout << "}";
            }
            std::cout << std::endl;
            return (toUpdateItr == newAttributes.end());
        }
        else
        {
            const Aws::DynamoDB::DynamoDBError error = result.GetError();
            std::cout << "Item was not updated, received error: " << error.GetMessage() << std::endl;
            if (error.ShouldRetry())
            {
                std::cout << "Retrying after 1 second..." << std::endl;
                std::this_thread::sleep_for(std::chrono::seconds(1));
                continue;
            }
            else
            {
                std::cout << "Not Retrying." << std::endl;
                return false;
            }
        }
    } while (true);
}

Aws::Vector<Aws::String> getDatasetsToUpdate(Aws::DynamoDB::DynamoDBClient const &dynamodbClient, Aws::String location, Aws::Vector<Aws::String> datasetIds)
{
    Aws::Vector<Aws::String> toUpdateIds;
    for (Aws::String datasetId : datasetIds)
    {
        if (updateFileInDataset(dynamodbClient, location, datasetId))
        {
            toUpdateIds.push_back(datasetId);
        }
    }
    return toUpdateIds;
}

bool updateVcfSummary(Aws::DynamoDB::DynamoDBClient const &dynamodbClient, Aws::String location, int64_t virtualStart, int64_t virtualEnd, RegionStats regionStats)
{
    Aws::DynamoDB::Model::UpdateItemRequest request;
    request.SetTableName(VCF_SUMMARIES_TABLE);
    Aws::DynamoDB::Model::AttributeValue keyValue;
    keyValue.SetS(location);
    request.AddKey("vcfLocation", keyValue);
    request.SetUpdateExpression("ADD variantCount :numVariants, callCount :numCalls DELETE toUpdate :sliceStringSet");
    request.SetConditionExpression("contains(toUpdate, :sliceString)");

    Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> expressionAttributeValues;

    Aws::DynamoDB::Model::AttributeValue numVariantsValue;
    numVariantsValue.SetN(to_string(regionStats.numVariants));
    expressionAttributeValues[":numVariants"] = numVariantsValue;

    Aws::DynamoDB::Model::AttributeValue numCallsValue;
    numCallsValue.SetN(static_cast<double>(regionStats.numCalls));
    expressionAttributeValues[":numCalls"] = numCallsValue;

    Aws::String sliceString = std::to_string(virtualStart) + "-" + std::to_string(virtualEnd);
    Aws::DynamoDB::Model::AttributeValue sliceStringSetValue;
    sliceStringSetValue.SetSS(Aws::Vector<Aws::String>{sliceString});
    expressionAttributeValues[":sliceStringSet"] = sliceStringSetValue;

    Aws::DynamoDB::Model::AttributeValue sliceStringValue;
    sliceStringValue.SetS(sliceString);
    expressionAttributeValues[":sliceString"] = sliceStringValue;

    request.SetExpressionAttributeValues(expressionAttributeValues);
    request.SetReturnValues(Aws::DynamoDB::Model::ReturnValue::UPDATED_NEW);
    do
    {
        std::cout << "Calling dynamodb::UpdateItem with key=\"" << location << "\" and sliceString=\"" << sliceString << "\"" << std::endl;
        const Aws::DynamoDB::Model::UpdateItemOutcome &result = dynamodbClient.UpdateItem(request);
        if (result.IsSuccess())
        {
            const Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> newAttributes = result.GetResult().GetAttributes();
            std::cout << ", callCount=";
            auto callCountItr = newAttributes.find("callCount");
            if (callCountItr != newAttributes.end())
            {
                std::cout << callCountItr->second.GetN();
            }
            std::cout << ", toUpdate=";
            auto toUpdateItr = newAttributes.find("toUpdate");
            if (toUpdateItr != newAttributes.end())
            {
                std::cout << "{";
                Aws::Vector<Aws::String> toUpdateNew = toUpdateItr->second.GetSS();
                for (Aws::String sliceStringRemaining : toUpdateNew)
                {
                    std::cout << "\"" << sliceStringRemaining << "\", ";
                }
                std::cout << "}";
            }
            std::cout << std::endl;
            return (toUpdateItr == newAttributes.end());
        }
        else
        {
            const Aws::DynamoDB::DynamoDBError error = result.GetError();
            std::cout << "Item was not updated, received error: " << error.GetMessage() << std::endl;
            if (error.ShouldRetry())
            {
                std::cout << "Retrying after 1 second..." << std::endl;
                std::this_thread::sleep_for(std::chrono::seconds(1));
                continue;
            }
            else
            {
                std::cout << "Not Retrying." << std::endl;
                return false;
            }
        }
    } while (true);
}

static aws::lambda_runtime::invocation_response lambdaHandler(
    aws::lambda_runtime::invocation_request const &req,
    // string const &req,
    Aws::DynamoDB::DynamoDBClient const &dynamodbClient,
    Aws::SNS::SNSClient const &snsClient)
{
    Aws::String messageString = awsutils::getMessageString(req);
    std::cout << "Message is: " << messageString << std::endl;
    Aws::Utils::Json::JsonValue message(messageString);
    Aws::Utils::Json::JsonView messageView = message.View();
    Aws::String location = messageView.GetString("location");
    int64_t virtualStart = messageView.GetInt64("virtual_start");
    int64_t virtualEnd = messageView.GetInt64("virtual_end");
    RegionStats regionStats = getRegionStats(location, virtualStart, virtualEnd);

    if (updateVcfSummary(dynamodbClient, location, virtualStart, virtualEnd, regionStats))
    {
        std::cout << "VCF has been completely summarised!" << std::endl;
        Aws::Vector<Aws::String> allDatasetIds = getAffectedDatasets(dynamodbClient, location);
        Aws::Vector<Aws::String> datasetsToUpdate = getDatasetsToUpdate(dynamodbClient, location, allDatasetIds);
        summariseDatasets(snsClient, datasetsToUpdate);
    }
    else
    {
        std::cout << "VCF has not yet been completely summarised." << std::endl;
    }
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
        auto handlerFunction = [&credentialsProvider, &config](aws::lambda_runtime::invocation_request const &req)
        {
            std::cout << "Event Received: " << req.payload << std::endl;
            Aws::DynamoDB::DynamoDBClient dynamodbClient(credentialsProvider, config);
            Aws::SNS::SNSClient snsClient(credentialsProvider, config);
            return lambdaHandler(req, dynamodbClient, snsClient);
            std::cout.flush();
        };
        aws::lambda_runtime::run_handler(handlerFunction);
    }
    // string req = "{\n    \"Records\": [\n        {\n            \"EventSource\": \"aws:sns\",\n            \"EventVersion\": \"1.0\",\n            \"EventSubscriptionArn\": \"arn:aws:sns:us-east-1:361439923243:summariseSlice:b9e01117-8264-4cd8-bfb3-631839f91403\",\n            \"Sns\": {\n                \"Type\": \"Notification\",\n                \"MessageId\": \"5fef7144-84a4-5213-a35a-2ac2a0ae0bd2\",\n                \"TopicArn\": \"arn:aws:sns:us-east-1:361439923243:summariseSlice\",\n                \"Subject\": null,\n                \"Message\": \"{\\\"location\\\": \\\"s3://vcf-simulations/population-1-chr21-100-samples-seed-0-21-full.vcf.gz\\\", \\\"virtual_start\\\": 3546251591680, \\\"virtual_end\\\": 5323904656990}\",\n                \"Timestamp\": \"2022-08-29T02:17:46.764Z\",\n                \"SignatureVersion\": \"1\",\n                \"Signature\": \"5C//p2CQG0peyIYWxHNN/HsYnmmTMw3XqV8tN5QhdQ+6mhcdIxpSlbOo7g5xWGmd+a4xb/HMDAG+og5iukio+7phPuLjfnYGhnAENBSTdgD/66GSSiBfgbV2I8cVyCsRh9SWAhE+/vIgmJnynp8gqE/LeVLfg+M+J1T5Pavv1jm4feHCUwaxd7RtynYvf8Nl6kXGfupRqxSJhDODaf59IL0M6Iyq+FvAkYIR9MMNypNGJ4UMDUcOlX+nbJDIzevehdBYnW8ryhCrPII+3tjVvRSe83gYc5yP/SCQkQZxQZlieH4ypEBXwMyyiqKd36AGAv20WEiDZss4yS19ckzihw==\",\n                \"SigningCertUrl\": \"https://sns.us-east-1.amazonaws.com/SimpleNotificationService-56e67fcb41f6fec09b0196692625d385.pem\",\n                \"UnsubscribeUrl\": \"https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:361439923243:summariseSlice:b9e01117-8264-4cd8-bfb3-631839f91403\",\n                \"MessageAttributes\": {}\n            }\n        }\n    ]\n}";
    // lambdaHandler(req, dynamodbClient, snsClient);
    Aws::ShutdownAPI(options);
    return 0;
}
