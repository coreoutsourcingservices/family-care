# Validation performed

Verification used an isolated, loopback PostgreSQL 16.4 instance with TLS on this Windows
machine. It did not run against the hosted Supabase project or send real emails.
Temporary tools/data are ignored under `.test-tools` / `.test-data` and are not shipped.

Results:

- 30 automated tests passed using real PostgreSQL.
- 100 concurrent database inserts generated unique role-prefixed IDs; deletion did not
  reuse IDs. IDs beyond 999999 expanded without truncation; ID mutation was rejected.
- Eight concurrent OTP verifications issued exactly one session.
- Concurrent refresh produced one success and one reuse rejection, revoking the family.
- SQLAlchemy metadata and generated SQL schema compared equal.
- An unprivileged database role was denied private-schema access.
- Admin verification/approval/login OTP, doctor review/rejection/resubmission, patient
  verification/JWT, expiry/attempts/resend/replay, password change/reset, bootstrap,
  suspension, JWT issuer/audience/purpose, cookie CSRF, logout and rate limits passed.
- SMTP worker send/retry behavior was tested with mocked delivery; SMTP was not configured.
- Alembic upgrade on an empty isolated database passed; repeating upgrade was a no-op.
- SQL bootstrap + Alembic stamp + upgrade on another isolated database passed.
- Running server returned HTTP 200 for `/health`, `/api/docs` and `/api/openapi.json`.
- Live API readiness returned HTTP 503 `database_not_configured`, as expected with no
  PostgreSQL DATABASE_URL. No hosted database password was available.

Not verified: hosted database deployment/grants, real SMTP delivery, end-to-end UI
clients (none built), and 200-RPS capacity. Flutter/web files are API integration
examples; no Flutter or browser build environment was run. No load test was run.
