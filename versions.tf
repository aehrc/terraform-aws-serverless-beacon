terraform {
  required_version = ">= 1.1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.48.0"
    }

    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.2.0"
    }

    local = {
      source  = "hashicorp/local"
      version = ">= 2.2.3"
    }

    null = {
      source  = "hashicorp/null"
      version = ">= 3.2.1"
    }

    external = {
      source  = "hashicorp/external"
      version = ">= 2.2.3"
    }
  }
}