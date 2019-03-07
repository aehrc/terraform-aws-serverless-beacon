#
# API Gateway
#
resource "aws_api_gateway_rest_api" "BeaconApi" {
  name = "BeaconApi"
  description = "API That implements the Beacon specification"
}

resource "aws_api_gateway_resource" "submit" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  parent_id = "${aws_api_gateway_rest_api.BeaconApi.root_resource_id}"
  path_part = "submit"
}

resource "aws_api_gateway_resource" "query" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  parent_id = "${aws_api_gateway_rest_api.BeaconApi.root_resource_id}"
  path_part = "query"
}

resource "aws_api_gateway_method" "root-options" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  resource_id = "${aws_api_gateway_rest_api.BeaconApi.root_resource_id}"
  http_method = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "root-options" {
  rest_api_id = "${aws_api_gateway_method.root-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.root-options.resource_id}"
  http_method = "${aws_api_gateway_method.root-options.http_method}"
  status_code = "200"

  response_parameters {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "root-options" {
  rest_api_id = "${aws_api_gateway_method.root-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.root-options.resource_id}"
  http_method = "${aws_api_gateway_method.root-options.http_method}"
  type = "MOCK"

  request_templates {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "root-options" {
  rest_api_id = "${aws_api_gateway_method.root-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.root-options.resource_id}"
  http_method = "${aws_api_gateway_method.root-options.http_method}"
  status_code = "${aws_api_gateway_method_response.root-options.status_code}"

  response_parameters {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  response_templates {
    "application/json" = ""
  }

  depends_on = ["aws_api_gateway_integration.root-options"]
}

resource "aws_api_gateway_method" "root-get" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  resource_id = "${aws_api_gateway_rest_api.BeaconApi.root_resource_id}"
  http_method = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "root-get" {
  rest_api_id = "${aws_api_gateway_method.root-get.rest_api_id}"
  resource_id = "${aws_api_gateway_method.root-get.resource_id}"
  http_method = "${aws_api_gateway_method.root-get.http_method}"
  status_code = "200"

  response_parameters {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "root-get" {
  rest_api_id = "${aws_api_gateway_method.root-get.rest_api_id}"
  resource_id = "${aws_api_gateway_method.root-get.resource_id}"
  http_method = "${aws_api_gateway_method.root-get.http_method}"
  type = "AWS_PROXY"
  uri = "${module.lambda-getInfo.invoke_arn}"
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "root-get" {
  rest_api_id = "${aws_api_gateway_method.root-get.rest_api_id}"
  resource_id = "${aws_api_gateway_method.root-get.resource_id}"
  http_method = "${aws_api_gateway_method.root-get.http_method}"
  status_code = "${aws_api_gateway_method_response.root-get.status_code}"

  response_templates {
    "application/json" = ""
  }

  depends_on = ["aws_api_gateway_integration.root-get"]
}

resource "aws_api_gateway_method" "submit-options" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  resource_id = "${aws_api_gateway_resource.submit.id}"
  http_method = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "submit-options" {
  rest_api_id = "${aws_api_gateway_method.submit-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-options.resource_id}"
  http_method = "${aws_api_gateway_method.submit-options.http_method}"
  status_code = "200"

  response_parameters {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-options" {
  rest_api_id = "${aws_api_gateway_method.submit-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-options.resource_id}"
  http_method = "${aws_api_gateway_method.submit-options.http_method}"
  type = "MOCK"

  request_templates {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "submit-options" {
  rest_api_id = "${aws_api_gateway_method.submit-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-options.resource_id}"
  http_method = "${aws_api_gateway_method.submit-options.http_method}"
  status_code = "${aws_api_gateway_method_response.submit-options.status_code}"

  response_parameters {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,PATCH,POST'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  response_templates {
    "application/json" = ""
  }

  depends_on = ["aws_api_gateway_integration.submit-options"]
}

resource "aws_api_gateway_method" "submit-patch" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  resource_id = "${aws_api_gateway_resource.submit.id}"
  http_method = "PATCH"
  authorization = "AWS_IAM"

}

resource "aws_api_gateway_method_response" "submit-patch" {
  rest_api_id = "${aws_api_gateway_method.submit-patch.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-patch.resource_id}"
  http_method = "${aws_api_gateway_method.submit-patch.http_method}"
  status_code = "200"

  response_parameters {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-patch" {
  rest_api_id = "${aws_api_gateway_method.submit-patch.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-patch.resource_id}"
  http_method = "${aws_api_gateway_method.submit-patch.http_method}"
  type = "AWS_PROXY"
  uri = "${module.lambda-submitDataset.invoke_arn}"
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "submit-patch" {
  rest_api_id = "${aws_api_gateway_method.submit-patch.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-patch.resource_id}"
  http_method = "${aws_api_gateway_method.submit-patch.http_method}"
  status_code = "${aws_api_gateway_method_response.submit-patch.status_code}"

  response_templates {
    "application/json" = ""
  }

  depends_on = ["aws_api_gateway_integration.submit-patch"]
}

resource "aws_api_gateway_method" "submit-post" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  resource_id = "${aws_api_gateway_resource.submit.id}"
  http_method = "POST"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_method_response" "submit-post" {
  rest_api_id = "${aws_api_gateway_method.submit-post.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-post.resource_id}"
  http_method = "${aws_api_gateway_method.submit-post.http_method}"
  status_code = "200"

  response_parameters {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-post" {
  rest_api_id = "${aws_api_gateway_method.submit-post.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-post.resource_id}"
  http_method = "${aws_api_gateway_method.submit-post.http_method}"
  type = "AWS_PROXY"
  uri = "${module.lambda-submitDataset.invoke_arn}"
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "submit-post" {
  rest_api_id = "${aws_api_gateway_method.submit-post.rest_api_id}"
  resource_id = "${aws_api_gateway_method.submit-post.resource_id}"
  http_method = "${aws_api_gateway_method.submit-post.http_method}"
  status_code = "${aws_api_gateway_method_response.submit-post.status_code}"

  response_templates {
    "application/json" = ""
  }

  depends_on = ["aws_api_gateway_integration.submit-post"]
}

resource "aws_api_gateway_method" "query-options" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  resource_id = "${aws_api_gateway_resource.query.id}"
  http_method = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "query-options" {
  rest_api_id = "${aws_api_gateway_method.query-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-options.resource_id}"
  http_method = "${aws_api_gateway_method.query-options.http_method}"
  status_code = "200"

  response_parameters {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "query-options" {
  rest_api_id = "${aws_api_gateway_method.query-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-options.resource_id}"
  http_method = "${aws_api_gateway_method.query-options.http_method}"
  type = "MOCK"

  request_templates {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "query-options" {
  rest_api_id = "${aws_api_gateway_method.query-options.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-options.resource_id}"
  http_method = "${aws_api_gateway_method.query-options.http_method}"
  status_code = "${aws_api_gateway_method_response.query-options.status_code}"

  response_parameters {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  response_templates {
    "application/json" = ""
  }

  depends_on = ["aws_api_gateway_integration.query-options"]
}

resource "aws_api_gateway_method" "query-get" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  resource_id = "${aws_api_gateway_resource.query.id}"
  http_method = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "query-get" {
  rest_api_id = "${aws_api_gateway_method.query-get.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-get.resource_id}"
  http_method = "${aws_api_gateway_method.query-get.http_method}"
  status_code = "200"

  response_parameters {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "query-get" {
  rest_api_id = "${aws_api_gateway_method.query-get.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-get.resource_id}"
  http_method = "${aws_api_gateway_method.query-get.http_method}"
  type = "AWS_PROXY"
  uri = "${module.lambda-queryDatasets.invoke_arn}"
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "query-get" {
  rest_api_id = "${aws_api_gateway_method.query-get.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-get.resource_id}"
  http_method = "${aws_api_gateway_method.query-get.http_method}"
  status_code = "${aws_api_gateway_method_response.query-get.status_code}"

  response_templates {
    "application/json" = ""
  }

  depends_on = ["aws_api_gateway_integration.query-get"]
}

resource "aws_api_gateway_method" "query-post" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  resource_id = "${aws_api_gateway_resource.query.id}"
  http_method = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "query-post" {
  rest_api_id = "${aws_api_gateway_method.query-post.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-post.resource_id}"
  http_method = "${aws_api_gateway_method.query-post.http_method}"
  status_code = "200"

  response_parameters {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "query-post" {
  rest_api_id = "${aws_api_gateway_method.query-post.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-post.resource_id}"
  http_method = "${aws_api_gateway_method.query-post.http_method}"
  type = "AWS_PROXY"
  uri = "${module.lambda-queryDatasets.invoke_arn}"
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "query-post" {
  rest_api_id = "${aws_api_gateway_method.query-post.rest_api_id}"
  resource_id = "${aws_api_gateway_method.query-post.resource_id}"
  http_method = "${aws_api_gateway_method.query-post.http_method}"
  status_code = "${aws_api_gateway_method_response.query-post.status_code}"

  response_templates {
    "application/json" = ""
  }

  depends_on = ["aws_api_gateway_integration.query-post"]
}

#
# Deployment
#
resource "aws_api_gateway_deployment" "BeaconApi" {
  rest_api_id = "${aws_api_gateway_rest_api.BeaconApi.id}"
  stage_name  = "prod"
  # taint deployment if any api resources change
  stage_description = "${md5(join("", list(
    md5(file("${path.module}/api.tf")),
    aws_api_gateway_method.root-options.id,
    aws_api_gateway_integration.root-options.id,
    aws_api_gateway_integration_response.root-options.id,
    aws_api_gateway_method_response.root-options.id,
    aws_api_gateway_method.root-get.id,
    aws_api_gateway_integration.root-get.id,
    aws_api_gateway_integration_response.root-get.id,
    aws_api_gateway_method_response.root-get.id,
    aws_api_gateway_method.submit-options.id,
    aws_api_gateway_integration.submit-options.id,
    aws_api_gateway_integration_response.submit-options.id,
    aws_api_gateway_method_response.submit-options.id,
    aws_api_gateway_method.submit-patch.id,
    aws_api_gateway_integration.submit-patch.id,
    aws_api_gateway_integration_response.submit-patch.id,
    aws_api_gateway_method_response.submit-patch.id,
    aws_api_gateway_method.submit-post.id,
    aws_api_gateway_integration.submit-post.id,
    aws_api_gateway_integration_response.submit-post.id,
    aws_api_gateway_method_response.submit-post.id,
    aws_api_gateway_method.query-options.id,
    aws_api_gateway_integration.query-options.id,
    aws_api_gateway_integration_response.query-options.id,
    aws_api_gateway_method_response.query-options.id,
    aws_api_gateway_method.query-get.id,
    aws_api_gateway_integration.query-get.id,
    aws_api_gateway_integration_response.query-get.id,
    aws_api_gateway_method_response.query-get.id,
    aws_api_gateway_method.query-post.id,
    aws_api_gateway_integration.query-post.id,
    aws_api_gateway_integration_response.query-post.id,
    aws_api_gateway_method_response.query-post.id
  )))}"
}
