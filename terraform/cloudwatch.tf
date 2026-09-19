# -----------------------------------------------------------------------------
# CloudWatch Logs — the system journal and what the containers write.
#
# user_data.sh installs the agent and points it at the configuration parameter
# below, so the configuration is changed by editing Terraform, not by opening a
# session on the host.
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "app" {
  name              = "/${var.project_name}/app"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${var.project_name}-app"
  }
}

resource "aws_iam_role_policy_attachment" "cwagent" {
  role       = aws_iam_role.app_ssm.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_ssm_parameter" "cwagent_config" {
  name        = "/${var.project_name}/cloudwatch-agent-config"
  description = "CloudWatch Agent configuration for the Ganesh application host."
  type        = "String"
  tier        = "Standard"

  value = jsonencode({
    agent = {
      run_as_user = "root"
    }
    logs = {
      logs_collected = {
        files = {
          collect_list = [
            {
              file_path       = "/var/log/messages"
              log_group_name  = aws_cloudwatch_log_group.app.name
              log_stream_name = "{instance_id}/messages"
              timezone        = "UTC"
            },
            {
              file_path       = "/var/lib/docker/containers/*/*-json.log"
              log_group_name  = aws_cloudwatch_log_group.app.name
              log_stream_name = "{instance_id}/docker"
              timezone        = "UTC"
            }
          ]
        }
      }
    }
  })
}
