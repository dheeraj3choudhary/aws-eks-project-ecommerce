# terraform/environments/dev/outputs.tf

output "cluster_name" { value = module.eks.cluster_name }
output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "ecr_repository_urls" { value = module.ecr.repository_urls }
output "rds_endpoint" { value = module.rds.endpoint }
output "db_secret_name" { value = module.secrets_manager.secret_name }
output "backend_sa_role_arn" { value = module.iam.backend_sa_role_arn }
output "alb_controller_role_arn" { value = module.iam.alb_controller_role_arn }
output "vpc_id" { value = module.vpc.vpc_id }
output "fluent_bit_role_arn" { value = module.iam.fluent_bit_role_arn }
