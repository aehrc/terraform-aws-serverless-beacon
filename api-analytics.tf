#
# analyses API Function /analytics
#
resource "aws_api_gateway_resource" "analytics" {
  path_part   = "analytics"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_resource" "analytics_proxy" {
  path_part   = "{proxy+}"
  parent_id   = aws_api_gateway_resource.analytics.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "analytics_proxy" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analytics_proxy.id
  http_method   = "ANY"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_method_response" "analytics_proxy" {
  rest_api_id = aws_api_gateway_method.analytics_proxy.rest_api_id
  resource_id = aws_api_gateway_method.analytics_proxy.resource_id
  http_method = aws_api_gateway_method.analytics_proxy.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "analytics_proxy" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  resource_id = aws_api_gateway_resource.analytics_proxy.id
  http_method = aws_api_gateway_method.analytics_proxy.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-analytics.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analytics_proxy" {
  rest_api_id = aws_api_gateway_method.analytics_proxy.rest_api_id
  resource_id = aws_api_gateway_method.analytics_proxy.resource_id
  http_method = aws_api_gateway_method.analytics_proxy.http_method
  status_code = aws_api_gateway_method_response.analytics_proxy.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analytics_proxy]
}

module "cors-analytics-proxy" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.analytics_proxy.id
}

resource "aws_lambda_permission" "APIanalytics_proxy" {
  statement_id  = "AllowAPIanalytics_proxyInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-analytics.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.analytics.path_part}/*"
}
