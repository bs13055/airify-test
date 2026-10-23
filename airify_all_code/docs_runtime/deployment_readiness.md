# Deployment Readiness

## Status: NOT PRODUCTION READY

V1 is designed for local development and feedback testing only.

## What Works Locally

- FastAPI serves API + frontend on localhost:8000
- Mock PM2.5 estimation (deterministic, no external calls)
- A/B experiment assignment
- Local SQLite event storage
- PWA-ready files (manifest, service worker)

## Requirements Before Any Public Deployment

1. **HTTPS**: Mandatory for PWA, security, and data in transit
2. **Domain**: Proper domain name with TLS certificate
3. **Environment**: Separate staging and production environments
4. **Monitoring**: Error tracking, uptime monitoring
5. **Backup**: Event data backup strategy
6. **Privacy**: PDPA compliance review
7. **Security**: Full security audit (see security_baseline.md)
8. **Scaling**: Load testing for expected user count
9. **Data**: Plan for event data retention and deletion

## Demo Deployment Options (Non-Production)

For internal team testing or limited user feedback:
- VPS (DigitalOcean, Linode) with Docker Compose
- Railway / Render (container hosting)
- Local network sharing (for in-person testing)

## NOT Recommended Yet

- AWS production deployment (overkill for demo)
- App Store / Play Store submission
- Public internet exposure without auth
- Production database without backup
