# AWS Cost Guardrails Stub

> **STATUS**: Design stub only. No AWS account or billing configured.

## Principles

1. **Start at zero**: No resources provisioned until explicitly needed.
2. **Free tier first**: Leverage free tier where possible during development.
3. **Budget alerts**: Set billing alerts before any resource creation.
4. **Right-size**: Use smallest viable instance sizes.
5. **Tear down**: All resources must be destroyable via IaC (no manual leftovers).

## Estimated Baseline (if deployed)

| Service          | Estimated Monthly | Notes                           |
|-----------------|-------------------|---------------------------------|
| ECS Fargate     | $10–30            | Small task, low traffic         |
| RDS Postgres    | $15–50            | db.t3.micro or serverless       |
| ElastiCache     | $10–25            | cache.t3.micro                  |
| S3              | <$5               | Minimal storage                 |
| Total baseline  | $35–110           | Development/staging only        |

## Guardrails

- Monthly budget alert at $50 (development), $200 (staging)
- No GPU instances unless explicitly approved
- No NAT Gateway unless required (use VPC endpoints)
- No multi-AZ for development environments
- Auto-shutdown for non-production outside business hours (future)

## Competition Environment

If Airify participates in a competition with AWS credits:
- Track spend daily
- Use spot instances where possible
- Destroy resources after competition ends
- Document all resources for clean teardown
