#
# index API Function /index
#
resource "aws_api_gateway_resource" "index" {
  path_part   = "index"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "index_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.index.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "index_post" {
  rest_api_id = aws_api_gateway_method.index_post.rest_api_id
  resource_id = aws_api_gateway_method.index_post.resource_id
  http_method = aws_api_gateway_method.index_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-index" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.index.id
}

# wire up lambda index
resource "aws_api_gateway_integration" "index_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.index.id
  http_method             = aws_api_gateway_method.index_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-indexer.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "index_post" {
  rest_api_id = aws_api_gateway_method.index_post.rest_api_id
  resource_id = aws_api_gateway_method.index_post.resource_id
  http_method = aws_api_gateway_method.index_post.http_method
  status_code = aws_api_gateway_method_response.index_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.index_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIindex" {
  statement_id  = "AllowAPIindexInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-indexer.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.index.path_part}"
}
