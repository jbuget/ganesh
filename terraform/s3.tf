# =============================================================================
# Where the files a project carries are put down.
#
# A private bucket, reached by the instance alone through the role it already
# carries. Nothing here is ever served directly to a browser: the API reads
# the bytes and serves them itself, which keeps one stable address per file —
# the address a pasted image is written under, in the markdown of an update
# that will outlive any signature.
#
# On a laptop the same adapter talks to the MinIO of `docker-compose.yml`.
# =============================================================================

resource "aws_s3_bucket" "attachments" {
  bucket = "${var.project_name}-attachments"

  # Everyone's captures, mock-ups and reports live here, and no register can
  # bring them back. Terraform does not get to drop them.
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "${var.project_name}-attachments"
  }
}

# Nothing in here is public, ever. Four switches rather than one: an ACL
# granted by mistake and a policy written by mistake are two different
# mistakes, and both are refused here.
resource "aws_s3_bucket_public_access_block" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Versioning is off on purpose: a file withdrawn from a project is meant to be
# gone, and a bucket quietly keeping every version of what somebody deleted
# would say otherwise.

# What the host may do with the bucket, and no more. Listing is granted on the
# bucket itself, reading and writing on what it holds: the two take different
# resources, and giving object actions on the bucket ARN grants nothing.
data "aws_iam_policy_document" "app_attachments" {
  statement {
    sid       = "ListAttachments"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.attachments.arn]
  }

  statement {
    sid       = "ReadWriteAttachments"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.attachments.arn}/*"]
  }
}

resource "aws_iam_role_policy" "app_attachments" {
  name   = "${var.project_name}-attachments"
  role   = aws_iam_role.app_ssm.id
  policy = data.aws_iam_policy_document.app_attachments.json
}
