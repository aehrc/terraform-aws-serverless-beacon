#include "awsutils.hpp"

Aws::String awsutils::getMessageString(aws::lambda_runtime::invocation_request const& req)
{
    Aws::Utils::Json::JsonValue json(req.payload);
    return json.View().GetArray("Records").GetItem(0).GetObject("Sns").GetString("Message");
}
