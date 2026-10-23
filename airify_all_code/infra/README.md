# Airify Infrastructure

This directory contains infrastructure planning documents and environment definitions.

## Structure

```
infra/
  portable/         — Local/portable environment (Docker Compose, migration plans)
  aws/              — AWS architecture stubs (design only, no resources created)
```

## Principles

- **Portable first**: The system runs locally without cloud dependencies.
- **No AWS lock-in**: AWS is one possible deployment target, not a requirement.
- **No real secrets**: All configuration uses placeholders or environment variables.
- **Migration-ready**: Architecture allows moving between cloud providers.

## Current Status

All documents here are **design stubs**. No infrastructure has been provisioned.
No AWS resources exist. No accounts, regions, or services are configured.
