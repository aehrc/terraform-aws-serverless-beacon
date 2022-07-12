#
# Analyses API Function /analyses
#
resource aws_api_gateway_resource analyses {
  path_part   = "analyses"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource aws_api_gateway_method analyses {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.analyses.id
  http_method   = "GET"
  authorization = "NONE"
}

resource aws_api_gateway_method_response analyses {
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

# enable CORS
module cors-analyses {
  source = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.analyses.id
}

# wire up lambda
resource aws_api_gateway_integration analyses {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.analyses.id
  http_method             = aws_api_gateway_method.analyses.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getAnalyses.lambda_function_invoke_arn
}

resource aws_api_gateway_integration_response analyses {
  rest_api_id = aws_api_gateway_method.analyses.rest_api_id
  resource_id = aws_api_gateway_method.analyses.resource_id
  http_method = aws_api_gateway_method.analyses.http_method
  status_code = aws_api_gateway_method_response.analyses.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.analyses]
}

# permit lambda invokation
resource aws_lambda_permission APIAnalyses {
  statement_id = "AllowAPIAnalysesInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-getAnalyses.lambda_function_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.analyses.path_part}"
}
