#include "readVcfData.hpp"

deque<generalutils::vcfData> ReadVcfData::getVcfData(Aws::String bucket, Aws::String targetFilepath, Aws::S3::S3Client &client, uint64_t rangeStart, uint64_t rangeEnd) {
    size_t bufferPos = 0;
    size_t dataLength = 0;
    char streamBuffer[BUFFER_SIZE];
    generalutils::vcfData vcf;
    deque<generalutils::vcfData> fileData;

    Aws::S3::Model::GetObjectOutcome response = awsutils::getS3Object(bucket, targetFilepath, client);
    Aws::IOStream &stream = response.GetResult().GetBody();
    gzip inputGzip = gzip(stream, response.GetResult().GetContentLength(), streamBuffer, sizeof(streamBuffer));
    inputGzip.inflateFile();

    do {
        if (checkForAvailableData(MIN_DATA_SIZE, bufferPos, inputGzip, dataLength)) {
            memcpy(reinterpret_cast<unsigned char*> (&vcf.pos), &streamBuffer[bufferPos], sizeof(generalutils::vcfData::pos));
            bufferPos += sizeof(generalutils::vcfData::pos);
            // Check if we can skip this start position
            if (rangeStart <= vcf.pos) {
                vcf.ref = readString(bufferPos, inputGzip, dataLength, streamBuffer);
                vcf.alt = readString(bufferPos, inputGzip, dataLength, streamBuffer);
                fileData.push_back(vcf);
            } else {
                // We need to move the buffer along by two strings worth if we are skipping this point
                bufferPos += streamBuffer[bufferPos] + 1;
                bufferPos += streamBuffer[bufferPos] + 1;
            }

        } else {
            throw runtime_error("Invalid File Read - getVcfData()");
        }
    } while ((dataLength != bufferPos && vcf.pos <= rangeEnd) || inputGzip.hasMoreData());

    return fileData;
}

string ReadVcfData::readString(size_t &bufferPos, gzip &inputGzip, size_t &dataLength, char *streamBuffer) {
    uint8_t stringLen = streamBuffer[bufferPos];
    string ret = "";
    // if (stringLen != 1) {
    //     cout << "Found string with len: " << (uint16_t) stringLen << " At Pos: " << bufferPos << endl;
    //     throw runtime_error("Invalid length read");
    // }
    bufferPos += 1; // A byte for the length
    if (checkForAvailableData(stringLen, bufferPos, inputGzip, dataLength)) {
        ret = string(stringLen, streamBuffer[bufferPos]);
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
