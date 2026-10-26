# Supabase PostgreSQL setup and auth cutover

The v1 API uses SQLAlchemy + Flask JWTs against a private `familycare` schema.
Existing `auth.users` and `public.profiles` are preserved. Supabase API/secret keys
are not used by v1. Never use an API key as a PostgreSQL password.

## 1. Connection

Supabase Dashboard → Connect → direct connection, or **session pooler** for IPv4.
Known direct host: `db.gludrdsinkyptcvixggd.supabase.co`, port 5432, database postgres.
The direct hostname may require IPv6. Copy exact pooler host/user from the dashboard;
do not guess a region. Percent-encode the password in the URI.

```dotenv
DATABASE_URL=postgresql+psycopg://APP_USER:ENCODED_PASSWORD@ACTUAL_HOST:5432/postgres?sslmode=require
MIGRATION_DATABASE_URL=postgresql+psycopg://MIGRATION_USER:ENCODED_PASSWORD@ACTUAL_HOST:5432/postgres?sslmode=require
```

Use `sslmode=verify-full&sslrootcert=...` with the downloaded Supabase CA when available.
The application rejects disabled TLS; `require` encrypts but does not verify hostname.
The connection pool is bounded: workers × (`DB_POOL_SIZE` + `DB_MAX_OVERFLOW`), plus
mail workers/migrations, must fit the Supabase project's connection budget.

## 2. Choose one schema installation path

**A: migrations** on an empty `familycare` schema:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
```

**B: SQL Editor**: paste and run all of `supabase/0001_identity.sql` once. Then:

```powershell
.\venv\Scripts\python.exe -m alembic stamp 0001_identity
```

Do not run migration `upgrade` after SQL bootstrap without stamping it. The migration
executes this exact SQL artifact. Do not run the old `legacy_supabase_auth.sql` for v1.
The SQL creates all eleven tables, UUID keys, constraints, indexes, ID sequences,
immutable ID/role trigger and private-schema grants. It does not create a superadmin
password in SQL; the seed command hashes it using Argon2id.

Check in SQL Editor:

```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'familycare' ORDER BY tablename;
SELECT public_id, full_name, role, approval_status FROM familycare.users;
```

## 3. Application database role

Use a separate migration/owner connection, and create a restricted application LOGIN
role with a strong password in SQL Editor. Set its real password privately:

```sql
CREATE ROLE familycare_app LOGIN PASSWORD 'REPLACE_WITH_A_NEW_RANDOM_DB_PASSWORD';
GRANT CONNECT ON DATABASE postgres TO familycare_app;
GRANT USAGE ON SCHEMA familycare TO familycare_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA familycare TO familycare_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA familycare TO familycare_app;
GRANT EXECUTE ON FUNCTION familycare.assign_public_id() TO familycare_app;
```

Do not execute the example unchanged. Point `DATABASE_URL` at this role afterwards.
Its grants are backend privileges, not end-user roles; Flask performs authorization.
Keep `familycare` OUT of Supabase's exposed Data API schemas. `anon`, `authenticated`
and `PUBLIC` have no access. Tables are private and are not designed for direct
Supabase client access using these Flask JWTs. New migrations must grant only the
new backend objects needed by `familycare_app`.

## 4. Superadmin bootstrap

Set `SUPERADMIN_EMAIL` to your notification email. For development only:

```dotenv
SUPERADMIN_USERNAME=superadmin
SUPERADMIN_PASSWORD=superadmin@2026
```

```powershell
.\venv\Scripts\python.exe -m scripts.seed_superadmin
```

If email/password are missing the command prompts privately. Existing account stays
unchanged. The first login returns a password-change challenge; submit current/new
password to `/api/v1/auth/initial-password` before receiving dashboard tokens.
Production rejects the default bootstrap password. Remove bootstrap password from
environment after seeding. Passwords are never printed or stored plaintext in Postgres.

## 5. Existing user cutover

Old `/api/auth/*`, `/api/doctor/*` and other unversioned routes are retired (404).
Existing Supabase JWTs/refresh tokens cannot authorize `/api/v1/*`. Keep old data for
review/backups; do not copy legacy passwords/hashes or blindly promote roles. For
existing accounts, enroll through the new registration/OTP/review flow or build a
reviewed, separately authorized profile importer with a reset/enrollment invitation.
There is no automatic old-user importer in this release. Update mobile/web clients
to the documented v1 URLs before cutover; never simultaneously treat both issuers
as equivalent. The legacy public schema's policies remain unchanged and must be
reviewed separately if old clients are to be decommissioned.

## Current activation prerequisites

Code can start without a DB; health/docs work, database-backed routes return HTTP 503.
An actual PostgreSQL connection/password and SMTP settings are required to activate
online workflows. The application does not substitute a local database in production.
