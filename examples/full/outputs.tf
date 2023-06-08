output "api_url" {
  value       = module.serverless-beacon.api_url
  description = "URL used to invoke the API."
}

output "cognito_client_id" {
  value       = module.serverless-beacon.cognito_client_id
  description = "Cognito client Id for user registration and login."
}

output "admin_login_command" {
  value       = module.serverless-beacon.admin_login_command
  description = "AWS cli command to get admin login token"
}

output "guest_login_command" {
  value       = module.serverless-beacon.guest_login_command
  description = "AWS cli command to get guest login token"
}
