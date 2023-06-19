output "api_url" {
  value       = aws_api_gateway_deployment.BeaconApi.invoke_url
  description = "URL used to invoke the API."
}

output "cognito_client_id" {
  value       = aws_cognito_user_pool_client.BeaconUserPool-client.id
  description = "Cognito client Id for user registration and login."
}

output "admin_login_command" {
  value       = "aws cognito-idp admin-initiate-auth --user-pool-id ${aws_cognito_user_pool.BeaconUserPool.id} --region ${var.region} --client-id ${aws_cognito_user_pool_client.BeaconUserPool-client.id} --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters USERNAME=${var.beacon-admin-username},PASSWORD=${var.beacon-admin-password} --output json --query AuthenticationResult.IdToken"
  description = "Command to sign in an admin"
}

output "guest_login_command" {
  value       = "aws cognito-idp admin-initiate-auth --user-pool-id ${aws_cognito_user_pool.BeaconUserPool.id} --region ${var.region} --client-id ${aws_cognito_user_pool_client.BeaconUserPool-client.id} --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters USERNAME=${var.beacon-guest-username},PASSWORD=${var.beacon-guest-password} --output json --query AuthenticationResult.IdToken"
  description = "Command to sign in a guest"
}
