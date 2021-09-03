#pragma once
#include <string.h>
#include <iostream>

using namespace std;

namespace generalutils {

    struct vcfData  {  
        uint8_t chrom;
        uint64_t pos;
        char ref;
        char alt;
    } __attribute__((packed));

    template <class T>
    T fast_atoi(const char* str, const size_t len) {
        T val = 0;
        for (size_t i=0; i < len; i++) {
            val = (val * 10) + (str[i] - '0');
        }
        return val;
    }

}
