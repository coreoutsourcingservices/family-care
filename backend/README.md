# Family Care backend API

Adult/women independent member logins and family email approval:
[Family invitations: requests, responses, OTP destinations and setup](../api-reference/woman_adule_api.md).
Run `venv/Scripts/python.exe -m alembic upgrade head` before starting the new API.
Set `FAMILY_INVITE_FRONTEND_URL` to the trusted public frontend origin for invitation links.
Invite/setup approval emails use SMTP synchronously; forgot-password emails use the existing mail worker.

Doctor signup → OTP → profile setup → admin approval: [Doctor onboarding](docs/DOCTOR_ONBOARDING.md).

Read-only admin patient/member directory: [API and UI details](docs/ADMIN_PATIENT_MEMBERS.md).

Child workspace account records, reminders, consultation requests and current
clinical-content availability: [Child frontend integration](docs/CHILD_FRONTEND_INTEGRATION.md).

Doctor referral IDs and patient connection APIs: [referral guide](docs/REFERRALS.md).

Patient self/member profiles, parent links and Cloudinary report uploads:
[patient care API guide with JSON and multipart examples](docs/PATIENT_CARE_API.md).
Cloudinary credentials must stay in local `.env`; restart after changing them. Live cloud upload has not been verified.

Flask modular backend for doctor, patient/customer, admin and superadmin identity.
Supabase is hosted PostgreSQL; Flask owns password hashing, email OTP, approval and JWT.
No Docker and no frontend/UI.

## Start (Windows)

```powershell
cd "D:\my data\core outsourcing services pvt\familycare\backend"
.\venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\venv\Scripts\python.exe scripts/configure_local.py
```

Fill `DATABASE_URL`, migration connection and SMTP settings privately in ignored `.env`.
Then follow `docs/SUPABASE_SETUP.md` to install `supabase/0001_identity.sql` or migrations.
The old Supabase Auth `public.profiles` database is preserved, but is not used by v1.

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m scripts.seed_superadmin
.\venv\Scripts\python.exe server.py
```

Run the email worker in a second terminal:

```powershell
.\venv\Scripts\python.exe -m scripts.mail_worker
```

Base URL: http://127.0.0.1:5001

- GET `/health`: server liveness (no DB required).
- GET `/api/v1/health/ready`: real database/schema readiness (503 if not configured).
- GET `/api/docs`: JSON API index; no UI.
- GET `/api/openapi.json`: OpenAPI 3.1 contract.
- All role routes use `/api/v1/superadmin`, `/api/v1/admin`, `/api/v1/doctors`, `/api/v1/patients`.
- Complete API list/examples: `docs/API_DOCUMENTATION.md`.
- Postman import: `docs/postman_collection.json`.

IDs: A000001 / D000001 / C000001 from PostgreSQL sequences; UUID relationship keys.
Passwords: 8-128 characters, Argon2id hashes. Development superadmin: username superadmin,
password superadmin@2026 when supplied to bootstrap; first login requires password change.
Production refuses the default bootstrap password. No public superadmin registration.

Patient signup JWT is issued only after email OTP verification. Admin/doctor require review.
All roles log in with email/password without login OTP. Approved and verified accounts are required.
Access JWT is 15 minutes; rotating/revocable refresh session defaults to 7 days.

## Structure

```text
backend/
  app.py                 # Factory, extensions, error handlers
  server.py              # Windows Waitress entry (5001)
  wsgi.py                # Linux Gunicorn entry
  core/                  # Config, database, shared models/security/schema/OpenAPI
  doctor/                # model/controller/routes/service/repository/schema
  patient/               # Same boundaries
  admin/                 # Same boundaries
  superadmin/            # Same boundaries
  auth/                  # Shared auth endpoints
  services/              # OTP/session/approval/outbox workflows
  templates/emails/      # Text email templates, no website UI
  migrations/            # Alembic revision (executes canonical SQL)
  supabase/0001_identity.sql
  scripts/               # Configuration, seeding, SMTP worker, docs export
  docs/                  # Setup, API, schema, auth, deployment, tests
  examples/              # Flutter/JavaScript API clients only
  tests/                 # Workflows, security, PostgreSQL concurrency, load script
  venv/                  # Local ignored Python environment
```

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Without TEST_DATABASE_URL, workflow tests use isolated SQLite and PostgreSQL tests skip.
SQLite is never accepted for running the real app. To verify real PostgreSQL locking,
provide a dedicated loopback test database whose name ends in `_test`:

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://TEST_USER:ENCODED_PASSWORD@127.0.0.1:55439/familycare_test?sslmode=require'
.\venv\Scripts\python.exe -m pytest -q
```

Tests recreate the `familycare` schema in that isolated database. Do not use real data.
They never select the production DATABASE_URL automatically. Email sends are mocked.

Regenerate API docs after route changes:

```powershell
.\venv\Scripts\python.exe -m scripts.export_api_docs
```

See `docs/DEPLOYMENT.md` for Windows/Linux deployment and performance validation.
100 concurrent clients / 200 RPS is a target, not a measured capacity claim.

## Signup OTP persistence and delivery

The register/verify-email/resend-otp URLs and request JSON remain the same.
Register writes no records to PostgreSQL. Validated details and an Argon2 password
hash are held in a temporary cache (10 minutes); OTP validity is 5 minutes, with
5 attempts and a 60-second resend cooldown. No plaintext password or OTP is cached.
Register sends OTP through SMTP before returning `email_status: "sent"` (SMTP acceptance,
not inbox confirmation). SMTP failures return HTTP 503 `email_delivery_failed`.
`public_id` and `user_id` are null until OTP verification creates the user/profile
and, for admins, an approval request in one database transaction. Verified doctors
receive a limited-purpose profile setup token instead. Their approval request is
created only after the professional profile, doctor address, clinic address and
years of experience are submitted through `/api/v1/doctors/setup-profile`.

Local development uses a bounded in-memory cache; restarting the API discards pending
signups, so register again. Production/multiple API processes must use the same Redis
`RATELIMIT_STORAGE_URI`; the pending cache uses Redis TTL and a distributed lock.
Existing accounts and old unverified records are preserved. Pending doctor credentials
are not reserved; database uniqueness is checked again when verification creates the account.

SMTP port 465 requires `SMTP_SSL=true` and `SMTP_STARTTLS=false`. Port 587 normally
uses `SMTP_SSL=false` and `SMTP_STARTTLS=true`. Reset/approval email still needs
`python -m scripts.mail_worker`. Signup email does not require the worker.

Current login flow: all roles use email + password without login OTP. Signup email OTP,
password-reset OTP, account approval and first-login password change are preserved.
Legacy superadmin username login remains compatible. Legacy verify-login-otp routes return HTTP 410.

Medical report image/PDF extraction and optional English translation: [OCR API and runtime setup](docs/REPORT_OCR_API.md). Run the separate `python -m scripts.report_worker` alongside the API.
