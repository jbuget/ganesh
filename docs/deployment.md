# Deploying Ganesh to AWS

The same shape as the other WAAT services — NOMAD, SALSA, SPARTA — so that
whoever is on call recognises what they are looking at. What differs is said
where it differs, and why.

## The shape of it

```
                    ganesh.waat.tools            api.ganesh.waat.tools
                            │                              │
                     ┌──────┴───────┐              ┌───────┴────────┐
                     │ AWS Amplify  │              │  EC2 t4g.micro │
                     │ Next.js SSR  │──── HTTPS ──▶│  Caddy (TLS)   │
                     │ (the BFF)    │              │    │           │
                     └──────────────┘              │    ▼           │
                                                   │  api:8000      │
                                                   │  (FastAPI)     │
                                                   └───────┬────────┘
                                                           │ private subnet-side
                                                   ┌───────▼────────┐
                                                   │ RDS Postgres18 │
                                                   └────────────────┘
```

- **The client** is served by AWS Amplify, built from `amplify.yml`. It is an
  SSR deployment, not a static export: its Route Handlers *are* the BFF.
- **The API** runs in Docker on one EC2 instance, behind Caddy, which obtains
  and renews its certificate on its own.
- **Postgres** is managed RDS, never publicly reachable: its security group
  admits the application host and nothing else.
- **Nothing listens on 22.** Deploys go through SSM Run Command, administration
  through SSM Session Manager. Both are outbound connections the agent opens —
  there is no inbound port to close and no key to rotate.
- **The database is still called `timesheet`**, user included. The product was
  renamed; the database was not, and renaming it now would cost a dump and a
  restore to buy nothing.

One deliberate gap with NOMAD: the client is not a static front calling a
public API with a `NEXT_PUBLIC_API_URL`. Ganesh's browser never calls the API
at all — it calls its own BFF, which holds the Entra token server-side. So the
API URL and the Entra secrets are Amplify's runtime environment, never part of
the browser bundle.

## Before the first apply

- `aws sso login --profile waat-prod` — everything below runs against
  **waat-prod** (account `880882846647`), region **eu-west-3**.
- Terraform ≥ 1.9.
- A GitHub classic PAT with scopes `repo` and `read:packages`. One token, two
  jobs: the host's `git fetch` of this private repository, and its `docker
  login` to GHCR.
- Rights on the `waat.tools` DNS zone.

## 1. Stand the infrastructure up

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # every default already fits
terraform init
terraform plan     # read it: the instance and the database must never say "replace"
terraform apply
```

It creates the VPC, the instance and its Elastic IP, the RDS instance, the two
SSM parameters (empty), the CloudWatch log group, and the IAM role GitHub
Actions assumes.

Note the outputs:

```bash
terraform output public_ip              # the A record
terraform output rds_endpoint           # goes into DATABASE_URL
terraform output github_deploy_role_arn # the AWS_DEPLOY_ROLE secret
```

> `prevent_destroy` guards the instance and the database. `terraform destroy`
> against this directory fails, and that is the point: the instance holds
> Caddy's certificate store, the database holds everyone's declared months.

## 2. Fill the parameters

Terraform creates the parameters and never their contents: a secret in the
state file is a secret on someone's laptop.

**The application environment.** Start from the template, fill in the RDS
endpoint and the password:

```bash
aws ssm get-parameter --profile waat-prod --region eu-west-3 \
  --name /ganesh/production/db_password --with-decryption \
  --query Parameter.Value --output text

cp server/.env.production.example server/.env.production
$EDITOR server/.env.production        # git-ignored

aws ssm put-parameter --profile waat-prod --region eu-west-3 \
  --name /ganesh/production/env --type SecureString --overwrite \
  --value file://server/.env.production
```

**The deploy token:**

```bash
aws ssm put-parameter --profile waat-prod --region eu-west-3 \
  --name /ganesh/production/deploy-token --type SecureString --overwrite \
  --value 'ghp_...'
```

## 3. DNS

Both records, in the `waat.tools` zone:

| Name | Type | Value |
|---|---|---|
| `api.ganesh.waat.tools` | A | the `public_ip` output |
| `ganesh.waat.tools` | CNAME | what Amplify hands you at step 6 |

**The A record must resolve before the first deploy.** Caddy answers an HTTP-01
challenge on port 80; with no record there is no challenge, and Let's Encrypt
rate-limits the retries.

## 4. GitHub

In `waat-fr/ganesh`:

- Check that **Actions is enabled**. A fork has it switched off by default,
  and the deploy workflow will simply never run.
- Create the **`production` environment**. The OIDC trust policy matches
  `...:environment:production`; without the environment the claim reads
  `ref:refs/heads/main`, and the role refuses the exchange with nothing
  readable to explain it.
- Repository secrets:
  - `AWS_DEPLOY_ROLE` — the `github_deploy_role_arn` output.
  - `TEAMS_WEBHOOK_URL` — the same channel the other services post to. It can
    wait: the notification steps are skipped when it is unset, so a deploy that
    worked does not come out red because nobody could be told about it.

## 5. First deploy

The workflow carries `if: github.repository == 'waat-fr/ganesh'`: it runs in
the fork and nowhere else, so a merge on the development repository does not
open a run that cannot succeed. Production therefore deploys from `main` **on
the fork** — after a merge upstream, sync it.

Push to `main`, or run the workflow by hand. It builds the API image for
**linux/arm64** (the host is Graviton; an amd64 image pulls fine and then
refuses to start), pushes it to GHCR, and hands the tag to the host over SSM.

The host then, by itself: fetches the repository at the target ref, reads
`server/.env` from Parameter Store, logs in to GHCR, pulls the image, restarts
the stack, applies `alembic upgrade head` inside the running container, and
checks `https://api.ganesh.waat.tools/api/v1/health`. **A deploy that leaves
the API down fails** — the health check is the last word, not a formality.

## 6. Amplify

Created in the console, not in Terraform: it holds the Entra client secret, and
Terraform state is not a vault.

1. New application → connect `waat-fr/ganesh`, branch `main`.
2. Amplify picks `amplify.yml` up on its own. The platform must be
   **WEB_COMPUTE** (SSR) — the BFF is Route Handlers, a static export would
   drop them silently.
3. Environment variables, on the branch:

   | Variable | Value |
   |---|---|
   | `AZURE_AD_TENANT_ID` | `28d878fd-3802-4f94-931c-79cdf0a419dc` |
   | `AZURE_AD_CLIENT_ID` | `c03d14e8-e876-4703-94a0-99bbda5d5d9d` |
   | `AZURE_AD_CLIENT_SECRET` | the WAATcher app registration's secret |
   | `AZURE_AD_REDIRECT_URI` | `https://ganesh.waat.tools/api/auth/callback/azure-ad` |

   `API_URL`, `API_PREFIX` and `APP_URL` are not here: `amplify.yml` writes them
   into `.env.production` at build time, so they stay readable in the
   repository and survive the application being recreated. Secrets do not get
   that treatment — the build artefact is not a vault either.
4. Custom domain `ganesh.waat.tools`, then the CNAME of step 3.
5. On the Entra app registration (shared with WAATcher), declare the redirect
   URI `https://ganesh.waat.tools/api/auth/callback/azure-ad`.

## Day to day

**A shell on the host** — no SSH, no key:

```bash
aws ssm start-session --profile waat-prod --region eu-west-3 --target <instance-id>
cd /home/ec2-user/ganesh
docker compose -f docker-compose.prod.yml --env-file server/.env logs -f api
```

**The logs**, without opening a session: CloudWatch, log group `/ganesh/app`,
the system journal and every container's output, kept 90 days.
`terraform output cloudwatch_logs_console_url` links straight to it.

**The database**, which is not publicly reachable — tunnel through the host:

```bash
aws ssm start-session --profile waat-prod --region eu-west-3 \
  --target <instance-id> \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{"host":["<rds-endpoint>"],"portNumber":["5432"],"localPortNumber":["55432"]}'
```

**Rolling back** is redeploying a known tag. Every image carries its commit
SHA, so from the host:

```bash
API_IMAGE=ghcr.io/waat-fr/ganesh-api:<sha> \
  docker compose -f docker-compose.prod.yml --env-file server/.env up -d
```

A migration does not roll back with it. Read `alembic downgrade` before
reaching for it, and on a schema change prefer rolling forward.

**Rotating the environment** is `put-parameter --overwrite` followed by a
deploy: the host only reads the parameter when it deploys.

## What is not done yet

**The sign-in flow does not exist.** The BFF carries `/api/auth/signout` and
the API proxy, and no `/api/auth/callback/azure-ad`: the `timesheet_token`
cookie is never set by anything. So production starts with `REQUIRE_AUTH=false`
and **the application is open to whoever knows the address**. That is a
deliberate, temporary step, not a state to settle into — the Entra flow is the
next piece, and the day it lands, `REQUIRE_AUTH=true` goes into the parameter
and the deploy that follows closes the door.

Also left for later, in rough order of how much they will be missed:

- **Staging.** Copy `terraform/` to `terraform/staging/`, change
  `environment`, the CIDRs and the host names. Nothing in the code changes.
- **Remote Terraform state.** It is local and git-ignored today, which means it
  lives on one laptop. S3 plus DynamoDB the day a second person applies — only
  the `backend` block moves.
- **Backups beyond RDS's seven days**, if the retention ever needs to outlive
  the instance.
- **Alarms.** The logs are shipped and the health check gates the deploy, but
  nothing watches the host between two deploys: a CPU credit balance hitting
  zero, a disk filling up or the API falling over at three in the morning are
  found by whoever opens the application next. Neither NOMAD nor SALSA has them
  either — which makes it a gap in the pattern, not in this stack.
