#
# datasets API Function /datasets
#
resource "aws_api_gateway_resource" "datasets" {
  path_part   = "datasets"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "datasets" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "datasets" {
  rest_api_id = aws_api_gateway_method.datasets.rest_api_id
  resource_id = aws_api_gateway_method.datasets.resource_id
  http_method = aws_api_gateway_method.datasets.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "datasets_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "datasets_post" {
  rest_api_id = aws_api_gateway_method.datasets_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets_post.resource_id
  http_method = aws_api_gateway_method.datasets_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

#
# datasets API Function /datasets/filtering_terms
#
resource "aws_api_gateway_resource" "datasets-filtering_terms" {
  path_part   = "filtering_terms"
  parent_id   = aws_api_gateway_resource.datasets.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "datasets-filtering_terms" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-filtering_terms.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "datasets-filtering_terms" {
  rest_api_id = aws_api_gateway_method.datasets-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.datasets-filtering_terms.resource_id
  http_method = aws_api_gateway_method.datasets-filtering_terms.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "datasets-filtering_terms_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-filtering_terms.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "datasets-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.datasets-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.datasets-filtering_terms_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /datasets/{id}
# 
resource "aws_api_gateway_resource" "datasets-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.datasets.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "datasets-id" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id" {
  rest_api_id = aws_api_gateway_method.datasets-id.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id.resource_id
  http_method = aws_api_gateway_method.datasets-id.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "datasets-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id_post" {
  rest_api_id = aws_api_gateway_method.datasets-id_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id_post.resource_id
  http_method = aws_api_gateway_method.datasets-id_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /datasets/{id}/filtering_terms
# 
resource "aws_api_gateway_resource" "datasets-id-filtering_terms" {
  path_part   = "filtering_terms"
  parent_id   = aws_api_gateway_resource.datasets-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "datasets-id-filtering_terms" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id-filtering_terms.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id-filtering_terms" {
  rest_api_id = aws_api_gateway_method.datasets-id-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-filtering_terms.resource_id
  http_method = aws_api_gateway_method.datasets-id-filtering_terms.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "datasets-id-filtering_terms_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id-filtering_terms.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.datasets-id-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.datasets-id-filtering_terms_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /datasets/{id}/biosamples
# 
resource "aws_api_gateway_resource" "datasets-id-biosamples" {
  path_part   = "biosamples"
  parent_id   = aws_api_gateway_resource.datasets-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "datasets-id-biosamples" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id-biosamples.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id-biosamples" {
  rest_api_id = aws_api_gateway_method.datasets-id-biosamples.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-biosamples.resource_id
  http_method = aws_api_gateway_method.datasets-id-biosamples.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "datasets-id-biosamples_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id-biosamples.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id-biosamples_post" {
  rest_api_id = aws_api_gateway_method.datasets-id-biosamples_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-biosamples_post.resource_id
  http_method = aws_api_gateway_method.datasets-id-biosamples_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /datasets/{id}/g_variants
# 
resource "aws_api_gateway_resource" "datasets-id-g_variants" {
  path_part   = "g_variants"
  parent_id   = aws_api_gateway_resource.datasets-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "datasets-id-g_variants" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id-g_variants.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id-g_variants" {
  rest_api_id = aws_api_gateway_method.datasets-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-g_variants.resource_id
  http_method = aws_api_gateway_method.datasets-id-g_variants.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "datasets-id-g_variants_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id-g_variants.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.datasets-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.datasets-id-g_variants_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /datasets/{id}/individuals
# 
resource "aws_api_gateway_resource" "datasets-id-individuals" {
  path_part   = "individuals"
  parent_id   = aws_api_gateway_resource.datasets-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "datasets-id-individuals" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id-individuals.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id-individuals" {
  rest_api_id = aws_api_gateway_method.datasets-id-individuals.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-individuals.resource_id
  http_method = aws_api_gateway_method.datasets-id-individuals.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "datasets-id-individuals_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.datasets-id-individuals.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "datasets-id-individuals_post" {
  rest_api_id = aws_api_gateway_method.datasets-id-individuals_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-individuals_post.resource_id
  http_method = aws_api_gateway_method.datasets-id-individuals_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-datasets" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.datasets.id
}

module "cors-datasets-filtering_terms" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.datasets-filtering_terms.id
}

module "cors-datasets-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.datasets-id.id
}

module "cors-datasets-id-filtering_terms" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.datasets-id-filtering_terms.id
}

module "cors-datasets-id-biosamples" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.datasets-id-biosamples.id
}

module "cors-datasets-id-g_variants" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.datasets-id-g_variants.id
}

module "cors-datasets-id-individuals" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.datasets-id-individuals.id
}

# wire up lambda datasets
resource "aws_api_gateway_integration" "datasets" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets.id
  http_method             = aws_api_gateway_method.datasets.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets" {
  rest_api_id = aws_api_gateway_method.datasets.rest_api_id
  resource_id = aws_api_gateway_method.datasets.resource_id
  http_method = aws_api_gateway_method.datasets.http_method
  status_code = aws_api_gateway_method_response.datasets.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets]
}

resource "aws_api_gateway_integration" "datasets_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets.id
  http_method             = aws_api_gateway_method.datasets_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets_post" {
  rest_api_id = aws_api_gateway_method.datasets_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets_post.resource_id
  http_method = aws_api_gateway_method.datasets_post.http_method
  status_code = aws_api_gateway_method_response.datasets_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets_post]
}

# wire up lambda datasets/filtering_terms
resource "aws_api_gateway_integration" "datasets-filtering_terms" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-filtering_terms.id
  http_method             = aws_api_gateway_method.datasets-filtering_terms.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-filtering_terms" {
  rest_api_id = aws_api_gateway_method.datasets-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.datasets-filtering_terms.resource_id
  http_method = aws_api_gateway_method.datasets-filtering_terms.http_method
  status_code = aws_api_gateway_method_response.datasets-filtering_terms.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-filtering_terms]
}

resource "aws_api_gateway_integration" "datasets-filtering_terms_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-filtering_terms.id
  http_method             = aws_api_gateway_method.datasets-filtering_terms_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.datasets-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.datasets-filtering_terms_post.http_method
  status_code = aws_api_gateway_method_response.datasets-filtering_terms_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-filtering_terms_post]
}

# wire up lambda datasets/{id}
resource "aws_api_gateway_integration" "datasets-id" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id.id
  http_method             = aws_api_gateway_method.datasets-id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id" {
  rest_api_id = aws_api_gateway_method.datasets-id.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id.resource_id
  http_method = aws_api_gateway_method.datasets-id.http_method
  status_code = aws_api_gateway_method_response.datasets-id.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id]
}

resource "aws_api_gateway_integration" "datasets-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id.id
  http_method             = aws_api_gateway_method.datasets-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id_post" {
  rest_api_id = aws_api_gateway_method.datasets-id_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id_post.resource_id
  http_method = aws_api_gateway_method.datasets-id_post.http_method
  status_code = aws_api_gateway_method_response.datasets-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id_post]
}

# wire up lambda datasets/{id}/filtering_terms
resource "aws_api_gateway_integration" "datasets-id-filtering_terms" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id-filtering_terms.id
  http_method             = aws_api_gateway_method.datasets-id-filtering_terms.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id-filtering_terms" {
  rest_api_id = aws_api_gateway_method.datasets-id-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-filtering_terms.resource_id
  http_method = aws_api_gateway_method.datasets-id-filtering_terms.http_method
  status_code = aws_api_gateway_method_response.datasets-id-filtering_terms.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id-filtering_terms]
}

resource "aws_api_gateway_integration" "datasets-id-filtering_terms_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id-filtering_terms.id
  http_method             = aws_api_gateway_method.datasets-id-filtering_terms_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.datasets-id-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.datasets-id-filtering_terms_post.http_method
  status_code = aws_api_gateway_method_response.datasets-id-filtering_terms_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id-filtering_terms_post]
}

# wire up lambda datasets/{id}/biosamples
resource "aws_api_gateway_integration" "datasets-id-biosamples" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id-biosamples.id
  http_method             = aws_api_gateway_method.datasets-id-biosamples.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id-biosamples" {
  rest_api_id = aws_api_gateway_method.datasets-id-biosamples.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-biosamples.resource_id
  http_method = aws_api_gateway_method.datasets-id-biosamples.http_method
  status_code = aws_api_gateway_method_response.datasets-id-biosamples.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id-biosamples]
}

resource "aws_api_gateway_integration" "datasets-id-biosamples_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id-biosamples.id
  http_method             = aws_api_gateway_method.datasets-id-biosamples_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id-biosamples_post" {
  rest_api_id = aws_api_gateway_method.datasets-id-biosamples_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-biosamples_post.resource_id
  http_method = aws_api_gateway_method.datasets-id-biosamples_post.http_method
  status_code = aws_api_gateway_method_response.datasets-id-biosamples_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id-biosamples_post]
}

# wire up lambda datasets/{id}/g_variants
resource "aws_api_gateway_integration" "datasets-id-g_variants" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id-g_variants.id
  http_method             = aws_api_gateway_method.datasets-id-g_variants.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id-g_variants" {
  rest_api_id = aws_api_gateway_method.datasets-id-g_variants.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-g_variants.resource_id
  http_method = aws_api_gateway_method.datasets-id-g_variants.http_method
  status_code = aws_api_gateway_method_response.datasets-id-g_variants.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id-g_variants]
}

resource "aws_api_gateway_integration" "datasets-id-g_variants_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id-g_variants.id
  http_method             = aws_api_gateway_method.datasets-id-g_variants_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id-g_variants_post" {
  rest_api_id = aws_api_gateway_method.datasets-id-g_variants_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-g_variants_post.resource_id
  http_method = aws_api_gateway_method.datasets-id-g_variants_post.http_method
  status_code = aws_api_gateway_method_response.datasets-id-g_variants_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id-g_variants_post]
}

# wire up lambda datasets/{id}/individuals
resource "aws_api_gateway_integration" "datasets-id-individuals" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id-individuals.id
  http_method             = aws_api_gateway_method.datasets-id-individuals.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id-individuals" {
  rest_api_id = aws_api_gateway_method.datasets-id-individuals.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-individuals.resource_id
  http_method = aws_api_gateway_method.datasets-id-individuals.http_method
  status_code = aws_api_gateway_method_response.datasets-id-individuals.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id-individuals]
}

resource "aws_api_gateway_integration" "datasets-id-individuals_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.datasets-id-individuals.id
  http_method             = aws_api_gateway_method.datasets-id-individuals_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getDatasets.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "datasets-id-individuals_post" {
  rest_api_id = aws_api_gateway_method.datasets-id-individuals_post.rest_api_id
  resource_id = aws_api_gateway_method.datasets-id-individuals_post.resource_id
  http_method = aws_api_gateway_method.datasets-id-individuals_post.http_method
  status_code = aws_api_gateway_method_response.datasets-id-individuals_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.datasets-id-individuals_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIdatasets" {
  statement_id  = "AllowAPIdatasetsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getDatasets.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.datasets.path_part}"
}

resource "aws_lambda_permission" "APIdatasetsFilteringTerms" {
  statement_id  = "AllowAPIdatasetsFilteringTermsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getDatasets.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.datasets.path_part}/${aws_api_gateway_resource.datasets-filtering_terms.path_part}"
}

resource "aws_lambda_permission" "APIdatasetsId" {
  statement_id  = "AllowAPIdatasetsIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getDatasets.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.datasets.path_part}/*"
}

resource "aws_lambda_permission" "APIdatasetsIdfiltering_terms" {
  statement_id  = "AllowAPIdatasetsIdfiltering_termsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getDatasets.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.datasets.path_part}/*/${aws_api_gateway_resource.datasets-id-filtering_terms.path_part}"
}

resource "aws_lambda_permission" "APIdatasetsIdbiosamples" {
  statement_id  = "AllowAPIdatasetsIdbiosamplesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getDatasets.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.datasets.path_part}/*/${aws_api_gateway_resource.datasets-id-biosamples.path_part}"
}

resource "aws_lambda_permission" "APIdatasetsIdg_variants" {
  statement_id  = "AllowAPIdatasetsIdg_variantsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getDatasets.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.datasets.path_part}/*/${aws_api_gateway_resource.datasets-id-g_variants.path_part}"
}

resource "aws_lambda_permission" "APIdatasetsIdindividuals" {
  statement_id  = "AllowAPIdatasetsIdindividualsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getDatasets.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.datasets.path_part}/*/${aws_api_gateway_resource.datasets-id-individuals.path_part}"
}
