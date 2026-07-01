#!/usr/bin/env bash
#
# Deploy the rag-assurance dashboard to AWS S3 static website hosting.
#
# Prereqs (one-time — see deploy/README.md):
#   - an AWS account
#   - AWS CLI installed and configured (`aws configure`)
#   - a globally-unique bucket name you choose
#
# Usage:
#   BUCKET=your-unique-bucket-name [REGION=us-east-1] ./deploy/deploy_s3.sh
#
set -euo pipefail

BUCKET="${BUCKET:?Set BUCKET=your-globally-unique-bucket-name}"
REGION="${REGION:-us-east-1}"
HERE="$(cd "$(dirname "$0")" && pwd)"
DASH="$HERE/../dashboard"

echo "==> Building the dashboard"
( cd "$DASH" && npm install --no-audit --no-fund && npm run build )

echo "==> Creating bucket '$BUCKET' in $REGION (skipped if it already exists)"
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET"
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration "LocationConstraint=$REGION"
  fi
fi

echo "==> Allowing public read (required for S3 static website hosting)"
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

POLICY_FILE="$(mktemp)"
cat > "$POLICY_FILE" <<JSON
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadForWebsite",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::$BUCKET/*"
  }]
}
JSON
aws s3api put-bucket-policy --bucket "$BUCKET" --policy "file://$POLICY_FILE"
rm -f "$POLICY_FILE"

echo "==> Configuring static website hosting"
aws s3 website "s3://$BUCKET/" --index-document index.html --error-document index.html

echo "==> Uploading dist/ (with --delete to prune old files)"
aws s3 sync "$DASH/dist/" "s3://$BUCKET/" --delete

echo ""
echo "Deployed. The website URL is shown in the S3 console under"
echo "  Bucket -> Properties -> Static website hosting."
echo "It is usually:  http://$BUCKET.s3-website-$REGION.amazonaws.com/"
