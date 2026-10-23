# AWS Services Matrix Stub

> **STATUS**: Design stub only. No AWS resources exist. No account configured.

## Service Matrix

| Airify Component     | AWS Service          | Required | Notes                     |
|---------------------|---------------------|----------|---------------------------|
| API                 | ECS Fargate         | Optional | Container hosting          |
| Database            | RDS PostgreSQL      | Optional | Managed Postgres           |
| Cache               | ElastiCache Redis   | Optional | Managed Redis              |
| Object Storage      | S3                  | Optional | File/model storage         |
| Secrets             | Secrets Manager     | Optional | API key storage            |
| Monitoring          | CloudWatch          | Optional | Logs and metrics           |
| Scheduler           | EventBridge         | Optional | Backend-controlled refresh |
| DNS                 | Route 53            | Optional | Domain management          |

## Key Points

- ALL services are marked "Optional" — Airify runs without AWS
- No service is hardcoded to AWS; all have non-AWS alternatives
- The competition environment (if any) may use AWS as one deployment option
- Provider refresh jobs would use EventBridge or equivalent scheduler
- Secrets Manager or Parameter Store for API keys (never in code/env files)
