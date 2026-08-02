#
# phenotypes API Function /phenotypes
#
resource "aws_api_gateway_resource" "phenotypes" {
  path_part   = "phenotypes"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "phenotypes" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.phenotypes.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "phenotypes" {
  rest_api_id = aws_api_gateway_method.phenotypes.rest_api_id
  resource_id = aws_api_gateway_method.phenotypes.resource_id
  http_method = aws_api_gateway_method.phenotypes.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "phenotypes_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.phenotypes.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "phenotypes_post" {
  rest_api_id = aws_api_gateway_method.phenotypes_post.rest_api_id
  resource_id = aws_api_gateway_method.phenotypes_post.resource_id
  http_method = aws_api_gateway_method.phenotypes_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-phenotypes" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.phenotypes.id
}

# wire up lambda phenotypes
resource "aws_api_gateway_integration" "phenotypes" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.phenotypes.id
  http_method             = aws_api_gateway_method.phenotypes.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getPhenotypes.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "phenotypes" {
  rest_api_id = aws_api_gateway_method.phenotypes.rest_api_id
  resource_id = aws_api_gateway_method.phenotypes.resource_id
  http_method = aws_api_gateway_method.phenotypes.http_method
  status_code = aws_api_gateway_method_response.phenotypes.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.phenotypes]
}

resource "aws_api_gateway_integration" "phenotypes_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.phenotypes.id
  http_method             = aws_api_gateway_method.phenotypes_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getPhenotypes.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "phenotypes_post" {
  rest_api_id = aws_api_gateway_method.phenotypes_post.rest_api_id
  resource_id = aws_api_gateway_method.phenotypes_post.resource_id
  http_method = aws_api_gateway_method.phenotypes_post.http_method
  status_code = aws_api_gateway_method_response.phenotypes_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.phenotypes_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIphenotypes" {
  statement_id  = "AllowAPIphenotypesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getPhenotypes.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.phenotypes.path_part}"
}