#
# g_variants API Function /g_variants
#
resource "aws_api_gateway_resource" "g_variants" {
  path_part   = "g_variants"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "g_variants" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "g_variants" {
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

resource "aws_api_gateway_method" "g_variants_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "g_variants_post" {
  rest_api_id = aws_api_gateway_method.g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.g_variants_post.resource_id
  http_method = aws_api_gateway_method.g_variants_post.http_method
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
resource "aws_api_gateway_resource" "g_variants-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.g_variants.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "g_variants-id" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants-id.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "g_variants-id" {
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

resource "aws_api_gateway_method" "g_variants-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "g_variants-id_post" {
  rest_api_id = aws_api_gateway_method.g_variants-id_post.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id_post.resource_id
  http_method = aws_api_gateway_method.g_variants-id_post.http_method
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
resource "aws_api_gateway_resource" "g_variants-id-biosamples" {
  path_part   = "biosamples"
  parent_id   = aws_api_gateway_resource.g_variants-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "g_variants-id-biosamples" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants-id-biosamples.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "g_variants-id-biosamples" {
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

resource "aws_api_gateway_method" "g_variants-id-biosamples_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants-id-biosamples.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "g_variants-id-biosamples_post" {
  rest_api_id = aws_api_gateway_method.g_variants-id-biosamples_post.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-biosamples_post.resource_id
  http_method = aws_api_gateway_method.g_variants-id-biosamples_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /g_variants/{id}/individuals
# 
resource "aws_api_gateway_resource" "g_variants-id-individuals" {
  path_part   = "individuals"
  parent_id   = aws_api_gateway_resource.g_variants-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "g_variants-id-individuals" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants-id-individuals.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "g_variants-id-individuals" {
  rest_api_id = aws_api_gateway_method.g_variants-id-individuals.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-individuals.resource_id
  http_method = aws_api_gateway_method.g_variants-id-individuals.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "g_variants-id-individuals_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.g_variants-id-individuals.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "g_variants-id-individuals_post" {
  rest_api_id = aws_api_gateway_method.g_variants-id-individuals_post.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-individuals_post.resource_id
  http_method = aws_api_gateway_method.g_variants-id-individuals_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-g_variants" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.g_variants.id
}

module "cors-g_variants-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.g_variants-id.id
}

module "cors-g_variants-id-biosamples" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.g_variants-id-biosamples.id
}

module "cors-g_variants-id-individuals" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.g_variants-id-individuals.id
}

# wire up lambda g_variants
resource "aws_api_gateway_integration" "g_variants" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants.id
  http_method             = aws_api_gateway_method.g_variants.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "g_variants" {
  rest_api_id = aws_api_gateway_method.g_variants.rest_api_id
  resource_id = aws_api_gateway_method.g_variants.resource_id
  http_method = aws_api_gateway_method.g_variants.http_method
  status_code = aws_api_gateway_method_response.g_variants.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants]
}

resource "aws_api_gateway_integration" "g_variants_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants.id
  http_method             = aws_api_gateway_method.g_variants_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "g_variants_post" {
  rest_api_id = aws_api_gateway_method.g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.g_variants_post.resource_id
  http_method = aws_api_gateway_method.g_variants_post.http_method
  status_code = aws_api_gateway_method_response.g_variants_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants_post]
}

# wire up lambda g_variants/{id}
resource "aws_api_gateway_integration" "g_variants-id" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants-id.id
  http_method             = aws_api_gateway_method.g_variants-id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "g_variants-id" {
  rest_api_id = aws_api_gateway_method.g_variants-id.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id.resource_id
  http_method = aws_api_gateway_method.g_variants-id.http_method
  status_code = aws_api_gateway_method_response.g_variants-id.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants-id]
}

resource "aws_api_gateway_integration" "g_variants-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants-id.id
  http_method             = aws_api_gateway_method.g_variants-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "g_variants-id_post" {
  rest_api_id = aws_api_gateway_method.g_variants-id_post.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id_post.resource_id
  http_method = aws_api_gateway_method.g_variants-id_post.http_method
  status_code = aws_api_gateway_method_response.g_variants-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants-id_post]
}

# wire up lambda g_variants/{id}/biosamples
resource "aws_api_gateway_integration" "g_variants-id-biosamples" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants-id-biosamples.id
  http_method             = aws_api_gateway_method.g_variants-id-biosamples.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "g_variants-id-biosamples" {
  rest_api_id = aws_api_gateway_method.g_variants-id-biosamples.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-biosamples.resource_id
  http_method = aws_api_gateway_method.g_variants-id-biosamples.http_method
  status_code = aws_api_gateway_method_response.g_variants-id-biosamples.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants-id-biosamples]
}

resource "aws_api_gateway_integration" "g_variants-id-biosamples_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants-id-biosamples.id
  http_method             = aws_api_gateway_method.g_variants-id-biosamples_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "g_variants-id-biosamples_post" {
  rest_api_id = aws_api_gateway_method.g_variants-id-biosamples_post.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-biosamples_post.resource_id
  http_method = aws_api_gateway_method.g_variants-id-biosamples_post.http_method
  status_code = aws_api_gateway_method_response.g_variants-id-biosamples_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants-id-biosamples_post]
}

# wire up lambda g_variants/{id}/individuals
resource "aws_api_gateway_integration" "g_variants-id-individuals" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants-id-individuals.id
  http_method             = aws_api_gateway_method.g_variants-id-individuals.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "g_variants-id-individuals" {
  rest_api_id = aws_api_gateway_method.g_variants-id-individuals.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-individuals.resource_id
  http_method = aws_api_gateway_method.g_variants-id-individuals.http_method
  status_code = aws_api_gateway_method_response.g_variants-id-individuals.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants-id-individuals]
}

resource "aws_api_gateway_integration" "g_variants-id-individuals_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.g_variants-id-individuals.id
  http_method             = aws_api_gateway_method.g_variants-id-individuals_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getGenomicVariants.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "g_variants-id-individuals_post" {
  rest_api_id = aws_api_gateway_method.g_variants-id-individuals_post.rest_api_id
  resource_id = aws_api_gateway_method.g_variants-id-individuals_post.resource_id
  http_method = aws_api_gateway_method.g_variants-id-individuals_post.http_method
  status_code = aws_api_gateway_method_response.g_variants-id-individuals_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.g_variants-id-individuals_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIg_variants" {
  statement_id  = "AllowAPIg_variantsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getGenomicVariants.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.g_variants.path_part}"
}

resource "aws_lambda_permission" "APIg_variantsId" {
  statement_id  = "AllowAPIg_variantsIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getGenomicVariants.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.g_variants.path_part}/*"
}

resource "aws_lambda_permission" "APIg_variantsIdbiosamples" {
  statement_id  = "AllowAPIg_variantsIdbiosamplesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getGenomicVariants.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.g_variants.path_part}/*/${aws_api_gateway_resource.g_variants-id-biosamples.path_part}"
}

resource "aws_lambda_permission" "APIg_variantsIdindividuals" {
  statement_id  = "AllowAPIg_variantsIdindividualsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getGenomicVariants.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.g_variants.path_part}/*/${aws_api_gateway_resource.g_variants-id-individuals.path_part}"
}
