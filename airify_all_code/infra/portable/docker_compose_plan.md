# Docker Compose Plan

## Overview

Local development environment using Docker Compose. All services run locally
with no cloud dependencies and no real API keys.

## Services

| Service  | Image              | Purpose                          | Port  |
|----------|--------------------|----------------------------------|-------|
| api      | Dockerfile.api     | Airify FastAPI (mock mode)       | 8000  |
| postgres | postgres:16-alpine | Future persistence layer         | 5432  |
| redis    | redis:7-alpine     | Future cache layer               | 6379  |
| minio    | minio/minio        | Future object storage (S3-compat)| 9000  |

## Design Decisions

- **Mock mode default**: API runs with `AIRIFY_MODE=mock`, no live provider calls.
- **Named volumes**: Data persists across container restarts (local dev convenience).
- **No real secrets**: Placeholder credentials used for local services only.
- **No AWS dependency**: MinIO provides S3-compatible storage locally.

## Usage

```bash
docker compose up -d       # Start all services
docker compose logs api    # View API logs
docker compose down        # Stop all services
docker compose down -v     # Stop and remove volumes
```

## Future Additions

- Database migrations (Alembic or similar)
- Scheduler container (backend-controlled refresh jobs)
- Monitoring/observability containers (Grafana, Prometheus)
