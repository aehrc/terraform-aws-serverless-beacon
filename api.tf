#
# API Gateway
#

# TODO update submission pipeline
resource "aws_api_gateway_rest_api" "BeaconApi" {
  name        = "BeaconApi"
  description = "API That implements the Beacon specification"
}

resource "aws_api_gateway_resource" "submit" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  path_part   = "submit"
}

resource "aws_api_gateway_method" "submit-options" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  status_code = aws_api_gateway_method_response.submit-options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,PATCH,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-options]
}

resource "aws_api_gateway_method" "submit-patch" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "PATCH"
  authorization = "AWS_IAM"

}

resource "aws_api_gateway_method_response" "submit-patch" {
  rest_api_id = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id = aws_api_gateway_method.submit-patch.resource_id
  http_method = aws_api_gateway_method.submit-patch.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-patch" {
  rest_api_id             = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id             = aws_api_gateway_method.submit-patch.resource_id
  http_method             = aws_api_gateway_method.submit-patch.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-submitDataset.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "submit-patch" {
  rest_api_id = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id = aws_api_gateway_method.submit-patch.resource_id
  http_method = aws_api_gateway_method.submit-patch.http_method
  status_code = aws_api_gateway_method_response.submit-patch.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-patch]
}

resource "aws_api_gateway_method" "submit-post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_method_response" "submit-post" {
  rest_api_id = aws_api_gateway_method.submit-post.rest_api_id
  resource_id = aws_api_gateway_method.submit-post.resource_id
  http_method = aws_api_gateway_method.submit-post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-post" {
  rest_api_id             = aws_api_gateway_method.submit-post.rest_api_id
  resource_id             = aws_api_gateway_method.submit-post.resource_id
  http_method             = aws_api_gateway_method.submit-post.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-submitDataset.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "submit-post" {
  rest_api_id = aws_api_gateway_method.submit-post.rest_api_id
  resource_id = aws_api_gateway_method.submit-post.resource_id
  http_method = aws_api_gateway_method.submit-post.http_method
  status_code = aws_api_gateway_method_response.submit-post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-post]
}

#
# Deployment
#
resource "aws_api_gateway_deployment" "BeaconApi" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  # Without enabling create_before_destroy, 
  # API Gateway can return errors such as BadRequestException: 
  # Active stages pointing to this deployment must be moved or deleted on recreation.
  lifecycle {
    create_before_destroy = true
  }
  # taint deployment if any api resources change
  stage_description = md5(join("", [
    md5(file("${path.module}/api.tf")),
    md5(file("${path.module}/api-resource-info.tf")),
    md5(file("${path.module}/api-configuration.tf")),
    md5(file("${path.module}/api-map.tf")),
    md5(file("${path.module}/api-entry-types.tf")),
    md5(file("${path.module}/api-analyses.tf")),
    md5(file("${path.module}/api-genomics-variants.tf")),
    md5(file("${path.module}/api-filtering-terms.tf")),
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
    # /configuration
    aws_api_gateway_method.configuration.id,
    aws_api_gateway_integration.configuration.id,
    aws_api_gateway_integration_response.configuration.id,
    aws_api_gateway_method_response.configuration.id,
    # /info or /
    aws_api_gateway_method.info.id,
    aws_api_gateway_integration.info.id,
    aws_api_gateway_integration_response.info.id,
    aws_api_gateway_method_response.info.id,
    aws_api_gateway_method.root-get.id,
    aws_api_gateway_integration.root-get.id,
    aws_api_gateway_integration_response.root-get.id,
    aws_api_gateway_method_response.root-get.id,
    # /map
    aws_api_gateway_method.map.id,
    aws_api_gateway_integration.map.id,
    aws_api_gateway_integration_response.map.id,
    aws_api_gateway_method_response.map.id,
    # /entry_types
    aws_api_gateway_method.entry_types.id,
    aws_api_gateway_integration.entry_types.id,
    aws_api_gateway_integration_response.entry_types.id,
    aws_api_gateway_method_response.entry_types.id,
    # /filtering_terms
    aws_api_gateway_method.filtering_terms.id,
    aws_api_gateway_integration.filtering_terms.id,
    aws_api_gateway_integration_response.filtering_terms.id,
    aws_api_gateway_method_response.filtering_terms.id,
    # /analyses TODO update with other end points
    aws_api_gateway_method.analyses.id,
    aws_api_gateway_integration.analyses.id,
    aws_api_gateway_integration_response.analyses.id,
    aws_api_gateway_method_response.analyses.id,
    # /g_variants
    aws_api_gateway_method.g_variants.id,
    aws_api_gateway_method.g_variants_post.id,
    aws_api_gateway_integration.g_variants.id,
    aws_api_gateway_integration.g_variants_post.id,
    aws_api_gateway_integration_response.g_variants.id,
    aws_api_gateway_integration_response.g_variants_post.id,
    aws_api_gateway_method_response.g_variants.id,
    aws_api_gateway_method_response.g_variants_post.id,
    # /g_variants/{id}
    aws_api_gateway_method.g_variants-id.id,
    aws_api_gateway_method.g_variants-id_post.id,
    aws_api_gateway_integration.g_variants-id.id,
    aws_api_gateway_integration.g_variants-id_post.id,
    aws_api_gateway_integration_response.g_variants-id.id,
    aws_api_gateway_integration_response.g_variants-id_post.id,
    aws_api_gateway_method_response.g_variants-id.id,
    aws_api_gateway_method_response.g_variants-id_post.id,
    # /g_variants/{id}/biosamples
    aws_api_gateway_method.g_variants-id-biosamples.id,
    aws_api_gateway_method.g_variants-id-biosamples_post.id,
    aws_api_gateway_integration.g_variants-id-biosamples.id,
    aws_api_gateway_integration.g_variants-id-biosamples_post.id,
    aws_api_gateway_integration_response.g_variants-id-biosamples.id,
    aws_api_gateway_integration_response.g_variants-id-biosamples_post.id,
    aws_api_gateway_method_response.g_variants-id-biosamples.id,
    aws_api_gateway_method_response.g_variants-id-biosamples_post.id,
    # /g_variants/{id}/individuals
    aws_api_gateway_method.g_variants-id-individuals.id,
    aws_api_gateway_method.g_variants-id-individuals_post.id,
    aws_api_gateway_integration.g_variants-id-individuals.id,
    aws_api_gateway_integration.g_variants-id-individuals_post.id,
    aws_api_gateway_integration_response.g_variants-id-individuals.id,
    aws_api_gateway_integration_response.g_variants-id-individuals_post.id,
    aws_api_gateway_method_response.g_variants-id-individuals.id,
    aws_api_gateway_method_response.g_variants-id-individuals_post.id,
    # /individuals
    aws_api_gateway_method.individuals.id,
    aws_api_gateway_method.individuals_post.id,
    aws_api_gateway_integration.individuals.id,
    aws_api_gateway_integration.individuals_post.id,
    aws_api_gateway_integration_response.individuals.id,
    aws_api_gateway_integration_response.individuals_post.id,
    aws_api_gateway_method_response.individuals.id,
    aws_api_gateway_method_response.individuals_post.id,
    # /individuals/filtering_terms
    aws_api_gateway_method.individuals-filtering_terms.id,
    aws_api_gateway_method.individuals-filtering_terms_post.id,
    aws_api_gateway_integration.individuals-filtering_terms.id,
    aws_api_gateway_integration.individuals-filtering_terms_post.id,
    aws_api_gateway_integration_response.individuals-filtering_terms.id,
    aws_api_gateway_integration_response.individuals-filtering_terms_post.id,
    aws_api_gateway_method_response.individuals-filtering_terms.id,
    aws_api_gateway_method_response.individuals-filtering_terms_post.id,
    # /individuals/{id}
    aws_api_gateway_method.individuals-id.id,
    aws_api_gateway_method.individuals-id_post.id,
    aws_api_gateway_integration.individuals-id.id,
    aws_api_gateway_integration.individuals-id_post.id,
    aws_api_gateway_integration_response.individuals-id.id,
    aws_api_gateway_integration_response.individuals-id_post.id,
    aws_api_gateway_method_response.individuals-id.id,
    aws_api_gateway_method_response.individuals-id_post.id,
    # /individuals/{id}/biosamples
    aws_api_gateway_method.individuals-id-biosamples.id,
    aws_api_gateway_method.individuals-id-biosamples_post.id,
    aws_api_gateway_integration.individuals-id-biosamples.id,
    aws_api_gateway_integration.individuals-id-biosamples_post.id,
    aws_api_gateway_integration_response.individuals-id-biosamples.id,
    aws_api_gateway_integration_response.individuals-id-biosamples_post.id,
    aws_api_gateway_method_response.individuals-id-biosamples.id,
    aws_api_gateway_method_response.individuals-id-biosamples_post.id,
    # /individuals/{id}/g_variants
    aws_api_gateway_method.individuals-id-g_variants.id,
    aws_api_gateway_method.individuals-id-g_variants_post.id,
    aws_api_gateway_integration.individuals-id-g_variants.id,
    aws_api_gateway_integration.individuals-id-g_variants_post.id,
    aws_api_gateway_integration_response.individuals-id-g_variants.id,
    aws_api_gateway_integration_response.individuals-id-g_variants_post.id,
    aws_api_gateway_method_response.individuals-id-g_variants.id,
    aws_api_gateway_method_response.individuals-id-g_variants_post.id,
    # /biosamples
    aws_api_gateway_method.biosamples.id,
    aws_api_gateway_method.biosamples_post.id,
    aws_api_gateway_integration.biosamples.id,
    aws_api_gateway_integration.biosamples_post.id,
    aws_api_gateway_integration_response.biosamples.id,
    aws_api_gateway_integration_response.biosamples_post.id,
    aws_api_gateway_method_response.biosamples.id,
    aws_api_gateway_method_response.biosamples_post.id,
    # /biosamples/filtering_terms
    aws_api_gateway_method.biosamples-filtering_terms.id,
    aws_api_gateway_method.biosamples-filtering_terms_post.id,
    aws_api_gateway_integration.biosamples-filtering_terms.id,
    aws_api_gateway_integration.biosamples-filtering_terms_post.id,
    aws_api_gateway_integration_response.biosamples-filtering_terms.id,
    aws_api_gateway_integration_response.biosamples-filtering_terms_post.id,
    aws_api_gateway_method_response.biosamples-filtering_terms.id,
    aws_api_gateway_method_response.biosamples-filtering_terms_post.id,
    # /biosamples/{id}
    aws_api_gateway_method.biosamples-id.id,
    aws_api_gateway_method.biosamples-id_post.id,
    aws_api_gateway_integration.biosamples-id.id,
    aws_api_gateway_integration.biosamples-id_post.id,
    aws_api_gateway_integration_response.biosamples-id.id,
    aws_api_gateway_integration_response.biosamples-id_post.id,
    aws_api_gateway_method_response.biosamples-id.id,
    aws_api_gateway_method_response.biosamples-id_post.id,
    # /biosamples/{id}/analyses
    aws_api_gateway_method.biosamples-id-analyses.id,
    aws_api_gateway_method.biosamples-id-analyses_post.id,
    aws_api_gateway_integration.biosamples-id-analyses.id,
    aws_api_gateway_integration.biosamples-id-analyses_post.id,
    aws_api_gateway_integration_response.biosamples-id-analyses.id,
    aws_api_gateway_integration_response.biosamples-id-analyses_post.id,
    aws_api_gateway_method_response.biosamples-id-analyses.id,
    aws_api_gateway_method_response.biosamples-id-analyses_post.id,
    # /biosamples/{id}/g_variants
    aws_api_gateway_method.biosamples-id-g_variants.id,
    aws_api_gateway_method.biosamples-id-g_variants_post.id,
    aws_api_gateway_integration.biosamples-id-g_variants.id,
    aws_api_gateway_integration.biosamples-id-g_variants_post.id,
    aws_api_gateway_integration_response.biosamples-id-g_variants.id,
    aws_api_gateway_integration_response.biosamples-id-g_variants_post.id,
    aws_api_gateway_method_response.biosamples-id-g_variants.id,
    aws_api_gateway_method_response.biosamples-id-g_variants_post.id,
    # /biosamples/{id}/runs
    aws_api_gateway_method.biosamples-id-runs.id,
    aws_api_gateway_method.biosamples-id-runs_post.id,
    aws_api_gateway_integration.biosamples-id-runs.id,
    aws_api_gateway_integration.biosamples-id-runs_post.id,
    aws_api_gateway_integration_response.biosamples-id-runs.id,
    aws_api_gateway_integration_response.biosamples-id-runs_post.id,
    aws_api_gateway_method_response.biosamples-id-runs.id,
    aws_api_gateway_method_response.biosamples-id-runs_post.id,
    # /runs
    aws_api_gateway_method.runs.id,
    aws_api_gateway_method.runs_post.id,
    aws_api_gateway_integration.runs.id,
    aws_api_gateway_integration.runs_post.id,
    aws_api_gateway_integration_response.runs.id,
    aws_api_gateway_integration_response.runs_post.id,
    aws_api_gateway_method_response.runs.id,
    aws_api_gateway_method_response.runs_post.id,
    # /runs/filtering_terms
    aws_api_gateway_method.runs-filtering_terms.id,
    aws_api_gateway_method.runs-filtering_terms_post.id,
    aws_api_gateway_integration.runs-filtering_terms.id,
    aws_api_gateway_integration.runs-filtering_terms_post.id,
    aws_api_gateway_integration_response.runs-filtering_terms.id,
    aws_api_gateway_integration_response.runs-filtering_terms_post.id,
    aws_api_gateway_method_response.runs-filtering_terms.id,
    aws_api_gateway_method_response.runs-filtering_terms_post.id,
    # /runs/{id}
    aws_api_gateway_method.runs-id.id,
    aws_api_gateway_method.runs-id_post.id,
    aws_api_gateway_integration.runs-id.id,
    aws_api_gateway_integration.runs-id_post.id,
    aws_api_gateway_integration_response.runs-id.id,
    aws_api_gateway_integration_response.runs-id_post.id,
    aws_api_gateway_method_response.runs-id.id,
    aws_api_gateway_method_response.runs-id_post.id,
    # /runs/{id}/analyses
    aws_api_gateway_method.runs-id-analyses.id,
    aws_api_gateway_method.runs-id-analyses_post.id,
    aws_api_gateway_integration.runs-id-analyses.id,
    aws_api_gateway_integration.runs-id-analyses_post.id,
    aws_api_gateway_integration_response.runs-id-analyses.id,
    aws_api_gateway_integration_response.runs-id-analyses_post.id,
    aws_api_gateway_method_response.runs-id-analyses.id,
    aws_api_gateway_method_response.runs-id-analyses_post.id,
    # /runs/{id}/g_variants
    aws_api_gateway_method.runs-id-g_variants.id,
    aws_api_gateway_method.runs-id-g_variants_post.id,
    aws_api_gateway_integration.runs-id-g_variants.id,
    aws_api_gateway_integration.runs-id-g_variants_post.id,
    aws_api_gateway_integration_response.runs-id-g_variants.id,
    aws_api_gateway_integration_response.runs-id-g_variants_post.id,
    aws_api_gateway_method_response.runs-id-g_variants.id,
    aws_api_gateway_method_response.runs-id-g_variants_post.id,
    # /analyses
    aws_api_gateway_method.analyses.id,
    aws_api_gateway_method.analyses_post.id,
    aws_api_gateway_integration.analyses.id,
    aws_api_gateway_integration.analyses_post.id,
    aws_api_gateway_integration_response.analyses.id,
    aws_api_gateway_integration_response.analyses_post.id,
    aws_api_gateway_method_response.analyses.id,
    aws_api_gateway_method_response.analyses_post.id,
    # /analyses/{id}
    aws_api_gateway_method.analyses-id.id,
    aws_api_gateway_method.analyses-id_post.id,
    aws_api_gateway_integration.analyses-id.id,
    aws_api_gateway_integration.analyses-id_post.id,
    aws_api_gateway_integration_response.analyses-id.id,
    aws_api_gateway_integration_response.analyses-id_post.id,
    aws_api_gateway_method_response.analyses-id.id,
    aws_api_gateway_method_response.analyses-id_post.id,
    # /analyses/{id}/g_variants
    aws_api_gateway_method.analyses-id-g_variants.id,
    aws_api_gateway_method.analyses-id-g_variants_post.id,
    aws_api_gateway_integration.analyses-id-g_variants.id,
    aws_api_gateway_integration.analyses-id-g_variants_post.id,
    aws_api_gateway_integration_response.analyses-id-g_variants.id,
    aws_api_gateway_integration_response.analyses-id-g_variants_post.id,
    aws_api_gateway_method_response.analyses-id-g_variants.id,
    aws_api_gateway_method_response.analyses-id-g_variants_post.id,
    # /datasets
    aws_api_gateway_method.datasets.id,
    aws_api_gateway_method.datasets_post.id,
    aws_api_gateway_integration.datasets.id,
    aws_api_gateway_integration.datasets_post.id,
    aws_api_gateway_integration_response.datasets.id,
    aws_api_gateway_integration_response.datasets_post.id,
    aws_api_gateway_method_response.datasets.id,
    aws_api_gateway_method_response.datasets_post.id,
    # /datasets/filtering_terms
    aws_api_gateway_method.datasets-filtering_terms.id,
    aws_api_gateway_method.datasets-filtering_terms_post.id,
    aws_api_gateway_integration.datasets-filtering_terms.id,
    aws_api_gateway_integration.datasets-filtering_terms_post.id,
    aws_api_gateway_integration_response.datasets-filtering_terms.id,
    aws_api_gateway_integration_response.datasets-filtering_terms_post.id,
    aws_api_gateway_method_response.datasets-filtering_terms.id,
    aws_api_gateway_method_response.datasets-filtering_terms_post.id,
    # /datasets/{id}
    aws_api_gateway_method.datasets-id.id,
    aws_api_gateway_method.datasets-id_post.id,
    aws_api_gateway_integration.datasets-id.id,
    aws_api_gateway_integration.datasets-id_post.id,
    aws_api_gateway_integration_response.datasets-id.id,
    aws_api_gateway_integration_response.datasets-id_post.id,
    aws_api_gateway_method_response.datasets-id.id,
    aws_api_gateway_method_response.datasets-id_post.id,
    # /datasets/{id}/filtering_terms
    aws_api_gateway_method.datasets-id-filtering_terms.id,
    aws_api_gateway_method.datasets-id-filtering_terms_post.id,
    aws_api_gateway_integration.datasets-id-filtering_terms.id,
    aws_api_gateway_integration.datasets-id-filtering_terms_post.id,
    aws_api_gateway_integration_response.datasets-id-filtering_terms.id,
    aws_api_gateway_integration_response.datasets-id-filtering_terms_post.id,
    aws_api_gateway_method_response.datasets-id-filtering_terms.id,
    aws_api_gateway_method_response.datasets-id-filtering_terms_post.id,
    # /datasets/{id}/individuals
    aws_api_gateway_method.datasets-id-individuals.id,
    aws_api_gateway_method.datasets-id-individuals_post.id,
    aws_api_gateway_integration.datasets-id-individuals.id,
    aws_api_gateway_integration.datasets-id-individuals_post.id,
    aws_api_gateway_integration_response.datasets-id-individuals.id,
    aws_api_gateway_integration_response.datasets-id-individuals_post.id,
    aws_api_gateway_method_response.datasets-id-individuals.id,
    aws_api_gateway_method_response.datasets-id-individuals_post.id,
    # /datasets/{id}/g_variants
    aws_api_gateway_method.datasets-id-g_variants.id,
    aws_api_gateway_method.datasets-id-g_variants_post.id,
    aws_api_gateway_integration.datasets-id-g_variants.id,
    aws_api_gateway_integration.datasets-id-g_variants_post.id,
    aws_api_gateway_integration_response.datasets-id-g_variants.id,
    aws_api_gateway_integration_response.datasets-id-g_variants_post.id,
    aws_api_gateway_method_response.datasets-id-g_variants.id,
    aws_api_gateway_method_response.datasets-id-g_variants_post.id,
    # /datasets/{id}/biosamples
    aws_api_gateway_method.datasets-id-biosamples.id,
    aws_api_gateway_method.datasets-id-biosamples_post.id,
    aws_api_gateway_integration.datasets-id-biosamples.id,
    aws_api_gateway_integration.datasets-id-biosamples_post.id,
    aws_api_gateway_integration_response.datasets-id-biosamples.id,
    aws_api_gateway_integration_response.datasets-id-biosamples_post.id,
    aws_api_gateway_method_response.datasets-id-biosamples.id,
    aws_api_gateway_method_response.datasets-id-biosamples_post.id,
    # /cohorts
    aws_api_gateway_method.cohorts.id,
    aws_api_gateway_method.cohorts_post.id,
    aws_api_gateway_integration.cohorts.id,
    aws_api_gateway_integration.cohorts_post.id,
    aws_api_gateway_integration_response.cohorts.id,
    aws_api_gateway_integration_response.cohorts_post.id,
    aws_api_gateway_method_response.cohorts.id,
    aws_api_gateway_method_response.cohorts_post.id,
    # /cohorts/{id}
    aws_api_gateway_method.cohorts-id.id,
    aws_api_gateway_method.cohorts-id_post.id,
    aws_api_gateway_integration.cohorts-id.id,
    aws_api_gateway_integration.cohorts-id_post.id,
    aws_api_gateway_integration_response.cohorts-id.id,
    aws_api_gateway_integration_response.cohorts-id_post.id,
    aws_api_gateway_method_response.cohorts-id.id,
    aws_api_gateway_method_response.cohorts-id_post.id,
    # /cohorts/{id}/individuals
    aws_api_gateway_method.cohorts-id-individuals.id,
    aws_api_gateway_method.cohorts-id-individuals_post.id,
    aws_api_gateway_integration.cohorts-id-individuals.id,
    aws_api_gateway_integration.cohorts-id-individuals_post.id,
    aws_api_gateway_integration_response.cohorts-id-individuals.id,
    aws_api_gateway_integration_response.cohorts-id-individuals_post.id,
    aws_api_gateway_method_response.cohorts-id-individuals.id,
    aws_api_gateway_method_response.cohorts-id-individuals_post.id,
    # /cohorts/{id}/filtering_terms
    aws_api_gateway_method.cohorts-id-filtering_terms.id,
    aws_api_gateway_method.cohorts-id-filtering_terms_post.id,
    aws_api_gateway_integration.cohorts-id-filtering_terms.id,
    aws_api_gateway_integration.cohorts-id-filtering_terms_post.id,
    aws_api_gateway_integration_response.cohorts-id-filtering_terms.id,
    aws_api_gateway_integration_response.cohorts-id-filtering_terms_post.id,
    aws_api_gateway_method_response.cohorts-id-filtering_terms.id,
    aws_api_gateway_method_response.cohorts-id-filtering_terms_post.id,
  ]))
}

resource "aws_api_gateway_stage" "BeaconApi" {
  deployment_id = aws_api_gateway_deployment.BeaconApi.id
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  stage_name    = "prod"
}
