# =============================================================================
# Ganesh — production infrastructure, one flat stack.
#
# One EC2 host for the API behind Caddy, one managed Postgres, the secrets in
# SSM Parameter Store, and an OIDC role GitHub Actions assumes to deploy. The
# Next.js client is not here: AWS Amplify serves it (see `amplify.yml`), and
# the Amplify application itself is created in the console, not by Terraform —
# it holds the Entra secrets, and Terraform state is not a vault.
#
# Same layout as waat-fr/NOMAD, deliberately: a flat stack for a single
# environment. Staging, the day it comes, is a copy of this directory with its
# own state, not a `count` on every resource.
#
# Names are lowercase throughout — `ganesh`, matching the repository. The OIDC
# trust policy matches strings case-sensitively, and one capital in the wrong
# place there fails with nothing to read but "not authorized to perform
# sts:AssumeRoleWithWebIdentity".
# =============================================================================
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Local state, git-ignored. It carries resource IDs and the RDS password:
  # never commit it. If the team grows, move to S3 + DynamoDB — only this block
  # changes.
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# -----------------------------------------------------------------------------
# AMI — Amazon Linux 2023 ARM64, resolved through the parameter AWS publishes,
# so a rebuild never pins yesterday's image.
# -----------------------------------------------------------------------------
data "aws_ssm_parameter" "al2023_arm_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

# -----------------------------------------------------------------------------
# Networking — a VPC of its own, one public subnet, an internet gateway.
# -----------------------------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.subnet_cidr
  availability_zone       = var.subnet_az
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.project_name}-public"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# A second subnet in another AZ, there only because `aws_db_subnet_group`
# refuses fewer than two — even for a Single-AZ database. It is deliberately
# left out of the public route table: it falls back to the VPC's default one,
# which routes locally and nowhere else, so nothing in it can reach the
# internet. Subnets cost nothing; only what runs in them does.
resource "aws_subnet" "db_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.db_subnet_cidr
  availability_zone = var.db_subnet_az

  tags = {
    Name = "${var.project_name}-db-b"
  }
}

# -----------------------------------------------------------------------------
# IAM — the instance's own role. SSM Session Manager replaces SSH entirely.
# -----------------------------------------------------------------------------
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app_ssm" {
  name               = "${var.project_name}-ssm"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.app_ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# The host may read exactly two parameters — its environment and its deploy
# token — and decrypt them. Named one by one rather than by path prefix: a
# wildcard would silently widen the day someone adds a third parameter under
# the same namespace.
data "aws_iam_policy_document" "app_read_secret" {
  statement {
    sid     = "ReadAppSecrets"
    effect  = "Allow"
    actions = ["ssm:GetParameter"]
    resources = [
      aws_ssm_parameter.app_env.arn,
      aws_ssm_parameter.deploy_token.arn,
    ]
  }

  statement {
    sid       = "DecryptAppEnv"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.aws_region}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "app_read_secret" {
  name   = "${var.project_name}-read-app-env"
  role   = aws_iam_role.app_ssm.id
  policy = data.aws_iam_policy_document.app_read_secret.json
}

resource "aws_iam_instance_profile" "app_ssm" {
  name = "${var.project_name}-ssm"
  role = aws_iam_role.app_ssm.name
}
