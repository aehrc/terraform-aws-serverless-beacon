# Authentication and authorisation guide
## Contents

<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [Introduction ](#introduction)
- [Enabling API security](#enabling-api-security)
- [API access commands](#api-access-commands)
- [How API security works](#how-api-security-works)

<!-- TOC end -->

## Introduction 
We have provided the essential architectural templates to enable the token based authentication of the API access. If you are using the module configuration of sBeacon, modify the `main.tf` as follows. Alternatively, you can edit these variable in the `variables.tf` file.

## Enabling API security
```bash
# main.tf
module "serverless-beacon" {
    # add the following as desired
    beacon-enable-auth          = true
    beacon-guest-username       = "guest@gmail.com"
    beacon-guest-password       = "XXXXX"
    beacon-admin-username       = "admin@gmail.com"
    beacon-admin-password       = "XXXXX"
}
``` 
❗Important note❗ 

By default, passwords for the default users are set through the `main.tf` file. Please consider using a `terraform.tfvars` file in order to avoid accidentally commits of sensitive passwords to version control systems. Documentation is available at [https://developer.hashicorp.com/terraform/tutorials/configuration-language/variables](https://developer.hashicorp.com/terraform/tutorials/configuration-language/variables).

In order to retrieve the commands needed to get access token, add an `output.tf` file in the module configuration.
```bash
# outputs.tf
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
``` 
A examples are available at [../examples/minimum/](../examples/minimum/) and  [../examples/full](../examples/full).

## API access commands

Upon successful `terraform apply` you'll be prompted with an output similar to below.
```bash 
api_url = "https://XXXXX.execute-api.us-east-1.amazonaws.com/"
cognito_client_id = "XXXXX"
admin_login_command = "aws cognito-idp admin-initiate-auth --user-pool-id us-east-1_A89RD07je --region us-east-1 --client-id 100n0tno0e0sql96mcgciaa8to --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters USERNAME=admin@gmail.com,PASSWORD=XXXXX --output json --query AuthenticationResult.IdToken"
guest_login_command = "aws cognito-idp admin-initiate-auth --user-pool-id us-east-1_A89RD07je --region us-east-1 --client-id XXXXX --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters USERNAME=guest@gmail.com,PASSWORD=XXXXX --output json --query AuthenticationResult.IdToken"
```

Use either `admin_login_command` or `guest_login_command` to retrieve the **IdToken**. You can use this as the bearer token to access the API.

## How API security works

There are three groups of users `record-access-user-group`, `count-access-user-group` and `boolean-access-user-group`. Admin user belons to all three groups while guest has only **counts** and **boolean** access. Adding new users must be done using the Cognito User Pool as an administrator. Alternatively, infrastructure can be modified to support alternative authentication flows.
