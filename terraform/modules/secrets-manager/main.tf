# terraform/modules/secrets-manager/main.tf
# Stores RDS credentials as a JSON secret.
# The backend pod reads this secret via IRSA at startup.

resource "aws_secretsmanager_secret" "db" {
  name                    = var.secret_name
  description             = "RDS PostgreSQL credentials for ecommerce backend"
  recovery_window_in_days = var.recovery_window_days
  tags                    = { Name = var.secret_name }
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id

  # Stored as JSON — matches the format database.py expects
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = var.db_host
    port     = tostring(var.db_port)
    dbname   = var.db_name
  })
}
