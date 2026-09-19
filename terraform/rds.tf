# =============================================================================
# Managed Postgres.
#
# Never publicly reachable: it answers the application host's security group
# and nothing else. The master password is generated here and kept as its own
# SecureString for rotation, but the instance role is NOT given read access to
# it — it has no need, since the whole `server/.env` parameter already carries
# the DSN with the password in it.
# =============================================================================

resource "random_password" "db" {
  length  = 32
  special = false # URL-safe, so it drops into the postgresql+asyncpg:// DSN as is
}

resource "aws_ssm_parameter" "db_password" {
  name        = "/${var.project_name}/${var.environment}/db_password"
  description = "RDS master password. For reference and rotation; the app reads the full DSN from the env parameter."
  type        = "SecureString"
  value       = random_password.db.result

  tags = {
    Name = "${var.project_name}-rds-password"
  }
}

resource "aws_db_subnet_group" "main" {
  name        = "${var.project_name}-${var.environment}"
  description = "Ganesh ${var.environment} RDS subnet group"
  subnet_ids  = [aws_subnet.public.id, aws_subnet.db_b.id] # must span two AZs

  tags = {
    Name = "${var.project_name}-rds-subnet-group"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds"
  description = "Ganesh RDS: Postgres from the application host alone"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres from the application host"
    protocol        = "tcp"
    from_port       = 5432
    to_port         = 5432
    security_groups = [aws_security_group.app.id]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-${var.environment}"
  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az               = false
  publicly_accessible    = false

  backup_retention_period   = 7
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final"
  apply_immediately         = true

  tags = {
    Name = "${var.project_name}-rds"
  }

  # Everyone's declared months live here. Terraform does not get to drop them.
  lifecycle {
    prevent_destroy = true
  }
}
