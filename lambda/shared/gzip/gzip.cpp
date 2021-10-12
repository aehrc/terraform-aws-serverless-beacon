#include "gzip.hpp"
#include <limits.h>

gzip::gzip(iostream &result, long long contentLength, char *buffer, unsigned int bufferSize)
:_buffer(buffer)
,_bufferSize(bufferSize)
,_file(result)
,_fileSize(static_cast<unsigned int>(contentLength)) {
    // Setup gzip
    _zs.zalloc = Z_NULL;
    _zs.zfree = Z_NULL;
    _zs.opaque = Z_NULL;
    _zs.avail_in = 0;

    // Check that the _fileSize hasn't overflowed from contentLength
    if (contentLength > UINT_MAX) { throw runtime_error("Error: gzip is unable to proccess a contentLength of that magnitude"); }
}

int gzip::deflateFile(int level) {
    int ret, flush = Z_NO_FLUSH;
    string name  = "c"; // Give the compressed file a short name

    gz_header header; // <<< HEADER HERE
    header.name = (Bytef*)name.c_str();
    header.comment = Z_NULL;
    header.extra = Z_NULL;

    ret = deflateInit2(&_zs, level, Z_DEFLATED, 16+MAX_WBITS, 9, Z_DEFAULT_STRATEGY);
    deflateSetHeader(&_zs, &header);

    if (ret != Z_OK)
        return ret;

    do {
        _zs.avail_in = _bufferSize;
        _zs.next_in = (Bytef*)_buffer;
        flush = Z_FINISH;

        do {
            _zs.avail_out = sizeof(_fileData);
            _zs.next_out = (Bytef*)_fileData;
            ret = deflate(&_zs, flush);
            if (ret == Z_STREAM_ERROR) {
                throw runtime_error("zlib Stream Error");
            }
            _file.write(_fileData, sizeof(_fileData) - _zs.avail_out);
        } while (_zs.avail_out == 0);
        if (_zs.avail_in != 0) {
            throw runtime_error("zlib Buffer Error");
        }

    } while (flush != Z_FINISH);
    if (ret != Z_STREAM_END) {
        throw runtime_error("zlib Stream Not Finished");
    }

    deflateEnd(&_zs);
    return Z_OK;
}

int gzip::inflateFile() {
    int err = 0;
    if ((err = inflateInit2(&_zs, 16+MAX_WBITS)) != Z_OK) {
        cout << "Error: inflateInit2 " << err << endl;
    }
    if (err >= 0) {
        _proccessingData = true;
    }
    return err;
}

void gzip::endOfInput() {
    _proccessingData = false;
    inflateEnd(&_zs);
}

bool gzip::hasMoreData() {
    return _proccessingData;
}

unsigned int gzip::proccesData(unsigned int buffOutBeg, unsigned int buffOutEnd) {
    int err = 0;

    // Move unused data to the front of the buffer if there
    // is unprocessed data
    if (buffOutBeg != buffOutEnd) {
        memcpy(&_buffer[0], &_buffer[buffOutBeg], buffOutEnd-buffOutBeg);
    }

    // Set the buffer size avaliable
    _zs.avail_out = _bufferSize - (buffOutEnd-buffOutBeg);
    _zs.next_out = (Bytef*)&_buffer[buffOutEnd-buffOutBeg];

    // Start decompressing
    for (;;) {
        // Return data to be proccessed if bufferOut full
        if (_zs.avail_out == 0) {
            return _bufferSize;
        }

        // Handle Input buffer needing more data
        if (_zs.avail_in == 0) {
            _zs.avail_in = min(static_cast<unsigned int>(sizeof(_fileData)), _fileSize - _dataRead);
            _zs.next_in  = (Bytef*)&_fileData[0];
            _dataRead += _zs.avail_in;
            _file.read(_fileData, _zs.avail_in);
        }

        err = inflate(&_zs, Z_BLOCK);

        if (err == Z_STREAM_END) {
            // If we get a stream end and the input buffer is empty
            // then we are at the end of the file
            if (_zs.avail_in == 0 && _fileSize == _dataRead) {
                break;
            }

            // otherwise we still have more data, start the decompression again
            if ((err = inflateFile()) < 0) {
                cout << "Error: inflateFile() " << err << endl;
                break;
            }
        }  else {
            // If we get a negative number, it's a error and we should stop
            if (err < 0) {
                cout << "Error: inflate " << err << endl;
                break;
            }
        }
    }
    endOfInput();

    _length = _bufferSize - _zs.avail_out;
    // cout << "Length: " << _length << ", avail_out: " << _zs.avail_out << ", outBuffer: " << _bufferSize << ", rawfileSize: " << sizeof(_fileData) << endl;
    return _length;
}
