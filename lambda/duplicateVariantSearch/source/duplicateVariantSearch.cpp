#include "duplicateVariantSearch.hpp"

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

std::vector<generalutils::vcfData>::iterator DuplicateVariantSearch::searchForPosition(uint64_t pos, vector<generalutils::vcfData> &fileData, size_t offset) {
    return lower_bound(fileData.begin() + offset, fileData.end(), pos, comparePos);
}

bool DuplicateVariantSearch::isADuplicate(generalutils::vcfData *a, generalutils::vcfData *b) {
    return a->ref.compare(b->ref) == 0 && a->alt.compare(b->alt) == 0;
}

bool DuplicateVariantSearch::containsExistingFilepath(vector<size_t> &existingFilepaths, size_t filepath) {
    return find(existingFilepaths.begin(), existingFilepaths.end(), filepath) != existingFilepaths.end();
}


string DuplicateVariantSearch::to_zero_lead(const uint64_t value, const unsigned precision) {
    ostringstream oss;
    oss << setw(precision) << setfill('0') << value;
    return oss.str();
}

size_t DuplicateVariantSearch::searchForDuplicates() {
    size_t duplicatesCount = 0;
    size_t targetFilepathsLength = _targetFilepaths.GetLength();

    // for each file found to correspond with the current target range, retrieve two files at a time from the list, and search through to find duplicates
    if (targetFilepathsLength > 1) {

        map<string, vector<size_t>> duplicates = {};

        map<string, vector<generalutils::vcfData>> fileLookup;
        for (size_t j = 0; j < targetFilepathsLength; j++) {

            string targetFilepathJ = _targetFilepaths[j].AsString();
            if (fileLookup.count(targetFilepathJ) == 0) {
                fileLookup[targetFilepathJ] = ReadVcfData(_bucket, targetFilepathJ, _s3Client).getVcfData(_rangeStart, _rangeEnd);
                // cout << "File " << targetFilepathJ << " Size: " << fileLookup[targetFilepathJ].size() << endl;
            }

            vector<generalutils::vcfData> file1 = fileLookup[targetFilepathJ];

            for (size_t m = 0; m < targetFilepathsLength - 1; m++) {
                string targetFilepathM = _targetFilepaths[m].AsString();

                // strategically compare files only once
                if (j != m && fileLookup.count(targetFilepathM) > 0) {

                    vector<generalutils::vcfData> file2 = fileLookup[targetFilepathM];

                    // Skip the first part of the file if the data we are comparing doesn't matchup.
                    uint64_t filePosStart = max(_rangeStart, file2.front().pos);
                    std::vector<generalutils::vcfData>::iterator fileStart = searchForPosition(filePosStart, file1, 0);

                    
                    
                    size_t file2Offest = 0;
                    // search for duplicates of each struct in file1 against file2
                    for (std::vector<generalutils::vcfData>::iterator l = fileStart; l != file1.end(); ++l) {
                        vector<generalutils::vcfData>::iterator searchPosition = searchForPosition(l->pos, file2, file2Offest);
                        file2Offest = searchPosition - file2.begin();

                        // We have read to the end of file 2, exit the file 1 loop
                        if (searchPosition == file2.end()) {
                            // cout << "End found, exit now" << endl;
                            break;
                        }

                        // handle the case of multiple variants at one position
                        for (auto k = searchPosition; k != file2.end() && k->pos == l->pos && k->pos <= _rangeEnd; ++k) {
                            if (isADuplicate(l.base(), k.base())) {
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
        for (auto const& [key2, val2]: duplicates) {
            duplicatesCount += val2.size() - 1;
        }

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
