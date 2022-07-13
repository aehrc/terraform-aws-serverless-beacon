#
# g_variants API Function /g_variants
#
resource aws_api_gateway_resource g_variants {
  path_part   = "g_variants"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource aws_api_gateway_method g_variants {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants.id
  http_method   = "GET"
  authorization = "NONE"
}

resource aws_api_gateway_method_response g_variants {
  rest_api_id = aws_api_gateway_method.g_variants.rest_api_id
  resource_id = aws_api_gateway_method.g_variants.resource_id
  http_method = aws_api_gateway_method.g_variants.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /g_variants/{id}
# 
resource aws_api_gateway_resource g_variants-id {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.g_variants.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource aws_api_gateway_method g_variants-id {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants-id.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource aws_api_gateway_method_response g_variants-id {
  rest_api_id = aws_api_gateway_method.g_variants-id.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id.resource_id
  http_method = aws_api_gateway_method.g_variants-id.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /g_variants/{id}/biosamples
# 
resource aws_api_gateway_resource g_variants-id-biosamples {
  path_part   = "biosamples"
  parent_id   = aws_api_gateway_resource.g_variants-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource aws_api_gateway_method g_variants-id-biosamples {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants-id-biosamples.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource aws_api_gateway_method_response g_variants-id-biosamples {
  rest_api_id = aws_api_gateway_method.g_variants-id-biosamples.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-biosamples.resource_id
  http_method = aws_api_gateway_method.g_variants-id-biosamples.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module cors-biosamples {
  source = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.g_variants.id
}

module cors-biosamples-id {
  source = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.g_variants-id.id
}

module cors-biosamples-id-biosamples {
  source = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.g_variants-id-biosamples.id
}

# wire up lambda g_variants
resource aws_api_gateway_integration g_variants {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants.id
  http_method             = aws_api_gateway_method.g_variants.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource aws_api_gateway_integration_response g_variants {
  rest_api_id = aws_api_gateway_method.g_variants.rest_api_id
  resource_id = aws_api_gateway_method.g_variants.resource_id
  http_method = aws_api_gateway_method.g_variants.http_method
  status_code = aws_api_gateway_method_response.g_variants.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants]
}

# wire up lambda g_variants/{id}
resource aws_api_gateway_integration g_variants-id {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants-id.id
  http_method             = aws_api_gateway_method.g_variants-id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource aws_api_gateway_integration_response  g_variants-id {
  rest_api_id = aws_api_gateway_method.g_variants-id.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id.resource_id
  http_method = aws_api_gateway_method.g_variants-id.http_method
  status_code = aws_api_gateway_method_response.g_variants-id.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants-id]
}

# wire up lambda g_variants/{id}/biosamples
resource aws_api_gateway_integration g_variants-id-biosamples {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants-id-biosamples.id
  http_method             = aws_api_gateway_method.g_variants-id-biosamples.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource aws_api_gateway_integration_response  g_variants-id-biosamples {
  rest_api_id = aws_api_gateway_method.g_variants-id-biosamples.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-biosamples.resource_id
  http_method = aws_api_gateway_method.g_variants-id-biosamples.http_method
  status_code = aws_api_gateway_method_response.g_variants-id-biosamples.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants-id-biosamples]
}

# permit lambda invokation
resource aws_lambda_permission APIg_variants {
  statement_id = "AllowAPIg_variantsInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-getGenomicVariants.lambda_function_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.g_variants.path_part}"
}

resource aws_lambda_permission APIg_variantsId {
  statement_id = "AllowAPIg_variantsIdInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-getGenomicVariants.lambda_function_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.g_variants.path_part}/*"
}

resource aws_lambda_permission APIg_variantsIdGVariants {
  statement_id = "AllowAPIg_variantsIdGVariantsInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-getGenomicVariants.lambda_function_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.g_variants.path_part}/*/g_variants"
}
