# terraform/modules/iam/variables.tf

variable "cluster_name" {
  type = string
}

variable "oidc_provider_arn" {
  type = string
}

variable "oidc_provider_url" {
  type = string
}

variable "namespace" {
  type    = string
  default = "ecommerce"
}

variable "db_secret_arn" {
  type = string
}
