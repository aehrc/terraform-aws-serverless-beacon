#
# individuals API Function /individuals
#
resource "aws_api_gateway_resource" "individuals" {
  path_part   = "individuals"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "individuals" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "individuals" {
  rest_api_id = aws_api_gateway_method.individuals.rest_api_id
  resource_id = aws_api_gateway_method.individuals.resource_id
  http_method = aws_api_gateway_method.individuals.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "individuals_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "individuals_post" {
  rest_api_id = aws_api_gateway_method.individuals_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals_post.resource_id
  http_method = aws_api_gateway_method.individuals_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

#
# individuals API Function /individuals/filtering_terms
#
resource "aws_api_gateway_resource" "individuals-filtering_terms" {
  path_part   = "filtering_terms"
  parent_id   = aws_api_gateway_resource.individuals.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "individuals-filtering_terms" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals-filtering_terms.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "individuals-filtering_terms" {
  rest_api_id = aws_api_gateway_method.individuals-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.individuals-filtering_terms.resource_id
  http_method = aws_api_gateway_method.individuals-filtering_terms.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "individuals-filtering_terms_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals-filtering_terms.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "individuals-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.individuals-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.individuals-filtering_terms_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /individuals/{id}
# 
resource "aws_api_gateway_resource" "individuals-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.individuals.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "individuals-id" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals-id.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "individuals-id" {
  rest_api_id = aws_api_gateway_method.individuals-id.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id.resource_id
  http_method = aws_api_gateway_method.individuals-id.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "individuals-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "individuals-id_post" {
  rest_api_id = aws_api_gateway_method.individuals-id_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id_post.resource_id
  http_method = aws_api_gateway_method.individuals-id_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /individuals/{id}/biosamples
# 
resource "aws_api_gateway_resource" "individuals-id-biosamples" {
  path_part   = "biosamples"
  parent_id   = aws_api_gateway_resource.individuals-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "individuals-id-biosamples" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals-id-biosamples.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "individuals-id-biosamples" {
  rest_api_id = aws_api_gateway_method.individuals-id-biosamples.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id-biosamples.resource_id
  http_method = aws_api_gateway_method.individuals-id-biosamples.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "individuals-id-biosamples_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals-id-biosamples.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "individuals-id-biosamples_post" {
  rest_api_id = aws_api_gateway_method.individuals-id-biosamples_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id-biosamples_post.resource_id
  http_method = aws_api_gateway_method.individuals-id-biosamples_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /individuals/{id}/g_variants
# 
resource "aws_api_gateway_resource" "individuals-id-g_variants" {
  path_part   = "g_variants"
  parent_id   = aws_api_gateway_resource.individuals-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "individuals-id-g_variants" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals-id-g_variants.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "individuals-id-g_variants" {
  rest_api_id = aws_api_gateway_method.individuals-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id-g_variants.resource_id
  http_method = aws_api_gateway_method.individuals-id-g_variants.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "individuals-id-g_variants_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.individuals-id-g_variants.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "individuals-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.individuals-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.individuals-id-g_variants_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-individuals" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.individuals.id
}

module "cors-individuals-filtering_terms" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.individuals-filtering_terms.id
}

module "cors-individuals-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.individuals-id.id
}

module "cors-individuals-id-biosamples" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.individuals-id-biosamples.id
}

module "cors-individuals-id-g_variants" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.individuals-id-g_variants.id
}

# wire up lambda individuals
resource "aws_api_gateway_integration" "individuals" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals.id
  http_method             = aws_api_gateway_method.individuals.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals" {
  rest_api_id = aws_api_gateway_method.individuals.rest_api_id
  resource_id = aws_api_gateway_method.individuals.resource_id
  http_method = aws_api_gateway_method.individuals.http_method
  status_code = aws_api_gateway_method_response.individuals.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals]
}

resource "aws_api_gateway_integration" "individuals_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals.id
  http_method             = aws_api_gateway_method.individuals_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals_post" {
  rest_api_id = aws_api_gateway_method.individuals_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals_post.resource_id
  http_method = aws_api_gateway_method.individuals_post.http_method
  status_code = aws_api_gateway_method_response.individuals_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals_post]
}

# wire up lambda individuals/filtering_terms
resource "aws_api_gateway_integration" "individuals-filtering_terms" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals-filtering_terms.id
  http_method             = aws_api_gateway_method.individuals-filtering_terms.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals-filtering_terms" {
  rest_api_id = aws_api_gateway_method.individuals-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.individuals-filtering_terms.resource_id
  http_method = aws_api_gateway_method.individuals-filtering_terms.http_method
  status_code = aws_api_gateway_method_response.individuals-filtering_terms.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals-filtering_terms]
}

resource "aws_api_gateway_integration" "individuals-filtering_terms_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals-filtering_terms.id
  http_method             = aws_api_gateway_method.individuals-filtering_terms_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.individuals-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.individuals-filtering_terms_post.http_method
  status_code = aws_api_gateway_method_response.individuals-filtering_terms_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals-filtering_terms_post]
}

# wire up lambda individuals/{id}
resource "aws_api_gateway_integration" "individuals-id" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals-id.id
  http_method             = aws_api_gateway_method.individuals-id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals-id" {
  rest_api_id = aws_api_gateway_method.individuals-id.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id.resource_id
  http_method = aws_api_gateway_method.individuals-id.http_method
  status_code = aws_api_gateway_method_response.individuals-id.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals-id]
}

resource "aws_api_gateway_integration" "individuals-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals-id.id
  http_method             = aws_api_gateway_method.individuals-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals-id_post" {
  rest_api_id = aws_api_gateway_method.individuals-id_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id_post.resource_id
  http_method = aws_api_gateway_method.individuals-id_post.http_method
  status_code = aws_api_gateway_method_response.individuals-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals-id_post]
}

# wire up lambda individuals/{id}/biosamples
resource "aws_api_gateway_integration" "individuals-id-biosamples" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals-id-biosamples.id
  http_method             = aws_api_gateway_method.individuals-id-biosamples.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals-id-biosamples" {
  rest_api_id = aws_api_gateway_method.individuals-id-biosamples.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id-biosamples.resource_id
  http_method = aws_api_gateway_method.individuals-id-biosamples.http_method
  status_code = aws_api_gateway_method_response.individuals-id-biosamples.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals-id-biosamples]
}

resource "aws_api_gateway_integration" "individuals-id-biosamples_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals-id-biosamples.id
  http_method             = aws_api_gateway_method.individuals-id-biosamples_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals-id-biosamples_post" {
  rest_api_id = aws_api_gateway_method.individuals-id-biosamples_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id-biosamples_post.resource_id
  http_method = aws_api_gateway_method.individuals-id-biosamples_post.http_method
  status_code = aws_api_gateway_method_response.individuals-id-biosamples_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals-id-biosamples_post]
}

# wire up lambda individuals/{id}/g_variants
resource "aws_api_gateway_integration" "individuals-id-g_variants" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals-id-g_variants.id
  http_method             = aws_api_gateway_method.individuals-id-g_variants.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals-id-g_variants" {
  rest_api_id = aws_api_gateway_method.individuals-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id-g_variants.resource_id
  http_method = aws_api_gateway_method.individuals-id-g_variants.http_method
  status_code = aws_api_gateway_method_response.individuals-id-g_variants.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals-id-g_variants]
}

resource "aws_api_gateway_integration" "individuals-id-g_variants_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.individuals-id-g_variants.id
  http_method             = aws_api_gateway_method.individuals-id-g_variants_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getIndividuals.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "individuals-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.individuals-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.individuals-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.individuals-id-g_variants_post.http_method
  status_code = aws_api_gateway_method_response.individuals-id-g_variants_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.individuals-id-g_variants_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIindividuals" {
  statement_id  = "AllowAPIindividualsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getIndividuals.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.individuals.path_part}"
}

resource "aws_lambda_permission" "APIindividualsFilteringTerms" {
  statement_id  = "AllowAPIindividualsFilteringTermsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getIndividuals.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.individuals.path_part}/${aws_api_gateway_resource.individuals-filtering_terms.path_part}"
}

resource "aws_lambda_permission" "APIindividualsId" {
  statement_id  = "AllowAPIindividualsIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getIndividuals.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.individuals.path_part}/*"
}

resource "aws_lambda_permission" "APIindividualsIdbiosamples" {
  statement_id  = "AllowAPIindividualsIdbiosamplesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getIndividuals.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.individuals.path_part}/*/${aws_api_gateway_resource.individuals-id-biosamples.path_part}"
}

resource "aws_lambda_permission" "APIindividualsIdg_variants" {
  statement_id  = "AllowAPIindividualsIdg_variantsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getIndividuals.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.individuals.path_part}/*/${aws_api_gateway_resource.individuals-id-g_variants.path_part}"
}
