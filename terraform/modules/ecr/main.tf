# terraform/modules/ecr/main.tf
# Two ECR repositories — one for frontend, one for backend.
# Lifecycle policy keeps only the last 10 images to control storage costs.

resource "aws_ecr_repository" "repos" {
  for_each             = toset(var.repository_names)
  name                 = each.value
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true                # free basic vulnerability scanning
  }

  tags = { Name = each.value }
}

resource "aws_ecr_lifecycle_policy" "cleanup" {
  for_each   = aws_ecr_repository.repos
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}
