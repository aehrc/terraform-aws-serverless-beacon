#pragma once
#include <string.h>
#include <queue>
#include <map>
#include <iostream>

using namespace std;

namespace generalutils {

    struct vcfData  {  
        uint64_t pos;
        string ref;
        string alt;
    };

    // Contig to number lookup, must not exceed 15
    // as we are packing two into one byte
    const map<char, uint8_t> sequenceToBinary = {
        {'A', 1},
        {'C', 2},
        {'G', 3},
        {'T', 4},
        {'N', 5},
        {'a', 1},
        {'c', 2},
        {'g', 3},
        {'t', 4},
        {'n', 5},
        {'*', 6},
        {'.', 7},
        // Spare Positions
        // {'-',13},
        // {'-',14},
        // {'-',15},
    };

    template <class T>
    T fast_atoi(const char* str, const size_t len) {
        T val = 0;
        for (size_t i=0; i < len; i++) {
            val = (T)((val * 10) + (str[i] - '0'));
        }
        return val;
    }

    string to_zero_lead(const uint64_t value, const unsigned precision);
}
