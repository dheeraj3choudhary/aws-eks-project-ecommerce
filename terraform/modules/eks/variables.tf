# terraform/modules/eks/variables.tf

variable "cluster_name"        { type = string }
variable "kubernetes_version"  { type = string; default = "1.30" }
variable "private_subnet_ids"  { type = list(string) }
variable "public_access_cidrs" { type = list(string); default = ["0.0.0.0/0"] }
variable "node_instance_type"  { type = string; default = "t3.medium" }
variable "capacity_type"       { type = string; default = "ON_DEMAND" }
variable "node_desired"        { type = number; default = 2 }
variable "node_min"            { type = number; default = 1 }
variable "node_max"            { type = number; default = 5 }
