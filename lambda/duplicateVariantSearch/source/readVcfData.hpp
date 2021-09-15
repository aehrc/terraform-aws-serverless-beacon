#pragma once

#include <awsutils.hpp>
#include <generalutils.hpp>

#define BUFFER_SIZE 1000000
constexpr size_t MIN_DATA_SIZE = sizeof(generalutils::vcfData::pos) + 4;

struct vcfRegionData  { 
    string filepath; 
    uint16_t chrom;
    uint64_t startRange;
    uint64_t endRange;
};

class ReadVcfData {
    private:
    Aws::S3::Model::GetObjectOutcome _response;
    Aws::IOStream &_stream;
    char _streamBuffer[BUFFER_SIZE];
    vector<generalutils::vcfData> _fileData;
    size_t _dataLength = BUFFER_SIZE;

    bool checkForAvailableData(size_t bytesNeeded, size_t &bufferPos);
    string readString(size_t &bufferPos);

    public:
    ReadVcfData(Aws::String bucket, Aws::String targetFilepath, Aws::S3::S3Client &client);
    vector<generalutils::vcfData> getVcfData();
};
