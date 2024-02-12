terraform {
  required_version = ">= 1.3.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.33.0"
    }

    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.4.2"
    }

    local = {
      source  = "hashicorp/local"
      version = ">= 2.4.1"
    }

    null = {
      source  = "hashicorp/null"
      version = ">= 3.2.2"
    }

    external = {
      source  = "hashicorp/external"
      version = ">= 2.3.2"
    }

    docker = {
      source  = "kreuzwerker/docker"
      version = ">= 3.0.2"
    }
  }
}