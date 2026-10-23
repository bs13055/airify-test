# Security Baseline

## V1 Security Status

This platform is a local demo. Production deployment requires additional
security hardening.

## Current Measures

- No real secrets in codebase
- Environment variables for configuration (no .env file committed)
- CORS restricted to localhost in development
- Security headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- No authentication required (demo mode)
- Does not ask for personal information; PII-like payload keys are stripped before storage (optional free-text feedback may still contain user-entered data)
- Location rounded before storage
- SQLite local storage only (not network-accessible)

## Not Yet Implemented

- HTTPS (required for production)
- Authentication / authorization
- Rate limiting
- Input sanitization beyond Pydantic validation
- SQL injection prevention (parameterized queries used, but no sensitive data)
- CSRF protection
- Secure cookies
- Content Security Policy (restrictive)
- Audit logging
- Penetration testing

## Production Requirements

Before public deployment:
1. HTTPS with valid TLS certificate
2. Authentication system (if user accounts needed)
3. Rate limiting on all endpoints
4. Full Content Security Policy
5. Security audit
6. Dependency vulnerability scanning
7. OWASP Top 10 review
8. PDPA compliance review
9. Data encryption at rest
10. Secure session management

## Secrets Management

- Real API keys must NEVER be in code, docs, or .env files in repo
- Use environment variables or approved secret manager
- Rotate keys regularly
- Audit access to secrets
