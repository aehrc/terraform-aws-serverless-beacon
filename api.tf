#
# API Gateway
#
resource "aws_api_gateway_rest_api" "BeaconApi" {
  name        = "BeaconApi"
  description = "API That implements the Beacon specification"
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
  # https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_deployment#terraform-resources
  # NOTE: The configuration below will satisfy ordering considerations,
  #       but not pick up all future REST API changes. More advanced patterns
  #       are possible, such as using the filesha1() function against the
  #       Terraform configuration file(s) or removing the .id references to
  #       calculate a hash against whole resources. Be aware that using whole
  #       resources will show a difference after the initial implementation.
  #       It will stabilize to only change when resources change afterwards.
  triggers = {
    redeployment = sha1(jsonencode([
      # /submit-dataset
      aws_api_gateway_method.submit-dataset_post,
      aws_api_gateway_integration.submit-dataset_post,
      aws_api_gateway_integration_response.submit-dataset_post,
      aws_api_gateway_method_response.submit-dataset_post,
      # /submit-cohort
      aws_api_gateway_method.submit-cohort_post,
      aws_api_gateway_integration.submit-cohort_post,
      aws_api_gateway_integration_response.submit-cohort_post,
      aws_api_gateway_method_response.submit-cohort_post,
      # /configuration
      aws_api_gateway_method.configuration,
      aws_api_gateway_integration.configuration,
      aws_api_gateway_integration_response.configuration,
      aws_api_gateway_method_response.configuration,
      # /info or /
      aws_api_gateway_method.info,
      aws_api_gateway_integration.info,
      aws_api_gateway_integration_response.info,
      aws_api_gateway_method_response.info,
      aws_api_gateway_method.root-get,
      aws_api_gateway_integration.root-get,
      aws_api_gateway_integration_response.root-get,
      aws_api_gateway_method_response.root-get,
      # /map
      aws_api_gateway_method.map,
      aws_api_gateway_integration.map,
      aws_api_gateway_integration_response.map,
      aws_api_gateway_method_response.map,
      # /entry_types
      aws_api_gateway_method.entry_types,
      aws_api_gateway_integration.entry_types,
      aws_api_gateway_integration_response.entry_types,
      aws_api_gateway_method_response.entry_types,
      # /filtering_terms
      aws_api_gateway_method.filtering_terms,
      aws_api_gateway_integration.filtering_terms,
      aws_api_gateway_integration_response.filtering_terms,
      aws_api_gateway_method_response.filtering_terms,
      # /samples
      aws_api_gateway_method.samples,
      aws_api_gateway_method.samples_post,
      aws_api_gateway_integration.samples,
      aws_api_gateway_integration.samples_post,
      aws_api_gateway_integration_response.samples,
      aws_api_gateway_integration_response.samples_post,
      aws_api_gateway_method_response.samples,
      aws_api_gateway_method_response.samples_post,
      # /snps
      aws_api_gateway_method.snps,
      aws_api_gateway_method.snps_post,
      aws_api_gateway_integration.snps,
      aws_api_gateway_integration.snps_post,
      aws_api_gateway_integration_response.snps,
      aws_api_gateway_integration_response.snps_post,
      aws_api_gateway_method_response.snps,
      aws_api_gateway_method_response.snps_post,
      # /genotypes
      aws_api_gateway_method.genotypes,
      aws_api_gateway_method.genotypes_post,
      aws_api_gateway_integration.genotypes,
      aws_api_gateway_integration.genotypes_post,
      aws_api_gateway_integration_response.genotypes,
      aws_api_gateway_integration_response.genotypes_post,
      aws_api_gateway_method_response.genotypes,
      aws_api_gateway_method_response.genotypes_post,
      # /phenotypes
      aws_api_gateway_method.phenotypes,
      aws_api_gateway_method.phenotypes_post,
      aws_api_gateway_integration.phenotypes,
      aws_api_gateway_integration.phenotypes_post,
      aws_api_gateway_integration_response.phenotypes,
      aws_api_gateway_integration_response.phenotypes_post,
      aws_api_gateway_method_response.phenotypes,
      aws_api_gateway_method_response.phenotypes_post,
      # index
      aws_api_gateway_method.index_post,
      aws_api_gateway_integration.index_post,
      aws_api_gateway_method_response.index_post,
      # admin
      aws_api_gateway_method.admin_proxy,
      aws_api_gateway_integration.admin_proxy,
      aws_api_gateway_integration_response.admin_proxy,
      aws_api_gateway_method_response.admin_proxy,
      # analytics
      aws_api_gateway_method.analytics_proxy,
      aws_api_gateway_integration.analytics_proxy,
      aws_api_gateway_integration_response.analytics_proxy,
      aws_api_gateway_method_response.analytics_proxy,
      # askbeacon
      aws_api_gateway_method.ask_proxy,
      aws_api_gateway_integration.ask_proxy,
      aws_api_gateway_integration_response.ask_proxy,
      aws_api_gateway_method_response.ask_proxy,
    ]))
  }
}

resource "aws_api_gateway_stage" "BeaconApi" {
  deployment_id = aws_api_gateway_deployment.BeaconApi.id
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  stage_name    = "prod"
}
