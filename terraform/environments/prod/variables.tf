# terraform/environments/prod/variables.tf

variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "vpc_cidr" {
  type    = string
  default = "10.1.0.0/16"           # separate CIDR from dev
}

variable "kubernetes_version" {
  type    = string
  default = "1.30"
}

variable "node_instance_type" {
  type    = string
  default = "t3.large"              # larger nodes for prod
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.small"           # upgrade to db.r6g.large for heavy load
}
