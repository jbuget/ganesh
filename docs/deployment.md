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

The Gemini key is part of that same file, and optional: without it La Gazette
generates digests with their facts and no chapeau. Nothing else in the
application touches it.

`S3_BUCKET` is in it too — the `attachments_bucket` output — and carries no
key beside it: the instance reaches the bucket through the role it already
has, and botocore finds that on its own. A key written there would be a key
to rotate, for nothing.

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

1. New application → connect `waat-fr/ganesh`, branch `main`. Authorise
   through the **GitHub App**, not a personal access token: a token here would
   have to be renewed, and the one the deploy uses is meant to disappear.
2. Amplify picks `amplify.yml` up on its own. The platform must be
   **WEB_COMPUTE** (SSR) — the BFF is Route Handlers, a static export would
   drop them silently.
3. Environment variables, on the application rather than on the branch —
   one branch is deployed and a variable posted on it would have to be posted
   again on the next one:

   | Variable | Value |
   |---|---|
   | `AZURE_AD_TENANT_ID` | `28d878fd-3802-4f94-931c-79cdf0a419dc` |
   | `AZURE_AD_CLIENT_ID` | `7941db35-0f8d-4200-adc3-11964170dd1e` |
   | `AZURE_AD_CLIENT_SECRET` | the secret of that same app registration |
   | `AZURE_AD_REDIRECT_URI` | `https://ganesh.waat.tools/api/auth/callback/azure-ad` |
   | `SESSION_SECRET` | a long random string, this environment's own |
   | `ALLOWED_EMAIL_DOMAIN` | `waat.fr` |
   | `AUTH_ENTRA` | `true`, or `false` to open the fallback door |

   `SESSION_SECRET` seals the session cookie, and nothing works without it:
   sign-in answers 500 for everyone. Generate one per environment — sharing it
   between two would let a session forged in one be spent in the other. The
   build fails outright when it is unset, rather than shipping a client nobody
   can sign in to.

   **The console hands these to the build, not to the running server.** A route
   handler reading `process.env.SESSION_SECRET` at run time finds nothing, and
   signing in answers 500 with `SESSION_SECRET est absent` in the logs. So
   `amplify.yml` copies every one of them into `.env.production` at build time,
   which is how Next reads server environment here. There is no other way in
   short of giving the branch a compute role.

   The secrets therefore live in the build artefact. That cost is weighed and
   accepted: the artefact is readable by whoever can read the Amplify
   deployment — the same people who can read the console variables they come
   from. Nothing reaches the browser: only `NEXT_PUBLIC_` names would, and
   there are none.

   `API_URL`, `API_PREFIX` and `APP_URL` are not in the console at all:
   `amplify.yml` writes them straight in, so they stay readable in the
   repository and survive the application being recreated.
4. Custom domain `ganesh.waat.tools`, then the CNAME of step 3.
5. On Ganesh's own app registration, declare the redirect URI
   `https://ganesh.waat.tools/api/auth/callback/azure-ad` — done. Entra sends
   people back to an address it has been told about and to no other, so a URI
   that is not declared ends the sign-in on a Microsoft error page.

   **The client secret expires.** The day it does, everybody is turned away at
   the door, and the whole of the diagnosis is that Entra refuses the
   exchange. Putting a fresh secret in the console and rebuilding is the fix;
   `AUTH_ENTRA=false` on both sides is the way to get back in meanwhile.

## What production actually is

Written down because half of it is not in Terraform: the Amplify application is
created in the console, and nothing else records its identifiers.

| | |
|---|---|
| AWS account | `880882846647` (`waat-prod`), region `eu-west-3` |
| API host | EC2 `i-0fd877b529458bfb2`, Elastic IP `13.39.143.94` |
| Database | `ganesh-production.cro4wywkgx89.eu-west-3.rds.amazonaws.com:5432`, db `timesheet` |
| Amplify app | `ganesh-production`, app id `d5gyiguzjy1oj`, platform `WEB_COMPUTE` |
| Amplify default URL | `https://main.d5gyiguzjy1oj.amplifyapp.com` |
| Images | `ghcr.io/waat-fr/ganesh-api`, tagged by commit SHA |
| DNS | zone `waat.tools`, **at OVH** — not Route 53. Every record is made by hand. |

The Terraform-managed half is one command away: `terraform output` in
`terraform/`. The Amplify half is the table above.

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
deploy: the host only reads the parameter when it deploys. That is also how
the Gemini key or the model of La Gazette is changed — there is no screen for
either, on purpose: a key the application could hand back is a key worth
stealing.

## What is not done yet

In rough order of how much they will be missed:

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
