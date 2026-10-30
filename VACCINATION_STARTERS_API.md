# Child vaccination schedules and reminders

Local portals: admin `http://127.0.0.1:3005/vaccination`, doctor `http://127.0.0.1:5175/doctor/vaccination`, customer `http://127.0.0.1:5174/customer/child/vaccination`. Backend base: `http://127.0.0.1:5001/api/v1`.

## Imported reference data

26 UIP doses and 18 IAP additional entries, version `familycare-0-12-2026-v1`. Imported as **DRAFT**, never automatically approved or published. The IAP list is the requested additional subset, not the entire IAP immunization programme. No routine UIP entry is created for ages 11–12. Annual influenza follow-ups and HPV product-specific multidose regimens require a doctor to prepare the appropriate schedule.

Sources linked in each draft: [MoHFW RISE national schedule and fIPV3 guidance](https://risemohfw.in/rise-guidelines), [IAP-ACVIP 2025 recommendations, published in 2026](https://www.indianpediatrics.net/may2026/311.pdf). Reference content and intervals must be checked by the medical reviewer before publication. JE is conditional on endemic district; IAP entries require individual clinical assessment to reconcile product, prior doses and UIP overlap. Historical doses are never fabricated.

One-time operator import (assigns draft ownership, does not attest on behalf of the owner):

```powershell
cd backend
venv/Scripts/python.exe scripts/import_vaccination_starters.py --admin-id <active-admin-uuid> --doctor-id <qualified-doctor-uuid>
```

Re-import skips the same scheme/vaccine/dose/version, including already published versions. The local import created all 44 drafts. Ownership is assigned to the administrator and qualified doctor passed to the import script. Other qualified doctors can view IAP drafts; only the owner can edit or submit them. Admins retain the existing schedule management controls. A Git push does not import data into another database; run the import there with that environment's account IDs.

## Authentication

All endpoints below require the corresponding authenticated role. Web uses existing role-scoped cookies, `X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare`, and `X-CSRF-Token` on writes. App clients use the existing bearer authentication flow (`Authorization: Bearer <access-token>`). Do not place tokens in URLs. JSON writes use `Content-Type: application/json`.

| Method and path | Role | Body / behavior |
| --- | --- | --- |
| POST `/admin/vaccination/import-uip` | ADMIN | `{}` imports UIP drafts |
| POST `/superadmin/vaccination/import-uip` | SUPERADMIN | `{}` imports UIP drafts |
| POST `/doctors/vaccination/import-iap` | qualified DOCTOR | `{}` imports IAP drafts |
| GET `/doctors/vaccination/schedules?page=1&per_page=100` | qualified DOCTOR | Paginated IAP drafts and versions |
| PUT `/doctors/vaccination/schedules/{schedule_id}` | qualified author DOCTOR | Full existing `ScheduleInput`; IAP and vaccine identity remain fixed |
| GET `/doctors/vaccination/reviewers` | DOCTOR | Available qualified independent reviewers |
| POST `/doctors/vaccination/schedules/{schedule_id}/submit-review` | qualified author DOCTOR | `{"reviewer_id":"<other-doctor-uuid>"}` |
| GET `/doctors/care-profiles/{child_id}/vaccination-plan` | connected qualified DOCTOR | Child header, published `UIP` and `IAP` timelines |
| POST `/doctors/care-profiles/{child_id}/vaccination-plan` | connected qualified DOCTOR | Child-specific applicability decision below |
| GET/PUT `/children/{child_id}/vaccination-context` | owner PATIENT | Country, state, district, gender, history and email consent |
| GET `/children/{child_id}/vaccinations?schedule_type=UIP&view=all` | owner PATIENT | Published doses, computed status, dates and reasons |
| GET `/children/{child_id}/reminders` | owner PATIENT | Eligible reminders for the current day |

Import returns HTTP 200, for example:

```json
{"created":26,"skipped":0,"schedule_type":"UIP","message":"Drafts saved. Independent medical review and admin publication are required."}
```

Existing publication flow remains: independent doctor reviews through `/doctors/vaccination-reviews/{schedule_id}` using substantive notes and attestation; admin publishes through `/admin/vaccination/schedules/{schedule_id}/publish`. A doctor cannot medically approve their own draft; changed content invalidates approval.

Child-specific decision request:

```json
{"schedule_id":"<published-schedule-uuid>","decision":"CONFIRM","notes":"At least 20 characters of actual clinical assessment.","attestation":true}
```

`decision` is `CONFIRM` or `NOT_APPLICABLE`. HTTP 200 returns a saved message. This records applicability, not administration or catch-up dates. Requires a currently connected child, confirmed country/history, state/district for JE and applicable sex/gender for HPV. Parent context changes, doctor reassignment, DOB changes or schedule changes invalidate the confirmation. History and minimum interval checks still apply.

Context PUT example (email is opt-in):

```json
{"country":"IN","state":"Delhi","district":"New Delhi","gender":"Girls","history_status":"PARENT_REPORTED","email_reminders":false}
```

Statuses retain backward-compatible machine values. New `display_status` is `Completed`, `Upcoming`, `Overdue`, `Doctor Review`, or `Not Applicable`; machine `DUE` displays Upcoming with `due_now: true`. Completed means a recorded parent-reported administration. Marking a row as read does not complete it.

## Reminders

Imported policies: in-app enabled, 7 and 1 days before, during the due window, and 1 and 7 days after the window. They exclude completed, not-applicable and review-required doses. Only published effective schedules participate. Stable schedule IDs identify reminders.

```json
{"id":"schedule-<uuid>","kind":"vaccination","title":"Vaccine · Dose 1","date":"2026-11-06","status":"UPCOMING","display_status":"Upcoming","days_until_due":7,"message":"टीके की तारीख 7 दिन में आने वाली है।","source":"PUBLISHED_SCHEDULE","delivery_status":"IN_APP","schedule_id":"<uuid>"}
```

The customer bell refreshes reminders every 60 seconds while visible and on returning to the tab. App clients can consume the same authenticated reminder endpoint. This change does **not** add a WebSocket or background mobile push transport. Email additionally requires the parent's explicit opt-in, an enabled published email policy and the existing mail worker; imported drafts default to email disabled. No email delivery is claimed by an in-app response.

Typical errors: 401 unauthenticated, 403 wrong role/draft owner, 404 child not connected, 409 draft immutable/unpublished decision, 422 invalid fields, missing history or medical qualification. JSON errors follow the existing `error.code`, `error.message`, `error.fields` shape.

## Verification

Backend tests cover imports, duplicate prevention, role boundaries, review/publication, context-scoped applicability, invalidation, due dates, notification suppression and email consent. Browser tests use intercepted synthetic data and make no live patient changes: `node app/scripts/check-vaccination-starters.mjs`.

## Complete app integration examples

UUIDs below are placeholders. Use IDs returned by authenticated list endpoints. All paths use the `/api/v1` base above. Login with the appropriate `/admin/login`, `/superadmin/login`, `/doctors/login` or `/patients/login` endpoint and the existing authentication flow. App requests can explicitly set `X-Auth-Transport: bearer` along with `Authorization: Bearer <access-token>`.

### Edit an IAP draft

`PUT /doctors/vaccination/schedules/{schedule_id}` requires a full replacement body, not a partial patch. Start with the current draft and retain all clinical rules unless intentionally changing them. Omit response-only properties such as `id`, `status`, `vaccine`, `created_by`, `reviewer_id`, `published_at` and `medical_review`.

```json
{
  "vaccine_id": "<catalog-vaccine-uuid>",
  "schedule_type": "IAP",
  "dose_code": "FLU1",
  "dose_name": "Dose 1",
  "version": "familycare-0-12-2026-v1",
  "age_label": "6 months",
  "age_unit": "months",
  "age_start": 6,
  "age_end": 6,
  "minimum_age": null,
  "maximum_age": null,
  "previous_dose_code": "",
  "minimum_interval_days": null,
  "route": "IM",
  "injection_site": "",
  "instructions": "Review prior doses and vaccine product before administration.",
  "source_url": "https://www.indianpediatrics.net/may2026/311.pdf",
  "source_reference": "IAP-ACVIP 2025 recommendations, Table 2",
  "effective_from": "2026-10-30",
  "effective_to": null,
  "eligibility": {
    "gender": "All", "country": "IN", "states": [], "districts": [],
    "programme": "IAP", "requires_clinical_review": true, "active": true
  },
  "reminders": {
    "before_days": [1, 7], "on_due": true, "overdue_days": [1, 7],
    "language": "hi", "in_app": true, "email": false, "enabled": true
  }
}
```

HTTP 200 returns `{"schedule": {...}}` containing the updated full schedule and `status: "DRAFT"`. Invalid age ranges, non-HTTPS sources, or an incomplete previous-dose/minimum-interval pair return 422. Editing a different author's draft or a UIP draft through this doctor endpoint returns 403; editing a non-draft returns 409.

`GET /doctors/vaccination/schedules?page=1&per_page=100` returns:

```json
{
  "items": [
    {
      "id": "<schedule-uuid>", "status": "DRAFT", "schedule_type": "IAP",
      "dose_code": "FLU1", "dose_name": "Dose 1", "version": "familycare-0-12-2026-v1",
      "created_by": "<author-uuid>", "reviewer_id": null, "published_at": null,
      "vaccine": {"id": "<vaccine-uuid>", "code": "FC_FLU", "name_en": "Influenza"}
    }
  ],
  "total": 18, "page": 1, "per_page": 100
}
```

This response example shows a subset of schedule fields; the API also returns the source, age, eligibility and reminder fields illustrated in the replacement body.

### Review and publish

1. Author sends `POST /doctors/vaccination/schedules/{id}/submit-review` with `{"reviewer_id":"<independent-doctor-uuid>"}`. HTTP 200 returns `{"schedule":{...}}` with `status: "IN_REVIEW"`.
2. Assigned reviewer loads `GET /doctors/vaccination-reviews?page=1&per_page=100`, returning the paginated `items/total/page/per_page` shape.
3. Reviewer submits `POST /doctors/vaccination-reviews/{id}`:

```json
{"decision":"APPROVE","notes":"Actual source and dose assessment, at least 20 characters.","attestation":true}
```

HTTP 200 returns `{"schedule":{...}}` with `status: "APPROVED"` and the recorded professional review. `REJECT` returns the schedule to `DRAFT`. This example is an API contract, not an instruction to approve without medical review.

4. Admin sends `POST /admin/vaccination/schedules/{id}/publish` with `{}`. HTTP 200 returns `{"schedule":{...}}` with `status: "PUBLISHED"`. Superadmin uses the equivalent `/superadmin/vaccination/...` route.

Admin also has GET/POST `/admin/vaccination/vaccines`, GET/POST `/admin/vaccination/schedules`, PUT `/admin/vaccination/schedules/{id}`, PUT `.../{id}/eligibility`, PUT `.../{id}/reminders`, GET `/admin/vaccination/reviewers`, POST `.../{id}/submit-review`, POST `.../{id}/withdraw`, POST `.../{id}/retire` (`{"reason":"At least 10 characters"}`), and GET `/admin/vaccination/audit`. Vaccine and schedule creation return 201; the other successful writes return 200. Equivalent superadmin routes preserve that role boundary.

### Read child statuses and notifications

`GET /children/{child_id}/vaccinations?schedule_type=IAP&view=all` returns a timeline including:

```json
{
  "schedule_type": "IAP",
  "total": 1,
  "total_published": 1,
  "items": [{
    "id": "<schedule-uuid>", "dose_name": "Dose 1", "schedule_type": "IAP",
    "recommended_date": "2026-11-06", "window_end": "2026-11-06",
    "status": "UPCOMING", "display_status": "Upcoming", "due_now": false,
    "reasons": [], "vaccine": {"name_en":"Influenza"}
  }],
  "publication": {"state":"PUBLISHED","message":"Published vaccination schedules are available."}
}
```

The full response also includes child age, context, counts and presentation metadata. `view` accepts `all`, `current`, `upcoming`, `completed`, `overdue`, `review_required`, `not_applicable`. Age-view filtering and the computed clinical status are separate: use each item's `status` for the status badge. An unpublished plan returns an empty list with `publication.state: "REVIEW_PENDING"` rather than exposing draft doses.

`GET /doctors/care-profiles/{child_id}/vaccination-plan` returns `{"child":{"id":"<child-uuid>","name":"Example child"},"UIP":{...},"IAP":{...}}`; both programme objects contain `items`, `counts`, `context`, `status` and `message` from their published timelines.

`GET /children/{child_id}/reminders` wraps reminders as `{"items":[...],"total":1,"preferences":{"in_app":true},"message":"..."}`. A disabled preference or no matching reminder day returns an empty list. PUT `/children/{child_id}/reminder-preferences` with `{"in_app":false}` disables the in-app list. This is separate from `email_reminders` consent.

Example app request (no credentials embedded):

```javascript
const response = await fetch(`${base}/api/v1/children/${childId}/reminders`, {
  headers: {Authorization: `Bearer ${accessToken}`, 'X-Auth-Transport': 'bearer'}
});
const data = await response.json();
if (!response.ok) throw new Error(data.error?.message || 'Could not load reminders');
renderReminders(data.items);
```

Representative error:

```json
{"error":{"code":"context_required","message":"Ask the parent to confirm location and vaccination history first"}}
```
