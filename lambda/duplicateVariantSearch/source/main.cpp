#include <iostream>
#include <queue>
#include <stdint.h>
#include <math.h>
#include <awsutils.hpp>
#include <generalutils.hpp>

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
constexpr float VCF_SEARCH_BASE_PAIR_RANGE = 100000.0;
uint const BUFFER_SIZE = 200000 * sizeof(generalutils::vcfData);

struct vcfRegionData  { 
    string filepath; 
    uint16_t chrom;
    uint64_t startRange;
    uint64_t endRange;
};

struct range {
    uint64_t start;
    uint64_t end;
};

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

class DuplicateVariantSearch {
    private:
    Aws::S3::S3Client s3Client;
    string s3Bucket = "large-test-vcfs"; // Todo

    vector<string> retrieveS3Objects(Aws::String bucket) {
        vector<string> objectKeys;
        vector<string> bucketObjectKeys = awsutils::retrieveBucketObjectKeys(bucket, s3Client);
        copy_if(bucketObjectKeys.begin(), bucketObjectKeys.end(), back_inserter(objectKeys), [](string s) { return s.find("output") != std::string::npos; });
        return objectKeys;
    }

    vcfRegionData getFileNameInfo(string s) {
        vcfRegionData regions;
        regions.filepath = s;

        char cstr[s.size() + 1];
        strcpy(cstr, s.c_str());

        vector<string> split;
        char *token = strtok(cstr, "_");
        
        while (token != NULL) {
            split.push_back(token);
            token = strtok(NULL, "_");
        }
        string range = split.back();
        split.pop_back();
        regions.chrom = generalutils::fast_atoi<uint16_t>(split.back().c_str(), split.back().length());

        string startRange = range.substr(0, range.find('-'));
        string endRange = range.substr(range.find('-') + 1, range.size());
        
        regions.startRange = generalutils::fast_atoi<uint64_t>(startRange.c_str(), startRange.length());
        regions.endRange = generalutils::fast_atoi<uint64_t>(endRange.c_str(), endRange.length());

        // cout << regions.chrom << " / " << range << " / " << (int)regions.startRange << " / " << (int)regions.endRange << endl;
        return regions;
    }

    void readFileContent() {
        Aws::S3::Model::GetObjectOutcome response = awsutils::getS3Object(s3Bucket, "filename", s3Client); // Todo
    }

    void createChromRegionsMap(map<uint16_t, range> &chromLookup, vcfRegionData &insertItem) {
        if (chromLookup.find(insertItem.chrom) != chromLookup.end() ) {  // If we havent seen this chrom before, add a record.
            chromLookup[insertItem.chrom] = range{insertItem.startRange, insertItem.endRange};
        } else {
            if (chromLookup[insertItem.chrom].start > insertItem.startRange) {
                chromLookup[insertItem.chrom].start = insertItem.startRange;
            }
            if (chromLookup[insertItem.chrom].end < insertItem.endRange) {
                chromLookup[insertItem.chrom].end = insertItem.endRange;
            }
        }
        cout << insertItem.filepath << " Chrom: " << (int)(insertItem.chrom) << " Start: " << (int)(insertItem.startRange) << " End: " << (int)(insertItem.endRange) << endl;
    }

    void filterForCorrespondingChromFilepaths(
        vector<vcfRegionData> &currentSearchTargets,
        vector<vcfRegionData> regionData,
        uint16_t chrom
    ) {
        for (vcfRegionData rd : regionData) {
            if (rd.chrom == chrom) {
                currentSearchTargets.push_back(rd);
            }
        }
    }

    void filterForCorrespondingRegion(
        vector<vcfRegionData> &currentSearchTargets,
        vector<vcfRegionData> regionData,
        uint64_t start,
        uint64_t end
    ) {
        for (vcfRegionData rd : regionData) {
            if (rd.startRange >= start || rd.endRange < end) {
                currentSearchTargets.push_back(rd);
            }
        }
    }

    public:
    DuplicateVariantSearch(Aws::S3::S3Client client):
        s3Client(client)
    {}
    // sizeof(generalutils::vcfData)
    vector<generalutils::vcfData> streamS3Outcome(Aws::S3::Model::GetObjectOutcome &response) {
        vector<generalutils::vcfData> fileData;

        auto& stream = response.GetResult().GetBody();
        char streamBuffer[BUFFER_SIZE];
        stream.seekg(0, stream.beg);
        string currentRow;
        while (stream.good()) {
            stream.read(streamBuffer, sizeof(streamBuffer));
            size_t bytesRead = stream.gcount();

            for (int i = 0; i < bytesRead; i+=sizeof(generalutils::vcfData)) {
                generalutils::vcfData vcf;
                // Need to check if the buffer has enough info in it for a vcfData read
                unsigned char *rawData = reinterpret_cast<unsigned char*> (&vcf);
                memcpy(rawData, &streamBuffer[i], sizeof(generalutils::vcfData));
                fileData.push_back(vcf);
            }
        }
        return fileData;
    }

    bool searchForDuplicates() {
        vector<string> s3Objects = retrieveS3Objects(s3Bucket);
        map<uint16_t, range> chromLookup;

        vector<vcfRegionData> regionData;
        for (Aws::String filepath : s3Objects) {
            regionData.push_back(getFileNameInfo(filepath));
            createChromRegionsMap(chromLookup, regionData.back()); 
        }

        for (auto const& [key, val]: chromLookup) {
            cout << "Chrom: " << key << " Start: " << val.start << " End: " << val.end << endl;
            uint64_t searchLoopsTotal = ceil((val.end - val.start) / VCF_SEARCH_BASE_PAIR_RANGE); // the number of times to loop through to cover the entire range
            cout << "searchLoopsTotal: " << searchLoopsTotal << endl;
            for (uint i = 0; i < searchLoopsTotal; i++) {
                vector<vcfRegionData> currentSearchTargets;
                filterForCorrespondingChromFilepaths(currentSearchTargets, regionData, key);
                uint rangeStart = val.start + (VCF_SEARCH_BASE_PAIR_RANGE * i);
                filterForCorrespondingRegion(currentSearchTargets, regionData, rangeStart, rangeStart + VCF_SEARCH_BASE_PAIR_RANGE); // search through a portion of the range each time

                cout << "currentSearchTargets size: " << currentSearchTargets.size() << endl;
                // for each file found to correspond with the current target range, retrieve two files from the list, and search through to find duplicates
                if (currentSearchTargets.size() > 1) {
                    
                    for (size_t j = 0; j < currentSearchTargets.size() - 1; j++) {
                        Aws::S3::Model::GetObjectOutcome response1 = awsutils::getS3Object(s3Bucket, currentSearchTargets[j].filepath, s3Client);
                        Aws::S3::Model::GetObjectOutcome response2 = awsutils::getS3Object(s3Bucket, currentSearchTargets[j+1].filepath, s3Client);
                        vector<generalutils::vcfData> file1 = streamS3Outcome(response1);
                        vector<generalutils::vcfData> file2 = streamS3Outcome(response2);

                        cout << "file 1 size: " << file1.size() << endl;
                        cout << "file 2 size: " << file2.size() << endl;
                    }


                } else {
                    cout << "Only one file for this region, continue" << endl;
                }

            }
        }

    }

};


static aws::lambda_runtime::invocation_response lambdaHandler(aws::lambda_runtime::invocation_request const& req,
    Aws::S3::S3Client const& s3Client, Aws::DynamoDB::DynamoDBClient const& dynamodbClient, Aws::SNS::SNSClient const& snsClient)
{
    Aws::String messageString = awsutils::getMessageString(req);
    std::cout << "Message is: " << messageString << std::endl;
    Aws::Utils::Json::JsonValue message(messageString);
    Aws::Utils::Json::JsonView messageView = message.View();

    DuplicateVariantSearch duplicateVariantSearch = DuplicateVariantSearch(s3Client);

    duplicateVariantSearch.searchForDuplicates();

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
