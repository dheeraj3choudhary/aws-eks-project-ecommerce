# terraform/modules/iam/outputs.tf

output "backend_sa_role_arn"     { value = aws_iam_role.backend_sa.arn }
output "alb_controller_role_arn" { value = aws_iam_role.alb_controller.arn }
