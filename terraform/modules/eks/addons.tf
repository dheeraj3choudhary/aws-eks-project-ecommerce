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

# -----------------------------
# Default StorageClass (gp3)
# -----------------------------
resource "kubernetes_storage_class" "gp3" {
  metadata {
    name = "gp3"

    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner = "ebs.csi.aws.com"

  parameters = {
    type = "gp3"
  }

  reclaim_policy      = "Delete"
  volume_binding_mode = "WaitForFirstConsumer"
}
