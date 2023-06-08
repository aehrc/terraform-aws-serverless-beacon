#
# biosamples API Function /biosamples
#
resource "aws_api_gateway_resource" "biosamples" {
  path_part   = "biosamples"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "biosamples" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "biosamples" {
  rest_api_id = aws_api_gateway_method.biosamples.rest_api_id
  resource_id = aws_api_gateway_method.biosamples.resource_id
  http_method = aws_api_gateway_method.biosamples.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "biosamples_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "biosamples_post" {
  rest_api_id = aws_api_gateway_method.biosamples_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples_post.resource_id
  http_method = aws_api_gateway_method.biosamples_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

#
# biosamples API Function /biosamples/filtering_terms
#
resource "aws_api_gateway_resource" "biosamples-filtering_terms" {
  path_part   = "filtering_terms"
  parent_id   = aws_api_gateway_resource.biosamples.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "biosamples-filtering_terms" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-filtering_terms.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "biosamples-filtering_terms" {
  rest_api_id = aws_api_gateway_method.biosamples-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-filtering_terms.resource_id
  http_method = aws_api_gateway_method.biosamples-filtering_terms.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "biosamples-filtering_terms_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-filtering_terms.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "biosamples-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.biosamples-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.biosamples-filtering_terms_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /biosamples/{id}
# 
resource "aws_api_gateway_resource" "biosamples-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.biosamples.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "biosamples-id" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-id.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "biosamples-id" {
  rest_api_id = aws_api_gateway_method.biosamples-id.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id.resource_id
  http_method = aws_api_gateway_method.biosamples-id.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "biosamples-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "biosamples-id_post" {
  rest_api_id = aws_api_gateway_method.biosamples-id_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id_post.resource_id
  http_method = aws_api_gateway_method.biosamples-id_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /biosamples/{id}/analyses
# 
resource "aws_api_gateway_resource" "biosamples-id-analyses" {
  path_part   = "analyses"
  parent_id   = aws_api_gateway_resource.biosamples-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "biosamples-id-analyses" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-id-analyses.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "biosamples-id-analyses" {
  rest_api_id = aws_api_gateway_method.biosamples-id-analyses.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-analyses.resource_id
  http_method = aws_api_gateway_method.biosamples-id-analyses.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "biosamples-id-analyses_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-id-analyses.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "biosamples-id-analyses_post" {
  rest_api_id = aws_api_gateway_method.biosamples-id-analyses_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-analyses_post.resource_id
  http_method = aws_api_gateway_method.biosamples-id-analyses_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /biosamples/{id}/g_variants
# 
resource "aws_api_gateway_resource" "biosamples-id-g_variants" {
  path_part   = "g_variants"
  parent_id   = aws_api_gateway_resource.biosamples-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "biosamples-id-g_variants" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-id-g_variants.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "biosamples-id-g_variants" {
  rest_api_id = aws_api_gateway_method.biosamples-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-g_variants.resource_id
  http_method = aws_api_gateway_method.biosamples-id-g_variants.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "biosamples-id-g_variants_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-id-g_variants.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "biosamples-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.biosamples-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.biosamples-id-g_variants_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /biosamples/{id}/runs
# 
resource "aws_api_gateway_resource" "biosamples-id-runs" {
  path_part   = "runs"
  parent_id   = aws_api_gateway_resource.biosamples-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "biosamples-id-runs" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-id-runs.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "biosamples-id-runs" {
  rest_api_id = aws_api_gateway_method.biosamples-id-runs.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-runs.resource_id
  http_method = aws_api_gateway_method.biosamples-id-runs.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "biosamples-id-runs_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.biosamples-id-runs.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "biosamples-id-runs_post" {
  rest_api_id = aws_api_gateway_method.biosamples-id-runs_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-runs_post.resource_id
  http_method = aws_api_gateway_method.biosamples-id-runs_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-biosamples" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.biosamples.id
}

module "cors-biosamples-filtering_terms" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.biosamples-filtering_terms.id
}

module "cors-biosamples-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.biosamples-id.id
}

module "cors-biosamples-id-analyses" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.biosamples-id-analyses.id
}

module "cors-biosamples-id-g_variants" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.biosamples-id-g_variants.id
}

module "cors-biosamples-id-runs" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.biosamples-id-runs.id
}

# wire up lambda biosamples
resource "aws_api_gateway_integration" "biosamples" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples.id
  http_method             = aws_api_gateway_method.biosamples.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples" {
  rest_api_id = aws_api_gateway_method.biosamples.rest_api_id
  resource_id = aws_api_gateway_method.biosamples.resource_id
  http_method = aws_api_gateway_method.biosamples.http_method
  status_code = aws_api_gateway_method_response.biosamples.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples]
}

resource "aws_api_gateway_integration" "biosamples_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples.id
  http_method             = aws_api_gateway_method.biosamples_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples_post" {
  rest_api_id = aws_api_gateway_method.biosamples_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples_post.resource_id
  http_method = aws_api_gateway_method.biosamples_post.http_method
  status_code = aws_api_gateway_method_response.biosamples_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples_post]
}

# wire up lambda biosamples/filtering_terms
resource "aws_api_gateway_integration" "biosamples-filtering_terms" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-filtering_terms.id
  http_method             = aws_api_gateway_method.biosamples-filtering_terms.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-filtering_terms" {
  rest_api_id = aws_api_gateway_method.biosamples-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-filtering_terms.resource_id
  http_method = aws_api_gateway_method.biosamples-filtering_terms.http_method
  status_code = aws_api_gateway_method_response.biosamples-filtering_terms.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-filtering_terms]
}

resource "aws_api_gateway_integration" "biosamples-filtering_terms_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-filtering_terms.id
  http_method             = aws_api_gateway_method.biosamples-filtering_terms_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.biosamples-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.biosamples-filtering_terms_post.http_method
  status_code = aws_api_gateway_method_response.biosamples-filtering_terms_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-filtering_terms_post]
}

# wire up lambda biosamples/{id}
resource "aws_api_gateway_integration" "biosamples-id" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-id.id
  http_method             = aws_api_gateway_method.biosamples-id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-id" {
  rest_api_id = aws_api_gateway_method.biosamples-id.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id.resource_id
  http_method = aws_api_gateway_method.biosamples-id.http_method
  status_code = aws_api_gateway_method_response.biosamples-id.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-id]
}

resource "aws_api_gateway_integration" "biosamples-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-id.id
  http_method             = aws_api_gateway_method.biosamples-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-id_post" {
  rest_api_id = aws_api_gateway_method.biosamples-id_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id_post.resource_id
  http_method = aws_api_gateway_method.biosamples-id_post.http_method
  status_code = aws_api_gateway_method_response.biosamples-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-id_post]
}

# wire up lambda biosamples/{id}/analyses
resource "aws_api_gateway_integration" "biosamples-id-analyses" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-id-analyses.id
  http_method             = aws_api_gateway_method.biosamples-id-analyses.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-id-analyses" {
  rest_api_id = aws_api_gateway_method.biosamples-id-analyses.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-analyses.resource_id
  http_method = aws_api_gateway_method.biosamples-id-analyses.http_method
  status_code = aws_api_gateway_method_response.biosamples-id-analyses.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-id-analyses]
}

resource "aws_api_gateway_integration" "biosamples-id-analyses_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-id-analyses.id
  http_method             = aws_api_gateway_method.biosamples-id-analyses_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-id-analyses_post" {
  rest_api_id = aws_api_gateway_method.biosamples-id-analyses_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-analyses_post.resource_id
  http_method = aws_api_gateway_method.biosamples-id-analyses_post.http_method
  status_code = aws_api_gateway_method_response.biosamples-id-analyses_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-id-analyses_post]
}

# wire up lambda biosamples/{id}/g_variants
resource "aws_api_gateway_integration" "biosamples-id-g_variants" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-id-g_variants.id
  http_method             = aws_api_gateway_method.biosamples-id-g_variants.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-id-g_variants" {
  rest_api_id = aws_api_gateway_method.biosamples-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-g_variants.resource_id
  http_method = aws_api_gateway_method.biosamples-id-g_variants.http_method
  status_code = aws_api_gateway_method_response.biosamples-id-g_variants.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-id-g_variants]
}

resource "aws_api_gateway_integration" "biosamples-id-g_variants_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-id-g_variants.id
  http_method             = aws_api_gateway_method.biosamples-id-g_variants_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.biosamples-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.biosamples-id-g_variants_post.http_method
  status_code = aws_api_gateway_method_response.biosamples-id-g_variants_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-id-g_variants_post]
}

# wire up lambda biosamples/{id}/runs
resource "aws_api_gateway_integration" "biosamples-id-runs" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-id-runs.id
  http_method             = aws_api_gateway_method.biosamples-id-runs.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-id-runs" {
  rest_api_id = aws_api_gateway_method.biosamples-id-runs.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-runs.resource_id
  http_method = aws_api_gateway_method.biosamples-id-runs.http_method
  status_code = aws_api_gateway_method_response.biosamples-id-runs.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-id-runs]
}

resource "aws_api_gateway_integration" "biosamples-id-runs_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.biosamples-id-runs.id
  http_method             = aws_api_gateway_method.biosamples-id-runs_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getBiosamples.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "biosamples-id-runs_post" {
  rest_api_id = aws_api_gateway_method.biosamples-id-runs_post.rest_api_id
  resource_id = aws_api_gateway_method.biosamples-id-runs_post.resource_id
  http_method = aws_api_gateway_method.biosamples-id-runs_post.http_method
  status_code = aws_api_gateway_method_response.biosamples-id-runs_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.biosamples-id-runs_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIbiosamples" {
  statement_id  = "AllowAPIbiosamplesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getBiosamples.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.biosamples.path_part}"
}

resource "aws_lambda_permission" "APIbiosamplesFilteringTerms" {
  statement_id  = "AllowAPIbiosamplesFilteringTermsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getBiosamples.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.biosamples.path_part}/${aws_api_gateway_resource.biosamples-filtering_terms.path_part}"
}

resource "aws_lambda_permission" "APIbiosamplesId" {
  statement_id  = "AllowAPIbiosamplesIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getBiosamples.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.biosamples.path_part}/*"
}

resource "aws_lambda_permission" "APIbiosamplesIdanalyses" {
  statement_id  = "AllowAPIbiosamplesIdanalysesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getBiosamples.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.biosamples.path_part}/*/${aws_api_gateway_resource.biosamples-id-analyses.path_part}"
}

resource "aws_lambda_permission" "APIbiosamplesIdg_variants" {
  statement_id  = "AllowAPIbiosamplesIdg_variantsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getBiosamples.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.biosamples.path_part}/*/${aws_api_gateway_resource.biosamples-id-g_variants.path_part}"
}

resource "aws_lambda_permission" "APIbiosamplesIdruns" {
  statement_id  = "AllowAPIbiosamplesIdrunsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getBiosamples.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.biosamples.path_part}/*/${aws_api_gateway_resource.biosamples-id-runs.path_part}"
}
