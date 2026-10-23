# infra/ssl

TLS/HTTPS notes (documentation only — **not executed on COM2**). **No certificates, keys, or
secrets are stored here.**

Two supported paths (pick one — see `02_DOMAIN_DNS_SSL_RUNBOOK.md`):

1. **Caddy** — automatic HTTPS (ACME) with a tiny Caddyfile; simplest for a single host.
2. **Nginx + Certbot** — use `../nginx/airify.conf` for routing and Certbot for certificates
   (`certbot --nginx -d <domain>`), auto-renew via the Certbot timer.

Certificates live on the server (e.g. `/etc/letsencrypt/`), **never** in this repo.
