#pragma once

#include <iostream>
#include <queue>
#include <stdint.h>
#include <stdlib.h>
#include <zlib.h>
#include <regex>
#include <generalutils.hpp>
#include <awsutils.hpp>

#include <aws/core/Aws.h>
#include <aws/core/utils/stream/PreallocatedStreamBuf.h>
#include <aws/s3/S3Client.h>
#include <aws/s3/model/GetObjectRequest.h>

#include "fast_atoi.h"
#include "stopwatch.h"
#include "constants.h"

// #define INCLUDE_STOP_WATCH
// #define DEBUG_ON

using namespace std;

// A non-copying iostream.
// See https://stackoverflow.com/questions/35322033/aws-c-sdk-uploadpart-times-out
// https://stackoverflow.com/questions/13059091/creating-an-input-stream-from-constant-memory
class StringViewStream : Aws::Utils::Stream::PreallocatedStreamBuf, public Aws::IOStream
{
public:
    StringViewStream(uint8_t *data, size_t nbytes)
        : Aws::Utils::Stream::PreallocatedStreamBuf(data, nbytes), Aws::IOStream(this)
    {
    }
};

class Downloader
{
    Aws::S3::Model::GetObjectRequest m_request;
    Aws::S3::S3Client m_s3Client;
    thread m_thread;

public:
    size_t downloadSize;
    Downloader(Aws::String const &bucket, Aws::String const &key, uint8_t *windowStart, size_t numBytes)
        : m_s3Client(awsutils::getNewClient()), downloadSize(0)
    {
        m_request.SetBucket(bucket);
        m_request.SetKey(key);
        m_request.SetResponseStreamFactory([windowStart, numBytes]()
                                           { return Aws::New<StringViewStream>(TAG, windowStart, numBytes); });
    }

    static void download(Aws::S3::S3Client const &s3Client, Aws::S3::Model::GetObjectRequest request, uint_fast64_t firstByte, size_t numBytes)
    {
        Aws::String byteRange = "bytes=" + to_string(firstByte) + "-" + to_string(firstByte + numBytes - 1);
        request.SetRange(byteRange);
        cout << "Attempting to download s3://" << request.GetBucket() << "/" << request.GetKey() << " with byterange: \"" << byteRange << "\"" << endl;
        Aws::S3::Model::GetObjectOutcome response = s3Client.GetObject(request);
        if (!response.IsSuccess())
        {
            cout << "Could not download data." << endl;
            cout << response.GetError().GetMessage() << endl;
        }
        size_t totalBytes = response.GetResult().GetContentLength();
        cout << "Finished download. Got " << totalBytes << " bytes." << endl;
    }

    void startDownload(uint_fast64_t firstByte, size_t numBytes)
    {
        if (numBytes > 0)
        {
            m_thread = thread(download, m_s3Client, m_request, firstByte, numBytes);
            downloadSize = numBytes;
        }
    }

    size_t join()
    {
        if (m_thread.joinable())
        {
            m_thread.join();
            return downloadSize;
        }
        else
        {
            return 0;
        }
    }
};
