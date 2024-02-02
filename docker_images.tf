data "aws_region" "current" {}

data "aws_caller_identity" "this" {}

data "aws_ecr_authorization_token" "token" {}

locals {
  ecr_repo_name = "sbeacon-lambda-containers"
}

provider "docker" {
  registry_auth {
    address  = format("%v.dkr.ecr.%v.amazonaws.com", data.aws_caller_identity.this.account_id, data.aws_region.current.name)
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
  ecr_repo        = local.ecr_repo_name
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
