#
# submit cohort API Function /submit-cohort
#
resource "aws_api_gateway_resource" "submit-cohort" {
  path_part   = "submit_cohort"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "submit-cohort_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.submit-cohort.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "submit-cohort_post" {
  rest_api_id = aws_api_gateway_method.submit-cohort_post.rest_api_id
  resource_id = aws_api_gateway_method.submit-cohort_post.resource_id
  http_method = aws_api_gateway_method.submit-cohort_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# Update cohort /submit-cohort/{id}
# 
resource "aws_api_gateway_resource" "submit-cohort-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.submit-cohort.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "submit-cohort-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.submit-cohort-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "submit-cohort-id_post" {
  rest_api_id = aws_api_gateway_method.submit-cohort-id_post.rest_api_id
  resource_id = aws_api_gateway_method.submit-cohort-id_post.resource_id
  http_method = aws_api_gateway_method.submit-cohort-id_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-submit-cohort" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.submit-cohort.id
}

module "cors-submit-cohort-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.submit-cohort-id.id
}

# wire up lambda submit-cohort
resource "aws_api_gateway_integration" "submit-cohort_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.submit-cohort.id
  http_method             = aws_api_gateway_method.submit-cohort_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-submitDataset.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "submit-cohort_post" {
  rest_api_id = aws_api_gateway_method.submit-cohort_post.rest_api_id
  resource_id = aws_api_gateway_method.submit-cohort_post.resource_id
  http_method = aws_api_gateway_method.submit-cohort_post.http_method
  status_code = aws_api_gateway_method_response.submit-cohort_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-cohort_post]
}

resource "aws_api_gateway_integration" "submit-cohort-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.submit-cohort-id.id
  http_method             = aws_api_gateway_method.submit-cohort-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-submitDataset.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "submit-cohort-id_post" {
  rest_api_id = aws_api_gateway_method.submit-cohort-id_post.rest_api_id
  resource_id = aws_api_gateway_method.submit-cohort-id_post.resource_id
  http_method = aws_api_gateway_method.submit-cohort-id_post.http_method
  status_code = aws_api_gateway_method_response.submit-cohort-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-cohort-id_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIsubmit-cohort" {
  statement_id  = "AllowAPIsubmit-cohortInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-submitDataset.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.submit-cohort.path_part}"
}

resource "aws_lambda_permission" "APIsubmit-cohortId" {
  statement_id  = "AllowAPIsubmit-cohortIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-submitDataset.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.submit-cohort.path_part}/*"
}
