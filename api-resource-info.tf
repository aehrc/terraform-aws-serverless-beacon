#
# getInfo API Function /info
#
resource "aws_api_gateway_resource" "info" {
  path_part   = "info"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "info" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.info.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "info" {
  rest_api_id = aws_api_gateway_method.info.rest_api_id
  resource_id = aws_api_gateway_method.info.resource_id
  http_method = aws_api_gateway_method.info.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# getInfo API Function /
# 
resource "aws_api_gateway_method" "root-get" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "root-get" {
  rest_api_id = aws_api_gateway_method.root-get.rest_api_id
  resource_id = aws_api_gateway_method.root-get.resource_id
  http_method = aws_api_gateway_method.root-get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-info" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.info.id
}

module "cors-info-root" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_method.root-get.resource_id
}

# wire up lambda
resource "aws_api_gateway_integration" "info" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.info.id
  http_method             = aws_api_gateway_method.info.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getInfo.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "info" {
  rest_api_id = aws_api_gateway_method.info.rest_api_id
  resource_id = aws_api_gateway_method.info.resource_id
  http_method = aws_api_gateway_method.info.http_method
  status_code = aws_api_gateway_method_response.info.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.info]
}

resource "aws_api_gateway_integration" "root-get" {
  rest_api_id             = aws_api_gateway_method.root-get.rest_api_id
  resource_id             = aws_api_gateway_method.root-get.resource_id
  http_method             = aws_api_gateway_method.root-get.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getInfo.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "root-get" {
  rest_api_id = aws_api_gateway_method.root-get.rest_api_id
  resource_id = aws_api_gateway_method.root-get.resource_id
  http_method = aws_api_gateway_method.root-get.http_method
  status_code = aws_api_gateway_method_response.root-get.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.root-get]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIGetInfo" {
  statement_id  = "AllowAPIGetInfoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getInfo.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.info.path_part}"
}

resource "aws_lambda_permission" "APIGetinfo-root" {
  statement_id  = "AllowAPIGetinfoRootInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getInfo.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/"
}

