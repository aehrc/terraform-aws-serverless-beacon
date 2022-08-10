#pragma once

#include <iostream>
#include <queue>
#include <stdint.h>
#include <stdlib.h>
#include <zlib.h>
#include <regex>
#include <generalutils.hpp>

#include <aws/core/Aws.h>
#include <aws/core/utils/memory/stl/AWSVector.h>

#include "fast_atoi.h"
#include "stopwatch.h"
#include "downloader.h"
#include "constants.h"

// #define INCLUDE_STOP_WATCH
// #define DEBUG_ON

using namespace std;

struct VcfChunk
{
    const uint_fast64_t startCompressed;
    const uint_fast16_t startUncompressed;
    const uint_fast64_t endCompressed;
    const uint_fast16_t endUncompressed;
    VcfChunk(uint64_t virtualStart, uint64_t virtualEnd)
        : startCompressed(virtualStart >> 16), startUncompressed(virtualStart & 0xffff), endCompressed(virtualEnd >> 16), endUncompressed(virtualEnd & 0xffff) {}
};

// See http://samtools.github.io/hts-specs/SAMv1.pdf section 4.1 "The BGZF compression format"
class VcfChunkReader
{
public:
    const size_t startCompressed;
    const size_t totalBytes;
    const size_t numBytes;
    size_t requestedBytes;
    uint8_t *gzipBytes;
    size_t blockStart;
    size_t nextBlockStart;
    const size_t finalBlock;
    const uint_fast32_t finalUncompressed;
    unsigned char *inflateWindow;
    char *uncompressedChars;
    char *readBufferStart;
    size_t readBufferLength;
    Aws::Vector<char> readAltBuffer;
    uint_fast64_t charPos;
    z_stream zStream;
    uint_fast16_t currentSlice;
    Aws::Vector<Downloader> downloaders;
    size_t windowIndex;
    size_t windowStart;
    size_t totalCSize;
    uint_fast64_t totalUSize;
    uint_fast16_t blockXlen;
    size_t blockCompressedStart;
    uint_fast32_t blockChars;
#ifdef INCLUDE_STOP_WATCH
    stop_watch stopWatch;
#endif
    uint reads;

public:
    VcfChunkReader(Aws::String bucket, Aws::String key, VcfChunk chunk)
        : startCompressed(chunk.startCompressed),
          totalBytes(BGZIP_MAX_BLOCKSIZE + chunk.endCompressed - startCompressed),
          numBytes(BGZIP_MAX_BLOCKSIZE + std::min(DOWNLOAD_SLICE_NUM * MAX_DOWNLOAD_SLICE_SIZE, totalBytes)),
          requestedBytes(0), gzipBytes(new uint8_t[numBytes]),
          nextBlockStart(BGZIP_MAX_BLOCKSIZE), finalBlock(chunk.endCompressed - startCompressed),
          finalUncompressed(chunk.endUncompressed), uncompressedChars(new char[BGZIP_MAX_BLOCKSIZE]),
          readBufferStart(uncompressedChars), readBufferLength(0),
          charPos(0), currentSlice(1), windowIndex(0), windowStart(BGZIP_MAX_BLOCKSIZE), totalCSize(0),
          totalUSize(0), blockChars(0)
    {
#ifdef INCLUDE_STOP_WATCH
        stopWatch = stop_watch();
#endif
        reads = 0;
        do
        {
            downloaders.push_back(Downloader(bucket, key, gzipBytes + BGZIP_MAX_BLOCKSIZE + requestedBytes, bytesToRequest()));
            downloadNext();
            if (windowIndex == 0)
            {
                // Let the first download finish before starting the others so we can start processing right away
                downloaders[windowIndex].join();
            }
            windowIndex++;
        } while (requestedBytes + BGZIP_MAX_BLOCKSIZE < numBytes);
        std::cout << "Downloading " << totalBytes << " bytes using " << windowIndex << " additional threads." << std::endl;
        windowIndex = 0;
        getNextBlock();

        // Initialise z_stream
        zStream.zalloc = Z_NULL;
        zStream.zfree = Z_NULL;
        zStream.opaque = Z_NULL;

        seek(chunk.startUncompressed);
    }

    void addToReadAltBuffer(char *buf, size_t length, size_t &altBufferPos)
    {
        if (readAltBuffer.size() < altBufferPos + length)
        {
            readAltBuffer.resize(altBufferPos + length);
        }
        readBufferLength += length;
        std::copy(buf, buf + length, readAltBuffer.begin() + altBufferPos);
        altBufferPos += length;
    }

    void downloadNext()
    {
        downloaders[windowIndex].startDownload(startCompressed + requestedBytes, bytesToRequest());
        requestedBytes += bytesToRequest();
    }

    uint_fast8_t get8(uint8_t *buf)
    {
        return static_cast<uint_fast8_t>(*buf);
    }

    uint_fast16_t get16(uint8_t *buf)
    {
        uint16_t value;
        memcpy(&value, buf, 2);
        return static_cast<uint_fast16_t>(le16toh(value));
    }

    uint_fast32_t get32(uint8_t *buf)
    {
        uint32_t value;
        memcpy(&value, buf, 4);
        return static_cast<uint_fast32_t>(le32toh(value));
    }

    void getBlockDetails()
    {
        if (memcmp(gzipBytes + blockStart, BGZIP_BLOCK_START, BGZIP_BLOCK_START_LENGTH) != 0)
        {
            std::cout << "Block " << blockStart << " does not start with correct bytes" << std::endl;
        }
        blockXlen = get16(gzipBytes + blockStart + XLEN_OFFSET);
        blockCompressedStart = blockStart + XLEN_OFFSET + 2 + blockXlen;

        bool bSizeFound = false;
        uint8_t *fieldStart = gzipBytes + blockStart + XLEN_OFFSET + 2;
        do
        {
            if (memcmp(fieldStart, BGZIP_FIELD_START, BGZIP_FIELD_START_LENGTH) == 0)
            {
                nextBlockStart = blockStart + get16(fieldStart + BGZIP_FIELD_START_LENGTH) + 1;
                totalCSize += nextBlockStart - blockStart;
                bSizeFound = true;
                break;
            }
            else
            {
                fieldStart += get16(fieldStart + 2);
            }
        } while (fieldStart < gzipBytes + blockCompressedStart);
        if (!bSizeFound)
        {
            std::cout << "Block " << blockStart << " does not have extra field for BSIZE" << std::endl;
        }
        blockChars = moreBlocks() ? get32(gzipBytes + nextBlockStart - 4) : finalUncompressed;
        totalUSize += blockChars;
    }

    bool getNextBlock()
    {
        if (moreBlocks() && charPos >= blockChars)
        {
            charPos -= blockChars;
            blockStart = nextBlockStart;
            size_t nextWindow = windowStart + downloaders[windowIndex].downloadSize;
            // Check if the next download window is coming up
            if (nextWindow < blockStart + BGZIP_MAX_BLOCKSIZE)
            {
                if (windowIndex + 1 == downloaders.size())
                {
                    // If this is the final window in the buffer, move back to the start
                    memcpy(gzipBytes + BGZIP_MAX_BLOCKSIZE + blockStart - nextWindow, gzipBytes + blockStart, nextWindow - blockStart);
                    blockStart = BGZIP_MAX_BLOCKSIZE + blockStart - nextWindow;
                    downloadNext();
                    windowIndex = 0;
                    windowStart = BGZIP_MAX_BLOCKSIZE;
                    downloaders[windowIndex].join();
                }
                else if (nextWindow < blockStart)
                {
                    // We're clear of the current download window, so we can overwrite it and move to the next.
                    downloadNext();
                    windowStart = nextWindow;
                    windowIndex++;
                }
                else
                {
                    downloaders[windowIndex + 1].join();
                }
            }
            getBlockDetails();
        }
        return keepReading();
    }

    size_t getReadLength()
    {
        return readBufferLength;
    }

    const char *getReadStart()
    {
        return readBufferStart;
    }

    bool keepReading()
    {
        return moreBlocks() || charPos < blockChars;
    }

    bool moreBlocks()
    {
        return totalCSize <= finalBlock;
    }

    template <bool first = false>
    void readBlock()
    {
        zStream.next_in = gzipBytes + blockCompressedStart;
        zStream.avail_in = static_cast<uint>(nextBlockStart - blockStart - blockXlen - 20);
        zStream.next_out = reinterpret_cast<unsigned char *>(uncompressedChars);
        zStream.avail_out = static_cast<uint>(blockChars);
        if (first)
        {
            inflateInit2(&zStream, -15);
        }
        else
        {
            inflateReset(&zStream);
        }
#ifdef INCLUDE_STOP_WATCH
        stopWatch.start();
#endif
        inflate(&zStream, Z_FINISH);
        reads++;
#ifdef INCLUDE_STOP_WATCH
        stopWatch.stop();
        if (reads <= 10 || (reads > 15000 && reads <= 15010))
        {
            std::cout << "Inflate took: " << stopWatch << " to inflate " << nextBlockStart - blockStart - blockXlen - 20 << " bytes into " << blockChars << " bytes on read " << reads << std::endl;
        }
#endif
    }

    template <char charA, char charB>
    char readPastChars()
    {
        readBufferStart = uncompressedChars + charPos;
        readBufferLength = 0;
        size_t altBufferPos = 0;
        uint_fast64_t startCharPos;
        do
        {
            startCharPos = charPos;
            while (charPos < blockChars)
            {
                if (uncompressedChars[charPos] == charA || uncompressedChars[charPos] == charB)
                {
                    if (readBufferStart != nullptr)
                    {
                        readBufferLength += charPos - startCharPos;
                    }
                    else
                    {
                        addToReadAltBuffer(uncompressedChars + startCharPos, charPos - startCharPos, altBufferPos);
                        readBufferStart = readAltBuffer.data();
                    }
                    return uncompressedChars[charPos++];
                }
                else
                {
                    charPos++;
                }
            }
            if (!moreBlocks())
            {
                return '\0';
            }
            addToReadAltBuffer(uncompressedChars + startCharPos, blockChars - startCharPos, altBufferPos);
            readBufferStart = nullptr;
            getNextBlock();
            readBlock();
        } while (true);
    }

    size_t bytesToRequest()
    {
        return std::min(MAX_DOWNLOAD_SLICE_SIZE, totalBytes - requestedBytes);
    }

    template <size_t N = 1, char delim>
    bool skipPast()
    {
        size_t num = N;
        do
        {
            while (charPos < blockChars)
            {
                if (uncompressedChars[charPos++] == delim && ((N == 1) || (--num == 0)))
                {
                    return true;
                }
            }
            if (!moreBlocks())
            {
                return false;
            }
            getNextBlock();
            readBlock();
        } while (true);
    }

    uint_fast64_t skipPastAndCountChars(char delim)
    {
        uint_fast64_t numChars = 0;
        do
        {
            while (charPos < blockChars)
            {
                numChars += ((uncompressedChars[charPos] == '\t') || (uncompressedChars[charPos] == '/') || (uncompressedChars[charPos] == '|') || (uncompressedChars[charPos] == ';') || (uncompressedChars[charPos] == ':'));
                if (uncompressedChars[charPos++] == delim)
                {
                    return numChars;
                }
            }
            if (!moreBlocks())
            {
                return numChars;
            }
            getNextBlock();
            readBlock();
        } while (true);
    }

    bool seek(uint_fast64_t numChars)
    {
        charPos += numChars;
        if (charPos < blockChars)
        {
            return keepReading();
        }
        while ((blockChars <= charPos) && getNextBlock())
        {
            // Skip through blocks until we reach the desired charPos
        }
        readBlock();
        return keepReading();
    }

    ~VcfChunkReader()
    {
        inflateEnd(&zStream);
        delete[] uncompressedChars;
        delete[] gzipBytes;
    }
};
