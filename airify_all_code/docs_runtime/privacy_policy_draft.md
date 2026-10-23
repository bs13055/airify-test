# Privacy Policy Draft (V1 Demo)

> **Note**: This is a DRAFT for demonstration purposes only. Legal review
> is required before public deployment. This does not constitute a binding
> privacy policy.

## Overview

Airify Platform V1 is a demonstration platform for product feedback testing.
It collects minimal, anonymous interaction data to improve the product.

## What We Collect

| Data | Purpose | Stored |
|------|---------|--------|
| Anonymous session ID | Link interactions to one session | Locally (SQLite) |
| Approximate location (3 decimal places) | Understand geographic usage | Locally |
| Event type (page view, feedback click) | Understand user behavior | Locally |
| A/B variant assignment | Compare UI approaches | Locally |
| Optional text feedback | Improve product | Locally |
| Timestamp | Event ordering | Locally |

## What We Do NOT Ask For

This demo does not ask for your name, email, or phone number. Users are asked
not to enter personal information, address, or medical information. PII-like
payload keys (for example `name`, `email`, `phone`, `address`) are stripped
before storage. Because the optional text feedback field is free-form, it may
still contain whatever a user chooses to type, so users are warned before
submission.

The demo also does not intentionally collect:

- Exact location (coordinates are rounded to 3 decimals)
- Device ID or fingerprint
- IP address (not logged)
- Browsing history
- Photos, contacts, or messages
- Payment information

## Storage

All data is stored locally in a SQLite database on the server running
the demo. It is not transmitted to cloud services or third parties.

## Retention

Demo data may be deleted at any time. There is no guaranteed retention
period. Users can request deletion by contacting the project team.

## Third Parties

No data is shared with third parties. No analytics SDKs, advertising
networks, or external services receive any user data.

## Rights

Users may:
- Stop using the platform at any time
- Clear their browser localStorage to reset their session
- Request deletion of their events from the local database

## PDPA/GDPR Note

Full compliance with PDPA (Thailand) or GDPR (EU) requires:
- Formal privacy impact assessment
- Data protection officer designation (if applicable)
- Explicit consent mechanism for any personal data
- Right to access, rectification, and erasure implementation
- Data breach notification procedures

These requirements must be met before any public deployment that
processes personal data. The V1 demo reduces this risk by not asking
for personal information and stripping PII-like payload keys before
storage; it is not a claim of PDPA/GDPR compliance, and optional
free-text feedback may still contain user-entered data.

## Future Requirements

Before public release:
1. Legal review of this policy
2. PDPA compliance assessment
3. Consent mechanism if health data is added
4. Data processing agreements if cloud hosting is used
5. Regular privacy audits
