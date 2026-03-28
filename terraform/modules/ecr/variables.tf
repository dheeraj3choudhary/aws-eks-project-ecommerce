# terraform/modules/ecr/variables.tf

variable "repository_names" {
  type    = list(string)
  default = ["ecommerce-frontend", "ecommerce-backend"]
}
