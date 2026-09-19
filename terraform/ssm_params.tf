# =============================================================================
# The application's secrets, in SSM Parameter Store.
#
# The whole production `server/.env` lives here as ONE SecureString. The host
# reads it itself at deploy time and writes it to disk: the value never enters
# the SendCommand payload, which is logged and readable by anyone who can call
# `ssm:GetCommandInvocation`.
#
# The real values are set OUT OF BAND, through the CLI, never through
# Terraform — so no secret ever lands in the state file. Terraform creates the
# parameter and then ignores what is in it.
# =============================================================================

resource "aws_ssm_parameter" "app_env" {
  name        = "/${var.project_name}/${var.environment}/env"
  description = "Production server/.env for Ganesh, read by the host at deploy time."
  type        = "SecureString"
  value       = "PLACEHOLDER — set out of band with `aws ssm put-parameter --overwrite`."

  lifecycle {
    # Managed outside Terraform. Never overwrite it on apply.
    ignore_changes = [value]
  }

  tags = {
    Name = "${var.project_name}-app-env"
  }
}

# One GitHub classic PAT doing both jobs: `git fetch` on the private repository
# (the host needs the compose file and the Caddyfile) and `docker login` to
# GHCR to pull the image CI built. Scopes: `repo` and `read:packages`.
resource "aws_ssm_parameter" "deploy_token" {
  name        = "/${var.project_name}/${var.environment}/deploy-token"
  description = "GitHub classic PAT (repo + read:packages): the host's git fetch and GHCR pull."
  type        = "SecureString"
  value       = "PLACEHOLDER — set out of band with `aws ssm put-parameter --overwrite`."

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Name = "${var.project_name}-deploy-token"
  }
}
