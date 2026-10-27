# Child Healthcare and Vaccination API Guide

Prepared on 27 October 2026. All examples and interface field descriptions are in English.

**Implementation status:** Section 1 describes routes already registered in this repository. Sections 2–9 specify proposed additions from the supplied requirements; those routes are not implemented or deployed by this document. Existing APIs are unchanged. Proposed JSON is a contract example, not a response obtained from the running server.

Base URL: `http://127.0.0.1:5001`

## 1. Existing APIs you can use now

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/patients/register` | Start parent/patient registration and email verification |
| POST | `/api/v1/patients/verify-email` | Verify registration OTP and create the account |
| POST | `/api/v1/patients/login` | Email/password login; no login OTP |
| GET | `/api/v1/patients/me` | Read the authenticated parent account |
| POST | `/api/v1/patients/profiles` | Create a self/member care profile; use `module: "child"` for a child |
| GET | `/api/v1/patients/profiles?module=child` | List this parent's child profiles |
| GET | `/api/v1/patients/profiles/{profile_id}` | Read a selected child's profile |
| POST | `/api/v1/patients/profiles/{profile_id}/connect-doctor` | Connect this specific child to a doctor referral |
| POST | `/api/v1/patients/profiles/{profile_id}/reports` | Upload one medical report |
| GET | `/api/v1/patients/profiles/{profile_id}/reports` | List the child's reports |
| GET | `/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download` | Authorized report download/access |

Login and registration are public; profile/report routes require an authenticated PATIENT account. Use `Authorization: Bearer <access_token>` in Insomnia. GET requests have no body. List endpoints accept `page` and `per_page`; use the actual response pagination fields.

### Parent login

```http
POST /api/v1/patients/login
Content-Type: application/json
```

```json
{
  "email": "parent@example.com",
  "password": "YourExistingPassword"
}
```

Copy `access_token` from the successful response into Insomnia's enabled Bearer Token field. Do not use the refresh token as the Bearer token. Web clients continue using the existing cookie/CSRF transport.

### Register a child using the existing profile API

```http
POST /api/v1/patients/profiles
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "profile_type": "member",
  "module": "child",
  "full_name": "Aarav Kumar",
  "date_of_birth": "2022-03-01",
  "guardian_contact": "+919876543210",
  "emergency_contacts": [
    {
      "name": "Example Guardian",
      "mobile_number": "+919876543210",
      "relationship": "Father"
    }
  ]
}
```

Optional existing fields: `parent_profile_id` and `referral_id`. Omit them if not applicable. A parent profile must be an older adult/women profile owned by the same authenticated account. The account owner is derived from authentication, not a client-supplied owner ID.

The response has a `profile` object with UUID `id` and `public_id` such as `CH000001`. Existing child-profile and report URLs accept either identifier. The patient's account UUID and public ID such as `C000004` are not child profile IDs. See [care-profile public IDs](PROFILE_PUBLIC_IDS.md) for child/adult/women prefixes.

Current profile data includes `id`, `public_id`, `profile_type`, `module`, `full_name`, `date_of_birth`, `parent_profile_id`, `guardian_contact`, `emergency_contacts`, `doctor` and `created_at`. It does not currently return calculated age or vaccinations. Country/state/district, birth details and measurements are not accepted by the current create schema; those require the proposed extension below.

### Reports and doctor connection

Connect-doctor JSON:

```json
{"referral_id":"rahulkumarD000001"}
```

Use a real referral returned by the doctor API; the value above is illustrative.

Report upload uses `multipart/form-data` with exactly one field named `file`. Supported types: PDF, JPEG, PNG and WebP; maximum file size: 10 MB. Let Insomnia set the multipart boundary. Cloudinary must be configured. Cloudinary report responses include report ID, filename, folder, public ID and a short-lived access URL. Use the protected download endpoint for renewed access. Do not make children's medical reports publicly accessible.

## 2. Proposed child registration data

Reuse the existing care-profile identity and ownership checks. A future `/children` namespace should address the same child profile UUID, rather than creating an unrelated second identity.

```json
{
  "full_name": "Aarav Kumar",
  "date_of_birth": "2022-03-01",
  "country": "IN",
  "state": "Maharashtra",
  "district": "Pune",
  "sex": "male",
  "birth_weight_kg": 3.1,
  "birth_hospital": "Example Hospital",
  "premature_birth": false,
  "gestational_age_weeks": 39,
  "blood_group": null,
  "medical_conditions": [],
  "vaccination_history_status": "UNKNOWN",
  "parent_profile_id": null,
  "guardian_contact": "+919876543210"
}
```

Required new child data: name, valid DOB, country, state and district. Authenticated parent ownership is required and derived by the server. Sex and birth/medical details are optional or nullable. Store current weight/height as dated growth measurements, not undated profile attributes. Validate units, plausible input ranges, string lengths and future dates; avoid converting unknown medical facts into false/zero values.

For existing child profiles without location, retain their records and return an explicit missing-location/review state until completed. Do not guess clinical regional eligibility from the user's IP.

## 3. Complete proposed API list — not live yet

All paths below are relative to the base URL. `{child_id}` is the child's care-profile UUID. Parent routes must enforce child ownership on every request. Clinical data is not public.

### Child and dashboard

| Method | Proposed path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/children` | Create a child using the extended child schema |
| GET | `/api/v1/children` | List authenticated parent's children |
| GET | `/api/v1/children/{child_id}` | Child identity, DOB, location and demographic details |
| PUT | `/api/v1/children/{child_id}` | Update child details; recalculate derived age and routine windows |
| GET | `/api/v1/children/{child_id}/age` | Calendar-aware age, scope and primary/secondary categories |
| GET | `/api/v1/children/{child_id}/dashboard?schedule_type=UIP` | Consolidated dashboard for the selected child |
| GET | `/api/v1/children/{child_id}/health-guide` | Published, medically reviewed guidance for the current category |

### Vaccination

| Method | Proposed path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/vaccines` | Traceable vaccine catalog, without personalized administration advice |
| GET | `/api/v1/vaccination-schedules?schedule_type=UIP&country=IN` | Available approved schedule versions |
| GET | `/api/v1/children/{child_id}/vaccinations?schedule_type=UIP` | Routine timeline, history and review requirements |
| GET | `/api/v1/children/{child_id}/vaccinations/upcoming?schedule_type=UIP` | Future approved routine windows; no inferred catch-up prescriptions |
| GET | `/api/v1/children/{child_id}/vaccinations/history` | Actual reported/verified administration records |
| POST | `/api/v1/children/{child_id}/vaccinations/history` | Add a reported vaccination record |
| PATCH | `/api/v1/children/{child_id}/vaccinations/history/{record_id}` | Correct a record with an audit trail |
| GET | `/api/v1/children/{child_id}/reminders` | In-app reminder list and delivery status |
| PUT | `/api/v1/children/{child_id}/reminder-preferences` | Opt-in channels and reminder offsets |

Change `schedule_type` to `IAP` to request the separately versioned IAP schedule. Include a `schedule_version_id` when reproducing a previously displayed timeline. Never silently mix UIP and IAP doses.

### Other modules shown in the supplied dashboard image

These are additional proposed APIs; the existing report routes in Section 1 remain the report APIs.

| Method | Proposed path | Purpose |
| --- | --- | --- |
| GET, POST | `/api/v1/children/{child_id}/growth` | List/add dated height and weight measurements |
| PATCH | `/api/v1/children/{child_id}/growth/{measurement_id}` | Correct a measurement with an audit trail |
| GET, POST | `/api/v1/children/{child_id}/medical-history` | List/add allergies, conditions, procedures or visits |
| PATCH | `/api/v1/children/{child_id}/medical-history/{entry_id}` | Correct medical-history data |
| GET | `/api/v1/children/{child_id}/consultations` | Authorized consultation records, if consultation functionality is implemented |
| POST | `/api/v1/children/{child_id}/consultation-requests` | Request a consultation with the child's connected doctor |
| GET, POST | `/api/v1/children/{child_id}/care-notes` | Private parent care diary entries |
| PATCH, DELETE | `/api/v1/children/{child_id}/care-notes/{note_id}` | Edit/delete a private note under the retention policy |

Do not claim that locally saved diary entries already synchronize to the backend. Separate appointment requests from accepted/scheduled consultations. A doctor connected to the parent account is not automatically authorized for every child; retain explicit child-level access rules.

### Administrative and medical-review workflow

| Method | Proposed path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/admin/vaccination-schedules` | Import/create a draft source-traceable schedule version |
| PATCH | `/api/v1/admin/vaccination-schedules/{schedule_id}` | Edit a draft only |
| POST | `/api/v1/admin/vaccination-schedules/{schedule_id}/approve` | Publish after qualified medical review evidence is verified |
| GET | `/api/v1/admin/vaccination-schedules/audit-logs` | List import/edit/review/publication events |
| POST | `/api/v1/admin/child-health-guides` | Create a source-linked draft guide |
| PATCH | `/api/v1/admin/child-health-guides/{guide_id}` | Edit a draft guide |
| POST | `/api/v1/admin/child-health-guides/{guide_id}/approve` | Publish a medically reviewed guide |

Administrative authorization alone is not evidence of clinical qualification. Store the medical reviewer, review date and source/version references. Published versions must be immutable; corrections create a new version. Do not mark imported data approved automatically.

## 4. Proposed dashboard response

Example as of **2026-10-27**, for DOB **2022-03-01**. No vaccine history or approved clinical content is assumed. Null counts mean unknown/not assessed, not zero doses received.

```json
{
  "as_of_date": "2026-10-27",
  "child": {
    "id": "00000000-0000-4000-8000-000000000001",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2022-03-01",
    "country": "IN",
    "state": "Maharashtra",
    "district": "Pune",
    "age": {
      "completed_years": 4,
      "remaining_months": 7,
      "remaining_days": 26,
      "total_completed_months": 55,
      "total_days": 1701,
      "display": "4 years 7 months 26 days",
      "primary_category": "PRESCHOOLER",
      "secondary_categories": [],
      "in_child_module_scope": true
    }
  },
  "vaccination": {
    "schedule_type": "UIP",
    "schedule_version_id": null,
    "history_status": "UNKNOWN",
    "status": "REVIEW_REQUIRED",
    "completed_count": null,
    "upcoming_count": null,
    "potentially_overdue_count": null,
    "next_window": null,
    "history": [],
    "upcoming": [],
    "potentially_overdue": [],
    "review_reasons": [
      "VACCINATION_HISTORY_UNKNOWN",
      "NO_APPROVED_SCHEDULE_SELECTED"
    ]
  },
  "health_guide": {
    "category": "PRESCHOOLER",
    "available": false,
    "medical_review_status": "NOT_PUBLISHED",
    "sections": []
  },
  "growth": {
    "latest_measurement": null,
    "height_cm": null,
    "weight_kg": null,
    "bmi": null,
    "interpretation_status": "NOT_ASSESSED",
    "series": []
  },
  "medical_history": {"recorded_count": 0},
  "consultations": {"next_appointment": null},
  "care_notes": {"recorded_count": 0},
  "reports": {"recorded_count": 0},
  "reminders": []
}
```

The example UUID is a placeholder, not an existing child. Medical-history/report/note counts describe stored app records, not proof that a child has no conditions or previous care.

Frontend integration: list the parent's children; store selected child UUID; request that child's dashboard; cancel or ignore stale responses when switching children. Cache by child UUID, schedule version and effective date. Display missing measurements as **Not recorded**. Do not hardcode child-specific vaccine results or reuse another child's dashboard response.

## 5. Proposed record payloads

### Vaccination history

```json
{
  "vaccine_id": "00000000-0000-4000-8000-000000000002",
  "schedule_dose_id": null,
  "dose_number": 1,
  "actual_vaccination_date": "2022-03-01",
  "hospital_name": "Example Hospital",
  "vaccine_batch_number": null,
  "report_id": null,
  "remarks": "Entered from a paper vaccination card"
}
```

Use real catalog/report UUIDs. The server assigns `REPORTED`; parents cannot assign `VERIFIED`. Retain reported doses without a known schedule mapping and send ambiguous product/dose equivalence for clinical review. Reject future administration dates and dates before birth. Link records to the same child and retain correction history.

### Growth measurement

```json
{
  "measured_on": "2026-10-27",
  "height_cm": 105.2,
  "weight_kg": 17.4,
  "measurement_position": "standing",
  "remarks": "Measured at a clinic"
}
```

These are illustrative measurements, not normal-range advice. Calculate BMI only when valid height and weight are available. Do not apply adult BMI cutoffs to children. Growth interpretation requires the relevant validated pediatric reference, required demographic/measurement inputs and clinical review; otherwise return raw measurements without a diagnosis.

### Reminder preferences

```json
{
  "in_app": true,
  "email": false,
  "sms": false,
  "whatsapp": false,
  "days_before_window": [30, 7, 1],
  "timezone": "Asia/Kolkata"
}
```

Email/SMS/WhatsApp require configured delivery providers and opt-in. A saved preference does not imply delivery support. Use an idempotent scheduled worker; cancel/re-evaluate unsent reminders after an administered dose, DOB correction or schedule update. Never generate automatic catch-up reminders from an unvalidated rule.

## 6. Schedule data and clinical review

| Source checked | Verified form | Intended use |
| --- | --- | --- |
| [IAP-ACVIP 2025 recommendations, published in 2026](https://www.indianpediatrics.net/may2026/311.pdf) | Journal PDF; Table 2 contains the routine timetable | Separate IAP schedule import, with full footnotes and medical review |
| [WHO India vaccination schedule](https://immunizationdata.who.int/global/wiise-detail-page/vaccination-schedule-for-country_name?ISO_3_CODE=IND) | Country schedule reference portal based on WHO/UNICEF reporting | Cross-check the reported national schedule; it does not establish an individual child's vaccination history |
| [MoHFW Annual Report 2025–26](https://notto.mohfw.gov.in/WriteReadData/Portal/News/951_1_Annual_Report_of_the_MoH_FW__2025_-_2026.pdf) | Official publication with a National Immunization Schedule section | Versioned UIP source, subject to checking subsequent official updates before publication |

No documented personalized DOB-to-vaccination-plan API was verified from the supplied sources. Do not treat a PDF URL or WHO display page as a JSON endpoint. The additional MoHFW `Unit2NationalImmunizationSchedule.pdf` link found during checking returned 404 and is not a validated import source here.

Import authoritative tables into separate versioned UIP/IAP datasets. Retain source URL/title, publication and retrieval dates, document hash, source page/table/footnotes, effective dates, reviewer and approval status. Handle formulation alternatives, dose equivalence, regional applicability and special indications explicitly. A clinician must review the imported rules before they become actionable parent recommendations.

Suggested PostgreSQL entities: existing `care_profiles` plus a child-details extension; `vaccines`; `vaccination_schedule_versions`; `vaccination_schedule_doses`; `child_vaccination_records`; `vaccination_reminders`; `child_health_guides`; and separate growth/history/notes/consultation entities. Use profile foreign keys and additive migrations. Keep historical records and published schedule provenance; do not overwrite existing production data.

## 7. Schedule-engine rules

1. Calculate routine date windows from actual DOB. Use seven-day weeks and calendar-month/year arithmetic; define month-end and leap-day clamping consistently.
2. Select one approved, applicable schedule version. Region-dependent doses require verified location/eligibility, not IP inference.
3. Recorded administration is the only evidence of completion. Unknown history stays unknown; lack of an app record is not proof of no vaccination.
4. Proposed item states: `RECORDED`, `UPCOMING`, `DUE_WINDOW`, `POTENTIALLY_OVERDUE`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`. Distinguish parent-reported from clinician-verified administration.
5. A past routine window does not authorize administration now. Catch-up timing, previous-dose intervals, contraindications, combination products, prematurity, immune conditions and uncertain history require validated clinical rules or `REVIEW_REQUIRED`.
6. Display source, version, review status and relevant eligibility conditions with each recommendation. Do not fill empty timeline ages with invented vaccine entries.
7. Recalculate derived age/windows after DOB changes. Flag records that become inconsistent; do not silently delete them. Preserve history when the child leaves the module's age scope.

Clinical guidance sections requested by the product are feeding/nutrition, sleep, hygiene, milestones, safety, warning signs and doctor visits. Store and serve reviewed, source-linked content by category. This document does not invent clinical guidance or claim medical approval.

## 8. Access, errors and implementation checks

- The owner account comes from authentication. Every child and nested record request must check ownership and matching child ID. A different parent's child should not be discoverable.
- Permit connected doctors only through explicitly authorized doctor routes. Do not grant all administrative staff access to clinical files merely because they manage account approvals.
- Validate DOB, units, timestamps, referenced IDs, record status changes and source versions. Use existing rate limiting and web CSRF protection.
- Proposed clinical responses must distinguish unavailable/unreviewed data from no data. Use 401 for unauthenticated access, 404 for unavailable/not-owned resources, 422 for invalid input, and 409 for conflicting updates. These are proposed child-module contracts, not changes to existing routes.
- Required tests include exact category boundaries, leap years, month ends, future DOB, DOB edits, unknown history, window calculations, schedule-version selection, completed records, regional applicability, review gating, child switching, cross-parent access, reminder idempotency and suppression after an administered dose.

## 9. Age groups — exact product boundaries

These are the supplied product categories, not a claim that one universal clinical classification uses all of these boundaries. Use the detailed 0–12-year specification to resolve overlaps and the gap in the shorter informal list.

| Primary category | Exact calendar-age range | Secondary categories |
| --- | --- | --- |
| `NEWBORN` | Birth to less than 1 month | `INFANT` |
| `INFANT` | 1 month to less than 12 months | None |
| `TODDLER` | 12 months to less than 36 months | None |
| `PRESCHOOLER` | 36 months to less than 72 months | None |
| `SCHOOL_AGE` | 72 months to less than 120 months | None |
| `PRETEEN` | 120 months to less than 156 months | `SCHOOL_AGE` |

At exactly 13 years/156 completed months, return `in_child_module_scope: false` with an out-of-scope category, while retaining access to historical records. Five-year-olds remain preschoolers; ages 10–12 have primary category PRETEEN and secondary SCHOOL_AGE. Age is calculated on the server for the effective local date and is never permanently stored as an age counter.
