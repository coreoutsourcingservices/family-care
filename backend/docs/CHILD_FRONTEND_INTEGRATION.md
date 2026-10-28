# Child-care frontend integration

Updated 28 October 2026. The customer child workspace now persists records through
Flask rather than browser localStorage. Run `python -m alembic upgrade head` before
restarting the API. Migration `0006_child_records` adds three private tables; the
previously applied public-ID migration is preserved in the migration chain.

## Frontend

Open `/customer/child/dashboard` after patient login and selection/creation of a
child profile. The same workspace is served by the public app on 5173 and the
customer app on 5174. The existing profile/report/doctor referral flows remain.

- Dashboard: account records, server-calculated calendar age, reminders and explicit
  unpublished clinical-content states.
- Vaccination: separate UIP/IAP selectors and parent-reported completed/planned
  records. Published reviewed schedules supply routine windows; no catch-up prescription is generated.
- Growth, nutrition, medical history and care notes: create, edit, remove and reload
  records saved to the authenticated account. Weight uses kg and height uses cm.
- Consultation: parent journal entries are separate from requests to the doctor
  connected to this child. Request status is `REQUESTED`, never a booked appointment.
- Settings: in-app reminder toggle, account diary export and explicit import of
  older device entries. Successful imports are removed from local storage; retry
  uses `source_id` to avoid duplicate records. Nothing is silently uploaded.

## Routes now implemented

All `/children` routes require PATIENT authentication and ownership. All mutations
using cookies require the existing CSRF headers. Child IDs are care-profile UUIDs.
List routes return `items`, `total`, `page`, `per_page` (maximum 100).

| Method | Route | Result |
| --- | --- | --- |
| GET | `/api/v1/children` | Owned child profiles and calculated age |
| GET | `/api/v1/children/{id}` | Child identity and calculated age |
| GET | `/api/v1/children/{id}/age` | Calendar-aware age as of Indian product date |
| GET | `/api/v1/children/{id}/dashboard` | Counts, recent records and clinical availability |
| GET | `/api/v1/children/{id}/records` | Paginated account diary across record types |
| GET, POST | `/api/v1/children/{id}/vaccinations/history` | Parent-reported records |
| GET, POST | `/api/v1/children/{id}/growth` | Dated measurements |
| GET, POST | `/api/v1/children/{id}/nutrition` | Nutrition diary |
| GET, POST | `/api/v1/children/{id}/medical-history` | Parent-reported medical diary |
| GET, POST | `/api/v1/children/{id}/care-notes` | Private care notes |
| GET, POST | `/api/v1/children/{id}/consultations` | Parent consultation journal |
| GET, POST | `/api/v1/children/{id}/consultation-requests` | Requests for the connected doctor |
| PATCH, DELETE | Each record collection above + `/{record_id}` | Correction or soft removal with revision history |
| GET | `/api/v1/children/{id}/reminders` | Recorded dates and eligible published schedules, in-app delivery status |
| PUT | `/api/v1/children/{id}/reminder-preferences` | `{ "in_app": true }` |

The connected DOCTOR can read that child's consultation requests, or its own
paginated `/api/v1/doctors/consultation-requests` queue. This does not grant access
to private care notes or other unconnected children's records. Doctor appointment
acceptance, notifications and a doctor-facing request UI are not implemented.

Record POST returns `{ "record": {...} }` with HTTP 201; PATCH returns the same
shape with HTTP 200. DELETE returns a message. Data is labelled `PARENT_REPORTED`;
it does not become verified clinical history just by being saved.

Example growth record:

```json
{"title":"Clinic measurement","date":"2026-10-20","weight":"21.5","height":"116","notes":"Parent-reported"}
```

Example planned vaccination record:

```json
{"title":"Doctor-provided clinic date","date":"2026-11-20","status":"Planned","notes":"Confirm with clinic"}
```

## Reviewed vaccination content

Vaccination catalog, review/publication, eligibility, routine windows and opt-in
email reminders are implemented. Empty installations still return NOT_AVAILABLE
until a qualified reviewer approves and an administrator publishes source-based
versions. Health-guide clinical content remains unavailable. See
[Vaccination management](VACCINATION_MANAGEMENT.md) for the full workflow and APIs.

## Verification

Backend: `venv/Scripts/python.exe -m pytest tests/test_children.py tests/test_care.py -q`.
Tests cover ownership, missing authentication, validation, month-end age,
record revisions, deduplicated device imports, doctor request isolation and preferences.

Browser: run `tests/child_frontend_fixture.py` from backend, start app Vite with
`--config scripts/child-test-vite.config.mjs`, then run
`node app/scripts/check-child-api.mjs` from the repository root. This uses isolated
in-memory SQLite on 5501 and the test app on 5175, never Supabase or SMTP.
