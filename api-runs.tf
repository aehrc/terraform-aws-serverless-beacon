#
# runs API Function /runs
#
resource "aws_api_gateway_resource" "runs" {
  path_part   = "runs"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "runs" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "runs" {
  rest_api_id = aws_api_gateway_method.runs.rest_api_id
  resource_id = aws_api_gateway_method.runs.resource_id
  http_method = aws_api_gateway_method.runs.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "runs_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "runs_post" {
  rest_api_id = aws_api_gateway_method.runs_post.rest_api_id
  resource_id = aws_api_gateway_method.runs_post.resource_id
  http_method = aws_api_gateway_method.runs_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

#
# runs API Function /runs/filtering_terms
#
resource "aws_api_gateway_resource" "runs-filtering_terms" {
  path_part   = "filtering_terms"
  parent_id   = aws_api_gateway_resource.runs.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "runs-filtering_terms" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs-filtering_terms.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "runs-filtering_terms" {
  rest_api_id = aws_api_gateway_method.runs-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.runs-filtering_terms.resource_id
  http_method = aws_api_gateway_method.runs-filtering_terms.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "runs-filtering_terms_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs-filtering_terms.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "runs-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.runs-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.runs-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.runs-filtering_terms_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /runs/{id}
# 
resource "aws_api_gateway_resource" "runs-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.runs.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "runs-id" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs-id.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "runs-id" {
  rest_api_id = aws_api_gateway_method.runs-id.rest_api_id
  resource_id = aws_api_gateway_method.runs-id.resource_id
  http_method = aws_api_gateway_method.runs-id.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "runs-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "runs-id_post" {
  rest_api_id = aws_api_gateway_method.runs-id_post.rest_api_id
  resource_id = aws_api_gateway_method.runs-id_post.resource_id
  http_method = aws_api_gateway_method.runs-id_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /runs/{id}/analyses
# 
resource "aws_api_gateway_resource" "runs-id-analyses" {
  path_part   = "analyses"
  parent_id   = aws_api_gateway_resource.runs-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "runs-id-analyses" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs-id-analyses.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "runs-id-analyses" {
  rest_api_id = aws_api_gateway_method.runs-id-analyses.rest_api_id
  resource_id = aws_api_gateway_method.runs-id-analyses.resource_id
  http_method = aws_api_gateway_method.runs-id-analyses.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "runs-id-analyses_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs-id-analyses.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "runs-id-analyses_post" {
  rest_api_id = aws_api_gateway_method.runs-id-analyses_post.rest_api_id
  resource_id = aws_api_gateway_method.runs-id-analyses_post.resource_id
  http_method = aws_api_gateway_method.runs-id-analyses_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /runs/{id}/g_variants
# 
resource "aws_api_gateway_resource" "runs-id-g_variants" {
  path_part   = "g_variants"
  parent_id   = aws_api_gateway_resource.runs-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "runs-id-g_variants" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs-id-g_variants.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "runs-id-g_variants" {
  rest_api_id = aws_api_gateway_method.runs-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.runs-id-g_variants.resource_id
  http_method = aws_api_gateway_method.runs-id-g_variants.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "runs-id-g_variants_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.runs-id-g_variants.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "runs-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.runs-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.runs-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.runs-id-g_variants_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-runs" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.runs.id
}

module "cors-runs-filtering_terms" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.runs-filtering_terms.id
}

module "cors-runs-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.runs-id.id
}

module "cors-runs-id-analyses" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.runs-id-analyses.id
}

module "cors-runs-id-g_variants" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.runs-id-g_variants.id
}

# wire up lambda runs
resource "aws_api_gateway_integration" "runs" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs.id
  http_method             = aws_api_gateway_method.runs.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs" {
  rest_api_id = aws_api_gateway_method.runs.rest_api_id
  resource_id = aws_api_gateway_method.runs.resource_id
  http_method = aws_api_gateway_method.runs.http_method
  status_code = aws_api_gateway_method_response.runs.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs]
}

resource "aws_api_gateway_integration" "runs_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs.id
  http_method             = aws_api_gateway_method.runs_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs_post" {
  rest_api_id = aws_api_gateway_method.runs_post.rest_api_id
  resource_id = aws_api_gateway_method.runs_post.resource_id
  http_method = aws_api_gateway_method.runs_post.http_method
  status_code = aws_api_gateway_method_response.runs_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs_post]
}

# wire up lambda runs/filtering_terms
resource "aws_api_gateway_integration" "runs-filtering_terms" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs-filtering_terms.id
  http_method             = aws_api_gateway_method.runs-filtering_terms.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs-filtering_terms" {
  rest_api_id = aws_api_gateway_method.runs-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.runs-filtering_terms.resource_id
  http_method = aws_api_gateway_method.runs-filtering_terms.http_method
  status_code = aws_api_gateway_method_response.runs-filtering_terms.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs-filtering_terms]
}

resource "aws_api_gateway_integration" "runs-filtering_terms_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs-filtering_terms.id
  http_method             = aws_api_gateway_method.runs-filtering_terms_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.runs-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.runs-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.runs-filtering_terms_post.http_method
  status_code = aws_api_gateway_method_response.runs-filtering_terms_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs-filtering_terms_post]
}

# wire up lambda runs/{id}
resource "aws_api_gateway_integration" "runs-id" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs-id.id
  http_method             = aws_api_gateway_method.runs-id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs-id" {
  rest_api_id = aws_api_gateway_method.runs-id.rest_api_id
  resource_id = aws_api_gateway_method.runs-id.resource_id
  http_method = aws_api_gateway_method.runs-id.http_method
  status_code = aws_api_gateway_method_response.runs-id.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs-id]
}

resource "aws_api_gateway_integration" "runs-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs-id.id
  http_method             = aws_api_gateway_method.runs-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs-id_post" {
  rest_api_id = aws_api_gateway_method.runs-id_post.rest_api_id
  resource_id = aws_api_gateway_method.runs-id_post.resource_id
  http_method = aws_api_gateway_method.runs-id_post.http_method
  status_code = aws_api_gateway_method_response.runs-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs-id_post]
}

# wire up lambda runs/{id}/analyses
resource "aws_api_gateway_integration" "runs-id-analyses" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs-id-analyses.id
  http_method             = aws_api_gateway_method.runs-id-analyses.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs-id-analyses" {
  rest_api_id = aws_api_gateway_method.runs-id-analyses.rest_api_id
  resource_id = aws_api_gateway_method.runs-id-analyses.resource_id
  http_method = aws_api_gateway_method.runs-id-analyses.http_method
  status_code = aws_api_gateway_method_response.runs-id-analyses.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs-id-analyses]
}

resource "aws_api_gateway_integration" "runs-id-analyses_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs-id-analyses.id
  http_method             = aws_api_gateway_method.runs-id-analyses_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs-id-analyses_post" {
  rest_api_id = aws_api_gateway_method.runs-id-analyses_post.rest_api_id
  resource_id = aws_api_gateway_method.runs-id-analyses_post.resource_id
  http_method = aws_api_gateway_method.runs-id-analyses_post.http_method
  status_code = aws_api_gateway_method_response.runs-id-analyses_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs-id-analyses_post]
}

# wire up lambda runs/{id}/g_variants
resource "aws_api_gateway_integration" "runs-id-g_variants" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs-id-g_variants.id
  http_method             = aws_api_gateway_method.runs-id-g_variants.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs-id-g_variants" {
  rest_api_id = aws_api_gateway_method.runs-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.runs-id-g_variants.resource_id
  http_method = aws_api_gateway_method.runs-id-g_variants.http_method
  status_code = aws_api_gateway_method_response.runs-id-g_variants.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs-id-g_variants]
}

resource "aws_api_gateway_integration" "runs-id-g_variants_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.runs-id-g_variants.id
  http_method             = aws_api_gateway_method.runs-id-g_variants_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getRuns.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "runs-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.runs-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.runs-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.runs-id-g_variants_post.http_method
  status_code = aws_api_gateway_method_response.runs-id-g_variants_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.runs-id-g_variants_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIruns" {
  statement_id  = "AllowAPIrunsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getRuns.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.runs.path_part}"
}

resource "aws_lambda_permission" "APIrunsFilteringTerms" {
  statement_id  = "AllowAPIrunsFilteringTermsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getRuns.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.runs.path_part}/${aws_api_gateway_resource.runs-filtering_terms.path_part}"
}

resource "aws_lambda_permission" "APIrunsId" {
  statement_id  = "AllowAPIrunsIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getRuns.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.runs.path_part}/*"
}

resource "aws_lambda_permission" "APIrunsIdanalyses" {
  statement_id  = "AllowAPIrunsIdanalysesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getRuns.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.runs.path_part}/*/${aws_api_gateway_resource.runs-id-analyses.path_part}"
}

resource "aws_lambda_permission" "APIrunsIdg_variants" {
  statement_id  = "AllowAPIrunsIdg_variantsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getRuns.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.runs.path_part}/*/${aws_api_gateway_resource.runs-id-g_variants.path_part}"
}
