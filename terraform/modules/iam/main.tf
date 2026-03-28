# terraform/modules/iam/main.tf
# IRSA: creates an IAM role bound to the backend Kubernetes Service Account.
# The role allows the backend pod to call Secrets Manager — no static keys needed.

data "aws_caller_identity" "current" {}

locals {
  oidc_provider_id = replace(var.oidc_provider_url, "https://", "")
}

# ── IAM Role for Backend Service Account (IRSA) ───────────────────────────────
resource "aws_iam_role" "backend_sa" {
  name = "${var.cluster_name}-backend-irsa"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_provider_id}:sub" = "system:serviceaccount:${var.namespace}:backend-sa"
          "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

# ── Policy: allow reading the DB secret from Secrets Manager ──────────────────
resource "aws_iam_policy" "secrets_read" {
  name        = "${var.cluster_name}-backend-secrets-read"
  description = "Allow backend pod to read DB credentials from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
        Resource = var.db_secret_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backend_sa_secrets" {
  role       = aws_iam_role.backend_sa.name
  policy_arn = aws_iam_policy.secrets_read.arn
}

# ── IAM Role for AWS Load Balancer Controller ─────────────────────────────────
resource "aws_iam_role" "alb_controller" {
  name = "${var.cluster_name}-alb-controller"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_provider_id}:sub" = "system:serviceaccount:kube-system:aws-load-balancer-controller"
          "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

# AWS-managed policy for ALB controller (downloaded from AWS docs)
resource "aws_iam_policy" "alb_controller" {
  name   = "${var.cluster_name}-alb-controller-policy"
  policy = file("${path.module}/alb-controller-policy.json")
}

resource "aws_iam_role_policy_attachment" "alb_controller" {
  role       = aws_iam_role.alb_controller.name
  policy_arn = aws_iam_policy.alb_controller.arn
}
