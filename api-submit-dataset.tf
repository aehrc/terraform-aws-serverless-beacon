#
# submit dataset API Function /submit-dataset
#
resource "aws_api_gateway_resource" "submit-dataset" {
  path_part   = "submit_dataset"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "submit-dataset_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.submit-dataset.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "submit-dataset_post" {
  rest_api_id = aws_api_gateway_method.submit-dataset_post.rest_api_id
  resource_id = aws_api_gateway_method.submit-dataset_post.resource_id
  http_method = aws_api_gateway_method.submit-dataset_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# Update dataset /submit-dataset/{id}
# 
resource "aws_api_gateway_resource" "submit-dataset-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.submit-dataset.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "submit-dataset-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.submit-dataset-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "submit-dataset-id_post" {
  rest_api_id = aws_api_gateway_method.submit-dataset-id_post.rest_api_id
  resource_id = aws_api_gateway_method.submit-dataset-id_post.resource_id
  http_method = aws_api_gateway_method.submit-dataset-id_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-submit-dataset" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.submit-dataset.id
}

module "cors-submit-dataset-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.submit-dataset-id.id
}

# wire up lambda submit-dataset
resource "aws_api_gateway_integration" "submit-dataset_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.submit-dataset.id
  http_method             = aws_api_gateway_method.submit-dataset_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-submitDataset.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "submit-dataset_post" {
  rest_api_id = aws_api_gateway_method.submit-dataset_post.rest_api_id
  resource_id = aws_api_gateway_method.submit-dataset_post.resource_id
  http_method = aws_api_gateway_method.submit-dataset_post.http_method
  status_code = aws_api_gateway_method_response.submit-dataset_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-dataset_post]
}

resource "aws_api_gateway_integration" "submit-dataset-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.submit-dataset-id.id
  http_method             = aws_api_gateway_method.submit-dataset-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-submitDataset.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "submit-dataset-id_post" {
  rest_api_id = aws_api_gateway_method.submit-dataset-id_post.rest_api_id
  resource_id = aws_api_gateway_method.submit-dataset-id_post.resource_id
  http_method = aws_api_gateway_method.submit-dataset-id_post.http_method
  status_code = aws_api_gateway_method_response.submit-dataset-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-dataset-id_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIsubmit-dataset" {
  statement_id  = "AllowAPIsubmit-datasetInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-submitDataset.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.submit-dataset.path_part}"
}

resource "aws_lambda_permission" "APIsubmit-datasetId" {
  statement_id  = "AllowAPIsubmit-datasetIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-submitDataset.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.submit-dataset.path_part}/*"
}
