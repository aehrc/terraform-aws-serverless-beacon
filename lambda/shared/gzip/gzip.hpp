#pragma once

#include <zlib.h>
#include <iostream>
#include <fstream>
#include <stdint.h>
#include <cstring>
#include <iterator>
#include <algorithm>

using namespace std;

class gzip {
    char *_buffer;
    unsigned int _bufferSize;
    z_stream _zs;
    iostream &_file;
    unsigned int _fileSize = 0;
    unsigned int _dataRead = 0;
    unsigned int _length = 0;
    bool _proccessingData = false;
    char _fileData[1024] = {0};

    void endOfInput();

public:
    gzip(
        iostream &result,
        long long contentLength,
        char *bufferOut,
        unsigned int bufferOutSize);
    int deflateFile(int level);
    int inflateFile();
    bool hasMoreData();
    unsigned int proccesData(unsigned int buffOutBeg, unsigned int buffOutEnd);
};
