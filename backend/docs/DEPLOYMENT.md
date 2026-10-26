# Running the backend (no Docker)

## Windows PowerShell

```powershell
cd "D:\my data\core outsourcing services pvt\familycare\backend"
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\venv\Scripts\python.exe scripts/configure_local.py
```

Edit ignored `.env` with actual database/SMTP credentials. Signing secrets are generated
locally, kept out of Git and never printed. Activation is optional; explicit venv paths
avoid execution-policy issues. Configure database as in `SUPABASE_SETUP.md`, then:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m scripts.seed_superadmin
.\venv\Scripts\python.exe server.py
```

In a separate terminal:

```powershell
.\venv\Scripts\python.exe -m scripts.mail_worker
```

Server: `http://127.0.0.1:5001`. Liveness `/health`; readiness `/api/v1/health/ready`.
HTTP 503 readiness means database configuration/connectivity/schema is missing.
SMTP worker is required to deliver queued messages. Set `SMTP_HOST`, `SMTP_PORT`,
`SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and TLS mode. Gmail requires the account's
supported app-password/OAuth SMTP setup, not an invented credential. Provider quotas
and domain authentication affect deliverability. Development mail sinks can use
`SMTP_ALLOW_INSECURE=true`, `SMTP_STARTTLS=false` on loopback only.

Development memory rate limits are per-process. Production requires Redis. No API UI
is served; `/api/docs` is a JSON index and `/api/openapi.json` the importable contract.
Import `docs/postman_collection.json` to test APIs. Store access/refresh credentials
in private Postman environments; do not commit populated collections.

## Ubuntu VPS

Create a service user, Python venv, protected environment file; install requirements
(use `requirements.txt` on Linux; Windows lock omits platform-specific Gunicorn).
Install/start Redis and Nginx. Set `APP_ENV=production`, `COOKIE_SECURE=true`, exact
HTTPS `CORS_ORIGINS`, `RATELIMIT_STORAGE_URI=redis://...`, unique signing secrets and
the verified DB credentials. Bootstrap with a deployment-specific strong password.
Run migrations once with migration credentials; serve using the restricted DB role.

```bash
venv/bin/gunicorn --workers 2 --threads 4 --bind 127.0.0.1:5001 --timeout 30 wsgi:app
venv/bin/python -m scripts.mail_worker
```

Manage both as separate systemd services with restart policies, least filesystem
privileges and a secret environment file (mode 600). Reverse proxy HTTPS through Nginx:

```nginx
location / {
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Configure certificates and renewal for the actual domain. This app does not trust
forwarded client IP headers; rate limits key on the direct peer IP unless you add a
carefully configured proxy trust policy for your known Nginx hop. Do not blindly trust
arbitrary X-Forwarded-For. Plan per-user/per-IP limiter policy with this topology.
No wildcard CORS with credentials. HTTPS and secure cookies are mandatory in production.

Monitor readiness, 5xx/429 rates, database pool wait, SMTP queue age/FAILED counts,
delivery rate, worker restarts and audit events. Keep database backups and rehearse
restores. OTP/challenge expiry uses UTC; synchronize host clocks. Password/OTP/JWT
values and database URLs must never appear in logs.

SMTP delivery is at-least-once: a crash after SMTP acceptance but before commit may
duplicate a message. Stable Message-ID and single-use challenges make repeated mail
safe; exactly-once email delivery is not promised. Failed jobs stop after eight tries;
inspect provider/configuration before manually requeueing in the database.

## Performance validation

100 concurrent clients / 200 HTTP requests per second is a target, not measured capacity.
The included isolated k6 script uses 80% patient profile reads and 20% health requests.
It does NOT represent password-hash/sign-up throughput or SMTP delivery throughput.
Do not run it against production/hosted Supabase without explicit permission.
Prepare isolated accounts/tokens, a test database, Redis and a local mail sink. Configure
benchmark rate limits for the test workload intentionally; do not remove production
abuse controls to advertise a misleading result. With many clients behind a shared IP,
the default limiter can reject load; document policy and IP topology with results.

```bash
k6 run -e BASE_URL=http://127.0.0.1:5001 -e TOKENS=token1,token2 tests/load/traffic.js
```

Report CPU/RAM/OS, worker/thread/pool counts, DB location/size, token/client count,
test duration, actual achieved RPS, dropped iterations, error rates, p50/p95/p99,
CPU/memory/pool saturation. Target profile-read p95 <500ms and <1% unexpected errors.
Measure OTP queue-to-delivery latency separately. No 200-RPS benchmark has been run.
