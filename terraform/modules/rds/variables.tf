# terraform/modules/rds/variables.tf

variable "identifier"         { type = string }
variable "vpc_id"             { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "eks_node_sg_id"     { type = string }
variable "db_name"            { type = string; default = "ecommerce" }
variable "db_username"        { type = string; default = "ecommerceadmin" }
variable "db_password"        { type = string; sensitive = true }
variable "instance_class"     { type = string; default = "db.t3.micro" }
variable "allocated_storage"  { type = number; default = 20 }
variable "multi_az"           { type = bool;   default = false }
variable "deletion_protection"{ type = bool;   default = false }
variable "skip_final_snapshot"{ type = bool;   default = true }
