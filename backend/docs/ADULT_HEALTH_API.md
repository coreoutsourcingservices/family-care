# Adult Health

Customer workspace: `/customer/adult/dashboard`. Adult frontend files live in
`customer/src/modules/adult/`. Apply `0015_adult_records` before starting the API.

All adult log endpoints require an authenticated PATIENT session and an owned
adult profile. Existing child profiles older than 12 can use the workspace with
their original profile ID and reports. No records are transferred or deleted.

Base: `/api/v1/patients/adults/{profile_id}/records`

| Method | Path | Behavior |
| --- | --- | --- |
| GET | base | All nondeleted logs for the owned profile |
| POST | base | Create log; returns `record`, HTTP 201 |
| POST | base + `/{record_id}` | Edit same-type log; returns `record` |
| POST | base + `/{record_id}/delete` | Soft-delete; edit history retained |

Required: `kind`, `title` (1–160 characters), ISO `date`.
Optional: `notes` (max 2000), `context` (max 160), `status`
(`Recorded`, `Planned`, `Completed`).

| Kind | Measurements |
| --- | --- |
| bp | Required `systolic`, `diastolic`; optional `pulse` (mmHg / bpm) |
| glucose | Required `glucose` (mg/dL); context can describe fasting / after meal |
| lipids | Required `total`; optional `ldl`, `hdl`, `triglycerides` (mg/dL) |
| lifestyle | Optional `minutes` |
| medicine | Prescribed dose/frequency may be recorded in context |
| screening | Planned or completed preventive check |
| history | Condition, allergy or procedure history |
| consultation_request | Requires a connected doctor; preferred time in context |
| reminder | Planned health task; mark Completed to clear due badge |

Measurements must be positive finite numbers within storage limits. Log dates
cannot precede birth. Readings, history and lifestyle cannot be future dated.
Values remain self-reported and have no automated diagnosis or medication advice.
Each mutation retains an account-attributed revision.

Connected, approved doctors can read logs through their existing care-profile
records endpoint. Consultation requests join the existing doctor request list and
queue doctor notifications. Connection authorization is checked on every request.
Patient-created requests are not confirmed appointments.

Reports use existing profile report upload/download and OCR review endpoints.
Profile reports are refreshed on opening Adult Health and after upload.

Chart.js displays recorded BP and glucose trends and the latest cholesterol
panel. Empty accounts have explicit empty states. Adult reminders are in-app
only: the header bell links to due tasks on all adult pages. Patient background
Web Push is not included in this module.

Checks:
`python -m pytest tests/test_adult_records.py -q` from backend;
`node customer/scripts/check-adult.mjs` from repository root with Vite running.
Browser tests mock APIs and do not change real health records.
