#pragma once

#include <string>

using namespace std;

const string VARIANTS_BUCKET = getenv("VARIANTS_BUCKET");
const string OUTPUT_SIZE_LIMIT = getenv("VCF_S3_OUTPUT_SIZE_LIMIT");
const string SLICE_GAP = getenv("MAX_SLICE_GAP");
const size_t VCF_S3_OUTPUT_SIZE_LIMIT = static_cast<size_t>(atoi(OUTPUT_SIZE_LIMIT.c_str()));
const int MAX_SLICE_GAP = atoi(SLICE_GAP.c_str());
constexpr const char *TAG = "LAMBDA_ALLOC";
constexpr uint_fast32_t BGZIP_MAX_BLOCKSIZE = 65536;
constexpr uint_fast8_t BGZIP_BLOCK_START_LENGTH = 4;
constexpr const uint8_t BGZIP_BLOCK_START[BGZIP_BLOCK_START_LENGTH] = {0x1f, 0x8b, 0x08, 0x04};
constexpr uint_fast8_t BGZIP_FIELD_START_LENGTH = 4;
constexpr const uint8_t BGZIP_FIELD_START[BGZIP_FIELD_START_LENGTH] = {'B', 'C', 0x02, 0x00};
constexpr uint_fast16_t DOWNLOAD_SLICE_NUM = 4; // Maximum number of concurrent downloads
constexpr uint_fast64_t MAX_DOWNLOAD_SLICE_SIZE = 100000000;
constexpr uint_fast8_t XLEN_OFFSET = 10;