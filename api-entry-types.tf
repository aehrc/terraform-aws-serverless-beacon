#
# getEntryTypes API Function /entry_types
#
resource "aws_api_gateway_resource" "entry_types" {
  path_part   = "entry_types"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "entry_types" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.entry_types.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "entry_types" {
  rest_api_id = aws_api_gateway_method.entry_types.rest_api_id
  resource_id = aws_api_gateway_method.entry_types.resource_id
  http_method = aws_api_gateway_method.entry_types.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-entry_types" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.entry_types.id
}

# wire up lambda
resource "aws_api_gateway_integration" "entry_types" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.entry_types.id
  http_method             = aws_api_gateway_method.entry_types.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getEntryTypes.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "entry_types" {
  rest_api_id = aws_api_gateway_method.entry_types.rest_api_id
  resource_id = aws_api_gateway_method.entry_types.resource_id
  http_method = aws_api_gateway_method.entry_types.http_method
  status_code = aws_api_gateway_method_response.entry_types.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.entry_types]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIGetEntryTypes" {
  statement_id  = "AllowAPIGetEntryTypesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getEntryTypes.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.entry_types.path_part}"
}
