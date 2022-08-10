#include "readVcfData.hpp"

Aws::Vector<Aws::String> ReadVcfData::getVcfData(Aws::String bucket, Aws::String targetFilepath, Aws::S3::S3Client &client, uint64_t rangeStart, uint64_t rangeEnd) {
    size_t bufferPos = 0;
    size_t dataLength = 0;
    char streamBuffer[BUFFER_SIZE];
    generalutils::vcfData vcf;
    Aws::Vector<Aws::String> fileData;

    Aws::S3::Model::GetObjectOutcome response = awsutils::getS3Object(bucket, targetFilepath);
    Aws::IOStream &stream = response.GetResult().GetBody();
    gzip inputGzip = gzip(stream, response.GetResult().GetContentLength(), streamBuffer, sizeof(streamBuffer));
    inputGzip.inflateFile();

    do {
        if (checkForAvailableData(MIN_DATA_SIZE, bufferPos, inputGzip, dataLength)) {
            memcpy(reinterpret_cast<unsigned char*> (&vcf.pos), &streamBuffer[bufferPos], sizeof(generalutils::vcfData::pos));
            bufferPos += sizeof(generalutils::vcfData::pos);

            // Check if we can skip this start position
            if (rangeStart <= vcf.pos) {
                string refAlt = readString(bufferPos, inputGzip, dataLength, streamBuffer);
                fileData.push_back(to_string(vcf.pos) + refAlt);

            } else {
                // Skip the rest of the data
                uint16_t stringLen;
                memcpy(reinterpret_cast<char*>(&stringLen), &streamBuffer[bufferPos], sizeof(uint16_t)); // copy in the length bytes
                bufferPos += stringLen + sizeof(uint16_t);
            }

        } else {
            throw runtime_error("Invalid File Read - getVcfData()");
        }
    } while ((dataLength != bufferPos && vcf.pos <= rangeEnd) || inputGzip.hasMoreData());

    return fileData;
}

string ReadVcfData::readString(size_t &bufferPos, gzip &inputGzip, size_t &dataLength, char *streamBuffer) {
    uint16_t stringLen;
    string ret = "";

    memcpy(reinterpret_cast<char*>(&stringLen), &streamBuffer[bufferPos], sizeof(uint16_t)); // copy in the length bytes
    bufferPos += sizeof(uint16_t);

    if (checkForAvailableData(stringLen, bufferPos, inputGzip, dataLength)) {
        ret = string(&streamBuffer[bufferPos], stringLen);
        bufferPos += stringLen;
    } else {
        throw runtime_error("Invalid File Read - readString()");
    }
    return ret;
}

bool ReadVcfData::checkForAvailableData(size_t bytesNeeded, size_t &bufferPos, gzip &inputGzip, size_t &dataLength) {
    if (dataLength >= (bufferPos + bytesNeeded)) {
        return true;
    }
    if (!inputGzip.hasMoreData()) {
        return false;
    }
    dataLength = inputGzip.proccesData(bufferPos, dataLength);

    if (dataLength > 0) {
        bufferPos = 0;
        return true;
    }

    return false;
}
