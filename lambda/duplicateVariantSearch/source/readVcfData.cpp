#include "readVcfData.hpp"

ReadVcfData::ReadVcfData(Aws::String bucket, Aws::String targetFilepath, Aws::S3::S3Client &client) :
    _response(awsutils::getS3Object(bucket, targetFilepath, client)),
    _stream(_response.GetResult().GetBody())
{
    _stream.seekg(0, _stream.beg);
}


vector<generalutils::vcfData> ReadVcfData::getVcfData(uint64_t rangeStart, uint64_t rangeEnd) {
    size_t bufferPos = BUFFER_SIZE;
    generalutils::vcfData vcf;

    do {
        if (checkForAvailableData(MIN_DATA_SIZE, bufferPos)) {
            memcpy(reinterpret_cast<unsigned char*> (&vcf.pos), &_streamBuffer[bufferPos], sizeof(generalutils::vcfData::pos));
            bufferPos += sizeof(generalutils::vcfData::pos);
            // Check if we can skip this start position
            if (rangeStart <= vcf.pos) {
                vcf.ref = readString(bufferPos);
                vcf.alt = readString(bufferPos);
                _fileData.push_back(vcf);
            } else {
                // We need to move the buffer along by two strings worth if we are skipping this point
                bufferPos += _streamBuffer[bufferPos] + 1;
                bufferPos += _streamBuffer[bufferPos] + 1;
            }

        } else {
            throw runtime_error("Invalid File Read - getVcfData()");
        }
    } while (_dataLength != bufferPos && vcf.pos <= rangeEnd);

    return _fileData;
}

string ReadVcfData::readString(size_t &bufferPos) {
    uint8_t stringLen = _streamBuffer[bufferPos];
    string ret = "";
    // if (stringLen != 1) {
    //     cout << "Found string with len: " << (uint16_t) stringLen << " At Pos: " << bufferPos << endl;
    //     throw runtime_error("Invalid length read");
    // }
    bufferPos += 1; // A byte for the length
    if (checkForAvailableData(stringLen, bufferPos)) {
        ret = string(stringLen, _streamBuffer[bufferPos]);
        bufferPos += stringLen;
    } else {
        throw runtime_error("Invalid File Read - readString()");
    }
    return ret;
}

bool ReadVcfData::checkForAvailableData(size_t bytesNeeded, size_t &bufferPos) {
    if (_dataLength >= (bufferPos + bytesNeeded)) {
        return true;
    }

    if (!_stream.good()) {
        return false;
    }

    size_t bufferRemain = BUFFER_SIZE - bufferPos;

    if (_dataLength != bufferPos) {
        memcpy(&_streamBuffer[0], &_streamBuffer[bufferPos], bufferRemain);
    }

    _stream.read(&_streamBuffer[bufferRemain], BUFFER_SIZE - bufferRemain);
    _dataLength = _stream.gcount() + bufferRemain;

    if (_dataLength > 0) {
        bufferPos = 0;
        return true;
    }

    return false;
}
