#include <cstdlib>
#include <stdint.h>

static const uint64_t offsets[21] = {0,'0',
        '0'*11ull,
        '0'*111ull,
        '0'*1111ull,
        '0'*11111ull,
        '0'*111111ull,
        '0'*1111111ull,
        '0'*11111111ull,
        '0'*111111111ull,
        '0'*1111111111ull,
        '0'*11111111111ull,
        '0'*111111111111ull,
        '0'*1111111111111ull,
        '0'*11111111111111ull,
        '0'*111111111111111ull,
        '0'*1111111111111111ull,
        '0'*11111111111111111ull,
        '0'*111111111111111111ull,
        '0'*1111111111111111111ull,
        '0'*11111111111111111111ull};

//convert char *s to an unsigned 64bit integer
uint64_t atoui64(const char *s)
{
    uint64_t ret = s[0];
    uint8_t len = 1;
    while(s[len])
    {
        ret = ret*10 + s[len++];
    }
    return ret-offsets[len];
}

//convert char *s to an unsigned 32bit integer
uint32_t atoui32(const char *s)
{
    uint32_t ret = s[0];
    uint8_t len = 1;
    while(s[len])
    {
        ret = ret*10 + s[len++];
    }
    return ret-uint32_t(offsets[len]);
}

//convert char *s to an unsigned 64bit integer
//len is the number of numeric characters
//s does not require the trailing '\0'
uint64_t atoui64(const char *str, uint8_t len)
{
    size_t value = 0;
    switch (len) { // handle up to 20 digits, assume we're 64-bit
        case 20:    {value += str[len-20] * 10000000000000000000ull; [[fallthrough]];}
        case 19:    {value += str[len-19] * 1000000000000000000ull; [[fallthrough]];}
        case 18:    {value += str[len-18] * 100000000000000000ull; [[fallthrough]];}
        case 17:    {value += str[len-17] * 10000000000000000ull; [[fallthrough]];}
        case 16:    {value += str[len-16] * 1000000000000000ull; [[fallthrough]];}
        case 15:    {value += str[len-15] * 100000000000000ull; [[fallthrough]];}
        case 14:    {value += str[len-14] * 10000000000000ull; [[fallthrough]];}
        case 13:    {value += str[len-13] * 1000000000000ull; [[fallthrough]];}
        case 12:    {value += str[len-12] * 100000000000ull; [[fallthrough]];}
        case 11:    {value += str[len-11] * 10000000000ull; [[fallthrough]];}
        case 10:    {value += str[len-10] * 1000000000ull; [[fallthrough]];}
        case  9:    {value += str[len- 9] * 100000000ull; [[fallthrough]];}
        case  8:    {value += str[len- 8] * 10000000ull; [[fallthrough]];}
        case  7:    {value += str[len- 7] * 1000000ull; [[fallthrough]];}
        case  6:    {value += str[len- 6] * 100000ull; [[fallthrough]];}
        case  5:    {value += str[len- 5] * 10000ull; [[fallthrough]];}
        case  4:    {value += str[len- 4] * 1000ull; [[fallthrough]];}
        case  3:    {value += str[len- 3] * 100ull; [[fallthrough]];}
        case  2:    {value += str[len- 2] * 10ull; [[fallthrough]];}
        case  1:    {value += str[len- 1];}
    }
    return value - offsets[len];
}

//convert char *s to an unsigned 32bit integer
//len is the number of numeric characters
//s does not require the trailing '\0'
uint32_t atoui32(const char *str, uint8_t len)
{
    uint32_t value = 0;
    switch (len) { // handle up to 10 digits, assume we're 32-bit
            case 10:    {value += str[len-10] * 1000000000; [[fallthrough]];}
            case  9:    {value += str[len- 9] * 100000000; [[fallthrough]];}
            case  8:    {value += str[len- 8] * 10000000; [[fallthrough]];}
            case  7:    {value += str[len- 7] * 1000000; [[fallthrough]];}
            case  6:    {value += str[len- 6] * 100000; [[fallthrough]];}
            case  5:    {value += str[len- 5] * 10000; [[fallthrough]];}
            case  4:    {value += str[len- 4] * 1000; [[fallthrough]];}
            case  3:    {value += str[len- 3] * 100; [[fallthrough]];}
            case  2:    {value += str[len- 2] * 10; [[fallthrough]];}
            case  1:    {value += str[len- 1];}
        }
    return value - uint32_t(offsets[len]);
}
