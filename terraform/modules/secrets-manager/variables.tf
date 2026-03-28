# terraform/modules/secrets-manager/variables.tf

variable "secret_name"           { type = string; default = "prod/ecommerce/db" }
variable "db_username"           { type = string }
variable "db_password"           { type = string; sensitive = true }
variable "db_host"               { type = string }
variable "db_port"               { type = number; default = 5432 }
variable "db_name"               { type = string; default = "ecommerce" }
variable "recovery_window_days"  { type = number; default = 7 }
