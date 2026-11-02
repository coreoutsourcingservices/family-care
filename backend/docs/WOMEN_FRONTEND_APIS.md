# Women frontend → backend APIs

Base URL: `http://127.0.0.1:5001/api/v1`.
`{profile_id}` is the selected Women profile UUID; `{record_id}` is the diary UUID.
Create a new diary UUID in the client, then PUT with `version: 0`. For edits, send
the version returned by the server. All nine diary sections share the same API;
the `section` field selects the tab. They are stored in `women_diary_records`.

## Authentication

Bearer clients: `Authorization: Bearer <access_token>` and `Content-Type: application/json`.
Browser clients use HttpOnly session cookies and the existing `careApi` helper:

```http
X-Auth-Transport: cookie
X-FamilyCare-Portal: patient
X-Requested-With: FamilyCare
X-CSRF-Token: <csrf_token_for_writes>
```

Doctors use the `doctor` portal and their own CSRF token. Sharing grants determine
which tabs family/doctor accounts can read or edit; owner access does not need a grant.

## Every frontend section

| Frontend | Read API | Save API / section |
|---|---|---|
| Dashboard | `GET /women/profiles/{profile_id}/workspace` | Summary/chart calculated from returned server diary; no dashboard write |
| My health | Same workspace GET | `PUT /women/profiles/{profile_id}/diary/{record_id}`, `section: health` |
| Period & cycle | Same workspace GET | Same PUT, `section: cycle` |
| PCOS & hormonal | Same workspace GET | Same PUT, `section: pcos` |
| Pregnancy care | Same workspace GET | Same PUT, `section: pregnancy` |
| Fertility & reproductive | Same workspace GET | Same PUT, `section: fertility` |
| Symptoms & wellness | Same workspace GET | Same PUT, `section: symptoms` |
| Nutrition & lifestyle | Same workspace GET | Same PUT, `section: nutrition` |
| Screening & preventive | Same workspace GET | Same PUT, `section: screening` |
| Medical records | `GET /patients/profiles/{profile_id}/reports` (owner) | `POST /patients/profiles/{profile_id}/reports`, multipart `file` |
| Doctor consultation | Workspace GET + profile's doctor details | Diary PUT, `section: consultation`; separate connection and sharing APIs below |

Workspace response (`200 OK`):

```json
{
  "profile": {"id":"<profile UUID>","name":"Example Woman","dob":"1990-01-01"},
  "owner": true,
  "permissions": {"health":"edit","cycle":"edit","pcos":"edit","pregnancy":"edit","fertility":"edit","symptoms":"edit","nutrition":"edit","screening":"edit","records":"edit","consultation":"edit"},
  "access_expires_at": null,
  "records": [{"id":"<record UUID>","section":"cycle","version":"1","date":"2026-11-01","title":"Period entry","flow":"Medium"}]
}
```

An authorized recipient receives only permitted sections/records. The frontend
refreshes the workspace every 30 seconds and updates local state after successful
API writes. Existing localStorage diary data is uploaded only through **Import device diary**.

## Request JSON for each diary tab

Each example goes to `PUT /women/profiles/{profile_id}/diary/{record_id}`.

My health:

```json
{"section":"health","version":0,"data":{"date":"2026-11-02","title":"Health review","category":"General health","notes":"Personal notes"}}
```

Period & cycle:

```json
{"section":"cycle","version":0,"data":{"date":"2026-11-01","title":"Period entry","end":"2026-11-05","flow":"Medium","symptoms":"Recorded symptoms","notes":"Personal notes"}}
```

PCOS & hormonal:

```json
{"section":"pcos","version":0,"data":{"date":"2026-11-02","title":"Clinician visit","category":"Clinician diagnosis","severity":"Mild","notes":"Notes from clinician"}}
```

Pregnancy care:

```json
{"section":"pregnancy","version":0,"data":{"date":"2026-11-02","title":"Antenatal visit","category":"Antenatal visit","week":"12","due":"2027-05-01","notes":"Clinician-provided details"}}
```

Fertility & reproductive:

```json
{"section":"fertility","version":0,"data":{"date":"2026-11-02","title":"Questions for consultation","category":"Question for doctor","notes":"Questions to discuss"}}
```

Symptoms & wellness:

```json
{"section":"symptoms","version":0,"data":{"date":"2026-11-02","title":"Wellbeing entry","severity":"Mild","notes":"Symptoms and context"}}
```

Nutrition & lifestyle:

```json
{"section":"nutrition","version":0,"data":{"date":"2026-11-02","title":"Meal diary","category":"Meals","notes":"Meals recorded today"}}
```

Screening & preventive:

```json
{"section":"screening","version":0,"data":{"date":"2026-11-02","title":"Screening reminder","category":"Other screening","status":"Planned","next":"2026-12-01","notes":"Follow clinician guidance"}}
```

Doctor consultation (visit diary; this does not book an appointment):

```json
{"section":"consultation","version":0,"data":{"date":"2026-11-02","title":"Consultation notes","doctor":"Dr Example","status":"Planned","notes":"Questions and visit notes"}}
```

Successful save response (`200 OK`):

```json
{"record":{"id":"<record UUID>","section":"nutrition","version":"1","date":"2026-11-02","title":"Meal diary","category":"Meals","notes":"Meals recorded today"}}
```

Edit using the same PUT with `version: 1` and changed fields. The returned version
becomes `"2"`. Delete with `DELETE /women/profiles/{profile_id}/diary/{record_id}?version=2`.
Delete returns `200` with `{"message":"Diary entry deleted"}`.

## Profiles, medical reports and doctor connection

| Method | Path | Use |
|---|---|---|
| GET | `/patients/profiles?module=women` | Owner's Women profile list |
| GET | `/patients/profiles/{profile_id}` | Profile identity and connected doctor |
| GET/POST | `/patients/profiles/{profile_id}/reports` | Owner lists/uploads reports |
| GET | `/patients/profiles/{profile_id}/reports/{report_id}/download` | Owner's authenticated download |
| GET/POST | `/women/profiles/{profile_id}/reports` | Permission-checked shared report list/upload |
| GET | `/women/profiles/{profile_id}/reports/{report_id}/download` | Permission-checked shared download |
| DELETE | `/women/profiles/{profile_id}/reports/{report_id}` | Delete report with `records:edit` |
| POST | `/patients/profiles/{profile_id}/connect-doctor` | Owner connects doctor using `{"referral_id":"<doctor referral ID>"}` |
| DELETE | `/patients/profiles/{profile_id}/doctor` | Owner disconnects doctor and revokes their Women grant |
| GET/PUT | `/women/profiles/{profile_id}/sharing` | List recipients / save tab permissions |
| DELETE | `/women/profiles/{profile_id}/sharing/{grant_id}` | Revoke grant |
| GET | `/women/shared` | Recipient's active shared Women profiles |

Reports accept PDF/JPG/PNG/WebP, up to 10 MB per file; send multipart field `file`.
Upload returns `201` with `{"report":{"id":"...","name":"report.pdf", ...}}`.
Listing returns `200` with `{"items":[...]}`. The shared download returns file bytes.
Owner legacy downloads can return file bytes or a short-lived authenticated storage
URL. Report OCR/extraction is a separate existing workflow, not a diary prediction.

Grant PUT example (`200` response contains `grant`):

```json
{"recipient_id":"<accepted family member or connected doctor UUID>","permissions":{"cycle":"view","pregnancy":"edit","records":"view"},"expires_at":null}
```

`null` means No expiry until revoked/disconnected. For timed access send a future
timezone-aware timestamp, e.g. `"2026-12-01T12:00:00+05:30"`.

## Status and current limits

`200` read/save/delete; `201` report upload; `401` unauthenticated; `403` missing
view/edit permission or expired/revoked access; `404` resource missing; `409` stale
record version; `422` invalid fields; `413` oversized upload; `502/503` storage unavailable.

Cycle day, average interval and next-period estimate use saved period dates.
Cycle phase remains **Not assessed**; there is no backend diagnosis or fertility prediction.
Consultation diary saves notes and doctor connection/sharing; it does not book appointments.

See [Women tab access](WOMEN_TAB_ACCESS.md) for migration state and detailed sharing rules.
