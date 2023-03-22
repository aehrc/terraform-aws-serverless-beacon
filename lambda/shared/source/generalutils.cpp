#include "generalutils.hpp"
#include <sstream>
#include <iomanip>

namespace generalutils {
    string to_zero_lead(const uint64_t value, const unsigned precision) {
        ostringstream oss;
        oss << setw(precision) << setfill('0') << value;
        return oss.str();
    }
}
