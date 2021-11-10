#include "duplicateVariantSearch.hpp"
#include "thread.hpp"
#include <numeric>
#include <unordered_set>

#include "stopwatch.h"
// #define INCLUDE_STOP_WATCH

DuplicateVariantSearch::DuplicateVariantSearch(
    Aws::S3::S3Client &client,
    Aws::DynamoDB::DynamoDBClient &dynamodbClient,
    Aws::String bucket,
    uint64_t rangeStart,
    uint64_t rangeEnd,
    Aws::String contig,
    Aws::Utils::Array<Aws::Utils::Json::JsonView> targetFilepaths,
    Aws::String dataset
):
    _s3Client(client),
    _dynamodbClient(dynamodbClient),
    _bucket(bucket),
    _rangeStart(rangeStart),
    _rangeEnd(rangeEnd),
    _contig(contig),
    _targetFilepaths(targetFilepaths),
    _dataset(dataset) {}

void DuplicateVariantSearch::searchForDuplicates() {
    size_t numThreads = thread::hardware_concurrency() * 2;
    unordered_set<string> uniqueVariants;

    #ifdef INCLUDE_STOP_WATCH
        stop_watch stopWatch = stop_watch();
        stopWatch.start();
#endif
            Aws::Vector<future<Aws::Vector<Aws::String>>> fileList;
                thread_pool pool(numThreads);
                cout << "Starting " << numThreads << " download threads" << endl;
                for (size_t j = 0; j < _targetFilepaths.GetLength(); j++) {
                    fileList.push_back(pool.enqueue_task(ReadVcfData::getVcfData, _bucket, _targetFilepaths[j].AsString(), ref(_s3Client), _rangeStart, _rangeEnd));
                }
            for (size_t i = 0; i < fileList.size(); i++) {
                if (fileList[i].valid()) {
                    Aws::Vector<Aws::String> fileVariants = fileList[i].get();
                    for (size_t v = 0; v < fileVariants.size(); v++) {
                        uniqueVariants.insert(fileVariants[v]);
                    }
                    cout << "New number of variants: " << uniqueVariants.size() << endl;
                } else {
                    throw runtime_error("Invalid return value from thread"); 
                }
            }

#ifdef INCLUDE_STOP_WATCH
        stopWatch.stop();
        cout << "Files took: " << stopWatch << " to download "<< endl;
#endif

    cout << "Final Tally: " << uniqueVariants.size() << endl;
    int64_t finalTally = updateVariantDuplicates(uniqueVariants.size());

    if (finalTally >= 0) {
        cout << "All variants have been compared!" << endl;
        updateVariantCounts(finalTally);
    } else {
        cout << "All variants have not yet been compared" << endl;
    }
}

void DuplicateVariantSearch::updateVariantCounts(int64_t finalTally) {
    Aws::DynamoDB::Model::UpdateItemRequest request;
    request.SetTableName(getenv("DATASETS_TABLE"));
    Aws::DynamoDB::Model::AttributeValue keyValue;
    keyValue.SetS(_dataset);
    request.AddKey("id", keyValue);
    Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> expressionAttributeValues;
    Aws::DynamoDB::Model::AttributeValue duplicatesValue;
    request.SetUpdateExpression("ADD variantCount :variantCount");
    duplicatesValue.SetN(Aws::String(std::to_string(finalTally).c_str()));
    expressionAttributeValues[":variantCount"] = duplicatesValue;
    request.SetExpressionAttributeValues(expressionAttributeValues);
    request.SetReturnValues(Aws::DynamoDB::Model::ReturnValue::UPDATED_NEW);
    const Aws::DynamoDB::Model::UpdateItemOutcome& result = _dynamodbClient.UpdateItem(request);
    if (result.IsSuccess()) {
        const Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> newAttributes = result.GetResult().GetAttributes();
        auto uniqueVariants = newAttributes.find("variantCount");
        cout << "variant count: " << uniqueVariants->second.GetN() << endl;
    } else {
        const Aws::DynamoDB::DynamoDBError error = result.GetError();
        cout << "Item was not updated, received error: " << error.GetMessage() << endl;
        if (error.ShouldRetry()) {
            cout << "Retrying after 1 second..." << endl;
            this_thread::sleep_for(chrono::seconds(1));
        } else {
            cout << "Not Retrying." << endl;
        }
    }
}

int64_t DuplicateVariantSearch::updateVariantDuplicates(size_t totalCount) {
    Aws::DynamoDB::Model::AttributeValue partitionKey, sortKey;
    partitionKey.SetS(_contig);
    sortKey.SetS(_dataset);
    Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> key;
    key["contig"] = partitionKey;
    key["datasetKey"] = sortKey;

    Aws::DynamoDB::Model::UpdateItemRequest request;
    request.SetTableName(getenv("VARIANT_DUPLICATES_TABLE"));
    request.WithKey(key);
    request.SetUpdateExpression("ADD variantCount :numVariants DELETE toUpdate :sliceStringSet");
    request.SetConditionExpression("contains(toUpdate, :sliceString)");

    Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> expressionAttributeValues;

    Aws::DynamoDB::Model::AttributeValue numVariantsValue;
    numVariantsValue.SetN(static_cast<double>(totalCount));
    expressionAttributeValues[":numVariants"] = numVariantsValue;

    range item;
    item.start = _rangeStart;
    item.end = _rangeEnd;
    Aws::Utils::ByteBuffer bb = Aws::Utils::ByteBuffer(static_cast<unsigned char*>(static_cast<void*>(&item)), sizeof(item));

    Aws::DynamoDB::Model::AttributeValue sliceStringSetValue;
    sliceStringSetValue.SetBS(Aws::Vector<Aws::Utils::ByteBuffer>{bb});
    expressionAttributeValues[":sliceStringSet"] = sliceStringSetValue;

    Aws::DynamoDB::Model::AttributeValue sliceStringValue;
    sliceStringValue.SetB(bb);
    expressionAttributeValues[":sliceString"] = sliceStringValue;

    request.SetExpressionAttributeValues(expressionAttributeValues);
    request.SetReturnValues(Aws::DynamoDB::Model::ReturnValue::UPDATED_NEW);
    do {
        cout << "Calling dynamodb::UpdateItem with partition=\"" << _contig << "\", sort=\"" << _dataset << "\" and slice=\"" << _rangeStart << "_" << _rangeEnd << "\"" << endl;
        const Aws::DynamoDB::Model::UpdateItemOutcome& result = _dynamodbClient.UpdateItem(request);
        if (result.IsSuccess()) {
            const Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> newAttributes = result.GetResult().GetAttributes();
            cout << "Item was updated, new item has following values for these attributes: variantCount=";
            auto variantCountItr = newAttributes.find("variantCount");
            if (variantCountItr != newAttributes.end()) {
                cout << variantCountItr->second.GetN();
                
            }
            cout << ", toUpdate=";
            auto toUpdateItr = newAttributes.find("toUpdate");
            if (toUpdateItr != newAttributes.end()) {
                cout << "{";
                Aws::Vector<Aws::Utils::ByteBuffer> toUpdateNew = toUpdateItr->second.GetBS();
                for (Aws::Utils::ByteBuffer sliceStringRemaining : toUpdateNew) {
                    cout << "\"0x";
                    ios::fmtflags f(cout.flags());  // Store formatting state because "hex" changes it
                    for (size_t i = 0; i < sliceStringRemaining.GetLength(); i++) {
                        cout << hex << (unsigned int)sliceStringRemaining[i];
                    }
                    cout.flags(f);  // Restore the previous formatting flags
                    cout << "\", ";
                }
                cout << "}";
            }
            cout << endl;
            uint64_t duplicateCount = atol(variantCountItr->second.GetN().c_str());
            return toUpdateItr == newAttributes.end() ? duplicateCount : -1;
        } else {
            const Aws::DynamoDB::DynamoDBError error = result.GetError();
            cout << "Item was not updated, received error: " << error.GetMessage() << endl;
            if (error.ShouldRetry()) {
                cout << "Retrying after 1 second..." << endl;
                this_thread::sleep_for(chrono::seconds(1));
                continue;
            } else {
                cout << "Not Retrying." << endl;
                return -1;
            }
        }
    } while (true);
    
    return -1;
}
