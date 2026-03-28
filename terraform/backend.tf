# terraform/backend.tf
# Remote state stored in S3 with DynamoDB locking.
# Create the bucket and table before running terraform init:
#
#   aws s3api create-bucket \
#     --bucket ecommerce-eks-tfstate \
#     --region us-west-2
#
#   aws s3api put-bucket-versioning \
#     --bucket ecommerce-eks-tfstate \
#     --versioning-configuration Status=Enabled
#
#   aws dynamodb create-table \
#     --table-name ecommerce-eks-tflock \
#     --attribute-definitions AttributeName=LockID,AttributeType=S \
#     --key-schema AttributeName=LockID,KeyType=HASH \
#     --billing-mode PAY_PER_REQUEST \
#     --region us-west-2

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
    key            = "ecommerce-platform/${var.environment}/terraform.tfstate"
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
      Environment = var.environment
    }
  }
}