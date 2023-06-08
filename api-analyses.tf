#
# analyses API Function /analyses
#
resource "aws_api_gateway_resource" "analyses" {
  path_part   = "analyses"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "analyses" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "analyses" {
  rest_api_id = aws_api_gateway_method.analyses.rest_api_id
  resource_id = aws_api_gateway_method.analyses.resource_id
  http_method = aws_api_gateway_method.analyses.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "analyses_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "analyses_post" {
  rest_api_id = aws_api_gateway_method.analyses_post.rest_api_id
  resource_id = aws_api_gateway_method.analyses_post.resource_id
  http_method = aws_api_gateway_method.analyses_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

#
# analyses API Function /analyses/filtering_terms
#
resource "aws_api_gateway_resource" "analyses-filtering_terms" {
  path_part   = "filtering_terms"
  parent_id   = aws_api_gateway_resource.analyses.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "analyses-filtering_terms" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses-filtering_terms.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "analyses-filtering_terms" {
  rest_api_id = aws_api_gateway_method.analyses-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.analyses-filtering_terms.resource_id
  http_method = aws_api_gateway_method.analyses-filtering_terms.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "analyses-filtering_terms_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses-filtering_terms.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "analyses-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.analyses-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.analyses-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.analyses-filtering_terms_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /analyses/{id}
# 
resource "aws_api_gateway_resource" "analyses-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.analyses.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "analyses-id" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses-id.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "analyses-id" {
  rest_api_id = aws_api_gateway_method.analyses-id.rest_api_id
  resource_id = aws_api_gateway_method.analyses-id.resource_id
  http_method = aws_api_gateway_method.analyses-id.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "analyses-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "analyses-id_post" {
  rest_api_id = aws_api_gateway_method.analyses-id_post.rest_api_id
  resource_id = aws_api_gateway_method.analyses-id_post.resource_id
  http_method = aws_api_gateway_method.analyses-id_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /analyses/{id}/g_variants
# 
resource "aws_api_gateway_resource" "analyses-id-g_variants" {
  path_part   = "g_variants"
  parent_id   = aws_api_gateway_resource.analyses-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "analyses-id-g_variants" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses-id-g_variants.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "analyses-id-g_variants" {
  rest_api_id = aws_api_gateway_method.analyses-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.analyses-id-g_variants.resource_id
  http_method = aws_api_gateway_method.analyses-id-g_variants.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "analyses-id-g_variants_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses-id-g_variants.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "analyses-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.analyses-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.analyses-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.analyses-id-g_variants_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-analyses" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.analyses.id
}

module "cors-analyses-filtering_terms" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.analyses-filtering_terms.id
}

module "cors-analyses-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.analyses-id.id
}

module "cors-analyses-id-g_variants" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.analyses-id-g_variants.id
}

# wire up lambda analyses
resource "aws_api_gateway_integration" "analyses" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses.id
  http_method             = aws_api_gateway_method.analyses.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analyses" {
  rest_api_id = aws_api_gateway_method.analyses.rest_api_id
  resource_id = aws_api_gateway_method.analyses.resource_id
  http_method = aws_api_gateway_method.analyses.http_method
  status_code = aws_api_gateway_method_response.analyses.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses]
}

resource "aws_api_gateway_integration" "analyses_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses.id
  http_method             = aws_api_gateway_method.analyses_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analyses_post" {
  rest_api_id = aws_api_gateway_method.analyses_post.rest_api_id
  resource_id = aws_api_gateway_method.analyses_post.resource_id
  http_method = aws_api_gateway_method.analyses_post.http_method
  status_code = aws_api_gateway_method_response.analyses_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses_post]
}

# wire up lambda analyses/filtering_terms
resource "aws_api_gateway_integration" "analyses-filtering_terms" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses-filtering_terms.id
  http_method             = aws_api_gateway_method.analyses-filtering_terms.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analyses-filtering_terms" {
  rest_api_id = aws_api_gateway_method.analyses-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.analyses-filtering_terms.resource_id
  http_method = aws_api_gateway_method.analyses-filtering_terms.http_method
  status_code = aws_api_gateway_method_response.analyses-filtering_terms.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses-filtering_terms]
}

resource "aws_api_gateway_integration" "analyses-filtering_terms_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses-filtering_terms.id
  http_method             = aws_api_gateway_method.analyses-filtering_terms_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analyses-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.analyses-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.analyses-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.analyses-filtering_terms_post.http_method
  status_code = aws_api_gateway_method_response.analyses-filtering_terms_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses-filtering_terms_post]
}

# wire up lambda analyses/{id}
resource "aws_api_gateway_integration" "analyses-id" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses-id.id
  http_method             = aws_api_gateway_method.analyses-id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analyses-id" {
  rest_api_id = aws_api_gateway_method.analyses-id.rest_api_id
  resource_id = aws_api_gateway_method.analyses-id.resource_id
  http_method = aws_api_gateway_method.analyses-id.http_method
  status_code = aws_api_gateway_method_response.analyses-id.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses-id]
}

resource "aws_api_gateway_integration" "analyses-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses-id.id
  http_method             = aws_api_gateway_method.analyses-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analyses-id_post" {
  rest_api_id = aws_api_gateway_method.analyses-id_post.rest_api_id
  resource_id = aws_api_gateway_method.analyses-id_post.resource_id
  http_method = aws_api_gateway_method.analyses-id_post.http_method
  status_code = aws_api_gateway_method_response.analyses-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses-id_post]
}

# wire up lambda analyses/{id}/g_variants
resource "aws_api_gateway_integration" "analyses-id-g_variants" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses-id-g_variants.id
  http_method             = aws_api_gateway_method.analyses-id-g_variants.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analyses-id-g_variants" {
  rest_api_id = aws_api_gateway_method.analyses-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.analyses-id-g_variants.resource_id
  http_method = aws_api_gateway_method.analyses-id-g_variants.http_method
  status_code = aws_api_gateway_method_response.analyses-id-g_variants.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses-id-g_variants]
}

resource "aws_api_gateway_integration" "analyses-id-g_variants_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses-id-g_variants.id
  http_method             = aws_api_gateway_method.analyses-id-g_variants_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "analyses-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.analyses-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.analyses-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.analyses-id-g_variants_post.http_method
  status_code = aws_api_gateway_method_response.analyses-id-g_variants_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses-id-g_variants_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIanalyses" {
  statement_id  = "AllowAPIanalysesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getAnalyses.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.analyses.path_part}"
}

resource "aws_lambda_permission" "APIanalysesFilteringTerms" {
  statement_id  = "AllowAPIanalysesFilteringTermsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getAnalyses.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.analyses.path_part}/${aws_api_gateway_resource.analyses-filtering_terms.path_part}"
}

resource "aws_lambda_permission" "APIanalysesId" {
  statement_id  = "AllowAPIanalysesIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getAnalyses.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.analyses.path_part}/*"
}

resource "aws_lambda_permission" "APIanalysesIdg_variants" {
  statement_id  = "AllowAPIanalysesIdg_variantsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getAnalyses.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.analyses.path_part}/*/${aws_api_gateway_resource.analyses-id-g_variants.path_part}"
}
