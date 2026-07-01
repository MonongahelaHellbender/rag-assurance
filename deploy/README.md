# Deploying the dashboard to AWS (increment 4)

The dashboard is a static site (Vite build → `dashboard/dist/`), so the cheapest, most standard
cloud target is **AWS S3 static website hosting**. Cost is effectively free-tier (pennies/month).

`deploy_s3.sh` automates the whole thing. You run it once your AWS account exists — the deploy uses
**your** credentials, which is why it can't be run from the assistant.

## One-time setup

1. **Create an AWS account** — https://aws.amazon.com (needs a card; static hosting stays within free tier).
2. **Install the AWS CLI**
   ```bash
   brew install awscli        # macOS with Homebrew
   aws --version
   ```
3. **Create an access key + configure the CLI**
   - AWS console → IAM → Users → your user → Security credentials → Create access key (CLI use).
   - Then:
     ```bash
     aws configure            # paste the key id + secret, set region e.g. us-east-1
     ```
   - Best practice: don't use the root account for this — make an IAM user with only S3 permissions.

## Deploy

```bash
cd ~/Documents/Projects/rag-assurance
BUCKET=melissa-rag-assurance-demo ./deploy/deploy_s3.sh
```
Pick a **globally unique** bucket name (all of S3 shares one namespace). The script builds the app,
creates the bucket, enables website hosting, uploads `dist/`, and prints the URL.

To redeploy after changes: rebuild data if needed (`python3 scripts/export_report.py`) and re-run the
same command — `aws s3 sync --delete` updates only what changed.

## Two honest cautions

- **This makes the bucket public.** That's required for S3 website hosting, and it's fine here —
  the dashboard shows only the **synthetic** validation report, no sensitive data. But a public S3
  bucket is a classic data-leak path: **never put anything private (credentials, customer data,
  proprietary content) in this bucket.** Only the dashboard build goes here.
- **Cost:** within free tier for this traffic. Set a small AWS Budgets alert (e.g. $5) so you're
  notified if anything unexpected accrues.

## Production-grade upgrade (optional, more resume-worthy)

For HTTPS, a CDN, and **no public bucket**, front a *private* S3 bucket with **CloudFront + Origin
Access Control (OAC)**. That's the pattern a security-minded model-risk engineer would actually
demonstrate — "static site on S3, served via CloudFront with OAC, bucket not publicly readable."
Ask and I'll write the CloudFront version of the deploy.

## Free alternative (no AWS account)

If you want a live URL today without an AWS account/billing: push `rag-assurance` to a public GitHub
repo and use **GitHub Pages** or **Cloudflare Pages** (both free). That also counts as cloud
deployment on a résumé — it just isn't AWS specifically.
