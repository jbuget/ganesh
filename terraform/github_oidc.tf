# =============================================================================
# GitHub Actions reaching AWS through OIDC — no stored key, nothing to rotate.
#
# The runner exchanges a short-lived OIDC token for this role, which may do
# exactly one thing: trigger a deploy on this one instance through SSM Run
# Command.
# =============================================================================

# The OIDC provider is unique per AWS account and already exists in waat-prod,
# created by an earlier stack. We reference it rather than declare it: a second
# declaration fights `EntityAlreadyExists`, and worse, a `destroy` here would
# take every other project's deploy down with it.
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# -----------------------------------------------------------------------------
# Trust policy — this repository, this environment, nothing else.
#
# The job declares `environment: production`, so the `sub` claim reads
#   repo:waat-fr@<org-id>/ganesh@<repo-id>:environment:production
# and NOT the `ref:refs/heads/...` form, which is only emitted when the job has
# no environment. String conditions in IAM are case-sensitive.
# -----------------------------------------------------------------------------
data "aws_iam_policy_document" "github_deploy_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # waat-fr emits immutable numeric IDs inside the subject claim, so a rename
    # of the organisation or the repository changes only the name halves —
    # update github_org_slug / github_repo_slug if that ever happens.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org_slug}@${var.github_owner_id}/${var.github_repo_slug}@${var.github_repository_id}:environment:${var.github_environment}"]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  name               = "${var.project_name}-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_deploy_assume.json
  description        = "Assumed through OIDC by GitHub Actions to deploy Ganesh via SSM."
}

# -----------------------------------------------------------------------------
# What the deploy role may do, and no more.
#   - DescribeInstances: resolve the target by tag. IAM has no resource-level
#     control for this action, hence the `*`.
#   - SendCommand: only AWS-RunShellScript, only on this instance.
#   - Get/ListCommandInvocation: read back the result of the command we issued.
# -----------------------------------------------------------------------------
data "aws_iam_policy_document" "github_deploy" {
  statement {
    sid       = "ResolveInstanceByTag"
    effect    = "Allow"
    actions   = ["ec2:DescribeInstances"]
    resources = ["*"]
  }

  statement {
    sid     = "SendDeployCommand"
    effect  = "Allow"
    actions = ["ssm:SendCommand"]
    resources = [
      aws_instance.app.arn,
      "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript",
    ]
  }

  statement {
    sid       = "PollCommandResult"
    effect    = "Allow"
    actions   = ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_deploy" {
  name   = "${var.project_name}-github-deploy"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_deploy.json
}
