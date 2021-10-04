#include "duplicateVariantSearch.hpp"
#include "thread.hpp"

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

bool DuplicateVariantSearch::comparePos(generalutils::vcfData const &i, uint64_t j){ return i.pos < j; }

std::deque<generalutils::vcfData>::iterator DuplicateVariantSearch::searchForPosition(uint64_t pos, deque<generalutils::vcfData> &fileData, size_t offset) {
    return lower_bound(fileData.begin() + offset, fileData.end(), pos, comparePos);
}

bool DuplicateVariantSearch::isADuplicate(generalutils::vcfData &a, generalutils::vcfData &b) {
    return a.ref.compare(b.ref) == 0 && a.alt.compare(b.alt) == 0;
}

bool DuplicateVariantSearch::containsExistingFilepath(deque<size_t> &existingFilepaths, size_t filepath) {
    return find(existingFilepaths.begin(), existingFilepaths.end(), filepath) != existingFilepaths.end();
}

string DuplicateVariantSearch::to_zero_lead(const uint64_t value, const unsigned precision) {
    ostringstream oss;
    oss << setw(precision) << setfill('0') << value;
    return oss.str();
}

size_t DuplicateVariantSearch::compareFiles(
    uint64_t rangeStart,
    uint64_t rangeEnd,
    uint64_t targetFilepathsLength,
    deque<deque<generalutils::vcfData>> &fileLookup
) {
    // cout << "top: rangeStart: " << rangeStart << " rangeEnd: " << rangeEnd << endl;
    map<string, deque<size_t>> duplicates;
    for (size_t j = 0; j < targetFilepathsLength; j++) {
        for (size_t m = 0; m < targetFilepathsLength - 1; m++) {
            // strategically compare files only once
            if (j <= m) {
                break;
            }
            bool isInRange = (
                (fileLookup[j].front().pos <= fileLookup[m].front().pos && fileLookup[m].front().pos <= fileLookup[j].back().pos) || // If the start point lies within the range
                (fileLookup[j].front().pos <= fileLookup[m].back().pos && fileLookup[m].back().pos <= fileLookup[j].back().pos) || // If the end point lies within the range
                (fileLookup[m].front().pos < fileLookup[j].front().pos && fileLookup[j].back().pos < fileLookup[m].back().pos) // If the start and end point encompass the range
            );
            // bool isInRange2 = (
            //     (fileLookup[j].front().pos <= fileLookup[m].front().pos && fileLookup[m].front().pos <= fileLookup[j].back().pos) || // If the start point lies within the range
            //     (fileLookup[j].front().pos <= fileLookup[m].back().pos && fileLookup[m].back().pos <= fileLookup[j].back().pos) || // If the end point lies within the range
            //     (fileLookup[m].front().pos < fileLookup[j].front().pos && fileLookup[j].back().pos < fileLookup[m].back().pos) // If the start and end point encompass the range
            // );
            if (isInRange) {
                size_t file2Offest = 0;

                // Skip the first part of the file if the data we are comparing doesn't matchup.
                uint64_t filePosStart = max(rangeStart, fileLookup[m].front().pos);
                deque<generalutils::vcfData>::iterator file1Start = searchForPosition(filePosStart, fileLookup[j], 0);

                // search for duplicates of each struct in file1 against file2
                for (deque<generalutils::vcfData>::iterator l = file1Start; l != fileLookup[j].end(); ++l) {
                    deque<generalutils::vcfData>::iterator searchPosition = searchForPosition(l->pos, fileLookup[m], file2Offest);
                    file2Offest = searchPosition - fileLookup[m].begin();

                    // We have read to the end of file 2, exit the file 1 loop
                    if (searchPosition == fileLookup[m].end()) {
                        // cout << "End found, exit now" << endl;
                        break;
                    }

                    // handle the case of multiple variants at one position
                    for (auto k = searchPosition; k != fileLookup[m].end() && k->pos == l->pos && k->pos <= rangeEnd; ++k) {
                        if (isADuplicate(*l, *k)) {
                            // cout << "found a match! " << k->pos << "-" << k->ref << "-" << k->alt << " - " << l->pos << endl;

                            const string posRefAltKey = to_string(k->pos) + k->ref + "_" + k->alt;

                            if (duplicates.count(posRefAltKey) != 0) { // if k already exists
                                if (!containsExistingFilepath(duplicates[posRefAltKey], j)) {
                                    duplicates[posRefAltKey].push_back(j);
                                } 
                                if (!containsExistingFilepath(duplicates[posRefAltKey], m)) {
                                    duplicates[posRefAltKey].push_back(m);
                                }
                            } else {
                                duplicates[posRefAltKey] = { j, m };
                            }
                        }
                    }
                }
            }
        }
    }

    size_t duplicatesCount = 0; 
    for (auto const& [key2, val2]: duplicates) {
        duplicatesCount += val2.size() - 1;
    }
    // cout << "bottom: rangeStart: " << rangeStart << " rangeEnd: " << rangeEnd << endl;
    // cout << "Dupe " << duplicatesCount << endl;
    return duplicatesCount;
}

size_t DuplicateVariantSearch::searchForDuplicates() {
    size_t numThreads = thread::hardware_concurrency() * 2;
    size_t duplicatesCount = 0;
    size_t targetFilepathsLength = _targetFilepaths.GetLength();
    map<string, deque<size_t>> duplicates = {};
    deque<deque<generalutils::vcfData>> fileLookup;

    #ifdef INCLUDE_STOP_WATCH
        stop_watch stopWatch = stop_watch();
    #endif

    // for each file found to correspond with the current target range, retrieve two files at a time from the list, and search through to find duplicates
    if (targetFilepathsLength > 1) {
#ifdef INCLUDE_STOP_WATCH
        stopWatch.start();
#endif
        {
            deque<future<deque<generalutils::vcfData>>> fileList;
            {
                thread_pool pool(numThreads);
                cout << "Starting " << numThreads << " download threads" << endl;
                for (size_t j = 0; j < targetFilepathsLength; j++) {
                    fileList.push_back(pool.enqueue_task(ReadVcfData::getVcfData, _bucket, _targetFilepaths[j].AsString(), ref(_s3Client), _rangeStart, _rangeEnd));
                }
            }
            for (size_t i=0; i < fileList.size(); i++) {
                if (fileList[i].valid()) {
                    fileLookup.push_back(fileList[i].get());
                } else {
                    throw runtime_error("Invalid return value from thread"); 
                }
            }
        }

#ifdef INCLUDE_STOP_WATCH
        stopWatch.stop();
        cout << "Files took: " << stopWatch << " to download "<< std::endl;

        stopWatch.start();
#endif
        {
            deque<future<size_t>> duplicatesCountList;
            {
                thread_pool pool(numThreads);
                cout << "Starting " << numThreads << " worker threads" << endl;
                size_t inc = (_rangeEnd - _rangeStart) / (numThreads * 2);

                for (size_t i = 0; i < (numThreads * 2); i++) {
                    size_t start =_rangeStart + (inc * i), end = _rangeEnd;
                    if ((i + 1) < (numThreads * 2)) {
                        end = _rangeStart + ( inc * (i + 1)) - 1;
                    }
                    duplicatesCountList.push_back(pool.enqueue_task(DuplicateVariantSearch::compareFiles, start, end, targetFilepathsLength, ref(fileLookup)));
                }
            }
            for (size_t i=0; i < duplicatesCountList.size(); i++) {
                if (duplicatesCountList[i].valid()) {
                    duplicatesCount += duplicatesCountList[i].get();
                } else {
                    throw runtime_error("Invalid return value from thread"); 
                }
            }
        }
#ifdef INCLUDE_STOP_WATCH
        stopWatch.stop();
        cout << "compareFiles took: " << stopWatch << " to complete "<< std::endl;
#endif

    } else {
        cout << "Only one file for this region, continue" << endl;
    }

    cout << "Final Tally: " << duplicatesCount << endl;
    updateVariantDuplicates(duplicatesCount);
    return duplicatesCount;
}

bool DuplicateVariantSearch::updateVariantDuplicates(int64_t totalCount) {
    Aws::DynamoDB::Model::AttributeValue partitionKey, sortKey;
    partitionKey.SetS(_contig);
    sortKey.SetS(_dataset);
    Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> key;
    key["contig"] = partitionKey;
    key["datasetKey"] = sortKey;

    Aws::DynamoDB::Model::UpdateItemRequest request;
    request.SetTableName(getenv("VARIANT_DUPLICATES_TABLE"));
    request.WithKey(key);
    // for debugging
    // request.SetUpdateExpression("ADD duplicateCount :numVariants, updated :sliceStringSet DELETE toUpdate :sliceStringSet");
    // request.SetConditionExpression("contains(toUpdate, :sliceString) And NOT (contains(updated, :sliceString))");
    request.SetUpdateExpression("ADD duplicateCount :numVariants DELETE toUpdate :sliceStringSet");
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
        std::cout << "Calling dynamodb::UpdateItem with partition=\"" << _contig << "\", sort=\"" << _dataset << "\" and slice=\"" << _rangeStart << "_" << _rangeEnd << "\"" << std::endl;
        const Aws::DynamoDB::Model::UpdateItemOutcome& result = _dynamodbClient.UpdateItem(request);
        if (result.IsSuccess()) {
            const Aws::Map<Aws::String, Aws::DynamoDB::Model::AttributeValue> newAttributes = result.GetResult().GetAttributes();
            std::cout << "Item was updated, new item has following values for these attributes: duplicateCount=";
            auto duplicateCountItr = newAttributes.find("duplicateCount");
            if (duplicateCountItr != newAttributes.end()) {
                std::cout << duplicateCountItr->second.GetN();
            }
            std::cout << ", toUpdate=";
            auto toUpdateItr = newAttributes.find("toUpdate");
            if (toUpdateItr != newAttributes.end()) {
                std::cout << "{";
                Aws::Vector<Aws::String> toUpdateNew = toUpdateItr->second.GetSS();
                for (Aws::String sliceStringRemaining : toUpdateNew) {
                    std::cout << "\"" << sliceStringRemaining << "\", ";
                }
                std::cout << "}";
            }
            std::cout << std::endl;
            return (toUpdateItr == newAttributes.end());
        } else {
            const Aws::DynamoDB::DynamoDBError error = result.GetError();
            std::cout << "Item was not updated, received error: " << error.GetMessage() << std::endl;
            if (error.ShouldRetry()) {
                std::cout << "Retrying after 1 second..." << std::endl;
                std::this_thread::sleep_for(std::chrono::seconds(1));
                continue;
            } else {
                std::cout << "Not Retrying." << std::endl;
                return false;
            }
        }
    } while (true);
}
