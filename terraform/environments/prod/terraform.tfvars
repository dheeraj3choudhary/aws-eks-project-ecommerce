# terraform/environments/prod/terraform.tfvars
# Safe to commit — no secrets here.

aws_region         = "us-west-2"
environment        = "prod"
vpc_cidr           = "10.1.0.0/16"
kubernetes_version = "1.30"
node_instance_type = "t3.large"
db_instance_class  = "db.t3.small"
