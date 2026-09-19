#!/bin/bash
# ---------------------------------------------------------------------------
# Cloud-init bootstrap for the ${project_name} application host.
#
# Rendered by Terraform's templatefile() with:
#   - project_name         : project identifier, used for the deploy directory
#   - cwagent_config_param : SSM parameter holding the CloudWatch Agent config
#
# Installs Docker, the Compose plugin and the AWS CLI, and starts log
# shipping. It installs no application and holds no secret: the deploy script,
# running later through SSM, clones the repository and reads server/.env from
# Parameter Store. user_data is readable from the instance metadata — nothing
# confidential belongs in it.
# ---------------------------------------------------------------------------
set -euo pipefail

DEPLOY_USER="ec2-user"
APP_DIR="/home/$${DEPLOY_USER}/${project_name}"

# 1. System packages.
dnf update -y
dnf install -y docker git amazon-cloudwatch-agent unzip

# 1b. The AWS CLI — the deploy script reads Parameter Store with it. AL2023
# does not always ship it. On EC2 it picks up the instance profile by itself,
# so there is nothing to configure.
command -v aws >/dev/null 2>&1 || {
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o /tmp/awscliv2.zip
  (cd /tmp && unzip -q -o awscliv2.zip && ./aws/install --update)
}

# 2. Docker.
systemctl enable --now docker
usermod -aG docker "$${DEPLOY_USER}"

# 3. The Compose plugin (v2).
COMPOSE_VERSION="v2.32.4"
ARCH="$(uname -m)"  # aarch64 on Graviton
mkdir -p /usr/libexec/docker/cli-plugins
curl -fsSL \
  "https://github.com/docker/compose/releases/download/$${COMPOSE_VERSION}/docker-compose-linux-$${ARCH}" \
  -o /usr/libexec/docker/cli-plugins/docker-compose
chmod +x /usr/libexec/docker/cli-plugins/docker-compose

# 4. CloudWatch Agent — configuration read from SSM, then started.
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -c ssm:${cwagent_config_param} -s

# 5. The deploy directory. The first deploy clones into it.
install -d -o "$${DEPLOY_USER}" -g "$${DEPLOY_USER}" "$${APP_DIR}"
