# terraform/environments/dev/terraform.tfvars
# Part of commit but make sure no secrets are added here

aws_region         = "us-west-2"
environment        = "dev"
vpc_cidr           = "10.0.0.0/16"
kubernetes_version = "1.30"
node_instance_type = "t3.medium"
db_instance_class  = "db.t3.micro"
