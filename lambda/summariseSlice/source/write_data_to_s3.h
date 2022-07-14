#pragma once

#include <iostream>
#include <queue>
#include <stdint.h>
#include <stdlib.h>
#include <regex>
#include <generalutils.hpp>
#include <gzip.hpp>

#include <aws/core/Aws.h>
#include <aws/s3/S3Client.h>
#include <aws/s3/model/PutObjectRequest.h>

#include "fast_atoi.h"
#include "stopwatch.h"
#include "constants.h"

using namespace std;

class writeDataToS3
{
private:
    string s3BucketKey;
    Aws::S3::S3Client const &s3Client;
    queue<generalutils::vcfData> vcfBuffer;
    uint16_t startBasePairRegion;
    string contig = "";

    int stringToFile(char *fileBuffer, string &ref, string &alt)
    {
        uint16_t length = static_cast<uint16_t>(ref.size() + alt.size() + 1);
        memcpy(&fileBuffer[0], reinterpret_cast<char *>(&length), sizeof(uint16_t));
        string outString = ref + "_" + alt;
        memcpy(&fileBuffer[2], outString.c_str(), length);
        return length + sizeof(uint16_t); // Return the string length and the length int
    }

    bool saveOutputToS3(string objectName, Aws::S3::S3Client const &client, queue<generalutils::vcfData> &input)
    {
        size_t bufferSize = VCF_S3_OUTPUT_SIZE_LIMIT;
        char *fileBuffer = new char[VCF_S3_OUTPUT_SIZE_LIMIT];
        unsigned int bufferLength = 0;
        size_t accBufferLength = 0;

        const std::shared_ptr<Aws::IOStream> input_data = Aws::MakeShared<Aws::StringStream>(TAG, std::stringstream::in | std::stringstream::out | std::stringstream::binary);
        while (!input.empty())
        {
            if (bufferLength + input.front().ref.size() + input.front().alt.size() + sizeof(input.front().pos) > bufferSize)
            {
                gzip gz(*input_data, 0, fileBuffer, bufferLength);
                gz.deflateFile(Z_BEST_COMPRESSION);
                accBufferLength += bufferLength;
                bufferLength = 0;
            }
            memcpy(&fileBuffer[bufferLength], reinterpret_cast<char *>(&input.front().pos), sizeof(input.front().pos));
            bufferLength += sizeof(input.front().pos);
            bufferLength += stringToFile(&fileBuffer[bufferLength], input.front().ref, input.front().alt);
            input.pop();
        }

        if (bufferLength > 0)
        {
            gzip gz(*input_data, 0, fileBuffer, bufferLength);
            gz.deflateFile(Z_BEST_COMPRESSION);
            accBufferLength += bufferLength;
        }
        delete[] fileBuffer;

        // input_data->write(gzipBuffer, bufferSize);
        // input_data->seekg( 0, ios::end );
        // objectName += "-" + to_string(input_data->tellg());
        objectName += "-" + to_string(accBufferLength);

        Aws::S3::Model::PutObjectRequest request;
        request.SetBucket(VARIANTS_BUCKET);
        request.SetKey(objectName);
        request.SetBody(input_data);

        Aws::S3::Model::PutObjectOutcome outcome = client.PutObject(request);

        if (!outcome.IsSuccess())
        {
            cout << "Error: PutObjectBuffer: " << outcome.GetError().GetMessage() << endl;
            return false;
        }
        else
        {
            cout << "Success: Object '" << objectName << "' uploaded to bucket '" << VARIANTS_BUCKET << "'." << endl;
            return true;
        }
    }

    void saveNewFile()
    {
        if (vcfBuffer.size() > 0)
        {
            string fileNameAppend = "vcf-summaries/contig/" + contig + "/" + s3BucketKey + "/regions/" + to_string(vcfBuffer.front().pos) + "-" + to_string(vcfBuffer.back().pos);
            saveOutputToS3(fileNameAppend, s3Client, vcfBuffer);
        }
    }

    string compressSeq(const char *s, size_t n)
    {
        uint8_t contigBin;
        if (n == 1)
        {
            contigBin = generalutils::sequenceToBinary.at(s[0]);
            return string(1, contigBin);
        }

        // TODO look into ways to compress this a little
        // Ideas: DEL, INS, DUP could be compressed into one byte
        // Remove ':' char
        if (s[0] == '<' && s[n - 1] == '>')
        {
            // Return the contents of the variant genome
            return string(&s[1], n - 2);
        }

        string concat = "";
        // Pack two chars into one byte by using custom compression
        for (size_t i = 0; i < n; i += 2)
        {
            contigBin = generalutils::sequenceToBinary.at(s[i]);
            if (i + 1 < n)
            {
                contigBin = contigBin << 4;
                contigBin |= generalutils::sequenceToBinary.at(s[i + 1]);
            }
            concat.append((char *)(&contigBin));
        }
        return concat;
    }

public:
    writeDataToS3(string location, Aws::S3::S3Client const &client) : s3Client(client)
    {
        // Remove leading "s3://" and trailing ".vcf.gz"
        s3BucketKey = location.substr(5, location.size() - 12);
        replace(s3BucketKey.begin(), s3BucketKey.end(), '/', '%');
    }

    ~writeDataToS3()
    {
        saveNewFile();
    }

    // Read upto the INFO field
    void recordHeader(VcfChunkReader &reader)
    {
        generalutils::vcfData d;
        uint8_t loopPos = 0;

        if (contig.length() != 0)
        {
            reader.skipPast<1, '\t'>();
            loopPos = 1;
        }

        do
        {
            const char lastChar = reader.readPastChars<'\t', ','>();
            if (lastChar == '\0')
            {
                // EOF in the middle of CHROM POS REF ALT portion of vcf line, don't include this
                break;
            }
            const char *firstChar_p = reader.getReadStart();
            const size_t numChars = reader.getReadLength();
            if (numChars >= 1)
            {
                switch (++loopPos)
                {
                // one contig per read file
                case 1:
                    contig = string(firstChar_p, numChars);
                    break;
                case 2:
                    d.pos = generalutils::fast_atoi<uint64_t>(firstChar_p, numChars);

                    if (vcfBuffer.size() > 0)
                    {
                        if (d.pos < vcfBuffer.back().pos)
                        {
                            cout << "d.pos: " << d.pos << " vcfBuffer.back().pos: " << vcfBuffer.back().pos << endl;
                            throw runtime_error("unsorted file");
                        }

                        // Remove large gaps in file data by saving a new file when a large gap is found
                        if (d.pos > vcfBuffer.back().pos + MAX_SLICE_GAP)
                        {
                            saveNewFile();
                        }
                    }
                    reader.skipPast<1, '\t'>();
                    loopPos++;
                    break;
                case 4:
                    d.ref = compressSeq(firstChar_p, numChars);
                    break;
                case 5:
                    d.alt = compressSeq(firstChar_p, numChars);

                    // If we have more ref to proccess decrement the loop so we get the next
                    if (lastChar == ',')
                    {
                        loopPos--;
                    }

                    vcfBuffer.push(d);
                    // cout << "last char: " << lastChar << " " << (lastChar == ',') << endl;
                    break;
                default:
                    break;
                }
            }
        } while (loopPos <= 4);

        // Skip the last two fields so we exit with the reader pointing to the INFO field
        reader.skipPast<2, '\t'>();

        // Save the buffer to a file if we have reached a size limit
        if (vcfBuffer.size() > VCF_S3_OUTPUT_SIZE_LIMIT)
        {
            saveNewFile();
        }
    }
};
