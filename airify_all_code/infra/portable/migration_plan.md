# Migration Plan

## Overview

Airify is designed to be portable. This document outlines the migration strategy
for moving between deployment targets without vendor lock-in.

## Portability Principles

1. **No hard cloud dependencies**: Core application logic has zero AWS/GCP/Azure imports.
2. **Environment-driven configuration**: All external service URLs come from env vars.
3. **Interface-based storage**: Repository pattern allows swapping backends.
4. **Standard protocols**: S3-compatible storage (MinIO locally, S3/R2/GCS in cloud).

## Migration Targets

| From             | To               | Effort   | Notes                          |
|------------------|------------------|----------|--------------------------------|
| Local Docker     | AWS ECS/Fargate  | Medium   | Swap env vars, add IAM         |
| Local Docker     | Railway/Render   | Low      | Dockerfile already portable    |
| AWS              | GCP Cloud Run    | Low      | Same container, different env  |
| AWS              | Self-hosted      | Low      | Docker Compose on any VM       |

## Database Migration

- Local: PostgreSQL via Docker Compose
- Cloud: Managed Postgres (RDS, Cloud SQL, Supabase, etc.)
- Migration: Alembic scripts (future), same schema everywhere

## Cache Migration

- Local: Redis via Docker Compose
- Cloud: Managed Redis (ElastiCache, Upstash, etc.)
- Interface: Same `REDIS_URL` env var everywhere

## Object Storage Migration

- Local: MinIO (S3-compatible)
- Cloud: AWS S3, Cloudflare R2, GCS (all S3-compatible)
- Interface: Same `OBJECT_STORAGE_ENDPOINT` + `OBJECT_STORAGE_BUCKET` env vars

## Migration-Out-of-AWS Design

If Airify is deployed to AWS in the future, the following ensures easy migration out:
- No AWS SDK (boto3) in application code
- No AWS-specific service abstractions in core logic
- All AWS interactions via environment-configured endpoints
- Infrastructure-as-code kept separate from application code
