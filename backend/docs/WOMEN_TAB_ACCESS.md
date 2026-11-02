# Women tab access and server diary

Women profile owners choose an accepted family member or the profile's connected,
approved doctor, then select View or View + Edit for each tab. For an invited woman,
the woman with her own login controls permission; the inviting family does not.
No sharing starts just because a doctor is connected. No email is sent by these APIs.

The UI offers 1 day, 7 days, 1 calendar month custom local date/time and No expiry (until revoked); it converts
expiry to a timezone-aware ISO timestamp. The server checks expiry on every read,
write and report download. Owner can replace a recipient's permission or revoke it.
Disconnection ends doctor access and revokes their grant. Edit permission does not
allow changing profile identity, connecting doctors or managing sharing.

## Tabs and storage

Keys: `health`, `cycle`, `pcos`, `pregnancy`, `fertility`, `symptoms`, `nutrition`,
`screening`, `records`, `consultation`. The recipient's Dashboard is a summary of
only their allowed tabs. A missing key means no access. `view` permits reading;
`edit` also permits adding, updating and deleting diary records. Medical records
edit permits upload/delete of reports; source files are not edited in place.
Personal calendar reminders are owner-only. Check-in entries use `symptoms` permission.
Consultation diary entries do not create appointments.

Women diary is now stored in PostgreSQL. Older localStorage entries remain on the
device until the owner chooses **Import device diary**, which uploads them explicitly.
Existing IDs are skipped, and the original device data is retained. Previously
granted broad family/doctor access does not bypass Women tab permissions.
Child/adult permissions keep their existing behavior.

## Authentication and routes

Base: `http://127.0.0.1:5001/api/v1`. All routes require a valid PATIENT or approved
DOCTOR session. Sharing routes require the profile's patient owner. Use
`Authorization: Bearer <access_token>`, or cookie transport with
`X-Auth-Transport: cookie`, `X-FamilyCare-Portal: patient|doctor`,
`X-Requested-With: FamilyCare` and `X-CSRF-Token` for writes.

| Method | Path | Result |
|---|---|---|
| GET | `/women/shared` | `{ "items": [{"id":"...","name":"...","permissions":{"cycle":"view"}}] }` |
| GET | `/women/profiles/{id}/workspace` | Basic identity, `owner`, authorized `permissions`, filtered `records`, `access_expires_at` |
| GET | `/women/profiles/{id}/sharing` | Owner's eligible `recipients`, tab labels and grant history |
| PUT | `/women/profiles/{id}/sharing` | Create/replace this recipient's timed grant |
| DELETE | `/women/profiles/{id}/sharing/{grant_id}` | Revoke immediately |
| PUT | `/women/profiles/{id}/diary/{record_id}` | Add/update a UUID record with optimistic version check |
| DELETE | `/women/profiles/{id}/diary/{record_id}?version=1` | Soft-delete the current version |
| GET | `/women/profiles/{id}/reports` | Reports, only with `records` view/edit permission |
| POST | `/women/profiles/{id}/reports` | Multipart `file`, with `records:edit`; PDF/JPEG/PNG/WebP, up to 10 MB |
| GET | `/women/profiles/{id}/reports/{report_id}/download` | Authenticated file bytes; no reusable storage URL |
| DELETE | `/women/profiles/{id}/reports/{report_id}` | Delete report, with `records:edit` |

Example grant request (use a future expiry):

```json
{
  "recipient_id": "22222222-2222-4222-8222-222222222222",
  "permissions": {"cycle":"view", "pregnancy":"edit", "records":"view"},
  "expires_at": "2026-12-01T12:00:00+05:30"
}
```

`200` response:

```json
{
  "grant": {
    "id":"...", "recipient_id":"...", "name":"Selected recipient", "role":"DOCTOR",
    "permissions":{"cycle":"view","pregnancy":"edit","records":"view"},
    "expires_at":"2026-12-01T06:30:00Z", "active":true
  }
}
```

Diary PUT body (version `0` for new records; returned version for updates):

```json
{"section":"cycle","version":0,"data":{"date":"2026-11-01","title":"Period entry","flow":"Medium","notes":"Personal diary"}}
```

`200`: `{"record":{"id":"...","section":"cycle","version":"1","date":"2026-11-01","title":"Period entry","flow":"Medium","notes":"Personal diary"}}`.

Status codes: `401` invalid session; `403` missing tab/edit permission, expired/revoked
grant or non-owner management; `404` missing profile/record/report; `409` stale version
or attempted resurrection; `422` invalid tab/recipient/expiry/data; `413` oversized file;
`502/503` storage/provider unavailable. Refresh after `409` before editing again.

Recipient pages: family `/customer/women/shared`, doctor `/doctor/patients` → shared
Women profiles → `/doctor/women/{profile_id}`. Owner: Women sidebar **Doctor consultation**
or **Manage family & doctor access** on any diary page.

Apply `backend/venv/Scripts/python.exe -m alembic upgrade head` before restarting.
Migration `0021_women_tab_access` creates diary and consent tables without replacing data.

Migration integration (2026-11-02): remote main restored `0021_customer_notes`.
Migration `0023_merge_notes_women` joins that revision and `0022_women_no_expiry`.
Run `alembic upgrade head`; existing notes, diary data and consent are preserved.
No-expiry grants use explicit `"expires_at": null`. Missing expiry fields remain invalid.
