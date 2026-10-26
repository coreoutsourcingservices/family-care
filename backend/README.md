# Family Care backend API

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
Admin/patient login requires password and email OTP; approved doctor uses email/password.
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
