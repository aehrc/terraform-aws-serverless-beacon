output "api_url" {
  value = "${aws_api_gateway_deployment.BeaconApi.invoke_url}"
}
