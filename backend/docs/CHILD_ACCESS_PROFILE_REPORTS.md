# Child access, profile management, report classification and notifications

Apply migrations through `0017_realtime_notifications`. The existing deployed
`0015_adult_records` revision is preserved. Do not stamp or reset database history.

## Child profiles

Creating a child now defaults `guardian_name` and `guardian_contact` to the verified
patient account's name and mobile when omitted. The add-child screen prepopulates
both fields and permits overrides. The child's own name is entered separately.

`PATCH /api/v1/patients/profiles/{id}` accepts `full_name`, `date_of_birth`,
`guardian_name`, `guardian_contact`, and `emergency_contacts`. Only the owner can
update a member profile. Dates cannot be future dated or place existing child
records before birth; Child Care edits remain ages 0–12.

`DELETE /api/v1/patients/profiles/{id}` soft-removes an owned member profile.
Private records are retained for audit. The profile disappears from patient and
doctor workspaces, report/record APIs become inaccessible, and new reminders stop.
Deleting an account's self profile is not supported here.

Frontend: Child Care → Settings → Edit profile / Delete child profile.

## Doctor boundaries

Approved connected doctors can GET/POST:
`/api/v1/doctors/care-profiles/{id}/child-records/{area}`.
Areas: `vaccination`, `growth`, `nutrition`, `care`.
POST uses the existing `RecordInput` schema. Growth requires weight in kg and
height in cm. Entries retain the author and a revision and are labelled
`DOCTOR_REPORTED`; families can read them but cannot overwrite/delete them.
The family receives a generic notification when a doctor adds an entry.

Private child medical-history entries and consultation journals are excluded from
the doctor's clinical-records list. Unconnected profiles remain inaccessible.
Only reports explicitly attached to an authorised care entry/certificate are
visible to the connected doctor. Unclassified and medical-history-only documents
stay private. Adult profile sharing retains its existing scope.

Doctor frontend: Child Care for patient entries; Vaccination for IAP drafts and
child-specific applicability. The catalog's independent qualified review and
admin publication requirements remain intact. Admin catalog access does not
grant access to private patient files.

The family can download its medical history and choose whom to share it with;
there is no public unauthenticated medical-history URL.

## Reports and categorisation

The existing OCR API and explicit translation-consent flow are unchanged.
`scripts.report_worker` must run alongside the API; PaddleOCR runs in `.ocr-venv`.
Document language is selected by the user, not silently guessed.

After successful OCR, conservative keyword classification stores Vaccination,
Prescriptions, Scans, Lab tests, or Others on the report. Ambiguous text remains
Others. This is document organisation, not diagnosis. User-reviewed categories
are not overwritten by later OCR. Report lists return `category` and
`category_reviewed` across devices.

`PATCH /patients/profiles/{id}/reports/{report_id}/category`
with `{"category":"Lab tests"}` saves an owner's category correction.

`POST /patients/profiles/{id}/reports/{report_id}/import`:

```json
{
  "kind": "growth",
  "reviewed": true,
  "record": {
    "title": "Reviewed measurements",
    "date": "2026-10-20",
    "weight": "18",
    "height": "110",
    "notes": "Checked against original"
  }
}
```

Requires an owned report with completed/partial readable extraction. Kinds:
growth, vaccination, history, nutrition. Import is idempotent by report and kind.
Measurements/dates must be reviewed; nothing becomes a clinical record just
because OCR produced it. The confirmation explains original-document sharing.
`GET /patients/profiles/{id}/imported-records` lists reviewed imports.
Child imports also appear in their normal child-care sections and growth chart.
Child BMI is calculated from a recorded measurement; adult BMI cutoffs and
unreviewed paediatric normal ranges are not generated.

## Realtime notifications

REST base `/api/v1/notifications`: GET inbox, GET `/unread-count`, POST
`/socket-ticket`, `/test`, `/{id}/read`, `/read-all`. All roles require their
existing eligible authenticated session and cookie CSRF for mutations.
Each operation is user-scoped; clients cannot choose another recipient.

Inbox fields: `items`, `total`, `unread_count`, `page`, `per_page`.
Items include integer `id`, `type`, `title`, `body`, `data`, `created_at`, `read_at`.

Run `python -m scripts.notification_socket` for raw WebSocket
`ws://127.0.0.1:5002/ws/notifications`. First frame within five seconds:
`{"type":"auth","ticket":"TICKET_FROM_REST"}`. Tickets expire in 60 seconds
and cannot authenticate clinical APIs. The gateway validates origins, session
revocation, account eligibility and password version, sends `ready` then
`notification` / `unread_count`, and rechecks the session every two seconds.

Customer notifications persist across page navigation. Reconnect uses a fresh
ticket, jittered backoff and REST resync; unread state refreshes on foreground.
The REST inbox also refreshes periodically if the gateway is unavailable.
Browser alerts require a user permission gesture. Never put tickets in URLs.

The gateway scans due child vaccination records and eligible published reminder
policies once per minute, notifies parent and connected doctor with generic text,
and deduplicates events. Doctor events also reach the existing doctor inbox and
configured Web Push delivery queue. Read state is synchronised between inboxes.
No clinical values or report text are placed in OS notification bodies.

For deployment, proxy `/ws/notifications` with WSS upgrade support and configure
`VITE_NOTIFICATION_WS_URL` when using another gateway origin. Keep gateway ports
private. Customer closed-app mobile FCM/APNs/Web Push is not implemented; live
web/mobile browser connections and the persisted inbox are supported.

Verification uses synthetic isolated data: `tests/test_child_controls.py`,
`tests/test_notification_socket.py`, `tests/test_report_text.py`, and browser
`node app/scripts/check-child-controls.mjs`. The socket test uses a real loopback
WebSocket, including origin rejection and session revocation; browser APIs are
mocked. No real patient report or email is used by these tests.

Connected doctor cards include professional details and a short-lived URL for the
uploaded profile photo; degree documents are never included. Owner-only
`GET /api/v1/patients/profiles/{profile_id}/doctor-overview` returns paginated care
entries authored by the currently connected doctor, excluding family entries.
Doctor child-care `prescription` entries use the existing `care` record kind with
`category: Prescription` and require clinician-entered instructions. These are
displayed in the patient overview alongside vaccinations and other care notes.
The doctor patient list opens `/doctor/patients/{profile_id}`; shared document
access restrictions remain enforced by the API.

Doctor-authored vaccination history supports
`DELETE /api/v1/doctors/care-profiles/{profile_id}/child-records/vaccination/{record_id}`.
Only the current connected authoring doctor can remove their own entry. Removal
is soft, audited with a record revision, and notifies the owning family. Family
entries and entries by another doctor are denied. Shared schedule doses use the
existing child-specific applicability review instead: `NOT_APPLICABLE` preserves
the shared catalog and other children's plans. The doctor UI requires a clinical
reason and explicit professional attestation; it also supports review/restore.

Customer vaccination pages show recorded doses first and age-wise UIP/IAP plans
below. Both portals default to the combined view and allow either programme to
be selected separately. The current age group opens first for each child.
