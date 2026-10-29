# Child Vaccination API — Frontend Integration

Updated: 28 October 2026. Backend: `http://127.0.0.1:5001/api/v1`.
Frontend page: `http://127.0.0.1:5173/customer/child/vaccination` (also 5174).

## 1. Find the selected child

`GET /children?page=1&per_page=100`

Requires PATIENT login. Use `items[].id`, the **child care-profile UUID**, not the parent account ID, name or public ID. For an already selected profile, use `profile.id` from the existing customer profile selector. This endpoint lists only the signed-in patient's children.

## 2. Get the child's vaccine list

```http
GET /api/v1/children/{child_profile_id}/vaccinations?schedule_type=UIP&view=current
```

### Parameters

| Parameter | Values | Default |
| --- | --- | --- |
| `schedule_type` | `UIP`, `IAP` (separate programmes) | `UIP` |
| `view` | `current`, `upcoming`, `completed`, `overdue`, `review_required`, `not_applicable`, `all` | `all` |
| `schedule_version_id` | Optional exact published schedule-version UUID | Current effective versions |

### What each view means

| View | Behaviour |
| --- | --- |
| `current` | Today's date is inside the child's DOB-based routine age window; excludes completed and not-applicable doses. Unknown history/eligibility can still require review. |
| `upcoming` | Routine window starts in the future; excludes completed/not-applicable doses. |
| `overdue` | Routine window has passed; excludes completed/not-applicable doses. May include review-required records; use `status` to label accurately. |
| `completed` | A matching dose has a parent-reported completed record. |
| `review_required` | Missing eligibility/history, required individual assessment or unresolved dose interval. Can overlap age-based views. |
| `not_applicable` | Outside the published location/gender rule or rule inactive. |
| `all` | All currently effective published doses, including future ages and not-applicable entries. |

Only doses created in the administrative schedule workflow, approved by an assigned qualified doctor, and then **published** appear. Catalog-only vaccines, drafts and approved-but-unpublished doses are excluded. An empty list must not be replaced with a hardcoded vaccine schedule. The five catalog entries already added do not by themselves create published dose schedules.

### Example response (synthetic data, not a medical schedule)

```json
{
  "status": "AVAILABLE",
  "schedule_type": "UIP",
  "view": "current",
  "as_of_date": "2026-10-28",
  "child": {
    "id": "11111111-1111-4111-8111-111111111111",
    "name": "Example child",
    "date_of_birth": "2026-10-28",
    "age": {
      "completed_years": 0,
      "remaining_months": 0,
      "remaining_days": 0,
      "total_completed_months": 0,
      "total_days": 0,
      "display": "0 years 0 months 0 days",
      "primary_category": "NEWBORN",
      "secondary_categories": [],
      "in_child_module_scope": true
    }
  },
  "total": 1,
  "total_published": 2,
  "counts": {
    "COMPLETED": 0,
    "UPCOMING": 1,
    "DUE": 1,
    "OVERDUE": 0,
    "NOT_APPLICABLE": 0,
    "REVIEW_REQUIRED": 0
  },
  "view_counts": {
    "all": 2,
    "current": 1,
    "upcoming": 1,
    "overdue": 0,
    "completed": 0,
    "review_required": 0,
    "not_applicable": 0
  },
  "context": {
    "country": "IN",
    "gender": "Unknown",
    "history_status": "PARENT_REPORTED",
    "email_reminders": false
  },
  "message": "Routine dates use published, medically reviewed versions. History is parent-reported. This is not a catch-up prescription.",
  "items": [{
    "id": "22222222-2222-4222-8222-222222222222",
    "vaccine_id": "33333333-3333-4333-8333-333333333333",
    "vaccine": {
      "id": "33333333-3333-4333-8333-333333333333",
      "code": "EXAMPLE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Synthetic example only",
      "description_en": "Synthetic example only",
      "description_hi": "",
      "active": true
    },
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "schedule_type": "UIP",
    "age_label": "Example age window",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 1,
    "age_relation": "CURRENT",
    "views": ["all", "current"],
    "recommended_date": "2026-10-28",
    "window_end": "2026-10-29",
    "completed_date": null,
    "status": "DUE",
    "reasons": [],
    "route": "Other",
    "injection_site": "",
    "instructions": "Synthetic example only",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic example",
    "medical_review": {
      "name": "Example reviewer",
      "qualification": "Example qualification",
      "registration": "EXAMPLE",
      "council": "Example council",
      "notes": "Synthetic example review notes only",
      "reviewed_at": "2026-10-28T00:00:00Z"
    },
    "reminders": {
      "before_days": [7], "on_due": true, "overdue_days": [7],
      "language": "en", "in_app": true, "email": false, "enabled": true
    }
  }]
}
```

`total` counts the selected view. `total_published`, `counts` and `view_counts` describe the whole published timeline, not just the selected view. Views overlap; do not add their counts. `status: AVAILABLE` means published content exists, even when the selected view has zero items. `NOT_AVAILABLE` means no effective published doses exist for that programme. An empty view does not prove a child has no medically due vaccinations.

## 3. Frontend request

Use the existing helper (handles cookie authentication, token refresh and errors):

```ts
import {careApi} from './lib/careApi'; // adjust relative import

const result = await careApi(
  `/children/${childProfileId}/vaccinations?schedule_type=UIP&view=current`
);
```

Alternatively, from a frontend with the `/api` proxy:

```js
const response = await fetch(
  `/api/v1/children/${childProfileId}/vaccinations?schedule_type=UIP&view=current`,
  {
    credentials: 'include',
    headers: {
      'X-Auth-Transport': 'cookie',
      'X-Requested-With': 'FamilyCare'
    }
  }
);
const data = await response.json();
if (!response.ok) throw new Error(data.error?.message || 'Could not load vaccinations');
```
For API clients using existing login-issued Bearer tokens:
```sh
curl 'http://127.0.0.1:5001/api/v1/children/CHILD_PROFILE_UUID/vaccinations?schedule_type=UIP&view=current' \
  -H 'Authorization: Bearer PATIENT_ACCESS_TOKEN'
```

For one fetch with instant tabs, request `view=all`, render `items.filter(item => item.views.includes(activeView))`, and use `view_counts` for badge counts. The updated customer page uses this approach. Do not calculate age or routine dates again in the browser.

## 4. Status labels

| API status | Customer label |
| --- | --- |
| `DUE` | Due now |
| `UPCOMING` | Upcoming |
| `OVERDUE` | Overdue |
| `COMPLETED` | Completed — parent-reported |
| `REVIEW_REQUIRED` | Review required; show `reasons` |
| `NOT_APPLICABLE` | Not applicable; show `reasons` |

`age_relation` is `CURRENT`, `UPCOMING` or `PAST`; it describes timing, not clinical eligibility. A future dose can have `REVIEW_REQUIRED`. Birth dates and calendar month/year windows use the backend's India date. Completed status does not verify eligibility or establish clinical certification. Routine windows are never shifted into catch-up prescriptions.

## 5. Eligibility / reminder preferences

```http
GET /api/v1/children/{child_profile_id}/vaccination-context
PUT /api/v1/children/{child_profile_id}/vaccination-context
```

PUT body:

```json
{
  "country": "IN",
  "state": "Uttar Pradesh",
  "district": "Gautam Buddha Nagar",
  "gender": "Boys",
  "history_status": "PARENT_REPORTED",
  "email_reminders": false
}
```

Gender: `Unknown`, `Girls`, `Boys`. History: `UNKNOWN` or `PARENT_REPORTED`; select parent-reported only after the parent confirms known history. Use the location names in the published rules; state abbreviations such as `UP` are not automatically expanded. Missing details can require review. Saving preferences does not create a medical approval.

## 6. Save a dose record

```http
POST /api/v1/children/{child_profile_id}/vaccinations/history
```

```json
{
  "title": "Example vaccine / Example dose",
  "date": "2026-10-28",
  "status": "Completed",
  "vaccine_id": "33333333-3333-4333-8333-333333333333",
  "schedule_id": "22222222-2222-4222-8222-222222222222",
  "provider": "Clinic name",
  "vaccinator": "Vaccinator name",
  "batch_number": "Batch number",
  "notes": "Parent-reported vaccination card entry"
}
```

Use the selected list item's `id` as `schedule_id`. API derives dose code/programme from that version. Success: HTTP 201, `{ "record": { ... } }`. Status values are case-sensitive: `Completed`, `Planned`, `Missed`. Completed dates cannot be future dates. Reload the list after saving. History supports existing PATCH/DELETE routes with record UUIDs. Legacy unlisted parent records remain history, but do not create published schedule entries.

Certificates: first upload multipart `file` to `POST /patients/profiles/{child_profile_id}/reports`, then include the returned `report.id` as `certificate_id` in the record. PDF/JPEG/PNG/WebP, maximum 10 MB. Download: `GET /patients/profiles/{child_profile_id}/reports/{certificate_id}/download`. Files remain private and must belong to the same child.

Cookie-authenticated writes require existing CSRF handling; use `careApi(path, body, true, 'PUT')` for context and `careApi(path, body)` for POST. Do not send admin/superadmin portal cookies or tokens from the customer UI.

## 7. Errors and empty states

| HTTP | Meaning |
| --- | --- |
| 401 | Patient login expired or absent |
| 403 | Wrong role or invalid cookie/CSRF write request |
| 404 | Child not found or not owned by the logged-in patient |
| 422 | Invalid programme, view, version or input fields |
| 503 | Database temporarily unavailable |

Errors use `{ "error": { "code": "...", "message": "..." } }`. Keep loading, error, no published doses and empty selected view states distinct. Never show sample vaccines as real patient recommendations.


## 8. Publication readiness (empty-list fix)

The child-list response also includes `publication`:

```json
{
  "publication": {
    "state": "SETUP_REQUIRED",
    "catalog_count": 5,
    "message": "Your care team has not published a vaccination plan yet. Vaccine names in the catalog do not set a child's dose or date."
  }
}
```

States: `SETUP_REQUIRED` (catalog only or no setup), `REVIEW_PENDING` (draft/review in progress), `PUBLICATION_PENDING` (approved and awaiting admin publication), `NO_EFFECTIVE_SCHEDULE` (published versions exist but none currently effective), `PUBLISHED` (effective published list available).

When `total_published` is zero, show the publication message and **hide dose-count tabs**. Do not describe zero counts as a completed or up-to-date vaccination status. Keep published content and parent-reported history separate. The existing child page now follows this rule and hides the dose-entry form until a published dose can be selected.

Admin catalog rows include **Add dose schedule**; catalog-only installations also show **Create first dose draft**. These open a draft with that vaccine selected, without inventing ages, medical sources or approval.

## 9. API quick list

All routes below are relative to `http://127.0.0.1:5001/api/v1`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/children` | Select owned child care-profile UUID |
| GET | `/children/{id}/age` | Backend-calculated child age |
| GET | `/children/{id}/vaccinations?schedule_type=UIP&view=current` | Current age-window dose list |
| GET | `/children/{id}/vaccinations?schedule_type=UIP&view=upcoming` | Future age-window doses |
| GET | `/children/{id}/vaccinations?schedule_type=UIP&view=completed` | Parent-reported completed published doses |
| GET | `/children/{id}/vaccinations?schedule_type=UIP&view=all` | All published doses and badge counts |
| GET, PUT | `/children/{id}/vaccination-context` | Eligibility and email preference |
| GET, POST | `/children/{id}/vaccinations/history` | Parent-reported dose records |
| PATCH, DELETE | `/children/{id}/vaccinations/history/{record_id}` | Correct/remove record |
| GET | `/children/{id}/reminders` | Child reminder list |
| GET | `/vaccines` | Public catalog snapshots from published doses |
| GET | `/vaccination-schedules?schedule_type=UIP` | Effective published schedule versions |
| GET, POST | `/{portal}/vaccination/vaccines` | Staff catalog (`portal`: admin/superadmin) |
| GET, POST | `/{portal}/vaccination/schedules` | Staff dose versions |
| PUT | `/{portal}/vaccination/schedules/{id}` | Edit draft |
| POST | `/{portal}/vaccination/schedules/{id}/submit-review` | Assign qualified reviewer |
| GET | `/doctors/vaccination-reviews` | Doctor's assigned draft reviews |
| POST | `/doctors/vaccination-reviews/{id}` | Approve/reject review |
| POST | `/{portal}/vaccination/schedules/{id}/publish` | Publish unchanged approved version |

The staff and doctor endpoints require their respective authenticated roles. Customer authentication cannot access them.
