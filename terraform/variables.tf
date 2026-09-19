variable "aws_region" {
  description = "AWS region hosting the API. Paris, like every other WAAT stack."
  type        = string
  default     = "eu-west-3"
}

variable "aws_profile" {
  description = "AWS CLI profile (SSO) used against the target account."
  type        = string
  default     = "waat-prod"
}

variable "project_name" {
  description = <<-EOT
    Project identifier, used for tags, resource names, SSM paths and the deploy
    directory on the host. Lowercase, matching the repository name: the deploy
    script resolves the instance by `tag:Project`, and IAM compares strings
    case-sensitively.
  EOT
  type        = string
  default     = "ganesh"
}

variable "environment" {
  description = "Environment name, used for tagging and the SSM namespace."
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = <<-EOT
    EC2 instance type. ARM Graviton, and a step above NOMAD's t4g.nano: this
    host runs uvicorn with SQLAlchemy and asyncpg loaded, and applies Alembic
    migrations in-container at deploy. 1 GiB leaves room for that; 512 MiB
    would mean watching the OOM killer.
  EOT
  type        = string
  default     = "t4g.micro"
}

# -----------------------------------------------------------------------------
# GitHub OIDC — who is allowed to deploy.
# -----------------------------------------------------------------------------

variable "github_org_slug" {
  description = "GitHub organisation as it appears in the OIDC `sub` claim."
  type        = string
  default     = "waat-fr"
}

variable "github_repo_slug" {
  description = "Repository name as it appears in the OIDC `sub` claim. Case-sensitive: the repository is `ganesh`, lowercase."
  type        = string
  default     = "ganesh"
}

variable "github_owner_id" {
  description = <<-EOT
    Numeric GitHub organisation ID for waat-fr, matched against the OIDC
    `repository_owner_id` claim. The organisation emits immutable IDs in the
    subject, so authorising by ID survives a rename where a name would not.
    Find it: `gh api orgs/waat-fr --jq .id`.
  EOT
  type        = string
  default     = "236424188"
}

variable "github_repository_id" {
  description = <<-EOT
    Numeric GitHub repository ID for waat-fr/ganesh, matched against the OIDC
    `repository_id` claim. Immutable across renames.
    Find it: `gh api repos/waat-fr/ganesh --jq .id`.
  EOT
  type        = string
  default     = "1377592789"
}

variable "github_environment" {
  description = <<-EOT
    GitHub Actions environment gating the deploy job. It is part of the OIDC
    `sub` claim, so it must equal the `environment:` the workflow job declares.
  EOT
  type        = string
  default     = "production"
}

# -----------------------------------------------------------------------------
# Network
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block of the dedicated VPC."
  type        = string
  default     = "10.30.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block of the single public subnet."
  type        = string
  default     = "10.30.0.0/24"
}

variable "subnet_az" {
  description = "Availability zone of the public subnet."
  type        = string
  default     = "eu-west-3a"
}

variable "db_subnet_cidr" {
  description = "CIDR of the second-AZ subnet, there only to satisfy the RDS subnet group."
  type        = string
  default     = "10.30.1.0/24"
}

variable "db_subnet_az" {
  description = "Availability zone of the RDS-only second subnet. Must differ from subnet_az."
  type        = string
  default     = "eu-west-3b"
}

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

variable "db_engine_version" {
  description = "Postgres major version. 18, as in development."
  type        = string
  default     = "18"
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage, in GiB."
  type        = number
  default     = 20
}

variable "db_name" {
  description = <<-EOT
    Database name. `timesheet`, not `ganesh`: the product was renamed, the
    database was not, and renaming it now would cost a dump and a restore to
    buy nothing — nobody reads the name of a database.
  EOT
  type        = string
  default     = "timesheet"
}

variable "db_username" {
  description = "RDS master user. `timesheet`, for the same reason as db_name."
  type        = string
  default     = "timesheet"
}

# -----------------------------------------------------------------------------
# Observability
# -----------------------------------------------------------------------------

variable "cloudwatch_log_retention_days" {
  description = "Retention of the application log group, in days."
  type        = number
  default     = 90
}
