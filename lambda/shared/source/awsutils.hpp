#pragma once

#include <iostream>
#include <string>
#include <sstream>
#include <algorithm>
#include <iterator>
#include <iostream>

#include <aws/core/Aws.h>
#include <aws/lambda-runtime/runtime.h>
#include <aws/core/utils/json/JsonSerializer.h>


using namespace std;
using namespace Aws::Utils::Json;

class awsutils {
    public:
    static Aws::String getMessageString(aws::lambda_runtime::invocation_request const& req);
};
