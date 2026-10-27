# Doctor referrals and patient connections

Doctor referral IDs are generated after signup email verification creates the account.
`Dr Rahul Kumar` + the existing public ID `D000001` produces `rahulkumarD000001`.
The `Dr`/`Doctor` prefix, spaces and punctuation are removed; names are normalized to
ASCII lowercase. An empty transliteration uses `doctor`. The existing public ID is
preserved exactly, providing uniqueness. Referral IDs stay unchanged when a name changes.
Clients cannot choose a doctor's referral ID. Migration `0003_doctor_referrals` backfills
existing doctor profiles without changing their public IDs or other account data.

## Doctor referral details

Log in with email/password, then send the doctor's access token:

```http
GET /api/v1/doctors/referral
Authorization: Bearer DOCTOR_ACCESS_TOKEN
```

```json
{
  "doctor": {
    "referral_id": "rahulkumarD000001",
    "public_id": "D000001",
    "full_name": "Dr Rahul Kumar",
    "email": "rahul@example.com",
    "mobile_number": "+919876543211",
    "account_status": "ACTIVE",
    "approval_status": "APPROVED"
  }
}
```

Doctor login, `/doctors/me`, admin/superadmin doctor directories and approval responses
also include `user.referral_id`. The admin UI displays it next to the public ID.

## Optional referral on patient signup

```http
POST /api/v1/patients/register
Content-Type: application/json
```

```json
{
  "full_name": "Test Patient",
  "email": "YOUR_EMAIL@gmail.com",
  "mobile_number": "+919876543210",
  "password": "Patient@2026",
  "confirm_password": "Patient@2026",
  "referral_id": "rahulkumarD000001"
}
```

Use an actual referral ID from an approved active doctor. The field is optional.
Matching is case-insensitive. Invalid/unapproved/suspended referrals return HTTP 422
`invalid_referral` before email is sent. Signup still writes nothing to PostgreSQL
until email OTP is verified. Verification checks doctor eligibility again and inserts
the patient/profile/connection in one transaction. A failed check leaves no patient account.
Patient sessions and `/patients/me` include `user.referred_doctor` (null if unconnected).

## Connect an existing patient

```http
POST /api/v1/patients/connect-doctor
Authorization: Bearer PATIENT_ACCESS_TOKEN
Content-Type: application/json
```

```json
{"referral_id":"rahulkumarD000001"}
```

Each patient has one referring doctor. Repeating the same connection is idempotent;
trying a different doctor returns HTTP 409 `doctor_already_connected`. This endpoint
cannot modify another patient's connection and accepts no patient/user ID input.

- `GET /api/v1/patients/doctor`: connected doctor's name, email, mobile and referral ID.
- `GET /api/v1/doctors/patients?page=1&per_page=25`: authenticated doctor's own patients only.

These endpoints require the appropriate role and verified, approved, active sessions.
Contact details and patient lists are not exposed through an anonymous referral lookup.
Existing patients remain unconnected unless a referral is submitted.

Upgrade an existing database with `python -m alembic upgrade head` and restart the API
and worker. For a new SQL-bootstrap installation, stamp `0001_identity` after running
`supabase/0001_identity.sql`, then upgrade to head for referrals.

The deployed database had an externally managed `0002_care_profiles` revision whose
source was missing from this checkout. A no-op compatibility marker preserves that
history and its optional `care_profiles`/`care_reports` tables. Identity-only installs
do not create or depend on those external extension tables.
