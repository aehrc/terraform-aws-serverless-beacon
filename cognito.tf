# 
# Pool and client
# 
resource "aws_cognito_user_pool" "BeaconUserPool" {
  name = "sbeacon-users"

  admin_create_user_config {
    allow_admin_create_user_only = true
    invite_message_template {
      email_subject = "sBeacon registration"
      email_message = "Welcome to sBeacon, please use username: {username} and password: {####} to log in."
      sms_message   = "Welcome to sBeacon, please use username: {username} and password: {####} to log in."
    }
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  password_policy {
    minimum_length                   = 6
    require_lowercase                = false
    require_numbers                  = false
    require_symbols                  = false
    require_uppercase                = false
    temporary_password_validity_days = 7
  }

  schema {
    name                = "terraform"
    attribute_data_type = "Boolean"
  }
}

resource "aws_cognito_user_pool_client" "BeaconUserPool-client" {
  name = "sbeacon-users-client"

  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]
}

# 
# groups
# 
resource "aws_cognito_user_group" "record-access" {
  name         = "record-access-user-group"
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  description  = "Group of users who can access 'record' granularity"
}

resource "aws_cognito_user_group" "count-access" {
  name         = "count-access-user-group"
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  description  = "Group of users who can access 'count' granularity"
}

resource "aws_cognito_user_group" "boolean-access" {
  name         = "boolean-access-user-group"
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  description  = "Group of users who can access 'boolean' granularity"
}

# 
# default users
# 
resource "aws_cognito_user" "guest" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  username     = var.beacon-guest-username
  password     = var.beacon-guest-password

  attributes = {
    terraform      = true
    email          = var.beacon-guest-username
    email_verified = true
  }
}

resource "aws_cognito_user" "admin" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  username     = var.beacon-admin-username
  password     = var.beacon-admin-password

  attributes = {
    terraform      = true
    email          = var.beacon-admin-username
    email_verified = true
  }
}

# 
# group assignments
# 
# admin
resource "aws_cognito_user_in_group" "admin-record-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.record-access.name
  username     = aws_cognito_user.admin.username
}

resource "aws_cognito_user_in_group" "admin-count-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.count-access.name
  username     = aws_cognito_user.admin.username
}

resource "aws_cognito_user_in_group" "admin-boolean-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.boolean-access.name
  username     = aws_cognito_user.admin.username
}

# guest
resource "aws_cognito_user_in_group" "guest-count-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.count-access.name
  username     = aws_cognito_user.guest.username
}

resource "aws_cognito_user_in_group" "guest-boolean-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.boolean-access.name
  username     = aws_cognito_user.guest.username
}

# 
# authorizers
# 
resource "aws_api_gateway_authorizer" "BeaconUserPool-authorizer" {
  name          = "UserPoolAuthorizer-sbeacon"
  type          = "COGNITO_USER_POOLS"
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  provider_arns = [aws_cognito_user_pool.BeaconUserPool.arn]

  depends_on = [aws_api_gateway_rest_api.BeaconApi]
}
