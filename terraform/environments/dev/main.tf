# terraform/environments/dev/main.tf
# Wires all modules together for the dev environment together

locals {
  env          = "dev"
  cluster_name = "ecommerce-${local.env}"
  name         = "ecommerce-${local.env}"
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_ca_certificate)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      module.eks.cluster_name
    ]
  }
}

# ── Generate a random DB password ────────────────────────────────────────────
resource "random_password" "db" {
  length           = 24
  special          = true
  override_special = "!#$%^&*()-_=+[]"
}

# ── VPC ───────────────────────────────────────────────────────────────────────
module "vpc" {
  source       = "../../modules/vpc"
  name         = local.name
  vpc_cidr     = var.vpc_cidr
  cluster_name = local.cluster_name
}

# ── EKS ───────────────────────────────────────────────────────────────────────
module "eks" {
  source             = "../../modules/eks"
  cluster_name       = local.cluster_name
  kubernetes_version = var.kubernetes_version
  private_subnet_ids = module.vpc.private_subnet_ids
  node_instance_type = var.node_instance_type
  capacity_type      = "SPOT" # cost-save in dev
  node_desired       = 2
  node_min           = 1
  node_max           = 3
}

# ── ECR ───────────────────────────────────────────────────────────────────────
module "ecr" {
  source           = "../../modules/ecr"
  repository_names = ["ecommerce-frontend", "ecommerce-backend"]
}

# ── RDS ───────────────────────────────────────────────────────────────────────
module "rds" {
  source              = "../../modules/rds"
  identifier          = "${local.name}-postgres"
  vpc_id              = module.vpc.vpc_id
  vpc_cidr            = var.vpc_cidr
  private_subnet_ids  = module.vpc.private_subnet_ids
  eks_node_sg_id      = module.eks.node_security_group_id
  db_name             = "ecommerce"
  db_username         = "ecommerceadmin"
  db_password         = random_password.db.result
  instance_class      = var.db_instance_class
  multi_az            = false # single-AZ in dev to save cost
  deletion_protection = false
  skip_final_snapshot = true
}

# ── Secrets Manager ───────────────────────────────────────────────────────────
module "secrets_manager" {
  source      = "../../modules/secrets-manager"
  secret_name = "dev/ecommerce/db"
  db_username = "ecommerceadmin"
  db_password = random_password.db.result
  db_host     = module.rds.endpoint
  db_port     = module.rds.port
  db_name     = module.rds.db_name
}

# ── IAM / IRSA ────────────────────────────────────────────────────────────────
module "iam" {
  source            = "../../modules/iam"
  cluster_name      = local.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  namespace         = "ecommerce"
  db_secret_arn     = module.secrets_manager.secret_arn
}
