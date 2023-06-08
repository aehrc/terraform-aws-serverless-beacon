#
# cohorts API Function /cohorts
#
resource "aws_api_gateway_resource" "cohorts" {
  path_part   = "cohorts"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "cohorts" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.cohorts.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "cohorts" {
  rest_api_id = aws_api_gateway_method.cohorts.rest_api_id
  resource_id = aws_api_gateway_method.cohorts.resource_id
  http_method = aws_api_gateway_method.cohorts.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "cohorts_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.cohorts.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null
}

resource "aws_api_gateway_method_response" "cohorts_post" {
  rest_api_id = aws_api_gateway_method.cohorts_post.rest_api_id
  resource_id = aws_api_gateway_method.cohorts_post.resource_id
  http_method = aws_api_gateway_method.cohorts_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /cohorts/{id}
# 
resource "aws_api_gateway_resource" "cohorts-id" {
  path_part   = "{id}"
  parent_id   = aws_api_gateway_resource.cohorts.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "cohorts-id" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.cohorts-id.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "cohorts-id" {
  rest_api_id = aws_api_gateway_method.cohorts-id.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id.resource_id
  http_method = aws_api_gateway_method.cohorts-id.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "cohorts-id_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.cohorts-id.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "cohorts-id_post" {
  rest_api_id = aws_api_gateway_method.cohorts-id_post.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id_post.resource_id
  http_method = aws_api_gateway_method.cohorts-id_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /cohorts/{id}/filtering_terms
# 
resource "aws_api_gateway_resource" "cohorts-id-filtering_terms" {
  path_part   = "filtering_terms"
  parent_id   = aws_api_gateway_resource.cohorts-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "cohorts-id-filtering_terms" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.cohorts-id-filtering_terms.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "cohorts-id-filtering_terms" {
  rest_api_id = aws_api_gateway_method.cohorts-id-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id-filtering_terms.resource_id
  http_method = aws_api_gateway_method.cohorts-id-filtering_terms.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "cohorts-id-filtering_terms_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.cohorts-id-filtering_terms.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "cohorts-id-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.cohorts-id-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.cohorts-id-filtering_terms_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# /cohorts/{id}/individuals
# 
resource "aws_api_gateway_resource" "cohorts-id-individuals" {
  path_part   = "individuals"
  parent_id   = aws_api_gateway_resource.cohorts-id.id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "cohorts-id-individuals" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.cohorts-id-individuals.id
  http_method   = "GET"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "cohorts-id-individuals" {
  rest_api_id = aws_api_gateway_method.cohorts-id-individuals.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id-individuals.resource_id
  http_method = aws_api_gateway_method.cohorts-id-individuals.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method" "cohorts-id-individuals_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.cohorts-id-individuals.id
  http_method   = "POST"
  authorization = var.beacon-enable-auth ? "COGNITO_USER_POOLS" : "NONE"
  authorizer_id = var.beacon-enable-auth ? aws_api_gateway_authorizer.BeaconUserPool-authorizer.id : null

  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method_response" "cohorts-id-individuals_post" {
  rest_api_id = aws_api_gateway_method.cohorts-id-individuals_post.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id-individuals_post.resource_id
  http_method = aws_api_gateway_method.cohorts-id-individuals_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-cohorts" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.cohorts.id
}

module "cors-cohorts-id" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.cohorts-id.id
}

module "cors-cohorts-id-filtering_terms" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.cohorts-id-filtering_terms.id
}

module "cors-cohorts-id-individuals" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.cohorts-id-individuals.id
}

# wire up lambda cohorts
resource "aws_api_gateway_integration" "cohorts" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.cohorts.id
  http_method             = aws_api_gateway_method.cohorts.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getCohorts.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "cohorts" {
  rest_api_id = aws_api_gateway_method.cohorts.rest_api_id
  resource_id = aws_api_gateway_method.cohorts.resource_id
  http_method = aws_api_gateway_method.cohorts.http_method
  status_code = aws_api_gateway_method_response.cohorts.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.cohorts]
}

resource "aws_api_gateway_integration" "cohorts_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.cohorts.id
  http_method             = aws_api_gateway_method.cohorts_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getCohorts.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "cohorts_post" {
  rest_api_id = aws_api_gateway_method.cohorts_post.rest_api_id
  resource_id = aws_api_gateway_method.cohorts_post.resource_id
  http_method = aws_api_gateway_method.cohorts_post.http_method
  status_code = aws_api_gateway_method_response.cohorts_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.cohorts_post]
}

# wire up lambda cohorts/{id}
resource "aws_api_gateway_integration" "cohorts-id" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.cohorts-id.id
  http_method             = aws_api_gateway_method.cohorts-id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getCohorts.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "cohorts-id" {
  rest_api_id = aws_api_gateway_method.cohorts-id.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id.resource_id
  http_method = aws_api_gateway_method.cohorts-id.http_method
  status_code = aws_api_gateway_method_response.cohorts-id.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.cohorts-id]
}

resource "aws_api_gateway_integration" "cohorts-id_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.cohorts-id.id
  http_method             = aws_api_gateway_method.cohorts-id_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getCohorts.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "cohorts-id_post" {
  rest_api_id = aws_api_gateway_method.cohorts-id_post.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id_post.resource_id
  http_method = aws_api_gateway_method.cohorts-id_post.http_method
  status_code = aws_api_gateway_method_response.cohorts-id_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.cohorts-id_post]
}

# wire up lambda cohorts/{id}/filtering_terms
resource "aws_api_gateway_integration" "cohorts-id-filtering_terms" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.cohorts-id-filtering_terms.id
  http_method             = aws_api_gateway_method.cohorts-id-filtering_terms.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getCohorts.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "cohorts-id-filtering_terms" {
  rest_api_id = aws_api_gateway_method.cohorts-id-filtering_terms.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id-filtering_terms.resource_id
  http_method = aws_api_gateway_method.cohorts-id-filtering_terms.http_method
  status_code = aws_api_gateway_method_response.cohorts-id-filtering_terms.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.cohorts-id-filtering_terms]
}

resource "aws_api_gateway_integration" "cohorts-id-filtering_terms_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.cohorts-id-filtering_terms.id
  http_method             = aws_api_gateway_method.cohorts-id-filtering_terms_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getCohorts.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "cohorts-id-filtering_terms_post" {
  rest_api_id = aws_api_gateway_method.cohorts-id-filtering_terms_post.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id-filtering_terms_post.resource_id
  http_method = aws_api_gateway_method.cohorts-id-filtering_terms_post.http_method
  status_code = aws_api_gateway_method_response.cohorts-id-filtering_terms_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.cohorts-id-filtering_terms_post]
}

# wire up lambda cohorts/{id}/individuals
resource "aws_api_gateway_integration" "cohorts-id-individuals" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.cohorts-id-individuals.id
  http_method             = aws_api_gateway_method.cohorts-id-individuals.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getCohorts.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "cohorts-id-individuals" {
  rest_api_id = aws_api_gateway_method.cohorts-id-individuals.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id-individuals.resource_id
  http_method = aws_api_gateway_method.cohorts-id-individuals.http_method
  status_code = aws_api_gateway_method_response.cohorts-id-individuals.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.cohorts-id-individuals]
}

resource "aws_api_gateway_integration" "cohorts-id-individuals_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.cohorts-id-individuals.id
  http_method             = aws_api_gateway_method.cohorts-id-individuals_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getCohorts.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "cohorts-id-individuals_post" {
  rest_api_id = aws_api_gateway_method.cohorts-id-individuals_post.rest_api_id
  resource_id = aws_api_gateway_method.cohorts-id-individuals_post.resource_id
  http_method = aws_api_gateway_method.cohorts-id-individuals_post.http_method
  status_code = aws_api_gateway_method_response.cohorts-id-individuals_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.cohorts-id-individuals_post]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIcohorts" {
  statement_id  = "AllowAPIcohortsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getCohorts.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.cohorts.path_part}"
}

resource "aws_lambda_permission" "APIcohortsId" {
  statement_id  = "AllowAPIcohortsIdInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getCohorts.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.cohorts.path_part}/*"
}

resource "aws_lambda_permission" "APIcohortsIdfiltering_terms" {
  statement_id  = "AllowAPIcohortsIdfiltering_termsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getCohorts.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.cohorts.path_part}/*/${aws_api_gateway_resource.cohorts-id-filtering_terms.path_part}"
}

resource "aws_lambda_permission" "APIcohortsIdindividuals" {
  statement_id  = "AllowAPIcohortsIdindividualsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getCohorts.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.cohorts.path_part}/*/${aws_api_gateway_resource.cohorts-id-individuals.path_part}"
}
