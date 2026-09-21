#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Deploy the Ganesh API to its production host, through AWS SSM Run Command.
#
# Runs on the GitHub runner once OIDC has configured the AWS credentials. The
# host has no inbound port: the runner issues an ssm:SendCommand, the agent on
# the host pulls the script and runs it, and we poll for the result.
#
# The remote script is base64-encoded before it enters the payload.
# AWS-RunShellScript runs under /bin/sh, which mangles multi-line payloads and
# rejects anything bash-only; `base64 -d | bash` sidesteps both.
#
# Environment:
#   AWS_REGION    target region                        (default eu-west-3)
#   PROJECT_NAME  resolves the instance by tag:Project (default ganesh)
#   ENVIRONMENT   SSM parameter namespace              (default production)
#   DEPLOY_REF    git ref to deploy                    (default main)
#   GIT_REPO      owner/name of the private repository (default waat-fr/ganesh)
#   API_IMAGE     the GHCR image:tag to pull
#   HEALTH_URL    public health endpoint checked after the restart
# ---------------------------------------------------------------------------
set -euo pipefail

AWS_REGION="${AWS_REGION:-eu-west-3}"
PROJECT_NAME="${PROJECT_NAME:-ganesh}"
ENVIRONMENT="${ENVIRONMENT:-production}"
DEPLOY_REF="${DEPLOY_REF:-main}"
GIT_REPO="${GIT_REPO:-waat-fr/ganesh}"
API_IMAGE="${API_IMAGE:-ghcr.io/waat-fr/ganesh-api:latest}"
# The API is only on the internal compose network, so the check goes through
# Caddy over the public name: the real path a caller takes, TLS included.
HEALTH_URL="${HEALTH_URL:-https://api.ganesh.waat.tools/api/v1/health}"

APP_DIR="/home/ec2-user/${PROJECT_NAME}"
ENV_PARAM="/${PROJECT_NAME}/${ENVIRONMENT}/env"
# One classic PAT, two jobs: the git fetch and the GHCR login.
DEPLOY_TOKEN_PARAM="/${PROJECT_NAME}/${ENVIRONMENT}/deploy-token"

echo "==> Resolving the target instance by tag Project=${PROJECT_NAME}"
INSTANCE_ID="$(aws ec2 describe-instances \
  --region "$AWS_REGION" \
  --filters "Name=tag:Project,Values=${PROJECT_NAME}" \
            "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].InstanceId" --output text)"

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" = "None" ]; then
  echo "ERROR: no running instance tagged Project=${PROJECT_NAME}" >&2
  exit 1
fi
echo "    instance: ${INSTANCE_ID}"

# --- The script that runs on the host -------------------------------------
# Expanded HERE, on the runner: the ${...} referring to runner-side
# configuration are baked in. No secret is: the host fetches those from
# Parameter Store itself, so they never enter a payload that SSM logs.
read -r -d '' REMOTE_SCRIPT <<REMOTE || true
set -euo pipefail
export AWS_DEFAULT_REGION="${AWS_REGION}"
# AWS-RunShellScript runs as root with no \$HOME, and git then cannot find
# ~/.gitconfig, which breaks every --global read and write.
export HOME=/root
APP_DIR="${APP_DIR}"
# The exact tag to deploy. docker-compose.prod.yml reads it as \${API_IMAGE}.
export API_IMAGE="${API_IMAGE}"

# Each deploy hands the checkout back to ec2-user (see the chown below), so
# root's git always finds it untrusted. Re-declare the exception every run
# rather than depend on a fix someone once applied by hand.
git config --global --add safe.directory "\${APP_DIR}"

# The deploy PAT, fetched once: it serves the clone below and the GHCR login
# further down.
DEPLOY_TOKEN="\$(aws ssm get-parameter --name '${DEPLOY_TOKEN_PARAM}' --with-decryption --query Parameter.Value --output text)"
CLONE_URL="https://x-access-token:\${DEPLOY_TOKEN}@github.com/${GIT_REPO}.git"

# The first deploy clones; every later one hard-resets onto the target ref, so
# the tree on the host is exactly what the ref says and never a merge of it.
if [ ! -d "\${APP_DIR}/.git" ]; then
  rm -rf "\${APP_DIR}"
  git clone "\${CLONE_URL}" "\${APP_DIR}"
fi
cd "\${APP_DIR}"
git remote set-url origin "\${CLONE_URL}"
git fetch --prune origin
git reset --hard "origin/${DEPLOY_REF}"
git remote set-url origin "https://github.com/${GIT_REPO}.git"   # drop the token from the remote
# SSM ran all of this as root, so the checkout is root-owned. Hand it back, so
# that opening a session on the host does not mean reaching for sudo.
chown -R ec2-user:ec2-user "\${APP_DIR}"

# The production environment, read by the host itself: it never transits the
# SSM payload.
umask 077
aws ssm get-parameter --name '${ENV_PARAM}' --with-decryption --query Parameter.Value --output text > server/.env
chown ec2-user:ec2-user server/.env

# GHCR, with the same PAT. This host never builds an image.
echo "\${DEPLOY_TOKEN}" | docker login ghcr.io -u waat-fr --password-stdin

# Pull, restart, then migrate inside the running container — the application
# does not migrate at start-up, and running it once here beats racing workers.
# Pull and up print a wall of layer noise that would blow past SSM's ~24 KB
# stdout cap and truncate whatever failed afterwards. Keep them quiet so the
# alembic output, and its traceback, actually survives.
docker compose -f docker-compose.prod.yml --env-file server/.env pull >/dev/null
docker compose -f docker-compose.prod.yml --env-file server/.env up -d >/dev/null
docker compose -f docker-compose.prod.yml --env-file server/.env exec -T api alembic upgrade head

# Caddy reads its configuration from a bind mount, and `up -d` never notices
# that a mounted *file* changed: nothing in the service definition moved, so
# compose leaves the container alone and Caddy keeps serving the configuration
# it has held in memory since the last restart. A Caddyfile that reached the
# host and never reached Caddy is worse than one that was not deployed — the
# repository says one thing and the proxy does another.
#
# `reload` rather than `restart`: it is graceful, it drops no connection, and
# it leaves the certificate store alone. An invalid configuration comes back
# non-zero and fails the deploy, which is the answer we want — better a deploy
# that goes red than a proxy quietly running yesterday's rules.
docker compose -f docker-compose.prod.yml --env-file server/.env \
  exec -T caddy caddy reload --config /etc/caddy/Caddyfile

docker image prune -f >/dev/null 2>&1 || true

# Health check. A deploy that leaves the API down is a failed deploy.
for i in \$(seq 1 30); do
  if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
    echo "health OK after \${i} attempt(s)"
    exit 0
  fi
  sleep 4
done
echo "ERROR: health check failed at ${HEALTH_URL}" >&2
docker compose -f docker-compose.prod.yml logs --tail=50 api >&2 || true
exit 1
REMOTE

echo "==> Sending the deploy command through SSM (ref: ${DEPLOY_REF})"
B64="$(printf '%s' "$REMOTE_SCRIPT" | base64 | tr -d '\n')"

CMD_ID="$(aws ssm send-command \
  --region "$AWS_REGION" \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --comment "CD deploy ${DEPLOY_REF} $(git rev-parse --short HEAD 2>/dev/null || echo manual)" \
  --parameters "{\"commands\":[\"echo ${B64} | base64 -d | bash\"]}" \
  --query "Command.CommandId" --output text)"
echo "    command: ${CMD_ID}"

echo "==> Waiting for it to finish"
# `aws ssm wait` polls until terminal and exits non-zero on failure.
set +e
aws ssm wait command-executed --region "$AWS_REGION" \
  --command-id "$CMD_ID" --instance-id "$INSTANCE_ID"
WAIT_RC=$?
set -e

STATUS="$(aws ssm get-command-invocation --region "$AWS_REGION" \
  --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
  --query "Status" --output text)"

echo "----- stdout -----"
aws ssm get-command-invocation --region "$AWS_REGION" \
  --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
  --query "StandardOutputContent" --output text
echo "----- stderr -----"
aws ssm get-command-invocation --region "$AWS_REGION" \
  --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
  --query "StandardErrorContent" --output text

echo "==> Final status: ${STATUS}"
if [ "$STATUS" != "Success" ] || [ "$WAIT_RC" -ne 0 ]; then
  echo "ERROR: the deploy failed" >&2
  exit 1
fi
echo "==> Deploy succeeded"
