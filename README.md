# AWS ECS Fargate Task API

A FastAPI Task API deployed on **AWS ECS Fargate** behind an Application
Load Balancer, provisioned with **Terraform**, shipped with a
**GitHub Actions CI pipeline** (tests, Trivy scan, Terraform validate,
Docker build) and **Prometheus metrics**.

This is a portfolio project: a small, real service with production-style
plumbing — health checks, least-privilege IAM, ALB-only ingress to the
tasks, and CloudWatch logs — rather than a toy "hello world".

## Features

- Task CRUD API: create, list, get and delete tasks (`/tasks`)
- Health endpoint for the ALB target-group health check (`/health`)
- Prometheus metrics endpoint (`/metrics`): `tasks_created_total`,
  `tasks_total`
- Input validation with Pydantic (empty titles rejected with 422)
- Terraform: VPC, public subnets, internet gateway, ALB, ECS Fargate
  cluster/service/task definition, least-privilege execution role,
  CloudWatch log group (7-day retention)
- CI: pytest, Trivy filesystem scan (HIGH/CRITICAL, unfixed ignored),
  `terraform fmt` + `terraform validate`, Docker build (no push)
- Docker: multi-layer, non-root user, `HEALTHCHECK` on `/health`
- Local stack: `docker-compose.yml` runs the API plus Prometheus

## Architecture

```
Client -> Application Load Balancer (port 80)
        -> ECS Fargate service (1 task, 0.25 vCPU / 0.5 GB)
        -> FastAPI container (port 8000, /health, /metrics)
        -> CloudWatch Logs (/ecs/ecs-fargate-task-api)
Prometheus scrapes /metrics (local compose stack)
```

## Technologies

| Area | Choice | Why |
|---|---|---|
| API | FastAPI + Uvicorn | Async, typed, fast to test; standard for Python services |
| IaC | Terraform (AWS provider ~> 5.0) | Declarative, reviewable, destroyable |
| Compute | ECS Fargate | Serverless containers; no EC2 to patch |
| Load balancing | ALB | Health-checked routing; tasks accept traffic only from the ALB security group |
| Observability | Prometheus `/metrics` + CloudWatch Logs | Metrics for dashboards/alerts, logs for debugging |
| CI/CD | GitHub Actions | Tests, security scan, Terraform validate, Docker build on every push to `main` |
| Container | Docker, `python:3.12-alpine3.24` | Small base image, non-root user |

Alternatives considered: Lambda (already covered in
`aws-lambda-serverless-api` — Fargate fits long-running services
better), EKS (heavier and costlier for one service), ECS on EC2
(more patching for no benefit here).

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload --port 8000
# http://127.0.0.1:8000/health
```

Or with Docker Compose (API + Prometheus on :9090):

```bash
docker compose up --build
```

## Tests

```bash
pip install -r app/requirements.txt pytest==9.0.3 httpx==0.28.1
python -m pytest tests/ -v
```

Test results in this run (2026-10-26, local sandbox, no Docker daemon):
see "Testing results" below. CI re-runs the same suite on every push.

## Deploy (AWS)

> Cost warning: Fargate has no free tier. This uses the smallest size
> (0.25 vCPU / 0.5 GB, 1 task) and is meant as a short-lived demo —
> run `terraform destroy` when finished. No resources were provisioned
> by the author of this repository in this run; deployment requires
> your own AWS credentials.

```bash
cd terraform
terraform init
terraform plan -var image=<your-image>
terraform apply -var image=<your-image>
# API URL is printed as the `api_url` output (ALB DNS + /health)
terraform destroy
```

The container image is set with `-var image=...` (Docker Hub or ECR).
The 1:30 PM Docker Hub job publishes the image for this repo
separately; until then, build it locally with `docker build -t <image> .`

## Security considerations

- No secrets, credentials or tokens are stored in this repository.
- The ECS tasks accept traffic only from the ALB security group;
  the ALB exposes only port 80.
- The container runs as a non-root user; the base image is pinned.
- The ECS execution role uses only the managed
  `AmazonECSTaskExecutionRolePolicy`.
- CI runs a Trivy filesystem scan (vulnerabilities + secrets) that
  fails the build on HIGH/CRITICAL unfixed findings.
- The ALB listener is HTTP for demo simplicity — add an ACM
  certificate and an HTTPS listener before any real traffic.

## Testing results

- Local pytest, 2026-10-26: **8/8 passed** (root, health, create/get,
  list, 404, delete, validation, metrics).
- Docker build: **not run locally** — this environment has no Docker
  daemon. The Docker build runs in GitHub Actions CI instead.
- Terraform: `terraform fmt`/`validate` run in CI (no Terraform binary
  in this environment); no `terraform apply` was run, so no AWS
  resources exist for this project and there is no live URL yet.
- Deployment status: **Not available** (no AWS credentials in this
  environment; deployment is a manual step for the account owner).

## Project structure

```
app/                  FastAPI application (main.py, requirements.txt)
tests/                pytest suite (8 tests)
terraform/            VPC, ALB, ECS Fargate, IAM, CloudWatch (main/variables/outputs/versions)
monitoring/           Prometheus scrape config for local compose
.github/workflows/    CI: tests, Trivy scan, Terraform validate, Docker build
Dockerfile            Pinned Alpine Python image, non-root, HEALTHCHECK
docker-compose.yml    Local API + Prometheus stack
```
