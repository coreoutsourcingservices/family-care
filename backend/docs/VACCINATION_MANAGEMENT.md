# Vaccination management

Run `venv/Scripts/python.exe -m alembic upgrade head` (revision `0007_vaccination_management`), then restart the API and `python -m scripts.mail_worker`.

## Screens
- Admin: http://127.0.0.1:3005/vaccination
- Superadmin: http://127.0.0.1:3005/superadmin/vaccination
- Assigned medical reviewer: http://127.0.0.1:5173/doctor/vaccination-reviews
- Customer: http://127.0.0.1:5173/customer/child/vaccination (also port 5174)

Admin manages catalog, dose versions, eligibility, reminder policy and change history. No clinical master dataset is seeded. Draft entries must cite a source and effective dates. An approved DOCTOR account with an approved verification status, qualification and registration number must review the complete version and attest to source verification and competence. This uses the application's verification records; it does not automatically validate registration against an external medical registry.

Publication: DRAFT -> IN_REVIEW -> APPROVED -> PUBLISHED. Administrators assign a separate reviewer and publish after approval. Hash checks protect the reviewed payload. Published content is immutable; copy to a new version for corrections. Versions can be retired with a reason; historical referenced versions remain readable. Changing eligibility or reminders also requires a new reviewed version. Master vaccine deactivation removes its schedules from current recommendations.

Customer sees only effective, published versions, with UIP and IAP kept separate. For each vaccine/dose, latest effective-from date wins; publication time resolves ties. Country, applicable gender, state/district and parent-reported history determine eligibility. Unknown details or required individual assessment produce REVIEW_REQUIRED. Dates are original DOB-based routine windows, calendar-clamped for months/years. Missing prior doses or inconsistent intervals require review; no catch-up dates are generated. COMPLETED is explicitly parent-reported, including any remaining eligibility concerns. It does not establish clinical verification.

Customer records support published dose references or unlisted vaccination-card entries, Completed/Planned/Missed status, recorded date, clinic, vaccinator, batch, doctor-provided next date, notes and a private PDF/image certificate. Existing profile report upload/download enforces ownership and file limits. Certificate IDs from other profiles are rejected. Admin catalog permission does not grant access to private patient medical records.

The existing Child Care product UI remains ages 0–12. Catalog schemas can represent adolescent windows through 18; reaching those windows in a customer adolescent workspace requires extending the existing profile/module age policy. No automatic migration of older profiles is performed.

## API
All routes below start `/api/v1`. Cookie mutations require existing CSRF headers.

| Method | Route | Access |
| --- | --- | --- |
| GET, POST | `/{admin or superadmin}/vaccination/vaccines` | Respective portal role |
| PUT | `/{portal}/vaccination/vaccines/{id}` | Respective portal role |
| GET, POST | `/{portal}/vaccination/schedules` | Respective portal role |
| PUT | `/{portal}/vaccination/schedules/{id}` | Draft only |
| PUT | `/{portal}/vaccination/schedules/{id}/eligibility` or `/reminders` | Draft only |
| GET | `/{portal}/vaccination/reviewers` or `/audit` | Respective portal role |
| POST | `/{portal}/vaccination/schedules/{id}/submit-review` | `{reviewer_id}` |
| POST | `/{portal}/vaccination/schedules/{id}/withdraw`, `/publish`, `/retire` | Lifecycle checks; retire requires reason |
| GET | `/doctors/vaccination-reviews` | Qualified assigned reviewer |
| POST | `/doctors/vaccination-reviews/{id}` | `{decision: APPROVE or REJECT, notes, attestation}` |
| GET | `/vaccines`, `/vaccination-schedules?schedule_type=UIP` | Public published content |
| GET | `/vaccination-schedules/{id}` | Public published or retired version |
| GET, PUT | `/children/{id}/vaccination-context` | Owning patient |
| GET | `/children/{id}/vaccinations?schedule_type=UIP` | Owning patient timeline |
| POST | `/children/{id}/vaccinations/history` | Owning patient record |

Context: country IN, state, district, gender Unknown/Girls/Boys, history_status UNKNOWN/PARENT_REPORTED, email_reminders false by default.

## Reminders
In-app toggle remains per child. Published policy controls before-window offsets, due-window reminders, overdue offsets, language en/hi and channels. Email additionally requires explicit parent opt-in, eligible active verified owner, a determinate routine status, and an enabled email policy. Worker scans once per minute, with unique enqueue keys per profile/version/day/channel. Pending notifications recheck opt-out, completion, current version and eligibility before SMTP delivery; stale messages cancel. Emails contain a generic sign-in reminder, not medical record details. Existing SMTP outbox uses retries and at-least-once delivery; a crash after SMTP accepts mail can duplicate delivery. SMS is not implemented.

## Tests
`venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`

Browser: run `tests/vaccination_fixture.py` on 5501, Vite with `app/scripts/child-test-vite.config.mjs` on 5175, built Next on 3006 with BACKEND_URL=http://127.0.0.1:5501, then `node admin/tests/vaccination.mjs`. Fixtures use isolated SQLite and mocked file storage, never live patient writes or SMTP.

Frontend list filters, exact JSON shape and request examples: [Child vaccination frontend API](CHILD_VACCINATION_FRONTEND_API.md).
