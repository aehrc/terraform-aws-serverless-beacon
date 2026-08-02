#
# snps API Function /snps
#
resource "aws_api_gateway_resource" "snps" {
  path_part   = "snps"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "snps" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.snps.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "snps" {
  rest_api_id = aws_api_gateway_method.snps.rest_api_id
  resource_id = aws_api_gateway_method.snps.resource_id
  http_method = aws_api_gateway_method.snps.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "snps_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.snps.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "snps_post" {
  rest_api_id = aws_api_gateway_method.snps_post.rest_api_id
  resource_id = aws_api_gateway_method.snps_post.resource_id
  http_method = aws_api_gateway_method.snps_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-snps" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.snps.id
}

# wire up lambda snps
resource "aws_api_gateway_integration" "snps" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.snps.id
  http_method             = aws_api_gateway_method.snps.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getSnps.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "snps" {
  rest_api_id = aws_api_gateway_method.snps.rest_api_id
  resource_id = aws_api_gateway_method.snps.resource_id
  http_method = aws_api_gateway_method.snps.http_method
  status_code = aws_api_gateway_method_response.snps.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.snps]
}

resource "aws_api_gateway_integration" "snps_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.snps.id
  http_method             = aws_api_gateway_method.snps_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getSnps.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "snps_post" {
  rest_api_id = aws_api_gateway_method.snps_post.rest_api_id
  resource_id = aws_api_gateway_method.snps_post.resource_id
  http_method = aws_api_gateway_method.snps_post.http_method
  status_code = aws_api_gateway_method_response.snps_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.snps_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIsnps" {
  statement_id  = "AllowAPIsnpsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getSnps.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.snps.path_part}"
}