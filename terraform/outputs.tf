output "public_ip" {
  description = "The Elastic IP. This is what the api.ganesh.waat.tools A record points at."
  value       = aws_eip.app.public_ip
}

output "instance_id" {
  description = "EC2 instance ID, for SSM Session Manager."
  value       = aws_instance.app.id
}

output "ssm_session_command" {
  description = "Ready-to-run command opening an admin shell on the host."
  value       = "aws ssm start-session --profile ${var.aws_profile} --region ${var.aws_region} --target ${aws_instance.app.id}"
}

output "github_deploy_role_arn" {
  description = "The OIDC-assumed deploy role. Set it as the AWS_DEPLOY_ROLE repository secret."
  value       = aws_iam_role.github_deploy.arn
}

output "app_env_parameter_name" {
  description = "The SecureString holding server/.env. Its value is set out of band."
  value       = aws_ssm_parameter.app_env.name
}

output "deploy_token_parameter_name" {
  description = "The SecureString holding the deploy PAT. Its value is set out of band."
  value       = aws_ssm_parameter.deploy_token.name
}

output "rds_endpoint" {
  description = "RDS address. Folds into DATABASE_URL in the env parameter."
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS listener port."
  value       = aws_db_instance.main.port
}

output "db_password_parameter_name" {
  description = "The SecureString holding the RDS master password. Read it with your own SSO credentials."
  value       = aws_ssm_parameter.db_password.name
}

output "vpc_id" {
  description = "ID of the dedicated VPC."
  value       = aws_vpc.main.id
}

output "cloudwatch_log_group" {
  description = "Log group receiving the system journal and the container logs."
  value       = aws_cloudwatch_log_group.app.name
}

output "cloudwatch_logs_console_url" {
  description = "Direct console link to the log group."
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.app.name, "/", "$252F")}"
}

output "attachments_bucket" {
  description = <<-EOT
    The bucket holding the files projects carry. Goes into the production
    `server/.env` as S3_BUCKET; the host reaches it through its own role, so
    no key is needed beside it.
  EOT
  value       = aws_s3_bucket.attachments.bucket
}
