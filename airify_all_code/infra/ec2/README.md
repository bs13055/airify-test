# infra/ec2

EC2 deployment assumptions and notes (documentation only — **not executed on COM2**).

- **Target:** COM3 = Ubuntu EC2 instance. Do not assume it exists yet.
- **Security group (assumptions):** inbound 22 (SSH, your IP only), 80 (HTTP), 443 (HTTPS).
  Do not open the raw API port (8000) to the public internet — reach it only via the Nginx
  proxy.
- **Elastic IP:** allocate + associate so the domain A record is stable.
- **Do not** store `.pem` keys, real IPs, or secrets in this repo.

Full step-by-step (packages, Docker, copy project, env, run, verify) is in:
`airify_all_docs/03_deployment_runbooks/01_COM3_EC2_SETUP_RUNBOOK.md`.
Domain/DNS/SSL is in `02_DOMAIN_DNS_SSL_RUNBOOK.md`.
