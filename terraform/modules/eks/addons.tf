# EKS Addons - EBS CSI Driver + Default StorageClass + Metrics Server

# -----------------------------
# EBS CSI Driver Addon
# -----------------------------
resource "aws_eks_addon" "ebs_csi" {
  cluster_name      = var.cluster_name
  addon_name        = "aws-ebs-csi-driver"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
}

# -----------------------------
# Metrics Server Addon
# -----------------------------
resource "aws_eks_addon" "metrics_server" {
  cluster_name      = var.cluster_name
  addon_name        = "metrics-server"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
}
