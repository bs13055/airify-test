# AWS Architecture Stub

> **STATUS**: Design stub only. No AWS resources have been created.
> No account ID, region hardcoding, or live infrastructure exists.

## Overview

This document describes a POTENTIAL AWS deployment architecture for Airify.
It is included as a design reference only. AWS is one optional future deployment
target — Airify is designed to be portable and not AWS-locked.

## Potential Architecture

```
[Route 53] → [ALB] → [ECS Fargate (API)] → [RDS Postgres]
                                           → [ElastiCache Redis]
                                           → [S3 Bucket]
```

## Service Mapping

| Component       | AWS Service        | Alternative              |
|----------------|--------------------|--------------------------|
| Compute        | ECS Fargate        | Cloud Run, Railway, VM   |
| Database       | RDS PostgreSQL     | Cloud SQL, Supabase      |
| Cache          | ElastiCache Redis  | Upstash, local Redis     |
| Object Storage | S3                 | MinIO, R2, GCS           |
| DNS            | Route 53           | Cloudflare, any DNS      |
| Load Balancer  | ALB                | Cloud LB, Caddy, Traefik |

## Design Constraints

- AWS is an OPTIONAL adapter, not a requirement
- No boto3 in application code
- No AWS SDK imports in service layer
- All AWS access via standard protocols (HTTP, Postgres wire, Redis protocol, S3 API)
- Migration out of AWS must remain feasible at all times
