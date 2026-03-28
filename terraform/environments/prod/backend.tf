terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
  }

  backend "s3" {
    bucket         = "ecommerce-eks-tfstate"
    key            = "ecommerce-platform/prod/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "ecommerce-eks-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ecommerce-platform"
      ManagedBy   = "terraform"
      Environment = "prod"
    }
  }
}
