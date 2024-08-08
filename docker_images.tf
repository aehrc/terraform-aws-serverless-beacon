data "aws_ecr_authorization_token" "token" {}

provider "docker" {
  registry_auth {
    address  = format("%v.dkr.ecr.%v.amazonaws.com", data.aws_caller_identity.this.account_id, var.region)
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

# 
# analytics lambda container
# 
data "external" "analytics_lambda_source_hash" {
  program     = ["python", "./lambda/analytics/docker_prep.py"]
  working_dir = path.module
}

module "docker_image_analytics_lambda" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = true
  ecr_repo        = "sbeacon-analytics-lambda-containers"
  ecr_repo_lifecycle_policy = jsonencode({
    "rules" : [
      {
        "rulePriority" : 1,
        "description" : "Keep only the last 1 images",
        "selection" : {
          "tagStatus" : "any",
          "countType" : "imageCountMoreThan",
          "countNumber" : 1
        },
        "action" : {
          "type" : "expire"
        }
      }
    ]
  })
  use_image_tag = false
  source_path   = "${path.module}/lambda/analytics"

  triggers = {
    dir_sha = data.external.analytics_lambda_source_hash.result.hash
  }
}

# 
# askbeacon lambda container
# 
data "external" "askbeacon_lambda_source_hash" {
  program     = ["python", "./lambda/askbeacon/docker_prep.py"]
  working_dir = path.module
}

module "docker_image_askbeacon_lambda" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = true
  ecr_repo        = "sbeacon-askbeacon-lambda-containers"
  ecr_repo_lifecycle_policy = jsonencode({
    "rules" : [
      {
        "rulePriority" : 1,
        "description" : "Keep only the last 1 images",
        "selection" : {
          "tagStatus" : "any",
          "countType" : "imageCountMoreThan",
          "countNumber" : 1
        },
        "action" : {
          "type" : "expire"
        }
      }
    ]
  })
  use_image_tag = false
  source_path   = "${path.module}/lambda/askbeacon"

  triggers = {
    dir_sha = data.external.askbeacon_lambda_source_hash.result.hash
  }
}