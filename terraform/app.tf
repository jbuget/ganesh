# =============================================================================
# The Ganesh API host.
#
# A single EC2 instance (ARM, Amazon Linux 2023) running Caddy and the API in
# Docker. No inbound SSH: deploys go through SSM Run Command, admin through SSM
# Session Manager, both of which the agent opens outbound. There is nothing to
# rotate and no port to close.
# =============================================================================

# -----------------------------------------------------------------------------
# Security group — 80 and 443, and nothing else inbound.
# -----------------------------------------------------------------------------
resource "aws_security_group" "app" {
  # A security group cannot be renamed in place: a new name forces a replace,
  # and the old group cannot be deleted while the live instance holds it
  # (DependencyViolation). `name_prefix` with create_before_destroy lets
  # Terraform stand the new one up, move the instance onto it, then drop the
  # old.
  name_prefix = "${var.project_name}-sg-"
  description = "Ganesh API: public HTTP/HTTPS only, no SSH (deploy and admin via SSM)."
  vpc_id      = aws_vpc.main.id

  lifecycle {
    create_before_destroy = true
  }

  ingress {
    description = "HTTP: serving, and the ACME challenge Caddy answers"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound: GHCR pulls, SSM, DNS, ACME."
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# -----------------------------------------------------------------------------
# Elastic IP — the address the DNS record points at. It survives the instance.
# -----------------------------------------------------------------------------
resource "aws_eip" "app" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }
}

# -----------------------------------------------------------------------------
# The instance.
# -----------------------------------------------------------------------------
resource "aws_instance" "app" {
  ami           = data.aws_ssm_parameter.al2023_arm_ami.value
  instance_type = var.instance_type

  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true

  iam_instance_profile = aws_iam_instance_profile.app_ssm.name

  user_data = templatefile("${path.module}/user_data.sh", {
    project_name         = var.project_name
    cwagent_config_param = aws_ssm_parameter.cwagent_config.name
  })

  depends_on = [
    aws_route_table_association.public,
    aws_ssm_parameter.cwagent_config,
  ]

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  # The only compute host: it holds the Elastic IP association and Caddy's
  # certificate store. Replacing it means an outage and a fresh ACME issuance,
  # so destruction is forbidden, and the two attributes that would otherwise
  # force a replace on an unrelated edit are ignored. Always read the plan:
  # this resource must say `~ update in-place`, never `-/+ replace`.
  lifecycle {
    prevent_destroy = true
    ignore_changes  = [ami, user_data]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}"
  }
}

resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app.id
}
