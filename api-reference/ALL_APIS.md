# FamilyCare: all API methods

Base URL: `http://127.0.0.1:5001`. All registered GET/POST/PUT/PATCH/DELETE methods are listed below. Examples use synthetic values, not patient data. Replace UUIDs, tokens and example fields. JSON Schema contains validation constraints; a sample is not a clinical recommendation.

## Login and portal integration

| UI | URL | Backend login |
| --- | --- | --- |
| Public frontend | http://127.0.0.1:5173 | Links to customer/doctor flows |
| Customer frontend | http://127.0.0.1:5174/customer/login | POST /api/v1/patients/login |
| Doctor frontend | http://127.0.0.1:5175/doctor/login | POST /api/v1/doctors/login |
| Admin | http://127.0.0.1:3005 | POST /api/v1/admin/login |
| Superadmin | http://127.0.0.1:3005/superadmin | POST /api/v1/superadmin/login |

Web uses role-scoped HttpOnly cookie sessions. Send `X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare`, credentials include and `X-CSRF-Token` for authenticated mutations. App clients use `X-Auth-Transport: bearer` and `Authorization: Bearer <access_token>`. Never mix transports. JSON requests use Content-Type application/json; file uploads use multipart/form-data without manually setting its boundary.
  
Doctor login can return 202 for profile setup/review instead of a clinical access session. Follow `requires_profile_setup`, `setup_token` and approval status. Setup tokens authorize setup only. Notification tokens authorize the doctor notification inbox only. Standard access tokens authorize role-protected clinical/profile APIs.

## UI coverage and method availability

- Doctor Settings: authenticated profile-photo upload/replace/remove; header and connected-family cards use the saved photo. Setup additionally supports private degree documents. Signed image URLs last five minutes; refresh the owning profile endpoint to renew them.
- Admin and superadmin: Doctors list links to `/doctors/{public_id}` within the portal. Full profile and paginated connected-family metadata load from separate API endpoints. Approval/suspension remains a deliberate role-bound action.
- Customer child diary: list/create/edit/delete for vaccination history, medical history, growth, nutrition, consultations, care notes and consultation requests. Single-record GETs support deep-link clients.
- Customer adult diary: list/create, single-record GET, PATCH update and DELETE. Existing POST update/delete aliases remain compatible. PATCH currently expects the complete editable record body.
- Connected doctor removal uses DELETE on the selected profile and immediately revokes that doctor's access to that profile.
- Child/adult Settings: edit profile name/contact via PUT /patients/profiles/{profile_id}; DOB, ownership, profile type and medical approval identity are not writable through this endpoint.
- Vaccine catalog/schedules use drafts, independent medical review and administrator publication. Clinical history and published versions do not get arbitrary account-wide delete methods.
- Methods absent from the matrix are not implemented. A list-only or approval resource does not gain POST/DELETE just because another resource supports CRUD. Women profiles use shared profile/report/referral APIs; there is no invented women diary endpoint.
- Customer and approved doctor portals connect to /ws/notifications using a short-lived POST /notifications/socket-ticket ticket in the first auth frame. REST polling resynchronizes the inbox. Closed-app mobile push requires a separate device-push service.

## Reading this single-file reference

Generated on 2026-10-31 13:03 IST. This file includes every versioned REST operation, request examples, response examples, validation schemas, upload limits and realtime integration. Examples are synthetic contracts, not captured production responses. An endpoint appearing here does not mean its external SMTP, storage or OCR provider has been tested live. Path placeholders must be replaced with accessible resource IDs. Response examples show representative shapes; optional values depend on the record and account state.

For cookie authentication, public portals also send `X-FamilyCare-Portal: patient` or `doctor` on every request, including login and refresh. This keeps the two sessions independent. Bearer clients omit this header.

## Upload sizes and file response data

| Data | Limit / format |
| --- | --- |
| Ordinary request body | 16,384 bytes (16 KiB), unless the upload route overrides it |
| Patient profile health report | 10 MiB (10,485,760 bytes); PDF, JPEG, PNG or WebP; multipart field `file` |
| Doctor setup / profile image | 5 MiB (5,242,880 bytes); JPEG, PNG or WebP; multipart field `file` |
| Report upload request overhead | Up to 65,536 extra bytes beyond the report limit for multipart framing |
| Image upload request overhead | Up to 65,536 extra bytes beyond the image limit for multipart framing |

Upload JSON responses return metadata and, when configured, a temporary signed URL; they do not embed the original file bytes or base64. Download endpoints can return binary content: check the response Content-Type and Content-Disposition rather than parsing every response as JSON. Signed URLs expire; request fresh metadata to renew access. See each upload operation for its additional form fields and authentication. MB labels in the UI use the binary limits above.

## Implemented workflows

- Patient: register -> signup email OTP -> verify -> login -> create self/member profile -> use child/adult records, reports, referral and notifications.
- Doctor: register -> signup OTP -> setup profile/images -> admin review -> approved clinical login -> connected profiles, records, vaccination review and notifications.
- Admin/superadmin: login -> review accounts -> manage vaccine catalogue, schedule drafts, independent medical review, publication and visibility.
- Every child can read active UIP/IAP plans without a doctor referral. Dates derive from that child's DOB. Unpublished entries remain Doctor Review; completion records and doctor applicability decisions remain child-specific. Switching children retains the selected page.
- Reports: upload -> request extraction -> poll job -> optionally request translation with explicit consent -> review extracted values before importing a diary record. OCR and translation are separate operations.
- Women profiles use the shared profile, referral and report APIs. Only the methods in the inventory are implemented.

## Report upload, reading and deletion

OCR results generate editable drafts for medical history, prescriptions, growth, vaccination and nutrition when matching text is found. With `auto_read=true`, successful reading automatically saves unreviewed entries. Without automatic reading, the reviewed import endpoint remains available. The report `/import` endpoint accepts `kind: prescription` as an owner-reviewed Medicine entry in medical history. A history entry and prescription entry from the same report are independently deduplicated and both removed when the source report is deleted. No medicine dose or diagnosis is inferred beyond the extracted text.

Select the report category before selecting a file. Multipart uploads accept `category` (Doctor report, Lab tests, Prescriptions, Scans, Vaccination, Others), `source_language` and `auto_read=true`. The child reports UI requests automatic reading. Successful text extraction automatically creates source-linked, unreviewed medical history plus matching medicine, growth, nutrition and vaccination observations. Vaccination mentions remain Review pending and do not confirm administration. Rereading is deduplicated and never overwrites an owner-reviewed record. `Scans` means X-ray / imaging and skips OCR. Other documents can request text extraction; poll the report `/text` endpoint for results. `source_language` selects the printed language, `target_language` selects the display language, and `translate: true` requires `external_translation_consent: true` when these differ. Existing `translate_to_english` requests remain supported.

`DELETE /api/v1/patients/profiles/{profile_id}/reports/{report_id}` requires the patient session and CSRF header for cookie clients. It removes the stored file, extracted text and diary records imported from that report. Independently added records remain. Returns HTTP 200 with a confirmation message; inaccessible reports return 404 and storage deletion failure returns 502 without removing the database report.

## Every registered resource and verb

| Path | GET | POST | PUT | PATCH | DELETE |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/admin/dashboard` | Yes | — | — | — | — |
| `/api/v1/admin/doctor-requests` | Yes | — | — | — | — |
| `/api/v1/admin/doctors` | Yes | — | — | — | — |
| `/api/v1/admin/doctors/{user_id}` | Yes | — | — | — | — |
| `/api/v1/admin/doctors/{user_id}/approve` | — | Yes | — | — | — |
| `/api/v1/admin/doctors/{user_id}/check` | — | Yes | — | — | — |
| `/api/v1/admin/doctors/{user_id}/profiles` | Yes | — | — | — | — |
| `/api/v1/admin/doctors/{user_id}/reactivate` | — | Yes | — | — | — |
| `/api/v1/admin/doctors/{user_id}/reject` | — | Yes | — | — | — |
| `/api/v1/admin/doctors/{user_id}/suspend` | — | Yes | — | — | — |
| `/api/v1/admin/login` | — | Yes | — | — | — |
| `/api/v1/admin/me` | Yes | — | — | — | — |
| `/api/v1/admin/patients` | Yes | — | — | — | — |
| `/api/v1/admin/patients/{user_id}` | Yes | — | — | — | — |
| `/api/v1/admin/patients/{user_id}/profiles` | Yes | — | — | — | — |
| `/api/v1/admin/patients/{user_id}/profiles/{profile_id}` | Yes | — | — | — | — |
| `/api/v1/admin/register` | — | Yes | — | — | — |
| `/api/v1/admin/resend-otp` | — | Yes | — | — | — |
| `/api/v1/admin/search` | Yes | — | — | — | — |
| `/api/v1/admin/vaccination/audit` | Yes | — | — | — | — |
| `/api/v1/admin/vaccination/import-uip` | — | Yes | — | — | — |
| `/api/v1/admin/vaccination/reviewers` | Yes | — | — | — | — |
| `/api/v1/admin/vaccination/schedules` | Yes | Yes | — | — | — |
| `/api/v1/admin/vaccination/schedules/{schedule_id}` | — | — | Yes | — | — |
| `/api/v1/admin/vaccination/schedules/{schedule_id}/eligibility` | — | — | Yes | — | — |
| `/api/v1/admin/vaccination/schedules/{schedule_id}/publish` | — | Yes | — | — | — |
| `/api/v1/admin/vaccination/schedules/{schedule_id}/reminders` | — | — | Yes | — | — |
| `/api/v1/admin/vaccination/schedules/{schedule_id}/retire` | — | Yes | — | — | — |
| `/api/v1/admin/vaccination/schedules/{schedule_id}/submit-review` | — | Yes | — | — | — |
| `/api/v1/admin/vaccination/schedules/{schedule_id}/visibility` | — | — | — | Yes | — |
| `/api/v1/admin/vaccination/schedules/{schedule_id}/withdraw` | — | Yes | — | — | — |
| `/api/v1/admin/vaccination/vaccines` | Yes | Yes | — | — | — |
| `/api/v1/admin/vaccination/vaccines/{vaccine_id}` | — | — | Yes | — | — |
| `/api/v1/admin/verify-email` | — | Yes | — | — | — |
| `/api/v1/admin/verify-login-otp` | — | Yes | — | — | — |
| `/api/v1/auth/change-password` | — | Yes | — | — | — |
| `/api/v1/auth/forgot-password` | — | Yes | — | — | — |
| `/api/v1/auth/initial-password` | — | Yes | — | — | — |
| `/api/v1/auth/logout` | — | Yes | — | — | — |
| `/api/v1/auth/logout-all` | — | Yes | — | — | — |
| `/api/v1/auth/refresh` | — | Yes | — | — | — |
| `/api/v1/auth/request-email-verification` | — | Yes | — | — | — |
| `/api/v1/auth/resend-otp` | — | Yes | — | — | — |
| `/api/v1/auth/reset-password` | — | Yes | — | — | — |
| `/api/v1/auth/sessions` | Yes | — | — | — | — |
| `/api/v1/auth/sessions/{session_id}` | — | — | — | — | Yes |
| `/api/v1/children` | Yes | — | — | — | — |
| `/api/v1/children/{child_id}` | Yes | — | — | — | — |
| `/api/v1/children/{child_id}/age` | Yes | — | — | — | — |
| `/api/v1/children/{child_id}/care-notes` | Yes | Yes | — | — | — |
| `/api/v1/children/{child_id}/care-notes/{record_id}` | Yes | — | — | Yes | Yes |
| `/api/v1/children/{child_id}/consultation-requests` | Yes | Yes | — | — | — |
| `/api/v1/children/{child_id}/consultation-requests/{record_id}` | Yes | — | — | Yes | Yes |
| `/api/v1/children/{child_id}/consultations` | Yes | Yes | — | — | — |
| `/api/v1/children/{child_id}/consultations/{record_id}` | Yes | — | — | Yes | Yes |
| `/api/v1/children/{child_id}/dashboard` | Yes | — | — | — | — |
| `/api/v1/children/{child_id}/growth` | Yes | Yes | — | — | — |
| `/api/v1/children/{child_id}/growth/{record_id}` | Yes | — | — | Yes | Yes |
| `/api/v1/children/{child_id}/health-guide` | Yes | — | — | — | — |
| `/api/v1/children/{child_id}/medical-history` | Yes | Yes | — | — | — |
| `/api/v1/children/{child_id}/medical-history/{record_id}` | Yes | — | — | Yes | Yes |
| `/api/v1/children/{child_id}/nutrition` | Yes | Yes | — | — | — |
| `/api/v1/children/{child_id}/nutrition/{record_id}` | Yes | — | — | Yes | Yes |
| `/api/v1/children/{child_id}/records` | Yes | — | — | — | — |
| `/api/v1/children/{child_id}/reminder-preferences` | — | — | Yes | — | — |
| `/api/v1/children/{child_id}/reminders` | Yes | — | — | — | — |
| `/api/v1/children/{child_id}/vaccination-context` | Yes | — | Yes | — | — |
| `/api/v1/children/{child_id}/vaccinations` | Yes | — | — | — | — |
| `/api/v1/children/{child_id}/vaccinations/history` | Yes | Yes | — | — | — |
| `/api/v1/children/{child_id}/vaccinations/history/{record_id}` | Yes | — | — | Yes | Yes |
| `/api/v1/children/{child_id}/vaccinations/upcoming` | Yes | — | — | — | — |
| `/api/v1/children/{profile_id}/growth-nutrition-guide` | Yes | — | — | — | — |
| `/api/v1/doctors/approval-status` | — | Yes | — | — | — |
| `/api/v1/doctors/care-profiles` | Yes | — | — | — | — |
| `/api/v1/doctors/care-profiles/{profile_id}` | Yes | — | — | — | — |
| `/api/v1/doctors/care-profiles/{profile_id}/child-records/{area}` | Yes | Yes | — | — | — |
| `/api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide` | Yes | — | — | — | — |
| `/api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide/visibility` | — | — | — | Yes | — |
| `/api/v1/doctors/care-profiles/{profile_id}/records` | Yes | — | — | — | — |
| `/api/v1/doctors/care-profiles/{profile_id}/reports` | Yes | — | — | — | — |
| `/api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download` | Yes | — | — | — | — |
| `/api/v1/doctors/care-profiles/{profile_id}/vaccination-plan` | Yes | Yes | — | — | — |
| `/api/v1/doctors/consultation-requests` | Yes | — | — | — | — |
| `/api/v1/doctors/login` | — | Yes | — | — | — |
| `/api/v1/doctors/me` | Yes | — | — | — | — |
| `/api/v1/doctors/notifications` | Yes | — | — | — | — |
| `/api/v1/doctors/notifications/push-config` | Yes | — | — | — | — |
| `/api/v1/doctors/notifications/subscriptions` | — | Yes | — | — | Yes |
| `/api/v1/doctors/notifications/{notification_id}/read` | — | Yes | — | — | — |
| `/api/v1/doctors/patients` | Yes | — | — | — | — |
| `/api/v1/doctors/profile-photo` | Yes | Yes | Yes | — | Yes |
| `/api/v1/doctors/referral` | Yes | — | — | — | — |
| `/api/v1/doctors/register` | — | Yes | — | — | — |
| `/api/v1/doctors/resend-otp` | — | Yes | — | — | — |
| `/api/v1/doctors/resubmit` | — | Yes | — | — | — |
| `/api/v1/doctors/setup-images` | — | Yes | — | — | — |
| `/api/v1/doctors/setup-profile` | — | Yes | — | — | — |
| `/api/v1/doctors/vaccination-reviews` | Yes | — | — | — | — |
| `/api/v1/doctors/vaccination-reviews/{schedule_id}` | — | Yes | — | — | — |
| `/api/v1/doctors/vaccination/import-iap` | — | Yes | — | — | — |
| `/api/v1/doctors/vaccination/reviewers` | Yes | — | — | — | — |
| `/api/v1/doctors/vaccination/schedules` | Yes | — | — | — | — |
| `/api/v1/doctors/vaccination/schedules/{schedule_id}` | — | — | Yes | — | — |
| `/api/v1/doctors/vaccination/schedules/{schedule_id}/submit-review` | — | Yes | — | — | — |
| `/api/v1/doctors/verify-email` | — | Yes | — | — | — |
| `/api/v1/family-invitations/{token}` | Yes | — | — | — | — |
| `/api/v1/family-invitations/{token}/resend-otp` | — | Yes | — | — | — |
| `/api/v1/family-invitations/{token}/setup` | — | Yes | — | — | — |
| `/api/v1/family-invitations/{token}/verify-otp` | — | Yes | — | — | — |
| `/api/v1/health` | Yes | — | — | — | — |
| `/api/v1/health/ready` | Yes | — | — | — | — |
| `/api/v1/notifications` | Yes | — | — | — | — |
| `/api/v1/notifications/read-all` | — | Yes | — | — | — |
| `/api/v1/notifications/socket-ticket` | — | Yes | — | — | — |
| `/api/v1/notifications/test` | — | Yes | — | — | — |
| `/api/v1/notifications/unread-count` | Yes | — | — | — | — |
| `/api/v1/notifications/{notification_id}/read` | — | Yes | — | — | — |
| `/api/v1/patients/adults/{profile_id}/records` | Yes | Yes | — | — | — |
| `/api/v1/patients/adults/{profile_id}/records/{record_id}` | Yes | Yes | — | Yes | Yes |
| `/api/v1/patients/adults/{profile_id}/records/{record_id}/delete` | — | Yes | — | — | — |
| `/api/v1/patients/connect-doctor` | — | Yes | — | — | — |
| `/api/v1/patients/doctor` | Yes | — | — | — | — |
| `/api/v1/patients/family-invitations` | Yes | Yes | — | — | — |
| `/api/v1/patients/family-invitations/{invite_id}` | — | — | — | — | Yes |
| `/api/v1/patients/login` | — | Yes | — | — | — |
| `/api/v1/patients/me` | Yes | — | — | — | — |
| `/api/v1/patients/profiles` | Yes | Yes | — | — | — |
| `/api/v1/patients/profiles/{profile_id}` | Yes | — | Yes | Yes | Yes |
| `/api/v1/patients/profiles/{profile_id}/connect-doctor` | — | Yes | — | — | — |
| `/api/v1/patients/profiles/{profile_id}/doctor` | — | — | — | — | Yes |
| `/api/v1/patients/profiles/{profile_id}/doctor-overview` | Yes | — | — | — | — |
| `/api/v1/patients/profiles/{profile_id}/imported-records` | Yes | — | — | — | — |
| `/api/v1/patients/profiles/{profile_id}/reports` | Yes | Yes | — | — | — |
| `/api/v1/patients/profiles/{profile_id}/reports/{report_id}` | — | — | — | — | Yes |
| `/api/v1/patients/profiles/{profile_id}/reports/{report_id}/category` | — | — | — | Yes | — |
| `/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download` | Yes | — | — | — | — |
| `/api/v1/patients/profiles/{profile_id}/reports/{report_id}/import` | — | Yes | — | — | — |
| `/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text` | Yes | Yes | — | — | — |
| `/api/v1/patients/register` | — | Yes | — | — | — |
| `/api/v1/patients/report-text/options` | Yes | — | — | — | — |
| `/api/v1/patients/resend-otp` | — | Yes | — | — | — |
| `/api/v1/patients/verify-email` | — | Yes | — | — | — |
| `/api/v1/patients/verify-login-otp` | — | Yes | — | — | — |
| `/api/v1/superadmin/admin-requests` | Yes | — | — | — | — |
| `/api/v1/superadmin/admins` | Yes | — | — | — | — |
| `/api/v1/superadmin/admins/{user_id}/approve` | — | Yes | — | — | — |
| `/api/v1/superadmin/admins/{user_id}/reactivate` | — | Yes | — | — | — |
| `/api/v1/superadmin/admins/{user_id}/reject` | — | Yes | — | — | — |
| `/api/v1/superadmin/admins/{user_id}/suspend` | — | Yes | — | — | — |
| `/api/v1/superadmin/audit-logs` | Yes | — | — | — | — |
| `/api/v1/superadmin/dashboard` | Yes | — | — | — | — |
| `/api/v1/superadmin/doctors` | Yes | — | — | — | — |
| `/api/v1/superadmin/doctors/{user_id}` | Yes | — | — | — | — |
| `/api/v1/superadmin/doctors/{user_id}/profiles` | Yes | — | — | — | — |
| `/api/v1/superadmin/login` | — | Yes | — | — | — |
| `/api/v1/superadmin/me` | Yes | — | — | — | — |
| `/api/v1/superadmin/patients` | Yes | — | — | — | — |
| `/api/v1/superadmin/patients/{user_id}` | Yes | — | — | — | — |
| `/api/v1/superadmin/patients/{user_id}/profiles` | Yes | — | — | — | — |
| `/api/v1/superadmin/patients/{user_id}/profiles/{profile_id}` | Yes | — | — | — | — |
| `/api/v1/superadmin/search` | Yes | — | — | — | — |
| `/api/v1/superadmin/vaccination/audit` | Yes | — | — | — | — |
| `/api/v1/superadmin/vaccination/import-uip` | — | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/reviewers` | Yes | — | — | — | — |
| `/api/v1/superadmin/vaccination/schedules` | Yes | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}` | — | — | Yes | — | — |
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}/eligibility` | — | — | Yes | — | — |
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}/publish` | — | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}/reminders` | — | — | Yes | — | — |
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}/retire` | — | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}/submit-review` | — | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}/visibility` | — | — | — | Yes | — |
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw` | — | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/vaccines` | Yes | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/vaccines/{vaccine_id}` | — | — | Yes | — | — |
| `/api/v1/vaccination-schedules` | Yes | — | — | — | — |
| `/api/v1/vaccination-schedules/{schedule_id}` | Yes | — | — | — | — |
| `/api/v1/vaccines` | Yes | — | — | — | — |

## GET /api/v1/admin/dashboard

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/dashboard`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Doctor/patient dashboard; pending requests contain doctors only.

```json
{
  "counts": [
    {
      "role": "PATIENT",
      "approval_status": "APPROVED",
      "count": 3
    }
  ],
  "as_of": "2026-10-31",
  "metrics": {
    "administrators": {
      "total": 0,
      "this_month": 0
    },
    "doctors": {
      "total": 4,
      "this_month": 1
    },
    "patients": {
      "total": 3,
      "this_month": 1
    },
    "children": {
      "total": 5,
      "this_month": 1
    }
  },
  "monthly_growth": [
    {
      "month": "2026-10",
      "patients": 3,
      "doctors": 4,
      "administrators": 2
    }
  ],
  "recent_registrations": [
    {
      "id": "<UUID>",
      "public_id": "C000001",
      "full_name": "Example Patient",
      "email": "patient@example.com",
      "role": "PATIENT",
      "approval_status": "APPROVED",
      "account_status": "ACTIVE",
      "created_at": "<UTC timestamp>"
    }
  ],
  "pending_requests": {
    "total": 0,
    "items": []
  },
  "recent_activities": [
    {
      "id": "<UUID>",
      "action": "registered",
      "person": "Example Patient",
      "created_at": "<UTC timestamp>"
    }
  ],
  "child_care": {
    "total_children": 5,
    "active_guides": 4,
    "inactive_guides": 1,
    "growth_records": 2,
    "nutrition_records": 3,
    "vaccination_records": 4
  },
  "approved_doctors": 3
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/doctor-requests

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctor-requests`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/doctors

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctors`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
| `search` | query | False | `{"type": "string", "maxLength": 80}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/doctors/{user_id}

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "user": {
    "id": "<UUID>",
    "public_id": "D000001",
    "full_name": "Example doctor",
    "role": "DOCTOR",
    "approval_status": "APPROVED",
    "doctor": {
      "qualification": "MBBS",
      "images": {}
    }
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/doctors/{user_id}/approve

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/approve`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "approval_status": "APPROVED"
  },
  "email_status": "queued"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/doctors/{user_id}/check

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/check`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "doctor_status": "pending",
  "cached": false,
  "verification_check": {
    "checked_at": "<UTC timestamp>",
    "requires_admin_review": true,
    "auto_approved": false,
    "registration": {
      "status": "manual_review"
    },
    "address": {
      "status": "manual_review"
    },
    "clinic_postal": {
      "status": "manual_review"
    },
    "clinic": {
      "status": "manual_review"
    }
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/doctors/{user_id}/profiles

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/profiles`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<profile UUID>",
      "full_name": "Example member",
      "module": "child",
      "owner_id": "<patient UUID>",
      "date_of_birth": "2020-01-01"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/doctors/{user_id}/reactivate

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/reactivate`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "account_status": "ACTIVE"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/doctors/{user_id}/reject

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/reject`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "reason": "Registration details require correction"
}
```

Validation schema: `Rejection` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "reason": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Reason",
      "type": "string"
    }
  },
  "required": [
    "reason"
  ],
  "title": "Rejection",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "user": {
    "approval_status": "REJECTED"
  },
  "email_status": "queued"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/doctors/{user_id}/suspend

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/suspend`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "account_status": "SUSPENDED"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/login

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/admin/login`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

Validation schema: `Login` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    }
  },
  "required": [
    "email",
    "password"
  ],
  "title": "Login",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "access_token": "<signed JWT>",
  "refresh_token": "<opaque refresh token>",
  "expires_in": 900,
  "token_type": "Bearer",
  "user": {
    "id": "<UUID>",
    "public_id": "A000001",
    "role": "ADMIN",
    "full_name": "Example User",
    "email": "user@example.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/me

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/me`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "id": "<UUID>",
    "public_id": "A000001",
    "role": "ADMIN",
    "full_name": "Example User",
    "email": "user@example.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/patients

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/patients`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
| `search` | query | False | `{"type": "string", "maxLength": 80}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/patients/{user_id}

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/patients/{user_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "user": {
    "id": "<patient UUID>",
    "public_id": "C000001",
    "full_name": "Example patient",
    "role": "PATIENT",
    "created_at": "2026-10-30T00:00:00Z"
  },
  "profile_counts": {
    "total": 0,
    "members": 0,
    "self": 0,
    "child": 0,
    "adult": 0,
    "women": 0
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/patients/{user_id}/profiles

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/patients/{user_id}/profiles`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [
    {
      "id": "<profile UUID>",
      "profile_type": "member",
      "module": "child",
      "full_name": "Aarav Kumar",
      "date_of_birth": "2018-05-14",
      "parent_profile_id": "<parent profile UUID>",
      "doctor": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/patients/{user_id}/profiles/{profile_id}

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/patients/{user_id}/profiles/{profile_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/register

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/admin/register`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "full_name": "Example User",
  "email": "user@example.com",
  "mobile_number": "+919876543210",
  "password": "Choose-Your-Password8!",
  "confirm_password": "Choose-Your-Password8!"
}
```

Validation schema: `Registration` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    }
  },
  "required": [
    "full_name",
    "email",
    "mobile_number",
    "password",
    "confirm_password"
  ],
  "title": "Registration",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent",
  "public_id": null,
  "user_id": null,
  "approval_status": "PENDING_EMAIL_VERIFICATION",
  "message": "OTP sent to your email. Verify OTP to complete registration."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/resend-otp

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/admin/resend-otp`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>"
}
```

Validation schema: `Challenge` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    }
  },
  "required": [
    "challenge_token"
  ],
  "title": "Challenge",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/search

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/search`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
| `q` | query | False | `{"type": "string", "maxLength": 80}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Search matches

```json
{
  "items": [
    {
      "id": "<UUID>",
      "public_id": "C000001",
      "full_name": "Example Patient",
      "email": "patient@example.com",
      "role": "PATIENT",
      "approval_status": "APPROVED",
      "account_status": "ACTIVE",
      "created_at": "<UTC timestamp>"
    }
  ]
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/vaccination/audit

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/audit`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/vaccination/import-uip

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/import-uip`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "created": 26,
  "skipped": 0,
  "schedule_type": "UIP",
  "message": "Drafts saved. Independent medical review and admin publication are required."
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/vaccination/reviewers

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/reviewers`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<doctor UUID>",
      "name": "Example reviewer",
      "qualification": "MBBS",
      "registration": "EXAMPLE-1",
      "council": "Example council"
    }
  ]
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/vaccination/schedules

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/vaccination/schedules

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "child_visible": true,
  "active": true,
  "vaccine_id": "00000000-0000-4000-8000-000000000001",
  "schedule_type": "UIP",
  "dose_code": "Example value",
  "dose_name": "Example value",
  "version": "Example value",
  "age_label": "Example value",
  "age_unit": "days",
  "age_start": 0,
  "age_end": 0,
  "minimum_age": null,
  "maximum_age": null,
  "previous_dose_code": "",
  "minimum_interval_days": null,
  "route": "Oral",
  "injection_site": "",
  "instructions": "",
  "source_url": "https://example.org/guideline",
  "source_reference": "Example value",
  "effective_from": "2026-10-30",
  "effective_to": null,
  "eligibility": {
    "gender": "All",
    "country": "IN",
    "states": [],
    "districts": [],
    "programme": "",
    "requires_clinical_review": true,
    "active": true
  },
  "reminders": {
    "before_days": [],
    "on_due": true,
    "overdue_days": [],
    "language": "en",
    "in_app": true,
    "email": false,
    "enabled": true
  }
}
```

Validation schema: `ScheduleInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    },
    "vaccine_id": {
      "format": "uuid",
      "title": "Vaccine Id",
      "type": "string"
    },
    "schedule_type": {
      "enum": [
        "UIP",
        "IAP"
      ],
      "title": "Schedule Type",
      "type": "string"
    },
    "dose_code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Dose Code",
      "type": "string"
    },
    "dose_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Dose Name",
      "type": "string"
    },
    "version": {
      "maxLength": 80,
      "minLength": 1,
      "title": "Version",
      "type": "string"
    },
    "age_label": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Age Label",
      "type": "string"
    },
    "age_unit": {
      "enum": [
        "days",
        "weeks",
        "months",
        "years"
      ],
      "title": "Age Unit",
      "type": "string"
    },
    "age_start": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age Start",
      "type": "integer"
    },
    "age_end": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age End",
      "type": "integer"
    },
    "minimum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Age"
    },
    "maximum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Maximum Age"
    },
    "previous_dose_code": {
      "default": "",
      "maxLength": 40,
      "pattern": "^(?:[A-Z0-9][A-Z0-9_-]{0,39})?$",
      "title": "Previous Dose Code",
      "type": "string"
    },
    "minimum_interval_days": {
      "anyOf": [
        {
          "maximum": 3650,
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Interval Days"
    },
    "route": {
      "enum": [
        "Oral",
        "IM",
        "ID",
        "SC",
        "Other"
      ],
      "title": "Route",
      "type": "string"
    },
    "injection_site": {
      "default": "",
      "maxLength": 160,
      "title": "Injection Site",
      "type": "string"
    },
    "instructions": {
      "default": "",
      "maxLength": 2000,
      "title": "Instructions",
      "type": "string"
    },
    "source_url": {
      "format": "uri",
      "maxLength": 2083,
      "minLength": 1,
      "title": "Source Url",
      "type": "string"
    },
    "source_reference": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Source Reference",
      "type": "string"
    },
    "effective_from": {
      "format": "date",
      "title": "Effective From",
      "type": "string"
    },
    "effective_to": {
      "anyOf": [
        {
          "format": "date",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Effective To"
    },
    "eligibility": {
      "$ref": "#/components/schemas/EligibilityInput"
    },
    "reminders": {
      "$ref": "#/components/schemas/ReminderInput"
    }
  },
  "required": [
    "vaccine_id",
    "schedule_type",
    "dose_code",
    "dose_name",
    "version",
    "age_label",
    "age_unit",
    "age_start",
    "age_end",
    "route",
    "source_url",
    "source_reference",
    "effective_from"
  ],
  "title": "ScheduleInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/admin/vaccination/schedules/{schedule_id}

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "child_visible": true,
  "active": true,
  "vaccine_id": "00000000-0000-4000-8000-000000000001",
  "schedule_type": "UIP",
  "dose_code": "Example value",
  "dose_name": "Example value",
  "version": "Example value",
  "age_label": "Example value",
  "age_unit": "days",
  "age_start": 0,
  "age_end": 0,
  "minimum_age": null,
  "maximum_age": null,
  "previous_dose_code": "",
  "minimum_interval_days": null,
  "route": "Oral",
  "injection_site": "",
  "instructions": "",
  "source_url": "https://example.org/guideline",
  "source_reference": "Example value",
  "effective_from": "2026-10-30",
  "effective_to": null,
  "eligibility": {
    "gender": "All",
    "country": "IN",
    "states": [],
    "districts": [],
    "programme": "",
    "requires_clinical_review": true,
    "active": true
  },
  "reminders": {
    "before_days": [],
    "on_due": true,
    "overdue_days": [],
    "language": "en",
    "in_app": true,
    "email": false,
    "enabled": true
  }
}
```

Validation schema: `ScheduleInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    },
    "vaccine_id": {
      "format": "uuid",
      "title": "Vaccine Id",
      "type": "string"
    },
    "schedule_type": {
      "enum": [
        "UIP",
        "IAP"
      ],
      "title": "Schedule Type",
      "type": "string"
    },
    "dose_code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Dose Code",
      "type": "string"
    },
    "dose_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Dose Name",
      "type": "string"
    },
    "version": {
      "maxLength": 80,
      "minLength": 1,
      "title": "Version",
      "type": "string"
    },
    "age_label": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Age Label",
      "type": "string"
    },
    "age_unit": {
      "enum": [
        "days",
        "weeks",
        "months",
        "years"
      ],
      "title": "Age Unit",
      "type": "string"
    },
    "age_start": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age Start",
      "type": "integer"
    },
    "age_end": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age End",
      "type": "integer"
    },
    "minimum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Age"
    },
    "maximum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Maximum Age"
    },
    "previous_dose_code": {
      "default": "",
      "maxLength": 40,
      "pattern": "^(?:[A-Z0-9][A-Z0-9_-]{0,39})?$",
      "title": "Previous Dose Code",
      "type": "string"
    },
    "minimum_interval_days": {
      "anyOf": [
        {
          "maximum": 3650,
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Interval Days"
    },
    "route": {
      "enum": [
        "Oral",
        "IM",
        "ID",
        "SC",
        "Other"
      ],
      "title": "Route",
      "type": "string"
    },
    "injection_site": {
      "default": "",
      "maxLength": 160,
      "title": "Injection Site",
      "type": "string"
    },
    "instructions": {
      "default": "",
      "maxLength": 2000,
      "title": "Instructions",
      "type": "string"
    },
    "source_url": {
      "format": "uri",
      "maxLength": 2083,
      "minLength": 1,
      "title": "Source Url",
      "type": "string"
    },
    "source_reference": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Source Reference",
      "type": "string"
    },
    "effective_from": {
      "format": "date",
      "title": "Effective From",
      "type": "string"
    },
    "effective_to": {
      "anyOf": [
        {
          "format": "date",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Effective To"
    },
    "eligibility": {
      "$ref": "#/components/schemas/EligibilityInput"
    },
    "reminders": {
      "$ref": "#/components/schemas/ReminderInput"
    }
  },
  "required": [
    "vaccine_id",
    "schedule_type",
    "dose_code",
    "dose_name",
    "version",
    "age_label",
    "age_unit",
    "age_start",
    "age_end",
    "route",
    "source_url",
    "source_reference",
    "effective_from"
  ],
  "title": "ScheduleInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/admin/vaccination/schedules/{schedule_id}/eligibility

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/eligibility`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "gender": "All",
  "country": "IN",
  "states": [],
  "districts": [],
  "programme": "",
  "requires_clinical_review": true,
  "active": true
}
```

Validation schema: `EligibilityInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "gender": {
      "default": "All",
      "enum": [
        "All",
        "Girls",
        "Boys"
      ],
      "title": "Gender",
      "type": "string"
    },
    "country": {
      "const": "IN",
      "default": "IN",
      "title": "Country",
      "type": "string"
    },
    "states": {
      "items": {
        "type": "string"
      },
      "maxItems": 40,
      "title": "States",
      "type": "array"
    },
    "districts": {
      "items": {
        "type": "string"
      },
      "maxItems": 200,
      "title": "Districts",
      "type": "array"
    },
    "programme": {
      "default": "",
      "maxLength": 160,
      "title": "Programme",
      "type": "string"
    },
    "requires_clinical_review": {
      "default": true,
      "title": "Requires Clinical Review",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    }
  },
  "title": "EligibilityInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/publish

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/publish`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "PUBLISHED",
    "published_at": "2026-10-30T00:00:00Z",
    "created_by": "<author UUID>",
    "reviewer_id": "<reviewer UUID>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/admin/vaccination/schedules/{schedule_id}/reminders

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/reminders`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "before_days": [],
  "on_due": true,
  "overdue_days": [],
  "language": "en",
  "in_app": true,
  "email": false,
  "enabled": true
}
```

Validation schema: `ReminderInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "before_days": {
      "items": {
        "type": "integer"
      },
      "maxItems": 12,
      "title": "Before Days",
      "type": "array"
    },
    "on_due": {
      "default": true,
      "title": "On Due",
      "type": "boolean"
    },
    "overdue_days": {
      "items": {
        "type": "integer"
      },
      "maxItems": 12,
      "title": "Overdue Days",
      "type": "array"
    },
    "language": {
      "default": "en",
      "enum": [
        "en",
        "hi"
      ],
      "title": "Language",
      "type": "string"
    },
    "in_app": {
      "default": true,
      "title": "In App",
      "type": "boolean"
    },
    "email": {
      "default": false,
      "title": "Email",
      "type": "boolean"
    },
    "enabled": {
      "default": true,
      "title": "Enabled",
      "type": "boolean"
    }
  },
  "title": "ReminderInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/retire

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/retire`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "reason": "Example value"
}
```

Validation schema: `RetireInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "reason": {
      "maxLength": 1000,
      "minLength": 10,
      "title": "Reason",
      "type": "string"
    }
  },
  "required": [
    "reason"
  ],
  "title": "RetireInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "RETIRED",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": "<reviewer UUID>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/submit-review

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/submit-review`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "reviewer_id": "00000000-0000-4000-8000-000000000001"
}
```

Validation schema: `AssignReview` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "reviewer_id": {
      "format": "uuid",
      "title": "Reviewer Id",
      "type": "string"
    }
  },
  "required": [
    "reviewer_id"
  ],
  "title": "AssignReview",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "IN_REVIEW",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": "<reviewer UUID>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/admin/vaccination/schedules/{schedule_id}/visibility

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/visibility`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "active": false,
  "child_visible": true
}
```

Validation schema: `ScheduleVisibility` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "active": {
      "title": "Active",
      "type": "boolean"
    },
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    }
  },
  "required": [
    "active"
  ],
  "title": "ScheduleVisibility",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/withdraw

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/withdraw`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/vaccination/vaccines

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/vaccines`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/vaccination/vaccines

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/vaccines`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "code": "Example value",
  "name_en": "Example value",
  "name_hi": "",
  "category": "Government",
  "protects_against": "Example value",
  "description_en": "",
  "description_hi": "",
  "active": true
}
```

Validation schema: `VaccineInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Code",
      "type": "string"
    },
    "name_en": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Name En",
      "type": "string"
    },
    "name_hi": {
      "default": "",
      "maxLength": 160,
      "title": "Name Hi",
      "type": "string"
    },
    "category": {
      "enum": [
        "Government",
        "Optional"
      ],
      "title": "Category",
      "type": "string"
    },
    "protects_against": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Protects Against",
      "type": "string"
    },
    "description_en": {
      "default": "",
      "maxLength": 2000,
      "title": "Description En",
      "type": "string"
    },
    "description_hi": {
      "default": "",
      "maxLength": 2000,
      "title": "Description Hi",
      "type": "string"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    }
  },
  "required": [
    "code",
    "name_en",
    "category",
    "protects_against"
  ],
  "title": "VaccineInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "vaccine": {
    "code": "EXAMPLE_VACCINE",
    "name_en": "Example vaccine",
    "name_hi": "",
    "category": "Government",
    "protects_against": "Source-reviewed indication",
    "description_en": "",
    "description_hi": "",
    "active": true,
    "id": "00000000-0000-4000-8000-000000000001"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/admin/vaccination/vaccines/{vaccine_id}

Required roles: ADMIN

URL: `http://127.0.0.1:5001/api/v1/admin/vaccination/vaccines/{vaccine_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `vaccine_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "code": "Example value",
  "name_en": "Example value",
  "name_hi": "",
  "category": "Government",
  "protects_against": "Example value",
  "description_en": "",
  "description_hi": "",
  "active": true
}
```

Validation schema: `VaccineInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Code",
      "type": "string"
    },
    "name_en": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Name En",
      "type": "string"
    },
    "name_hi": {
      "default": "",
      "maxLength": 160,
      "title": "Name Hi",
      "type": "string"
    },
    "category": {
      "enum": [
        "Government",
        "Optional"
      ],
      "title": "Category",
      "type": "string"
    },
    "protects_against": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Protects Against",
      "type": "string"
    },
    "description_en": {
      "default": "",
      "maxLength": 2000,
      "title": "Description En",
      "type": "string"
    },
    "description_hi": {
      "default": "",
      "maxLength": 2000,
      "title": "Description Hi",
      "type": "string"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    }
  },
  "required": [
    "code",
    "name_en",
    "category",
    "protects_against"
  ],
  "title": "VaccineInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "vaccine": {
    "code": "EXAMPLE_VACCINE",
    "name_en": "Example vaccine",
    "name_hi": "",
    "category": "Government",
    "protects_against": "Source-reviewed indication",
    "description_en": "",
    "description_hi": "",
    "active": true,
    "id": "00000000-0000-4000-8000-000000000001"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/verify-email

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/admin/verify-email`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

Validation schema: `VerifyOTP` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    },
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    }
  },
  "required": [
    "challenge_token",
    "otp"
  ],
  "title": "VerifyOTP",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "message": "Email verified. Waiting for approval.",
  "user": {
    "approval_status": "PENDING_APPROVAL"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/verify-login-otp

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/admin/verify-login-otp`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

Validation schema: `VerifyOTP` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    },
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    }
  },
  "required": [
    "challenge_token",
    "otp"
  ],
  "title": "VerifyOTP",
  "type": "object"
}
```

HTTP 410 — Success

```json
{
  "error": {
    "code": "login_otp_disabled",
    "message": "Sign in with email and password; login OTP is no longer required"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/change-password

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

URL: `http://127.0.0.1:5001/api/v1/auth/change-password`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "current_password": "Old-Password8!",
  "new_password": "New-Password8!",
  "confirm_password": "New-Password8!"
}
```

Validation schema: `ChangePassword` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "current_password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Current Password",
      "type": "string"
    },
    "new_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "New Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    }
  },
  "required": [
    "current_password",
    "new_password",
    "confirm_password"
  ],
  "title": "ChangePassword",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "message": "Password changed. All sessions revoked; sign in again."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/forgot-password

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/auth/forgot-password`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "email": "user@example.com"
}
```

Validation schema: `ForgotPassword` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    }
  },
  "required": [
    "email"
  ],
  "title": "ForgotPassword",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "queued",
  "message": "If an eligible account exists, reset instructions are queued."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/initial-password

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/auth/initial-password`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "current_password": "Old-Password8!",
  "new_password": "New-Password8!",
  "confirm_password": "New-Password8!",
  "challenge_token": "<challenge_token>"
}
```

Validation schema: `InitialPassword` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "current_password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Current Password",
      "type": "string"
    },
    "new_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "New Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    },
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    }
  },
  "required": [
    "current_password",
    "new_password",
    "confirm_password",
    "challenge_token"
  ],
  "title": "InitialPassword",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "access_token": "<signed JWT>",
  "refresh_token": "<opaque refresh token>",
  "expires_in": 900,
  "token_type": "Bearer",
  "user": {
    "id": "<UUID>",
    "public_id": "C000001",
    "role": "PATIENT"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/logout

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

URL: `http://127.0.0.1:5001/api/v1/auth/logout`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "Logged out"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/logout-all

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

URL: `http://127.0.0.1:5001/api/v1/auth/logout-all`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "All sessions revoked"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/refresh

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/auth/refresh`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "refresh_token": "<refresh_token>"
}
```

Validation schema: `RefreshRequest` (included in openapi.json).

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "refresh_token"
  ],
  "properties": {
    "refresh_token": {
      "type": "string",
      "maxLength": 512
    }
  }
}
```

HTTP 200 — Success

```json
{
  "access_token": "<signed JWT>",
  "refresh_token": "<opaque refresh token>",
  "expires_in": 900,
  "token_type": "Bearer",
  "user": {
    "id": "<UUID>",
    "public_id": "C000001",
    "role": "PATIENT"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/request-email-verification

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/auth/request-email-verification`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

Validation schema: `Login` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    }
  },
  "required": [
    "email",
    "password"
  ],
  "title": "Login",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/resend-otp

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/auth/resend-otp`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>"
}
```

Validation schema: `Challenge` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    }
  },
  "required": [
    "challenge_token"
  ],
  "title": "Challenge",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/reset-password

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/auth/reset-password`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456",
  "new_password": "New-Password8!",
  "confirm_password": "New-Password8!"
}
```

Validation schema: `ResetPassword` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    },
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    },
    "new_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "New Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    }
  },
  "required": [
    "challenge_token",
    "otp",
    "new_password",
    "confirm_password"
  ],
  "title": "ResetPassword",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "message": "Password reset. Sign in again."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/auth/sessions

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

URL: `http://127.0.0.1:5001/api/v1/auth/sessions`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/auth/sessions/{session_id}

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

URL: `http://127.0.0.1:5001/api/v1/auth/sessions/{session_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `session_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Session revoked"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<child UUID>",
      "full_name": "Example child",
      "module": "child",
      "date_of_birth": "2020-01-01",
      "profile_type": "member",
      "doctor": null,
      "age": {
        "completed_years": 6,
        "remaining_months": 9,
        "remaining_days": 30,
        "total_completed_months": 81,
        "total_days": 2495,
        "display": "6 years 9 months 30 days",
        "primary_category": "SCHOOL_AGE",
        "secondary_categories": [],
        "in_child_module_scope": true
      }
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "child": {
    "id": "<child UUID>",
    "full_name": "Example child",
    "module": "child",
    "date_of_birth": "2020-01-01",
    "profile_type": "member",
    "doctor": null,
    "age": {
      "completed_years": 6,
      "remaining_months": 9,
      "remaining_days": 30,
      "total_completed_months": 81,
      "total_days": 2495,
      "display": "6 years 9 months 30 days",
      "primary_category": "SCHOOL_AGE",
      "secondary_categories": [],
      "in_child_module_scope": true
    }
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/age

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/age`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "age": {
    "completed_years": 6,
    "remaining_months": 9,
    "remaining_days": 30,
    "total_completed_months": 81,
    "total_days": 2495,
    "display": "6 years 9 months 30 days",
    "primary_category": "SCHOOL_AGE",
    "secondary_categories": [],
    "in_child_module_scope": true
  },
  "as_of_date": "2026-10-31"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/care-notes

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<record UUID>",
      "kind": "care",
      "title": "Example record",
      "date": "2026-10-30",
      "status": "Recorded",
      "notes": "Synthetic example",
      "verification_status": "PARENT_REPORTED"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/children/{child_id}/care-notes

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "title": "Example diary entry",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Account owner supplied record"
}
```

Validation schema: `RecordInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "care",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/children/{child_id}/care-notes/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/children/{child_id}/care-notes/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "notes": "Updated account owner notes"
}
```

Validation schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "title": "RecordInput",
  "type": "object",
  "minProperties": 1,
  "description": "Partial fields are merged with the existing record before validation."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "care",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/care-notes/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "care",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/consultation-requests

Required roles: PATIENT, DOCTOR

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<record UUID>",
      "kind": "consultation_request",
      "title": "Example record",
      "date": "2026-10-30",
      "status": "Recorded",
      "notes": "Synthetic example",
      "verification_status": "PARENT_REPORTED"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/children/{child_id}/consultation-requests

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "title": "Example diary entry",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Account owner supplied record"
}
```

Validation schema: `RecordInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "consultation_request",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/children/{child_id}/consultation-requests/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/children/{child_id}/consultation-requests/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "notes": "Updated account owner notes"
}
```

Validation schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "title": "RecordInput",
  "type": "object",
  "minProperties": 1,
  "description": "Partial fields are merged with the existing record before validation."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "consultation_request",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/consultation-requests/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "consultation_request",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/consultations

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<record UUID>",
      "kind": "consultation",
      "title": "Example record",
      "date": "2026-10-30",
      "status": "Recorded",
      "notes": "Synthetic example",
      "verification_status": "PARENT_REPORTED"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/children/{child_id}/consultations

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "title": "Example diary entry",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Account owner supplied record"
}
```

Validation schema: `RecordInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "consultation",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/children/{child_id}/consultations/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/children/{child_id}/consultations/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "notes": "Updated account owner notes"
}
```

Validation schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "title": "RecordInput",
  "type": "object",
  "minProperties": 1,
  "description": "Partial fields are merged with the existing record before validation."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "consultation",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/consultations/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "consultation",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/dashboard

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/dashboard`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "counts": [
    {
      "role": "ADMIN",
      "approval_status": "PENDING_APPROVAL",
      "count": 1
    }
  ]
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/growth

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/growth`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<record UUID>",
      "kind": "growth",
      "title": "Example record",
      "date": "2026-10-30",
      "status": "Recorded",
      "notes": "Synthetic example",
      "verification_status": "PARENT_REPORTED"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/children/{child_id}/growth

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/growth`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "title": "Example diary entry",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Account owner supplied record"
}
```

Validation schema: `RecordInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "growth",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/children/{child_id}/growth/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/growth/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/children/{child_id}/growth/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/growth/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "notes": "Updated account owner notes"
}
```

Validation schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "title": "RecordInput",
  "type": "object",
  "minProperties": 1,
  "description": "Partial fields are merged with the existing record before validation."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "growth",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/growth/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/growth/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "growth",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/health-guide

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/health-guide`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "status": "NOT_AVAILABLE",
  "items": [],
  "message": "No medically reviewed health guide has been published for this child. Ask your doctor for guidance."
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/medical-history

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<record UUID>",
      "kind": "history",
      "title": "Example record",
      "date": "2026-10-30",
      "status": "Recorded",
      "notes": "Synthetic example",
      "verification_status": "PARENT_REPORTED"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/children/{child_id}/medical-history

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "title": "Example diary entry",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Account owner supplied record"
}
```

Validation schema: `RecordInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "history",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/children/{child_id}/medical-history/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/children/{child_id}/medical-history/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "notes": "Updated account owner notes"
}
```

Validation schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "title": "RecordInput",
  "type": "object",
  "minProperties": 1,
  "description": "Partial fields are merged with the existing record before validation."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "history",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/medical-history/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "history",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/nutrition

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<record UUID>",
      "kind": "nutrition",
      "title": "Example record",
      "date": "2026-10-30",
      "status": "Recorded",
      "notes": "Synthetic example",
      "verification_status": "PARENT_REPORTED"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/children/{child_id}/nutrition

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "title": "Example diary entry",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Account owner supplied record"
}
```

Validation schema: `RecordInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "nutrition",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/children/{child_id}/nutrition/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/children/{child_id}/nutrition/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "notes": "Updated account owner notes"
}
```

Validation schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "title": "RecordInput",
  "type": "object",
  "minProperties": 1,
  "description": "Partial fields are merged with the existing record before validation."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "nutrition",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/nutrition/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "nutrition",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/records

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/records`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/children/{child_id}/reminder-preferences

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/reminder-preferences`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "in_app": false
}
```

Validation schema: `PreferencesInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "in_app": {
      "title": "In App",
      "type": "boolean"
    }
  },
  "required": [
    "in_app"
  ],
  "title": "PreferencesInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "in_app": true
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/reminders

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/reminders`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "preferences": {
    "in_app": true
  },
  "message": "Recorded-date and published-schedule reminders. Schedule emails require explicit parent opt-in; SMS is not enabled."
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/vaccination-context

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccination-context`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "context": {
    "country": "Example value",
    "state": "",
    "district": "",
    "gender": "Unknown",
    "history_status": "UNKNOWN",
    "email_reminders": false
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/children/{child_id}/vaccination-context

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccination-context`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "country": "Example value",
  "state": "",
  "district": "",
  "gender": "Unknown",
  "history_status": "UNKNOWN",
  "email_reminders": false
}
```

Validation schema: `ChildContextInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "country": {
      "const": "IN",
      "title": "Country",
      "type": "string"
    },
    "state": {
      "default": "",
      "maxLength": 120,
      "title": "State",
      "type": "string"
    },
    "district": {
      "default": "",
      "maxLength": 120,
      "title": "District",
      "type": "string"
    },
    "gender": {
      "default": "Unknown",
      "enum": [
        "Unknown",
        "Girls",
        "Boys"
      ],
      "title": "Gender",
      "type": "string"
    },
    "history_status": {
      "default": "UNKNOWN",
      "enum": [
        "UNKNOWN",
        "PARENT_REPORTED"
      ],
      "title": "History Status",
      "type": "string"
    },
    "email_reminders": {
      "default": false,
      "title": "Email Reminders",
      "type": "boolean"
    }
  },
  "required": [
    "country"
  ],
  "title": "ChildContextInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "context": {
    "country": "Example value",
    "state": "",
    "district": "",
    "gender": "Unknown",
    "history_status": "UNKNOWN",
    "email_reminders": false
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/vaccinations

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "counts": {
    "COMPLETED": 0,
    "UPCOMING": 0,
    "DUE": 0,
    "OVERDUE": 0,
    "NOT_APPLICABLE": 0,
    "REVIEW_REQUIRED": 0
  },
  "status": "NOT_AVAILABLE",
  "schedule_type": "UIP",
  "context": {},
  "message": "No reviewed schedule has been published for this schedule type."
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/vaccinations/history

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<record UUID>",
      "kind": "vaccination",
      "title": "Example record",
      "date": "2026-10-30",
      "status": "Recorded",
      "notes": "Synthetic example",
      "verification_status": "PARENT_REPORTED"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/children/{child_id}/vaccinations/history

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "title": "Example diary entry",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Account owner supplied record"
}
```

Validation schema: `RecordInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "vaccination",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/children/{child_id}/vaccinations/history/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/children/{child_id}/vaccinations/history/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "notes": "Updated account owner notes"
}
```

Validation schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "title": "RecordInput",
  "type": "object",
  "minProperties": 1,
  "description": "Partial fields are merged with the existing record before validation."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "vaccination",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/vaccinations/history/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "vaccination",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "PARENT_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/vaccinations/upcoming

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/upcoming`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "counts": {
    "COMPLETED": 0,
    "UPCOMING": 0,
    "DUE": 0,
    "OVERDUE": 0,
    "NOT_APPLICABLE": 0,
    "REVIEW_REQUIRED": 0
  },
  "status": "NOT_AVAILABLE",
  "schedule_type": "UIP",
  "context": {},
  "message": "No reviewed schedule has been published for this schedule type."
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{profile_id}/growth-nutrition-guide

Required roles: PATIENT. Default active for all children. Uses DOB and India calendar; no rows need to be provisioned. Inactive or age 13+ returns guide: null.

URL: `http://127.0.0.1:5001/api/v1/children/{profile_id}/growth-nutrition-guide`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success

```json
{
  "child": {
    "id": "<child UUID>",
    "full_name": "Example Child",
    "date_of_birth": "2026-02-28",
    "age": {
      "completed_years": 0,
      "remaining_months": 8,
      "remaining_days": 3,
      "total_completed_months": 8,
      "total_days": 245,
      "display": "0 years 8 months 3 days",
      "primary_category": "INFANT",
      "secondary_categories": [],
      "in_child_module_scope": true
    }
  },
  "active": true,
  "default_active": true,
  "status": "AVAILABLE",
  "updated_at": null,
  "updated_by": null,
  "version": "2026-10-31.v1",
  "age_band": {
    "id": "month-8",
    "label": "8–9 Months",
    "min_months": 8,
    "max_months_exclusive": 9
  },
  "guide": {
    "title": "Growth & Nutrition Guide for Children (0–12 Years)",
    "nutrition": {
      "id": "month-8",
      "min_months": 8,
      "max_months_exclusive": 9,
      "label": "8–9 Months",
      "foods": "Soft rice, lentils, fully cooked eggs, and fruits",
      "meal_frequency": "2–3 meals daily",
      "blocks": [
        {
          "type": "list",
          "items": [
            "Introduce appropriate complementary foods.",
            "Continue breastfeeding alongside solid foods.",
            "Gradually increase food variety, quantity, and texture.",
            "Breastfeeding can continue until two years of age or beyond."
          ]
        },
        {
          "type": "heading",
          "text": "Recommended First Foods After 6 Months"
        },
        {
          "type": "table",
          "headers": [
            "Food",
            "Preparation Method"
          ],
          "rows": [
            [
              "Moong Dal Khichdi",
              "Cook thoroughly and mash"
            ],
            [
              "Porridge (Dalia)",
              "Prepare with a thick, soft consistency"
            ],
            [
              "Banana",
              "Mash thoroughly"
            ],
            [
              "Papaya",
              "Mash into a smooth texture"
            ],
            [
              "Carrot",
              "Boil or steam and mash"
            ],
            [
              "Lentils",
              "Cook thoroughly and serve thick"
            ],
            [
              "Egg",
              "Cook completely and mash or chop appropriately"
            ],
            [
              "Yogurt",
              "Serve plain and unsweetened"
            ]
          ]
        },
        {
          "type": "paragraph",
          "text": "Start with small amounts, such as 2–3 teaspoons, and gradually increase according to the baby's appetite."
        },
        {
          "type": "paragraph",
          "text": "Avoid relying only on watery lentil soup or rice water. Provide thick, nutrient-rich complementary foods."
        }
      ]
    },
    "growth_monitoring": [
      {
        "type": "paragraph",
        "text": "Monitoring growth helps parents and healthcare professionals understand a child's development over time."
      },
      {
        "type": "paragraph",
        "text": "Growth monitoring should consider multiple measurements rather than focusing only on body weight."
      },
      {
        "type": "heading",
        "text": "Age-Wise Growth Tracking"
      },
      {
        "type": "table",
        "headers": [
          "Age",
          "Recommended Measurements"
        ],
        "rows": [
          [
            "Birth–6 Months",
            "Weight, Length, Head Circumference"
          ],
          [
            "6–12 Months",
            "Weight, Length, Head Circumference"
          ],
          [
            "1–2 Years",
            "Weight, Length, Head Circumference"
          ],
          [
            "2–3 Years",
            "Weight, Height"
          ],
          [
            "3–4 Years",
            "Weight, Height"
          ],
          [
            "4–5 Years",
            "Weight, Height"
          ],
          [
            "5–6 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "6–7 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "7–8 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "8–9 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "9–10 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "10–11 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "11–12 Years",
            "Weight, Height, BMI-for-Age"
          ]
        ]
      },
      {
        "type": "heading",
        "text": "WHO Growth Chart Recommendations"
      },
      {
        "type": "paragraph",
        "text": "**Children Aged 0–5 Years**"
      },
      {
        "type": "paragraph",
        "text": "Use the WHO Child Growth Standards."
      },
      {
        "type": "paragraph",
        "text": "**Children Aged 5–12 Years**"
      },
      {
        "type": "paragraph",
        "text": "Use the WHO Growth Reference for children aged 5–19 years."
      },
      {
        "type": "heading",
        "text": "Important Growth Indicators"
      },
      {
        "type": "list",
        "items": [
          "Weight-for-age, where applicable.",
          "Length/height-for-age.",
          "Weight-for-length or weight-for-height in younger children.",
          "BMI-for-age, where applicable.",
          "Head circumference in infants and young children.",
          "Growth trends over time."
        ]
      },
      {
        "type": "paragraph",
        "text": "Growth measurements should be interpreted using age- and sex-appropriate growth charts."
      },
      {
        "type": "paragraph",
        "text": "A single measurement does not provide a complete picture of a child's growth and development."
      }
    ],
    "food_safety": [
      {
        "type": "paragraph",
        "text": "Different food groups provide different nutrients required for healthy growth."
      },
      {
        "type": "heading",
        "text": "Recommended Nutrition Categories"
      },
      {
        "type": "table",
        "headers": [
          "Food Category",
          "Main Nutrients",
          "Food Sources"
        ],
        "rows": [
          [
            "Grains",
            "Carbohydrates, Fiber",
            "Chapati, rice, oats"
          ],
          [
            "Pulses",
            "Protein, Iron",
            "Lentils, chickpeas, kidney beans"
          ],
          [
            "Vegetables",
            "Vitamins, Minerals",
            "Spinach, carrot, pumpkin"
          ],
          [
            "Fruits",
            "Vitamins, Fiber",
            "Banana, guava, papaya"
          ],
          [
            "Dairy Products",
            "Calcium, Protein",
            "Milk, yogurt, paneer"
          ],
          [
            "Eggs, Meat & Fish",
            "Protein, Iron, Vitamin B12",
            "Eggs, chicken, fish"
          ],
          [
            "Healthy Fats",
            "Essential Fatty Acids",
            "Appropriate amounts of oils and seeds"
          ],
          [
            "Water",
            "Hydration",
            "Clean and safe drinking water"
          ]
        ]
      },
      {
        "type": "heading",
        "text": "Important Feeding Guidelines"
      },
      {
        "type": "paragraph",
        "text": "**0–6 Months:** Exclusively breastfed infants do not require additional water."
      },
      {
        "type": "paragraph",
        "text": "**After 6 Months:** Small amounts of safe drinking water can be introduced alongside complementary foods."
      },
      {
        "type": "paragraph",
        "text": "**After 12 Months:** Children should receive a varied, balanced diet and adequate safe drinking water."
      },
      {
        "type": "heading",
        "text": "⚠️ Food Safety Guidelines"
      },
      {
        "type": "paragraph",
        "text": "For children under 12 months:"
      },
      {
        "type": "list",
        "items": [
          "Do not give honey.",
          "Avoid using cow's milk as the main drink before 12 months.",
          "Provide appropriately prepared foods to reduce choking risks.",
          "Avoid hard or round foods that may cause choking."
        ]
      },
      {
        "type": "paragraph",
        "text": "For toddlers and young children:"
      },
      {
        "type": "list",
        "items": [
          "Avoid whole nuts, whole grapes, popcorn, and other choking hazards.",
          "Prepare food according to the child's chewing and swallowing abilities.",
          "Ensure meals are properly cooked.",
          "Maintain good food hygiene."
        ]
      },
      {
        "type": "heading",
        "text": "When to Consult a Pediatrician"
      },
      {
        "type": "paragraph",
        "text": "Seek medical advice when:"
      },
      {
        "type": "list",
        "items": [
          "A child's weight or length/height is not increasing as expected.",
          "The child has difficulty chewing or swallowing.",
          "The child persistently refuses food.",
          "A nutritional deficiency is suspected.",
          "Growth measurements show concerning changes over time."
        ]
      }
    ],
    "sources": [
      {
        "title": "WHO infant and young child feeding",
        "url": "https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding"
      },
      {
        "title": "ICMR–NIN Dietary Guidelines for Indians 2024",
        "url": "https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf"
      },
      {
        "title": "WHO Child Growth Standards",
        "url": "https://www.who.int/tools/child-growth-standards"
      },
      {
        "title": "WHO growth reference 5–19 years",
        "url": "https://www.who.int/tools/growth-reference-data-for-5to19-years"
      }
    ],
    "notice": "General educational guidance. Your clinician adapts it for allergies, feeding difficulties, prematurity or other needs. Growth needs age- and sex-appropriate charts, not adult BMI cutoffs. No supplement dose or individual calorie target is generated.",
    "provenance": "User-supplied educational guide; not an individual diagnosis or prescribed meal plan."
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/approval-status

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/doctors/approval-status`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

Validation schema: `Login` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    }
  },
  "required": [
    "email",
    "password"
  ],
  "title": "Login",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "public_id": "D000001",
  "email_verified": true,
  "approval_status": "PENDING_APPROVAL",
  "account_status": "ACTIVE",
  "rejection_reason": null
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [
    {
      "id": "<profile UUID>",
      "profile_type": "member",
      "module": "child",
      "full_name": "Aarav Kumar",
      "date_of_birth": "2018-05-14",
      "parent_profile_id": "<parent profile UUID>",
      "doctor": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/child-records/{area}

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/child-records/{area}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `area` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/care-profiles/{profile_id}/child-records/{area}

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/child-records/{area}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `area` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{}
```

Validation schema: `RecordInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide

Required roles: DOCTOR. Default active for all children. Uses DOB and India calendar; no rows need to be provisioned. Inactive or age 13+ returns guide: null.

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success

```json
{
  "child": {
    "id": "<child UUID>",
    "full_name": "Example Child",
    "date_of_birth": "2026-02-28",
    "age": {
      "completed_years": 0,
      "remaining_months": 8,
      "remaining_days": 3,
      "total_completed_months": 8,
      "total_days": 245,
      "display": "0 years 8 months 3 days",
      "primary_category": "INFANT",
      "secondary_categories": [],
      "in_child_module_scope": true
    }
  },
  "active": true,
  "default_active": true,
  "status": "AVAILABLE",
  "updated_at": null,
  "updated_by": null,
  "version": "2026-10-31.v1",
  "age_band": {
    "id": "month-8",
    "label": "8–9 Months",
    "min_months": 8,
    "max_months_exclusive": 9
  },
  "guide": {
    "title": "Growth & Nutrition Guide for Children (0–12 Years)",
    "nutrition": {
      "id": "month-8",
      "min_months": 8,
      "max_months_exclusive": 9,
      "label": "8–9 Months",
      "foods": "Soft rice, lentils, fully cooked eggs, and fruits",
      "meal_frequency": "2–3 meals daily",
      "blocks": [
        {
          "type": "list",
          "items": [
            "Introduce appropriate complementary foods.",
            "Continue breastfeeding alongside solid foods.",
            "Gradually increase food variety, quantity, and texture.",
            "Breastfeeding can continue until two years of age or beyond."
          ]
        },
        {
          "type": "heading",
          "text": "Recommended First Foods After 6 Months"
        },
        {
          "type": "table",
          "headers": [
            "Food",
            "Preparation Method"
          ],
          "rows": [
            [
              "Moong Dal Khichdi",
              "Cook thoroughly and mash"
            ],
            [
              "Porridge (Dalia)",
              "Prepare with a thick, soft consistency"
            ],
            [
              "Banana",
              "Mash thoroughly"
            ],
            [
              "Papaya",
              "Mash into a smooth texture"
            ],
            [
              "Carrot",
              "Boil or steam and mash"
            ],
            [
              "Lentils",
              "Cook thoroughly and serve thick"
            ],
            [
              "Egg",
              "Cook completely and mash or chop appropriately"
            ],
            [
              "Yogurt",
              "Serve plain and unsweetened"
            ]
          ]
        },
        {
          "type": "paragraph",
          "text": "Start with small amounts, such as 2–3 teaspoons, and gradually increase according to the baby's appetite."
        },
        {
          "type": "paragraph",
          "text": "Avoid relying only on watery lentil soup or rice water. Provide thick, nutrient-rich complementary foods."
        }
      ]
    },
    "growth_monitoring": [
      {
        "type": "paragraph",
        "text": "Monitoring growth helps parents and healthcare professionals understand a child's development over time."
      },
      {
        "type": "paragraph",
        "text": "Growth monitoring should consider multiple measurements rather than focusing only on body weight."
      },
      {
        "type": "heading",
        "text": "Age-Wise Growth Tracking"
      },
      {
        "type": "table",
        "headers": [
          "Age",
          "Recommended Measurements"
        ],
        "rows": [
          [
            "Birth–6 Months",
            "Weight, Length, Head Circumference"
          ],
          [
            "6–12 Months",
            "Weight, Length, Head Circumference"
          ],
          [
            "1–2 Years",
            "Weight, Length, Head Circumference"
          ],
          [
            "2–3 Years",
            "Weight, Height"
          ],
          [
            "3–4 Years",
            "Weight, Height"
          ],
          [
            "4–5 Years",
            "Weight, Height"
          ],
          [
            "5–6 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "6–7 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "7–8 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "8–9 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "9–10 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "10–11 Years",
            "Weight, Height, BMI-for-Age"
          ],
          [
            "11–12 Years",
            "Weight, Height, BMI-for-Age"
          ]
        ]
      },
      {
        "type": "heading",
        "text": "WHO Growth Chart Recommendations"
      },
      {
        "type": "paragraph",
        "text": "**Children Aged 0–5 Years**"
      },
      {
        "type": "paragraph",
        "text": "Use the WHO Child Growth Standards."
      },
      {
        "type": "paragraph",
        "text": "**Children Aged 5–12 Years**"
      },
      {
        "type": "paragraph",
        "text": "Use the WHO Growth Reference for children aged 5–19 years."
      },
      {
        "type": "heading",
        "text": "Important Growth Indicators"
      },
      {
        "type": "list",
        "items": [
          "Weight-for-age, where applicable.",
          "Length/height-for-age.",
          "Weight-for-length or weight-for-height in younger children.",
          "BMI-for-age, where applicable.",
          "Head circumference in infants and young children.",
          "Growth trends over time."
        ]
      },
      {
        "type": "paragraph",
        "text": "Growth measurements should be interpreted using age- and sex-appropriate growth charts."
      },
      {
        "type": "paragraph",
        "text": "A single measurement does not provide a complete picture of a child's growth and development."
      }
    ],
    "food_safety": [
      {
        "type": "paragraph",
        "text": "Different food groups provide different nutrients required for healthy growth."
      },
      {
        "type": "heading",
        "text": "Recommended Nutrition Categories"
      },
      {
        "type": "table",
        "headers": [
          "Food Category",
          "Main Nutrients",
          "Food Sources"
        ],
        "rows": [
          [
            "Grains",
            "Carbohydrates, Fiber",
            "Chapati, rice, oats"
          ],
          [
            "Pulses",
            "Protein, Iron",
            "Lentils, chickpeas, kidney beans"
          ],
          [
            "Vegetables",
            "Vitamins, Minerals",
            "Spinach, carrot, pumpkin"
          ],
          [
            "Fruits",
            "Vitamins, Fiber",
            "Banana, guava, papaya"
          ],
          [
            "Dairy Products",
            "Calcium, Protein",
            "Milk, yogurt, paneer"
          ],
          [
            "Eggs, Meat & Fish",
            "Protein, Iron, Vitamin B12",
            "Eggs, chicken, fish"
          ],
          [
            "Healthy Fats",
            "Essential Fatty Acids",
            "Appropriate amounts of oils and seeds"
          ],
          [
            "Water",
            "Hydration",
            "Clean and safe drinking water"
          ]
        ]
      },
      {
        "type": "heading",
        "text": "Important Feeding Guidelines"
      },
      {
        "type": "paragraph",
        "text": "**0–6 Months:** Exclusively breastfed infants do not require additional water."
      },
      {
        "type": "paragraph",
        "text": "**After 6 Months:** Small amounts of safe drinking water can be introduced alongside complementary foods."
      },
      {
        "type": "paragraph",
        "text": "**After 12 Months:** Children should receive a varied, balanced diet and adequate safe drinking water."
      },
      {
        "type": "heading",
        "text": "⚠️ Food Safety Guidelines"
      },
      {
        "type": "paragraph",
        "text": "For children under 12 months:"
      },
      {
        "type": "list",
        "items": [
          "Do not give honey.",
          "Avoid using cow's milk as the main drink before 12 months.",
          "Provide appropriately prepared foods to reduce choking risks.",
          "Avoid hard or round foods that may cause choking."
        ]
      },
      {
        "type": "paragraph",
        "text": "For toddlers and young children:"
      },
      {
        "type": "list",
        "items": [
          "Avoid whole nuts, whole grapes, popcorn, and other choking hazards.",
          "Prepare food according to the child's chewing and swallowing abilities.",
          "Ensure meals are properly cooked.",
          "Maintain good food hygiene."
        ]
      },
      {
        "type": "heading",
        "text": "When to Consult a Pediatrician"
      },
      {
        "type": "paragraph",
        "text": "Seek medical advice when:"
      },
      {
        "type": "list",
        "items": [
          "A child's weight or length/height is not increasing as expected.",
          "The child has difficulty chewing or swallowing.",
          "The child persistently refuses food.",
          "A nutritional deficiency is suspected.",
          "Growth measurements show concerning changes over time."
        ]
      }
    ],
    "sources": [
      {
        "title": "WHO infant and young child feeding",
        "url": "https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding"
      },
      {
        "title": "ICMR–NIN Dietary Guidelines for Indians 2024",
        "url": "https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf"
      },
      {
        "title": "WHO Child Growth Standards",
        "url": "https://www.who.int/tools/child-growth-standards"
      },
      {
        "title": "WHO growth reference 5–19 years",
        "url": "https://www.who.int/tools/growth-reference-data-for-5to19-years"
      }
    ],
    "notice": "General educational guidance. Your clinician adapts it for allergies, feeding difficulties, prematurity or other needs. Growth needs age- and sex-appropriate charts, not adult BMI cutoffs. No supplement dose or individual calorie target is generated.",
    "provenance": "User-supplied educational guide; not an individual diagnosis or prescribed meal plan."
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide/visibility

Required roles: DOCTOR. Changes only this child. Saved measurements and meal notes remain available. active must be a JSON boolean.

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide/visibility`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "active": false
}
```

Validation schema: `GuideVisibility` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "active": {
      "title": "Active",
      "type": "boolean"
    }
  },
  "required": [
    "active"
  ],
  "title": "GuideVisibility",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success

```json
{
  "child": {
    "id": "<child UUID>",
    "full_name": "Example Child",
    "date_of_birth": "2026-02-28",
    "age": {
      "completed_years": 0,
      "remaining_months": 8,
      "remaining_days": 3,
      "total_completed_months": 8,
      "total_days": 245,
      "display": "0 years 8 months 3 days",
      "primary_category": "INFANT",
      "secondary_categories": [],
      "in_child_module_scope": true
    }
  },
  "active": false,
  "default_active": true,
  "status": "INACTIVE",
  "updated_at": "<UTC timestamp>",
  "updated_by": "<connected doctor UUID>",
  "version": "2026-10-31.v1"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/records

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/records`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/reports

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/reports`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [
    {
      "id": "<report UUID>",
      "profile_id": "<profile UUID>",
      "name": "blood-test.pdf",
      "storage_provider": "cloudinary",
      "url": "<short-lived signed Cloudinary URL>",
      "public_id": "familycare/C000001/profiles/<profile UUID>/child/reports/<report UUID>_blood-test.pdf",
      "folder": "familycare/C000001/profiles/<profile UUID>/child/reports",
      "resource_type": "raw",
      "delivery_type": "authenticated",
      "url_expires_in": 300
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `report_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "report": {
    "id": "<report UUID>",
    "profile_id": "<profile UUID>",
    "name": "blood-test.pdf",
    "storage_provider": "cloudinary",
    "url": "<short-lived signed Cloudinary URL>",
    "public_id": "familycare/C000001/profiles/<profile UUID>/child/reports/<report UUID>_blood-test.pdf",
    "folder": "familycare/C000001/profiles/<profile UUID>/child/reports",
    "resource_type": "raw",
    "delivery_type": "authenticated",
    "url_expires_in": 300
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/vaccination-plan

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/vaccination-plan`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "child": {
    "id": "<child UUID>",
    "name": "Example child"
  },
  "UIP": {
    "items": [],
    "counts": {},
    "context": {},
    "status": "NOT_AVAILABLE",
    "message": "No reviewed schedule has been published for this schedule type."
  },
  "IAP": {
    "items": [],
    "counts": {},
    "context": {},
    "status": "NOT_AVAILABLE",
    "message": "No reviewed schedule has been published for this schedule type."
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/care-profiles/{profile_id}/vaccination-plan

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/vaccination-plan`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "schedule_id": "00000000-0000-4000-8000-000000000001",
  "decision": "CONFIRM",
  "notes": "Example value",
  "attestation": false
}
```

Validation schema: `Decision` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "schedule_id": {
      "format": "uuid",
      "title": "Schedule Id",
      "type": "string"
    },
    "decision": {
      "enum": [
        "CONFIRM",
        "NOT_APPLICABLE"
      ],
      "title": "Decision",
      "type": "string"
    },
    "notes": {
      "maxLength": 2000,
      "minLength": 20,
      "title": "Notes",
      "type": "string"
    },
    "attestation": {
      "title": "Attestation",
      "type": "boolean"
    }
  },
  "required": [
    "schedule_id",
    "decision",
    "notes",
    "attestation"
  ],
  "title": "Decision",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Child-specific applicability saved. Recorded doses and routine dates were not changed."
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/consultation-requests

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/consultation-requests`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/login

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/doctors/login`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

Validation schema: `Login` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    }
  },
  "required": [
    "email",
    "password"
  ],
  "title": "Login",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "access_token": "<signed JWT>",
  "refresh_token": "<opaque refresh token>",
  "expires_in": 900,
  "token_type": "Bearer",
  "user": {
    "id": "<UUID>",
    "public_id": "D000001",
    "role": "DOCTOR",
    "full_name": "Example User",
    "email": "user@example.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false,
    "referral_id": "rahulkumarD000001"
  }
}
```

HTTP 202 — Success

```json
{
  "requires_profile_setup": true,
  "setup_token": "<limited-purpose setup_token>",
  "user": {
    "approval_status": "PROFILE_REQUIRED"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/me

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/me`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "user": {
    "id": "<doctor UUID>",
    "public_id": "D000001",
    "full_name": "Example doctor",
    "email": "doctor@example.com",
    "role": "DOCTOR",
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "email_verified": true,
    "must_change_password": false,
    "referral_id": "exampleD000001",
    "doctor": {
      "qualification": "MBBS",
      "medical_registration_number": "EXAMPLE-1",
      "registering_council": "Example Council",
      "specialization": "General Medicine",
      "nmr_id": null,
      "verification_status": "APPROVED",
      "address": "Example address",
      "clinic_address": "Example clinic",
      "years_of_experience": 5,
      "images": {
        "profile_photo": {
          "name": "profile photo.png",
          "url": "<signed private image URL valid for five minutes>"
        }
      }
    }
  },
  "notification_token": "<doctor-notification-purpose JWT>"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/notifications

Signed doctor notification token required in Authorization bearer header; access/setup tokens are not interchangeable with this token.

URL: `http://127.0.0.1:5001/api/v1/doctors/notifications`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "unread": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/notifications/push-config

Signed doctor notification token required in Authorization bearer header; access/setup tokens are not interchangeable with this token.

URL: `http://127.0.0.1:5001/api/v1/doctors/notifications/push-config`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "public_key": "<VAPID public key>",
  "enabled": true
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/notifications/subscriptions

Signed doctor notification token required in Authorization bearer header; access/setup tokens are not interchangeable with this token.

URL: `http://127.0.0.1:5001/api/v1/doctors/notifications/subscriptions`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "endpoint": "https://push.example.org/device-subscription",
  "keys": {
    "p256dh": "<browser subscription p256dh key>",
    "auth": "<browser subscription auth key>"
  }
}
```

Validation schema:

```json
{
  "type": "object",
  "required": [
    "endpoint",
    "keys"
  ],
  "properties": {
    "endpoint": {
      "type": "string",
      "format": "uri"
    },
    "keys": {
      "type": "object",
      "required": [
        "p256dh",
        "auth"
      ],
      "properties": {
        "p256dh": {
          "type": "string"
        },
        "auth": {
          "type": "string"
        }
      }
    }
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "message": "Notifications enabled on this browser"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/doctors/notifications/subscriptions

Signed doctor notification token required in Authorization bearer header; access/setup tokens are not interchangeable with this token.

URL: `http://127.0.0.1:5001/api/v1/doctors/notifications/subscriptions`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "endpoint": "https://push.example.org/device-subscription"
}
```

Validation schema:

```json
{
  "type": "object",
  "required": [
    "endpoint"
  ],
  "properties": {
    "endpoint": {
      "type": "string",
      "format": "uri"
    }
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Notifications disabled on this browser"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/notifications/{notification_id}/read

Signed doctor notification token required in Authorization bearer header; access/setup tokens are not interchangeable with this token.

URL: `http://127.0.0.1:5001/api/v1/doctors/notifications/{notification_id}/read`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `notification_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Notification marked as read"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/patients

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/patients`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/profile-photo

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/profile-photo`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "photo": {
    "name": "profile photo.png",
    "url": "<short-lived signed private image URL>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/profile-photo

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/profile-photo`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **multipart/form-data**

```json
{
  "type": "object",
  "required": [
    "file"
  ],
  "properties": {
    "file": {
      "type": "string",
      "format": "binary",
      "description": "JPEG/PNG/WebP, max 5 MB"
    }
  }
}
```

Form data example (send the file as binary, not as JSON):

```json
{
  "file": "<binary file: example.pdf or example.png>"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "images": {
    "profile_photo": {
      "name": "profile photo.png",
      "url": "<short-lived signed private image URL>"
    }
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/doctors/profile-photo

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/profile-photo`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **multipart/form-data**

```json
{
  "type": "object",
  "required": [
    "file"
  ],
  "properties": {
    "file": {
      "type": "string",
      "format": "binary",
      "description": "JPEG/PNG/WebP, max 5 MB"
    }
  }
}
```

Form data example (send the file as binary, not as JSON):

```json
{
  "file": "<binary file: example.pdf or example.png>"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "images": {
    "profile_photo": {
      "name": "profile photo.png",
      "url": "<short-lived signed private image URL>"
    }
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/doctors/profile-photo

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/profile-photo`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "photo": null,
  "message": "Profile photo removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/referral

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/referral`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

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

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/register

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/doctors/register`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "full_name": "Example User",
  "email": "user@example.com",
  "mobile_number": "+919876543210",
  "password": "Choose-Your-Password8!",
  "confirm_password": "Choose-Your-Password8!"
}
```

Validation schema: `DoctorRegistration` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    },
    "qualification": {
      "anyOf": [
        {
          "maxLength": 200,
          "minLength": 2,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Qualification"
    },
    "medical_registration_number": {
      "anyOf": [
        {
          "pattern": "^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Medical Registration Number"
    },
    "registering_council": {
      "anyOf": [
        {
          "maxLength": 200,
          "minLength": 2,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Registering Council"
    },
    "specialization": {
      "anyOf": [
        {
          "maxLength": 200,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Specialization"
    },
    "nmr_id": {
      "anyOf": [
        {
          "maxLength": 100,
          "minLength": 1,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Nmr Id"
    }
  },
  "required": [
    "full_name",
    "email",
    "mobile_number",
    "password",
    "confirm_password"
  ],
  "title": "DoctorRegistration",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent",
  "public_id": null,
  "user_id": null,
  "approval_status": "PENDING_EMAIL_VERIFICATION",
  "message": "OTP sent to your email. Verify OTP to complete registration."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/resend-otp

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/doctors/resend-otp`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>"
}
```

Validation schema: `Challenge` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    }
  },
  "required": [
    "challenge_token"
  ],
  "title": "Challenge",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/resubmit

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/doctors/resubmit`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!",
  "qualification": "MBBS",
  "medical_registration_number": "EXAMPLE-12345",
  "registering_council": "Example Medical Council"
}
```

Validation schema: `Resubmission` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    },
    "qualification": {
      "maxLength": 200,
      "minLength": 2,
      "title": "Qualification",
      "type": "string"
    },
    "medical_registration_number": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$",
      "title": "Medical Registration Number",
      "type": "string"
    },
    "registering_council": {
      "maxLength": 200,
      "minLength": 2,
      "title": "Registering Council",
      "type": "string"
    }
  },
  "required": [
    "email",
    "password",
    "qualification",
    "medical_registration_number",
    "registering_council"
  ],
  "title": "Resubmission",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "message": "Resubmitted for review",
  "user": {
    "approval_status": "PENDING_APPROVAL"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/setup-images

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/doctors/setup-images`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **multipart/form-data**

```json
{
  "type": "object",
  "required": [
    "file",
    "setup_token",
    "kind"
  ],
  "properties": {
    "file": {
      "type": "string",
      "format": "binary",
      "description": "JPEG/PNG/WebP, max 5 MB"
    },
    "setup_token": {
      "type": "string"
    },
    "kind": {
      "type": "string",
      "enum": [
        "profile_photo",
        "degree_photo"
      ]
    }
  }
}
```

Form data example (send the file as binary, not as JSON):

```json
{
  "file": "<binary file: example.pdf or example.png>",
  "setup_token": "<setup_token>",
  "kind": "<kind>"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "images": {
    "profile_photo": {
      "name": "profile photo.png",
      "url": "<short-lived signed private image URL>"
    }
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/setup-profile

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/doctors/setup-profile`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "setup_token": "<limited-purpose setup_token>",
  "qualification": "MBBS",
  "medical_registration_number": "EXAMPLE-12345",
  "registering_council": "Example Medical Council",
  "specialization": "General Medicine",
  "address": "Example Street, Delhi 110001",
  "clinic_address": "Example Clinic, Delhi 110001",
  "years_of_experience": 5
}
```

Validation schema: `DoctorProfileSetup` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "setup_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Setup Token",
      "type": "string"
    },
    "qualification": {
      "maxLength": 200,
      "minLength": 2,
      "title": "Qualification",
      "type": "string"
    },
    "medical_registration_number": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$",
      "title": "Medical Registration Number",
      "type": "string"
    },
    "registering_council": {
      "maxLength": 200,
      "minLength": 2,
      "title": "Registering Council",
      "type": "string"
    },
    "specialization": {
      "anyOf": [
        {
          "maxLength": 200,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Specialization"
    },
    "nmr_id": {
      "anyOf": [
        {
          "maxLength": 100,
          "minLength": 1,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Nmr Id"
    },
    "address": {
      "maxLength": 1000,
      "minLength": 5,
      "title": "Address",
      "type": "string"
    },
    "clinic_address": {
      "maxLength": 1000,
      "minLength": 5,
      "title": "Clinic Address",
      "type": "string"
    },
    "years_of_experience": {
      "maximum": 80,
      "minimum": 0,
      "title": "Years Of Experience",
      "type": "integer"
    }
  },
  "required": [
    "setup_token",
    "qualification",
    "medical_registration_number",
    "registering_council",
    "address",
    "clinic_address",
    "years_of_experience"
  ],
  "title": "DoctorProfileSetup",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "message": "Your profile is under review.",
  "user": {
    "approval_status": "PENDING_APPROVAL"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/vaccination-reviews

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/vaccination-reviews`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/vaccination-reviews/{schedule_id}

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/vaccination-reviews/{schedule_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "decision": "APPROVE",
  "notes": "Example value",
  "attestation": false
}
```

Validation schema: `MedicalReview` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "decision": {
      "enum": [
        "APPROVE",
        "REJECT"
      ],
      "title": "Decision",
      "type": "string"
    },
    "notes": {
      "maxLength": 2000,
      "minLength": 20,
      "title": "Notes",
      "type": "string"
    },
    "attestation": {
      "title": "Attestation",
      "type": "boolean"
    }
  },
  "required": [
    "decision",
    "notes",
    "attestation"
  ],
  "title": "MedicalReview",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "APPROVED",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": "<reviewer UUID>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/vaccination/import-iap

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/vaccination/import-iap`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "created": 18,
  "skipped": 0,
  "schedule_type": "IAP",
  "message": "Drafts saved. Independent medical review and admin publication are required."
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/vaccination/reviewers

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/vaccination/reviewers`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<doctor UUID>",
      "name": "Example reviewer",
      "qualification": "MBBS",
      "registration": "EXAMPLE-1",
      "council": "Example council"
    }
  ]
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/vaccination/schedules

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/vaccination/schedules`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/doctors/vaccination/schedules/{schedule_id}

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/vaccination/schedules/{schedule_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "child_visible": true,
  "active": true,
  "vaccine_id": "00000000-0000-4000-8000-000000000001",
  "schedule_type": "UIP",
  "dose_code": "Example value",
  "dose_name": "Example value",
  "version": "Example value",
  "age_label": "Example value",
  "age_unit": "days",
  "age_start": 0,
  "age_end": 0,
  "minimum_age": null,
  "maximum_age": null,
  "previous_dose_code": "",
  "minimum_interval_days": null,
  "route": "Oral",
  "injection_site": "",
  "instructions": "",
  "source_url": "https://example.org/guideline",
  "source_reference": "Example value",
  "effective_from": "2026-10-30",
  "effective_to": null,
  "eligibility": {
    "gender": "All",
    "country": "IN",
    "states": [],
    "districts": [],
    "programme": "",
    "requires_clinical_review": true,
    "active": true
  },
  "reminders": {
    "before_days": [],
    "on_due": true,
    "overdue_days": [],
    "language": "en",
    "in_app": true,
    "email": false,
    "enabled": true
  }
}
```

Validation schema: `ScheduleInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    },
    "vaccine_id": {
      "format": "uuid",
      "title": "Vaccine Id",
      "type": "string"
    },
    "schedule_type": {
      "enum": [
        "UIP",
        "IAP"
      ],
      "title": "Schedule Type",
      "type": "string"
    },
    "dose_code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Dose Code",
      "type": "string"
    },
    "dose_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Dose Name",
      "type": "string"
    },
    "version": {
      "maxLength": 80,
      "minLength": 1,
      "title": "Version",
      "type": "string"
    },
    "age_label": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Age Label",
      "type": "string"
    },
    "age_unit": {
      "enum": [
        "days",
        "weeks",
        "months",
        "years"
      ],
      "title": "Age Unit",
      "type": "string"
    },
    "age_start": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age Start",
      "type": "integer"
    },
    "age_end": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age End",
      "type": "integer"
    },
    "minimum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Age"
    },
    "maximum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Maximum Age"
    },
    "previous_dose_code": {
      "default": "",
      "maxLength": 40,
      "pattern": "^(?:[A-Z0-9][A-Z0-9_-]{0,39})?$",
      "title": "Previous Dose Code",
      "type": "string"
    },
    "minimum_interval_days": {
      "anyOf": [
        {
          "maximum": 3650,
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Interval Days"
    },
    "route": {
      "enum": [
        "Oral",
        "IM",
        "ID",
        "SC",
        "Other"
      ],
      "title": "Route",
      "type": "string"
    },
    "injection_site": {
      "default": "",
      "maxLength": 160,
      "title": "Injection Site",
      "type": "string"
    },
    "instructions": {
      "default": "",
      "maxLength": 2000,
      "title": "Instructions",
      "type": "string"
    },
    "source_url": {
      "format": "uri",
      "maxLength": 2083,
      "minLength": 1,
      "title": "Source Url",
      "type": "string"
    },
    "source_reference": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Source Reference",
      "type": "string"
    },
    "effective_from": {
      "format": "date",
      "title": "Effective From",
      "type": "string"
    },
    "effective_to": {
      "anyOf": [
        {
          "format": "date",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Effective To"
    },
    "eligibility": {
      "$ref": "#/components/schemas/EligibilityInput"
    },
    "reminders": {
      "$ref": "#/components/schemas/ReminderInput"
    }
  },
  "required": [
    "vaccine_id",
    "schedule_type",
    "dose_code",
    "dose_name",
    "version",
    "age_label",
    "age_unit",
    "age_start",
    "age_end",
    "route",
    "source_url",
    "source_reference",
    "effective_from"
  ],
  "title": "ScheduleInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/vaccination/schedules/{schedule_id}/submit-review

Required roles: DOCTOR

URL: `http://127.0.0.1:5001/api/v1/doctors/vaccination/schedules/{schedule_id}/submit-review`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "reviewer_id": "00000000-0000-4000-8000-000000000001"
}
```

Validation schema: `AssignReview` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "reviewer_id": {
      "format": "uuid",
      "title": "Reviewer Id",
      "type": "string"
    }
  },
  "required": [
    "reviewer_id"
  ],
  "title": "AssignReview",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "IN_REVIEW",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": "<reviewer UUID>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/verify-email

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/doctors/verify-email`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

Validation schema: `VerifyOTP` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    },
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    }
  },
  "required": [
    "challenge_token",
    "otp"
  ],
  "title": "VerifyOTP",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "requires_profile_setup": true,
  "setup_token": "<limited-purpose setup_token>",
  "user": {
    "approval_status": "PROFILE_REQUIRED"
  },
  "doctor": {}
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/family-invitations/{token}

Invitation secret authorizes this operation; no login session required. One-use link expires in 24 hours.

URL: `http://127.0.0.1:5001/api/v1/family-invitations/{token}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `token` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success

```json
{
  "invitation": {
    "id": "<invitation UUID>",
    "full_name": "Example Member",
    "email": "member@example.com",
    "module": "women",
    "relationship": "Family member",
    "status": "PENDING",
    "expires_at": "<UTC timestamp, 24 hours after creation>",
    "profile_id": null
  },
  "family": {
    "full_name": "Example Family",
    "email": "family@example.com"
  },
  "form": {
    "full_name": "Example Member",
    "email": "member@example.com",
    "readonly": [
      "full_name",
      "email"
    ]
  },
  "otp_destination": "inviting_family_email",
  "shared_profile": true
}
```

HTTP 410 — Invitation expired, revoked or accepted

```json
{
  "error": {
    "code": "invite_unavailable",
    "message": "Invitation expired, revoked or already accepted"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/family-invitations/{token}/resend-otp

Invitation secret authorizes this operation; no login session required. One-use link expires in 24 hours.

URL: `http://127.0.0.1:5001/api/v1/family-invitations/{token}/resend-otp`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `token` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 202 — Success

```json
{
  "message": "Approval OTP sent to the inviting family email.",
  "email_status": "sent",
  "otp_destination": "inviting_family_email",
  "expires_in": 300,
  "resend_after": 60
}
```

HTTP 410 — Invitation expired, revoked or accepted

```json
{
  "error": {
    "code": "invite_unavailable",
    "message": "Invitation expired, revoked or already accepted"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/family-invitations/{token}/setup

Invitation secret authorizes this operation; no login session required. One-use link expires in 24 hours.

URL: `http://127.0.0.1:5001/api/v1/family-invitations/{token}/setup`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `token` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "full_name": "Example Member",
  "email": "member@example.com",
  "mobile_number": "+919876543211",
  "date_of_birth": "1995-02-28",
  "password": "Choose-Your-Password8!",
  "confirm_password": "Choose-Your-Password8!"
}
```

Validation schema: `FamilySetup` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    },
    "date_of_birth": {
      "format": "date",
      "title": "Date Of Birth",
      "type": "string"
    }
  },
  "required": [
    "full_name",
    "email",
    "mobile_number",
    "password",
    "confirm_password",
    "date_of_birth"
  ],
  "title": "FamilySetup",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 202 — Success

```json
{
  "message": "Approval OTP sent to the inviting family email.",
  "email_status": "sent",
  "otp_destination": "inviting_family_email",
  "expires_in": 300,
  "resend_after": 60
}
```

HTTP 410 — Invitation expired, revoked or accepted

```json
{
  "error": {
    "code": "invite_unavailable",
    "message": "Invitation expired, revoked or already accepted"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/family-invitations/{token}/verify-otp

Invitation secret authorizes this operation; no login session required. One-use link expires in 24 hours.

URL: `http://127.0.0.1:5001/api/v1/family-invitations/{token}/verify-otp`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `token` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "otp": "123456"
}
```

Validation schema: `FamilyOTP` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    }
  },
  "required": [
    "otp"
  ],
  "title": "FamilyOTP",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success

```json
{
  "message": "Profile setup complete. Opening your profile.",
  "access_token": "<member access JWT; omitted in cookie mode>",
  "refresh_token": "<member refresh token; omitted in cookie mode>",
  "expires_in": 900,
  "token_type": "Bearer",
  "redirect_url": "/customer/women/dashboard",
  "user": {
    "id": "<member UUID>",
    "public_id": "C000002",
    "full_name": "Example Member",
    "email": "member@example.com",
    "phone_number": "+919876543211",
    "role": "PATIENT",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false,
    "referred_doctor": null
  },
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "women",
    "full_name": "Example Member",
    "date_of_birth": "1995-02-28",
    "member_email": "member@example.com",
    "relationship": "Family member",
    "linked_member": true,
    "parent_profile_id": null,
    "guardian_contact": "",
    "guardian_name": "",
    "emergency_contacts": [],
    "doctor": null,
    "created_at": "<UTC timestamp>"
  },
  "family": {
    "full_name": "Example Family",
    "relationship": "Family member"
  }
}
```

HTTP 410 — Invitation expired, revoked or accepted

```json
{
  "error": {
    "code": "invite_unavailable",
    "message": "Invitation expired, revoked or already accepted"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/health

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/health`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "status": "ok",
  "service": "familycare-backend",
  "auth": "flask-jwt"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/health/ready

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/health/ready`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "status": "ready",
  "database": "postgresql"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/notifications

Required roles: PATIENT, DOCTOR, ADMIN, SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/notifications`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/notifications/read-all

Required roles: PATIENT, DOCTOR, ADMIN, SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/notifications/read-all`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/notifications/socket-ticket

Required roles: PATIENT, DOCTOR, ADMIN, SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/notifications/socket-ticket`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/notifications/test

Required roles: PATIENT, DOCTOR, ADMIN, SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/notifications/test`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/notifications/unread-count

Required roles: PATIENT, DOCTOR, ADMIN, SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/notifications/unread-count`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/notifications/{notification_id}/read

Required roles: PATIENT, DOCTOR, ADMIN, SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/notifications/{notification_id}/read`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `notification_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/adults/{profile_id}/records

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/adults/{profile_id}/records`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<record UUID>",
      "kind": "history",
      "title": "Example record",
      "date": "2026-10-30",
      "status": "Recorded",
      "notes": "Synthetic example",
      "verification_status": "SELF_REPORTED"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/adults/{profile_id}/records

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/adults/{profile_id}/records`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "kind": "history",
  "title": "Example history",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Existing condition recorded by the account owner"
}
```

Validation schema: `AdultInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "kind": {
      "enum": [
        "bp",
        "glucose",
        "lipids",
        "medicine",
        "lifestyle",
        "screening",
        "history",
        "consultation_request",
        "reminder"
      ],
      "title": "Kind",
      "type": "string"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "status": {
      "default": "Recorded",
      "enum": [
        "Recorded",
        "Planned",
        "Completed"
      ],
      "title": "Status",
      "type": "string"
    },
    "systolic": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 400,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Systolic"
    },
    "diastolic": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 300,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Diastolic"
    },
    "pulse": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 350,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Pulse"
    },
    "glucose": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 2000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Glucose"
    },
    "total": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 3000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Total"
    },
    "ldl": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 3000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Ldl"
    },
    "hdl": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 1000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Hdl"
    },
    "triglycerides": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 5000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Triglycerides"
    },
    "minutes": {
      "anyOf": [
        {
          "maximum": 1440,
          "minimum": 0,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minutes"
    },
    "context": {
      "default": "",
      "maxLength": 160,
      "title": "Context",
      "type": "string"
    }
  },
  "required": [
    "kind",
    "title",
    "date"
  ],
  "title": "AdultInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "history",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "SELF_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/adults/{profile_id}/records/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/adults/{profile_id}/records/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "kind": "history",
  "title": "Example history",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Existing condition recorded by the account owner"
}
```

Validation schema: `AdultInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "kind": {
      "enum": [
        "bp",
        "glucose",
        "lipids",
        "medicine",
        "lifestyle",
        "screening",
        "history",
        "consultation_request",
        "reminder"
      ],
      "title": "Kind",
      "type": "string"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "status": {
      "default": "Recorded",
      "enum": [
        "Recorded",
        "Planned",
        "Completed"
      ],
      "title": "Status",
      "type": "string"
    },
    "systolic": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 400,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Systolic"
    },
    "diastolic": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 300,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Diastolic"
    },
    "pulse": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 350,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Pulse"
    },
    "glucose": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 2000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Glucose"
    },
    "total": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 3000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Total"
    },
    "ldl": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 3000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Ldl"
    },
    "hdl": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 1000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Hdl"
    },
    "triglycerides": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 5000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Triglycerides"
    },
    "minutes": {
      "anyOf": [
        {
          "maximum": 1440,
          "minimum": 0,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minutes"
    },
    "context": {
      "default": "",
      "maxLength": 160,
      "title": "Context",
      "type": "string"
    }
  },
  "required": [
    "kind",
    "title",
    "date"
  ],
  "title": "AdultInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "history",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "SELF_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/adults/{profile_id}/records/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/adults/{profile_id}/records/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "history",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "SELF_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/patients/adults/{profile_id}/records/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/adults/{profile_id}/records/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "kind": "history",
  "title": "Example history",
  "date": "2026-10-01",
  "status": "Recorded",
  "notes": "Existing condition recorded by the account owner"
}
```

Validation schema: `AdultInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "kind": {
      "enum": [
        "bp",
        "glucose",
        "lipids",
        "medicine",
        "lifestyle",
        "screening",
        "history",
        "consultation_request",
        "reminder"
      ],
      "title": "Kind",
      "type": "string"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "status": {
      "default": "Recorded",
      "enum": [
        "Recorded",
        "Planned",
        "Completed"
      ],
      "title": "Status",
      "type": "string"
    },
    "systolic": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 400,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Systolic"
    },
    "diastolic": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 300,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Diastolic"
    },
    "pulse": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 350,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Pulse"
    },
    "glucose": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 2000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Glucose"
    },
    "total": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 3000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Total"
    },
    "ldl": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 3000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Ldl"
    },
    "hdl": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 1000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Hdl"
    },
    "triglycerides": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 5000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Triglycerides"
    },
    "minutes": {
      "anyOf": [
        {
          "maximum": 1440,
          "minimum": 0,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minutes"
    },
    "context": {
      "default": "",
      "maxLength": 160,
      "title": "Context",
      "type": "string"
    }
  },
  "required": [
    "kind",
    "title",
    "date"
  ],
  "title": "AdultInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "record": {
    "id": "<record UUID>",
    "kind": "history",
    "title": "Example record",
    "date": "2026-10-30",
    "status": "Recorded",
    "notes": "Synthetic example",
    "verification_status": "SELF_REPORTED"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/patients/adults/{profile_id}/records/{record_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/adults/{profile_id}/records/{record_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/adults/{profile_id}/records/{record_id}/delete

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/adults/{profile_id}/records/{record_id}/delete`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "message": "Record removed"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/connect-doctor

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/connect-doctor`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "referral_id": "rahulkumarD000001"
}
```

Validation schema: `ConnectDoctor` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "referral_id": {
      "maxLength": 160,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9]+$",
      "title": "Referral Id",
      "type": "string"
    }
  },
  "required": [
    "referral_id"
  ],
  "title": "ConnectDoctor",
  "type": "object"
}
```

HTTP 200 — Success

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

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/doctor

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/doctor`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

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

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/family-invitations

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/family-invitations`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "full_name": "Example Member",
  "email": "member@example.com",
  "module": "women",
  "relationship": "Family member"
}
```

Validation schema: `FamilyInvite` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "module": {
      "enum": [
        "adult",
        "women"
      ],
      "title": "Module",
      "type": "string"
    },
    "relationship": {
      "default": "Family member",
      "maxLength": 50,
      "minLength": 1,
      "title": "Relationship",
      "type": "string"
    }
  },
  "required": [
    "full_name",
    "email",
    "module"
  ],
  "title": "FamilyInvite",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success

```json
{
  "invitation": {
    "id": "<invitation UUID>",
    "full_name": "Example Member",
    "email": "member@example.com",
    "module": "women",
    "relationship": "Family member",
    "status": "PENDING",
    "expires_at": "<UTC timestamp, 24 hours after creation>",
    "profile_id": null
  },
  "email_status": "sent"
}
```

HTTP 410 — Invitation expired, revoked or accepted

```json
{
  "error": {
    "code": "invite_unavailable",
    "message": "Invitation expired, revoked or already accepted"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/family-invitations

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/family-invitations`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success

```json
{
  "items": [
    {
      "id": "<invitation UUID>",
      "full_name": "Example Member",
      "email": "member@example.com",
      "module": "women",
      "relationship": "Family member",
      "status": "PENDING",
      "expires_at": "<UTC timestamp, 24 hours after creation>",
      "profile_id": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

HTTP 410 — Invitation expired, revoked or accepted

```json
{
  "error": {
    "code": "invite_unavailable",
    "message": "Invitation expired, revoked or already accepted"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/patients/family-invitations/{invite_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/family-invitations/{invite_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `invite_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success

```json
{
  "message": "Invitation revoked"
}
```

HTTP 410 — Invitation expired, revoked or accepted

```json
{
  "error": {
    "code": "invite_unavailable",
    "message": "Invitation expired, revoked or already accepted"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/login

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/patients/login`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

Validation schema: `Login` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    }
  },
  "required": [
    "email",
    "password"
  ],
  "title": "Login",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "access_token": "<signed JWT>",
  "refresh_token": "<opaque refresh token>",
  "expires_in": 900,
  "token_type": "Bearer",
  "user": {
    "id": "<UUID>",
    "public_id": "C000001",
    "role": "PATIENT",
    "full_name": "Example User",
    "email": "user@example.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false,
    "referred_doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/me

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/me`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "id": "<UUID>",
    "public_id": "C000001",
    "role": "PATIENT",
    "full_name": "Example User",
    "email": "user@example.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false,
    "referred_doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/profiles

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "profile_type": "member",
  "module": "child",
  "full_name": "Aarav Kumar",
  "date_of_birth": "2018-05-14",
  "guardian_contact": "+919876543210",
  "emergency_contacts": [],
  "referral_id": "rahulkumarD000001"
}
```

Validation schema: `CareProfileCreate` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "profile_type": {
      "enum": [
        "self",
        "member"
      ],
      "title": "Profile Type",
      "type": "string"
    },
    "module": {
      "enum": [
        "child",
        "adult",
        "women"
      ],
      "title": "Module",
      "type": "string"
    },
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "date_of_birth": {
      "format": "date",
      "title": "Date Of Birth",
      "type": "string"
    },
    "parent_profile_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Parent Profile Id"
    },
    "guardian_name": {
      "default": "",
      "maxLength": 120,
      "title": "Guardian Name",
      "type": "string"
    },
    "guardian_contact": {
      "default": "",
      "maxLength": 20,
      "pattern": "^(?:\\+?[1-9][0-9]{7,14})?$",
      "title": "Guardian Contact",
      "type": "string"
    },
    "emergency_contacts": {
      "items": {
        "$ref": "#/components/schemas/EmergencyContact"
      },
      "maxItems": 5,
      "title": "Emergency Contacts",
      "type": "array"
    },
    "referral_id": {
      "anyOf": [
        {
          "maxLength": 160,
          "minLength": 1,
          "pattern": "^[A-Za-z0-9]+$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Referral Id"
    }
  },
  "required": [
    "profile_type",
    "module",
    "full_name",
    "date_of_birth"
  ],
  "title": "CareProfileCreate",
  "type": "object"
}
```

HTTP 201 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [
    {
      "id": "<profile UUID>",
      "profile_type": "member",
      "module": "child",
      "full_name": "Aarav Kumar",
      "date_of_birth": "2018-05-14",
      "parent_profile_id": "<parent profile UUID>",
      "doctor": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/patients/profiles/{profile_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "full_name": "Example value",
  "guardian_contact": ""
}
```

Validation schema: `CareProfileEdit` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "guardian_contact": {
      "default": "",
      "maxLength": 20,
      "pattern": "^(?:\\+?[1-9][0-9]{7,14})?$",
      "title": "Guardian Contact",
      "type": "string"
    }
  },
  "required": [
    "full_name"
  ],
  "title": "CareProfileEdit",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/patients/profiles/{profile_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{}
```

Validation schema: `CareProfileUpdate` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "date_of_birth": {
      "format": "date",
      "title": "Date Of Birth",
      "type": "string"
    },
    "guardian_name": {
      "default": "",
      "maxLength": 120,
      "title": "Guardian Name",
      "type": "string"
    },
    "guardian_contact": {
      "default": "",
      "maxLength": 20,
      "pattern": "^(?:\\+?[1-9][0-9]{7,14})?$",
      "title": "Guardian Contact",
      "type": "string"
    },
    "emergency_contacts": {
      "items": {
        "$ref": "#/components/schemas/EmergencyContact"
      },
      "maxItems": 5,
      "title": "Emergency Contacts",
      "type": "array"
    }
  },
  "required": [
    "full_name",
    "date_of_birth"
  ],
  "title": "CareProfileUpdate",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/patients/profiles/{profile_id}

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/profiles/{profile_id}/connect-doctor

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/connect-doctor`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "referral_id": "rahulkumarD000001"
}
```

Validation schema: `CareProfileReferral` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "referral_id": {
      "maxLength": 160,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9]+$",
      "title": "Referral Id",
      "type": "string"
    }
  },
  "required": [
    "referral_id"
  ],
  "title": "CareProfileReferral",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/patients/profiles/{profile_id}/doctor

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/doctor`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "profile": {
    "id": "<profile UUID>",
    "doctor": null
  },
  "message": "Doctor disconnected from this profile"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}/doctor-overview

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/doctor-overview`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}/imported-records

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/imported-records`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/profiles/{profile_id}/reports

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **multipart/form-data**

```json
{
  "type": "object",
  "required": [
    "file"
  ],
  "properties": {
    "file": {
      "type": "string",
      "format": "binary",
      "description": "PDF/JPEG/PNG/WebP; max 10 MB"
    }
  }
}
```

Form data example (send the file as binary, not as JSON):

```json
{
  "file": "<binary file: example.pdf or example.png>"
}
```

HTTP 201 — Success

```json
{
  "report": {
    "id": "<report UUID>",
    "profile_id": "<profile UUID>",
    "name": "blood-test.pdf",
    "storage_provider": "cloudinary",
    "url": "<short-lived signed Cloudinary URL>",
    "public_id": "familycare/C000001/profiles/<profile UUID>/child/reports/<report UUID>_blood-test.pdf",
    "folder": "familycare/C000001/profiles/<profile UUID>/child/reports",
    "resource_type": "raw",
    "delivery_type": "authenticated",
    "url_expires_in": 300
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}/reports

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [
    {
      "id": "<report UUID>",
      "profile_id": "<profile UUID>",
      "name": "blood-test.pdf",
      "storage_provider": "cloudinary",
      "url": "<short-lived signed Cloudinary URL>",
      "public_id": "familycare/C000001/profiles/<profile UUID>/child/reports/<report UUID>_blood-test.pdf",
      "folder": "familycare/C000001/profiles/<profile UUID>/child/reports",
      "resource_type": "raw",
      "delivery_type": "authenticated",
      "url_expires_in": 300
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/patients/profiles/{profile_id}/reports/{report_id}/category

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/category`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `report_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}/reports/{report_id}/download

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `report_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "report": {
    "id": "<report UUID>",
    "profile_id": "<profile UUID>",
    "name": "blood-test.pdf",
    "storage_provider": "cloudinary",
    "url": "<short-lived signed Cloudinary URL>",
    "public_id": "familycare/C000001/profiles/<profile UUID>/child/reports/<report UUID>_blood-test.pdf",
    "folder": "familycare/C000001/profiles/<profile UUID>/child/reports",
    "resource_type": "raw",
    "delivery_type": "authenticated",
    "url_expires_in": 300
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/profiles/{profile_id}/reports/{report_id}/import

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/import`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `report_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}/reports/{report_id}/text

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `report_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "analysis": {
    "status": "NOT_REQUESTED",
    "result": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/profiles/{profile_id}/reports/{report_id}/text

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `report_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "source_language": "hi",
  "translate_to_english": false,
  "external_translation_consent": false
}
```

Validation schema: `Options` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "source_language": {
      "default": "hi",
      "maxLength": 8,
      "title": "Source Language",
      "type": "string"
    },
    "translate_to_english": {
      "default": false,
      "title": "Translate To English",
      "type": "boolean"
    },
    "external_translation_consent": {
      "default": false,
      "title": "External Translation Consent",
      "type": "boolean"
    }
  },
  "title": "Options",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 202 — Success; example uses synthetic values

```json
{
  "analysis": {
    "report_id": "<report UUID>",
    "status": "QUEUED",
    "options": {
      "source_language": "hi",
      "translate_to_english": false,
      "external_translation_consent": false
    },
    "result": null,
    "error": null,
    "updated_at": "2026-10-30T00:00:00Z"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/register

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/patients/register`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "full_name": "Example User",
  "email": "user@example.com",
  "mobile_number": "+919876543210",
  "password": "Choose-Your-Password8!",
  "confirm_password": "Choose-Your-Password8!",
  "referral_id": "rahulkumarD000001"
}
```

Validation schema: `PatientRegistration` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    },
    "referral_id": {
      "anyOf": [
        {
          "maxLength": 160,
          "minLength": 1,
          "pattern": "^[A-Za-z0-9]+$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Referral Id"
    }
  },
  "required": [
    "full_name",
    "email",
    "mobile_number",
    "password",
    "confirm_password"
  ],
  "title": "PatientRegistration",
  "type": "object"
}
```

HTTP 202 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent",
  "public_id": null,
  "user_id": null,
  "approval_status": "PENDING_EMAIL_VERIFICATION",
  "message": "OTP sent to your email. Verify OTP to complete registration."
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/report-text/options

Required roles: PATIENT

URL: `http://127.0.0.1:5001/api/v1/patients/report-text/options`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "languages": [
    {
      "code": "hi",
      "name": "Hindi"
    },
    {
      "code": "en",
      "name": "English"
    },
    {
      "code": "mr",
      "name": "Marathi"
    },
    {
      "code": "ne",
      "name": "Nepali"
    },
    {
      "code": "sa",
      "name": "Sanskrit"
    },
    {
      "code": "ta",
      "name": "Tamil"
    },
    {
      "code": "te",
      "name": "Telugu"
    },
    {
      "code": "ur",
      "name": "Urdu"
    },
    {
      "code": "ar",
      "name": "Arabic"
    },
    {
      "code": "fr",
      "name": "French"
    },
    {
      "code": "de",
      "name": "German"
    },
    {
      "code": "es",
      "name": "Spanish"
    },
    {
      "code": "pt",
      "name": "Portuguese"
    },
    {
      "code": "ru",
      "name": "Russian"
    }
  ],
  "max_file_bytes": 10485760,
  "max_pages": 5,
  "target_language": "en",
  "translation_provider": "MyMemory via deep-translator",
  "translation_enabled": true,
  "max_translation_characters": 4000,
  "ocr_engine": "PaddleOCR",
  "configured": false
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/resend-otp

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/patients/resend-otp`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>"
}
```

Validation schema: `Challenge` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    }
  },
  "required": [
    "challenge_token"
  ],
  "title": "Challenge",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/verify-email

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/patients/verify-email`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

Validation schema: `VerifyOTP` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    },
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    }
  },
  "required": [
    "challenge_token",
    "otp"
  ],
  "title": "VerifyOTP",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "access_token": "<signed JWT>",
  "refresh_token": "<opaque refresh token>",
  "expires_in": 900,
  "token_type": "Bearer",
  "user": {
    "id": "<UUID>",
    "public_id": "C000001",
    "role": "PATIENT",
    "full_name": "Example User",
    "email": "user@example.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false,
    "referred_doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/verify-login-otp

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/patients/verify-login-otp`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

Validation schema: `VerifyOTP` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    },
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    }
  },
  "required": [
    "challenge_token",
    "otp"
  ],
  "title": "VerifyOTP",
  "type": "object"
}
```

HTTP 410 — Success

```json
{
  "error": {
    "code": "login_otp_disabled",
    "message": "Sign in with email and password; login OTP is no longer required"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/admin-requests

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/admin-requests`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/admins

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/admins`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
| `search` | query | False | `{"type": "string", "maxLength": 80}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/admins/{user_id}/approve

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/admins/{user_id}/approve`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "approval_status": "APPROVED"
  },
  "email_status": "queued"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/admins/{user_id}/reactivate

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/admins/{user_id}/reactivate`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "account_status": "ACTIVE"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/admins/{user_id}/reject

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/admins/{user_id}/reject`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "reason": "Registration details require correction"
}
```

Validation schema: `Rejection` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "reason": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Reason",
      "type": "string"
    }
  },
  "required": [
    "reason"
  ],
  "title": "Rejection",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "user": {
    "approval_status": "REJECTED"
  },
  "email_status": "queued"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/admins/{user_id}/suspend

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/admins/{user_id}/suspend`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "account_status": "SUSPENDED"
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/audit-logs

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/audit-logs`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/dashboard

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/dashboard`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Organization aggregate summary. Monthly growth contains 12 calendar months; examples abbreviate the series. Counts remain backward compatible.

```json
{
  "counts": [
    {
      "role": "PATIENT",
      "approval_status": "APPROVED",
      "count": 3
    }
  ],
  "as_of": "2026-10-31",
  "metrics": {
    "administrators": {
      "total": 2,
      "this_month": 1
    },
    "doctors": {
      "total": 4,
      "this_month": 1
    },
    "patients": {
      "total": 3,
      "this_month": 1
    },
    "children": {
      "total": 5,
      "this_month": 1
    }
  },
  "monthly_growth": [
    {
      "month": "2026-10",
      "patients": 3,
      "doctors": 4,
      "administrators": 2
    }
  ],
  "recent_registrations": [
    {
      "id": "<UUID>",
      "public_id": "C000001",
      "full_name": "Example Patient",
      "email": "patient@example.com",
      "role": "PATIENT",
      "approval_status": "APPROVED",
      "account_status": "ACTIVE",
      "created_at": "<UTC timestamp>"
    }
  ],
  "pending_requests": {
    "total": 0,
    "items": []
  },
  "recent_activities": [
    {
      "id": "<UUID>",
      "action": "registered",
      "person": "Example Patient",
      "created_at": "<UTC timestamp>"
    }
  ],
  "child_care": {
    "total_children": 5,
    "active_guides": 4,
    "inactive_guides": 1,
    "growth_records": 2,
    "nutrition_records": 3,
    "vaccination_records": 4
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/doctors

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/doctors`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
| `search` | query | False | `{"type": "string", "maxLength": 80}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/doctors/{user_id}

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/doctors/{user_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "user": {
    "id": "<UUID>",
    "public_id": "D000001",
    "full_name": "Example doctor",
    "role": "DOCTOR",
    "approval_status": "APPROVED",
    "doctor": {
      "qualification": "MBBS",
      "images": {}
    }
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/doctors/{user_id}/profiles

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/doctors/{user_id}/profiles`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<profile UUID>",
      "full_name": "Example member",
      "module": "child",
      "owner_id": "<patient UUID>",
      "date_of_birth": "2020-01-01"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/login

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/superadmin/login`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "email": "superadmin@example.com",
  "password": "Choose-Your-Password8!"
}
```

Validation schema: `SuperLogin` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "anyOf": [
        {
          "format": "email",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Email"
    },
    "username": {
      "anyOf": [
        {
          "maxLength": 80,
          "minLength": 1,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Username"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    }
  },
  "required": [
    "password"
  ],
  "title": "SuperLogin",
  "type": "object"
}
```

HTTP 200 — Success

```json
{
  "access_token": "<signed JWT>",
  "refresh_token": "<opaque refresh token>",
  "expires_in": 900,
  "token_type": "Bearer",
  "user": {
    "id": "<UUID>",
    "public_id": "superadmin",
    "role": "SUPERADMIN",
    "full_name": "Example User",
    "email": "user@example.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false
  }
}
```

HTTP 202 — Success

```json
{
  "requires_password_change": true,
  "challenge_token": "<challenge JWT>",
  "expires_in": 600
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/me

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/me`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "user": {
    "id": "<UUID>",
    "public_id": "superadmin",
    "role": "SUPERADMIN",
    "full_name": "Example User",
    "email": "user@example.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/patients

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/patients`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
| `search` | query | False | `{"type": "string", "maxLength": 80}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/patients/{user_id}

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/patients/{user_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "user": {
    "id": "<patient UUID>",
    "public_id": "C000001",
    "full_name": "Example patient",
    "role": "PATIENT",
    "created_at": "2026-10-30T00:00:00Z"
  },
  "profile_counts": {
    "total": 0,
    "members": 0,
    "self": 0,
    "child": 0,
    "adult": 0,
    "women": 0
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/patients/{user_id}/profiles

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/patients/{user_id}/profiles`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "items": [
    {
      "id": "<profile UUID>",
      "profile_type": "member",
      "module": "child",
      "full_name": "Aarav Kumar",
      "date_of_birth": "2018-05-14",
      "parent_profile_id": "<parent profile UUID>",
      "doctor": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/patients/{user_id}/profiles/{profile_id}

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/patients/{user_id}/profiles/{profile_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "child",
    "full_name": "Aarav Kumar",
    "date_of_birth": "2018-05-14",
    "parent_profile_id": "<parent profile UUID>",
    "doctor": null
  }
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/search

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/search`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
| `q` | query | False | `{"type": "string", "maxLength": 80}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Search matches

```json
{
  "items": [
    {
      "id": "<UUID>",
      "public_id": "C000001",
      "full_name": "Example Patient",
      "email": "patient@example.com",
      "role": "PATIENT",
      "approval_status": "APPROVED",
      "account_status": "ACTIVE",
      "created_at": "<UTC timestamp>"
    }
  ]
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/vaccination/audit

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/audit`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/vaccination/import-uip

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/import-uip`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "created": 26,
  "skipped": 0,
  "schedule_type": "UIP",
  "message": "Drafts saved. Independent medical review and admin publication are required."
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/vaccination/reviewers

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/reviewers`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "id": "<doctor UUID>",
      "name": "Example reviewer",
      "qualification": "MBBS",
      "registration": "EXAMPLE-1",
      "council": "Example council"
    }
  ]
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/vaccination/schedules

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/vaccination/schedules

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "child_visible": true,
  "active": true,
  "vaccine_id": "00000000-0000-4000-8000-000000000001",
  "schedule_type": "UIP",
  "dose_code": "Example value",
  "dose_name": "Example value",
  "version": "Example value",
  "age_label": "Example value",
  "age_unit": "days",
  "age_start": 0,
  "age_end": 0,
  "minimum_age": null,
  "maximum_age": null,
  "previous_dose_code": "",
  "minimum_interval_days": null,
  "route": "Oral",
  "injection_site": "",
  "instructions": "",
  "source_url": "https://example.org/guideline",
  "source_reference": "Example value",
  "effective_from": "2026-10-30",
  "effective_to": null,
  "eligibility": {
    "gender": "All",
    "country": "IN",
    "states": [],
    "districts": [],
    "programme": "",
    "requires_clinical_review": true,
    "active": true
  },
  "reminders": {
    "before_days": [],
    "on_due": true,
    "overdue_days": [],
    "language": "en",
    "in_app": true,
    "email": false,
    "enabled": true
  }
}
```

Validation schema: `ScheduleInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    },
    "vaccine_id": {
      "format": "uuid",
      "title": "Vaccine Id",
      "type": "string"
    },
    "schedule_type": {
      "enum": [
        "UIP",
        "IAP"
      ],
      "title": "Schedule Type",
      "type": "string"
    },
    "dose_code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Dose Code",
      "type": "string"
    },
    "dose_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Dose Name",
      "type": "string"
    },
    "version": {
      "maxLength": 80,
      "minLength": 1,
      "title": "Version",
      "type": "string"
    },
    "age_label": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Age Label",
      "type": "string"
    },
    "age_unit": {
      "enum": [
        "days",
        "weeks",
        "months",
        "years"
      ],
      "title": "Age Unit",
      "type": "string"
    },
    "age_start": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age Start",
      "type": "integer"
    },
    "age_end": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age End",
      "type": "integer"
    },
    "minimum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Age"
    },
    "maximum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Maximum Age"
    },
    "previous_dose_code": {
      "default": "",
      "maxLength": 40,
      "pattern": "^(?:[A-Z0-9][A-Z0-9_-]{0,39})?$",
      "title": "Previous Dose Code",
      "type": "string"
    },
    "minimum_interval_days": {
      "anyOf": [
        {
          "maximum": 3650,
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Interval Days"
    },
    "route": {
      "enum": [
        "Oral",
        "IM",
        "ID",
        "SC",
        "Other"
      ],
      "title": "Route",
      "type": "string"
    },
    "injection_site": {
      "default": "",
      "maxLength": 160,
      "title": "Injection Site",
      "type": "string"
    },
    "instructions": {
      "default": "",
      "maxLength": 2000,
      "title": "Instructions",
      "type": "string"
    },
    "source_url": {
      "format": "uri",
      "maxLength": 2083,
      "minLength": 1,
      "title": "Source Url",
      "type": "string"
    },
    "source_reference": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Source Reference",
      "type": "string"
    },
    "effective_from": {
      "format": "date",
      "title": "Effective From",
      "type": "string"
    },
    "effective_to": {
      "anyOf": [
        {
          "format": "date",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Effective To"
    },
    "eligibility": {
      "$ref": "#/components/schemas/EligibilityInput"
    },
    "reminders": {
      "$ref": "#/components/schemas/ReminderInput"
    }
  },
  "required": [
    "vaccine_id",
    "schedule_type",
    "dose_code",
    "dose_name",
    "version",
    "age_label",
    "age_unit",
    "age_start",
    "age_end",
    "route",
    "source_url",
    "source_reference",
    "effective_from"
  ],
  "title": "ScheduleInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/superadmin/vaccination/schedules/{schedule_id}

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "child_visible": true,
  "active": true,
  "vaccine_id": "00000000-0000-4000-8000-000000000001",
  "schedule_type": "UIP",
  "dose_code": "Example value",
  "dose_name": "Example value",
  "version": "Example value",
  "age_label": "Example value",
  "age_unit": "days",
  "age_start": 0,
  "age_end": 0,
  "minimum_age": null,
  "maximum_age": null,
  "previous_dose_code": "",
  "minimum_interval_days": null,
  "route": "Oral",
  "injection_site": "",
  "instructions": "",
  "source_url": "https://example.org/guideline",
  "source_reference": "Example value",
  "effective_from": "2026-10-30",
  "effective_to": null,
  "eligibility": {
    "gender": "All",
    "country": "IN",
    "states": [],
    "districts": [],
    "programme": "",
    "requires_clinical_review": true,
    "active": true
  },
  "reminders": {
    "before_days": [],
    "on_due": true,
    "overdue_days": [],
    "language": "en",
    "in_app": true,
    "email": false,
    "enabled": true
  }
}
```

Validation schema: `ScheduleInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    },
    "vaccine_id": {
      "format": "uuid",
      "title": "Vaccine Id",
      "type": "string"
    },
    "schedule_type": {
      "enum": [
        "UIP",
        "IAP"
      ],
      "title": "Schedule Type",
      "type": "string"
    },
    "dose_code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Dose Code",
      "type": "string"
    },
    "dose_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Dose Name",
      "type": "string"
    },
    "version": {
      "maxLength": 80,
      "minLength": 1,
      "title": "Version",
      "type": "string"
    },
    "age_label": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Age Label",
      "type": "string"
    },
    "age_unit": {
      "enum": [
        "days",
        "weeks",
        "months",
        "years"
      ],
      "title": "Age Unit",
      "type": "string"
    },
    "age_start": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age Start",
      "type": "integer"
    },
    "age_end": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age End",
      "type": "integer"
    },
    "minimum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Age"
    },
    "maximum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Maximum Age"
    },
    "previous_dose_code": {
      "default": "",
      "maxLength": 40,
      "pattern": "^(?:[A-Z0-9][A-Z0-9_-]{0,39})?$",
      "title": "Previous Dose Code",
      "type": "string"
    },
    "minimum_interval_days": {
      "anyOf": [
        {
          "maximum": 3650,
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Interval Days"
    },
    "route": {
      "enum": [
        "Oral",
        "IM",
        "ID",
        "SC",
        "Other"
      ],
      "title": "Route",
      "type": "string"
    },
    "injection_site": {
      "default": "",
      "maxLength": 160,
      "title": "Injection Site",
      "type": "string"
    },
    "instructions": {
      "default": "",
      "maxLength": 2000,
      "title": "Instructions",
      "type": "string"
    },
    "source_url": {
      "format": "uri",
      "maxLength": 2083,
      "minLength": 1,
      "title": "Source Url",
      "type": "string"
    },
    "source_reference": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Source Reference",
      "type": "string"
    },
    "effective_from": {
      "format": "date",
      "title": "Effective From",
      "type": "string"
    },
    "effective_to": {
      "anyOf": [
        {
          "format": "date",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Effective To"
    },
    "eligibility": {
      "$ref": "#/components/schemas/EligibilityInput"
    },
    "reminders": {
      "$ref": "#/components/schemas/ReminderInput"
    }
  },
  "required": [
    "vaccine_id",
    "schedule_type",
    "dose_code",
    "dose_name",
    "version",
    "age_label",
    "age_unit",
    "age_start",
    "age_end",
    "route",
    "source_url",
    "source_reference",
    "effective_from"
  ],
  "title": "ScheduleInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/superadmin/vaccination/schedules/{schedule_id}/eligibility

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/eligibility`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "gender": "All",
  "country": "IN",
  "states": [],
  "districts": [],
  "programme": "",
  "requires_clinical_review": true,
  "active": true
}
```

Validation schema: `EligibilityInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "gender": {
      "default": "All",
      "enum": [
        "All",
        "Girls",
        "Boys"
      ],
      "title": "Gender",
      "type": "string"
    },
    "country": {
      "const": "IN",
      "default": "IN",
      "title": "Country",
      "type": "string"
    },
    "states": {
      "items": {
        "type": "string"
      },
      "maxItems": 40,
      "title": "States",
      "type": "array"
    },
    "districts": {
      "items": {
        "type": "string"
      },
      "maxItems": 200,
      "title": "Districts",
      "type": "array"
    },
    "programme": {
      "default": "",
      "maxLength": 160,
      "title": "Programme",
      "type": "string"
    },
    "requires_clinical_review": {
      "default": true,
      "title": "Requires Clinical Review",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    }
  },
  "title": "EligibilityInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/publish

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/publish`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "PUBLISHED",
    "published_at": "2026-10-30T00:00:00Z",
    "created_by": "<author UUID>",
    "reviewer_id": "<reviewer UUID>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/superadmin/vaccination/schedules/{schedule_id}/reminders

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/reminders`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "before_days": [],
  "on_due": true,
  "overdue_days": [],
  "language": "en",
  "in_app": true,
  "email": false,
  "enabled": true
}
```

Validation schema: `ReminderInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "before_days": {
      "items": {
        "type": "integer"
      },
      "maxItems": 12,
      "title": "Before Days",
      "type": "array"
    },
    "on_due": {
      "default": true,
      "title": "On Due",
      "type": "boolean"
    },
    "overdue_days": {
      "items": {
        "type": "integer"
      },
      "maxItems": 12,
      "title": "Overdue Days",
      "type": "array"
    },
    "language": {
      "default": "en",
      "enum": [
        "en",
        "hi"
      ],
      "title": "Language",
      "type": "string"
    },
    "in_app": {
      "default": true,
      "title": "In App",
      "type": "boolean"
    },
    "email": {
      "default": false,
      "title": "Email",
      "type": "boolean"
    },
    "enabled": {
      "default": true,
      "title": "Enabled",
      "type": "boolean"
    }
  },
  "title": "ReminderInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/retire

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/retire`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "reason": "Example value"
}
```

Validation schema: `RetireInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "reason": {
      "maxLength": 1000,
      "minLength": 10,
      "title": "Reason",
      "type": "string"
    }
  },
  "required": [
    "reason"
  ],
  "title": "RetireInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "RETIRED",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": "<reviewer UUID>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/submit-review

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/submit-review`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "reviewer_id": "00000000-0000-4000-8000-000000000001"
}
```

Validation schema: `AssignReview` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "reviewer_id": {
      "format": "uuid",
      "title": "Reviewer Id",
      "type": "string"
    }
  },
  "required": [
    "reviewer_id"
  ],
  "title": "AssignReview",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "IN_REVIEW",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": "<reviewer UUID>"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PATCH /api/v1/superadmin/vaccination/schedules/{schedule_id}/visibility

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/visibility`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "active": false,
  "child_visible": true
}
```

Validation schema: `ScheduleVisibility` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "active": {
      "title": "Active",
      "type": "boolean"
    },
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    }
  },
  "required": [
    "active"
  ],
  "title": "ScheduleVisibility",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "DRAFT",
    "published_at": null,
    "created_by": "<author UUID>",
    "reviewer_id": null
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/vaccination/vaccines

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/vaccines`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [
    {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/vaccination/vaccines

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/vaccines`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "code": "Example value",
  "name_en": "Example value",
  "name_hi": "",
  "category": "Government",
  "protects_against": "Example value",
  "description_en": "",
  "description_hi": "",
  "active": true
}
```

Validation schema: `VaccineInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Code",
      "type": "string"
    },
    "name_en": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Name En",
      "type": "string"
    },
    "name_hi": {
      "default": "",
      "maxLength": 160,
      "title": "Name Hi",
      "type": "string"
    },
    "category": {
      "enum": [
        "Government",
        "Optional"
      ],
      "title": "Category",
      "type": "string"
    },
    "protects_against": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Protects Against",
      "type": "string"
    },
    "description_en": {
      "default": "",
      "maxLength": 2000,
      "title": "Description En",
      "type": "string"
    },
    "description_hi": {
      "default": "",
      "maxLength": 2000,
      "title": "Description Hi",
      "type": "string"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    }
  },
  "required": [
    "code",
    "name_en",
    "category",
    "protects_against"
  ],
  "title": "VaccineInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 201 — Success; example uses synthetic values

```json
{
  "vaccine": {
    "code": "EXAMPLE_VACCINE",
    "name_en": "Example vaccine",
    "name_hi": "",
    "category": "Government",
    "protects_against": "Source-reviewed indication",
    "description_en": "",
    "description_hi": "",
    "active": true,
    "id": "00000000-0000-4000-8000-000000000001"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/superadmin/vaccination/vaccines/{vaccine_id}

Required roles: SUPERADMIN

URL: `http://127.0.0.1:5001/api/v1/superadmin/vaccination/vaccines/{vaccine_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `vaccine_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
  "code": "Example value",
  "name_en": "Example value",
  "name_hi": "",
  "category": "Government",
  "protects_against": "Example value",
  "description_en": "",
  "description_hi": "",
  "active": true
}
```

Validation schema: `VaccineInput` (included in openapi.json).

```json
{
  "additionalProperties": false,
  "properties": {
    "code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Code",
      "type": "string"
    },
    "name_en": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Name En",
      "type": "string"
    },
    "name_hi": {
      "default": "",
      "maxLength": 160,
      "title": "Name Hi",
      "type": "string"
    },
    "category": {
      "enum": [
        "Government",
        "Optional"
      ],
      "title": "Category",
      "type": "string"
    },
    "protects_against": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Protects Against",
      "type": "string"
    },
    "description_en": {
      "default": "",
      "maxLength": 2000,
      "title": "Description En",
      "type": "string"
    },
    "description_hi": {
      "default": "",
      "maxLength": 2000,
      "title": "Description Hi",
      "type": "string"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    }
  },
  "required": [
    "code",
    "name_en",
    "category",
    "protects_against"
  ],
  "title": "VaccineInput",
  "type": "object"
}
```

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "vaccine": {
    "code": "EXAMPLE_VACCINE",
    "name_en": "Example vaccine",
    "name_hi": "",
    "category": "Government",
    "protects_against": "Source-reviewed indication",
    "description_en": "",
    "description_hi": "",
    "active": true,
    "id": "00000000-0000-4000-8000-000000000001"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/vaccination-schedules

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/vaccination-schedules`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "status": "NOT_AVAILABLE"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/vaccination-schedules/{schedule_id}

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/vaccination-schedules/{schedule_id}`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
    "child_visible": true,
    "active": true,
    "vaccine_id": "00000000-0000-4000-8000-000000000001",
    "schedule_type": "UIP",
    "dose_code": "D1",
    "dose_name": "Example dose",
    "version": "example-v1",
    "age_label": "Source-defined age",
    "age_unit": "days",
    "age_start": 0,
    "age_end": 0,
    "minimum_age": null,
    "maximum_age": null,
    "previous_dose_code": "",
    "minimum_interval_days": null,
    "route": "Other",
    "injection_site": "",
    "instructions": "",
    "source_url": "https://example.org/guideline",
    "source_reference": "Synthetic contract example only",
    "effective_from": "2026-10-30",
    "effective_to": null,
    "eligibility": {
      "gender": "All",
      "country": "IN",
      "states": [],
      "districts": [],
      "programme": "",
      "requires_clinical_review": true,
      "active": true
    },
    "reminders": {
      "before_days": [
        7
      ],
      "on_due": true,
      "overdue_days": [
        7
      ],
      "language": "en",
      "in_app": true,
      "email": false,
      "enabled": true
    },
    "id": "<schedule UUID>",
    "vaccine": {
      "code": "EXAMPLE_VACCINE",
      "name_en": "Example vaccine",
      "name_hi": "",
      "category": "Government",
      "protects_against": "Source-reviewed indication",
      "description_en": "",
      "description_hi": "",
      "active": true,
      "id": "00000000-0000-4000-8000-000000000001"
    },
    "status": "PUBLISHED",
    "published_at": "2026-10-30T00:00:00Z"
  }
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/vaccines

Required roles: public / limited challenge

URL: `http://127.0.0.1:5001/api/v1/vaccines`

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-FamilyCare-Portal` | header | False | `{"type": "string", "enum": ["patient", "doctor"]}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 400 — Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401 — Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403 — Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404 — Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409 — Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422 — Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429 — Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413 — Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415 — Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502 — Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503 — Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

HTTP 200 — Success; example uses synthetic values

```json
{
  "items": [],
  "total": 0,
  "status": "NOT_AVAILABLE"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## Integration notes: CHILD_PLAN_ACTIVATION.md

### Age-based child vaccination plans

Admin and superadmin add a vaccine, then a dose schedule with a name, guideline,
instructions, age unit and start/end age. New schedules default to `active: true`
and `child_visible: true`. For six calendar months use `age_unit: "months"`,
`age_start: 6`, `age_end: 6`. A child born 2026-01-31 sees 2026-07-31.
Calendar month ends are clamped, not approximated as 30 days.

#### Availability

`PATCH /api/v1/admin/vaccination/schedules/{schedule_id}/visibility`

Superadmin uses `/api/v1/superadmin/vaccination/schedules/{schedule_id}/visibility`.
Use the corresponding role's bearer token or authenticated cookie with CSRF.

Request:
```json
{"active": true, "child_visible": true}
```

Response 200:
```json
{"schedule":{"id":"<UUID>","status":"DRAFT","active":true,"child_visible":true}}
```
The actual response contains the complete schedule. `active: false` hides the
version. Retired versions return 409; unauthorized roles return 403; missing
versions return 404; invalid bodies return 422. Existing imported drafts default
to visible unless explicitly disabled. Published versions are
visible by default; this endpoint can deactivate and reactivate them.

`PUT /api/v1/admin/vaccination/vaccines/{vaccine_id}` (or superadmin equivalent)
accepts the full vaccine body including `active`. Deactivating the catalog entry
hides all its doses without deleting saved vaccination history.

#### Child and doctor reads

- Parent: `GET /api/v1/children/{child_id}/vaccinations?schedule_type=UIP&view=all`
- Connected doctor: `GET /api/v1/doctors/care-profiles/{child_id}/vaccination-plan`
  returns the identical child-specific timeline under `UIP` and `IAP`.

Each dose includes `recommended_date`, `window_end`, `publication_status`,
`status`, `display_status`, `instructions`, `vaccine` and source details.
An active unpublished entry has `publication_status: "DRAFT"` (or `IN_REVIEW`,
`APPROVED`) and `status: "REVIEW_REQUIRED"`. It is labelled Doctor Review and
does not send vaccination-due reminders. Activation does not attest to clinical
review. Reviewed, published doses retain the existing reminder/eligibility flow.
An active published version takes precedence over a pending version of the same
vaccine/dose. Refresh the child or doctor page after changing availability.

This is a vaccination plan feature. Medicine prescriptions and their dosage
remain separate doctor workflows.

The connected doctor can use `POST /api/v1/doctors/care-profiles/{child_id}/vaccination-plan`
with `schedule_id`, `decision: "NOT_APPLICABLE"`, substantive `notes` (20+ characters)
and `attestation: true` to deactivate applicability for this child only. `CONFIRM`
restores applicability after parent location/history are recorded. An unpublished
entry still requires schedule medical review even after individual confirmation.
Doctor actions never change other children's plans or the global catalog.


## Integration notes: PUBLIC_PORTAL_SESSIONS.md

### Patient and doctor browser sessions

Cookie clients send `X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare`
and `X-FamilyCare-Portal: patient` or `doctor` on login, reads, refresh and logout.
Use the same portal throughout a workflow. Cookies are HttpOnly:

| Portal | Access cookie | Refresh cookie |
| --- | --- | --- |
| Patient | fc_patient_access | fc_patient_refresh |
| Doctor | fc_doctor_access | fc_doctor_refresh |

Access cookies use `/api/v1`; refresh cookies use `/api/v1/auth`.
Authenticated mutations and refresh require the portal's `X-CSRF-Token`.
Login/refresh returns `csrf_token` without exposing session tokens in JSON.
The web client stores CSRF values separately per portal.

Doctor login/logout no longer replaces the patient's cookie. An old shared
cookie is accepted only for its matching role. If it belongs to another portal,
the API returns HTTP 401 with `error.code: portal_session_changed`; the web app
opens the appropriate login page. Sign in once if an old tab has this error.
Legacy clients without this header and bearer-token app clients keep their
existing contract. Admin/superadmin continue using their existing proxy cookies.

After login, patient vaccination reads use
`GET /api/v1/children/{child_id}/vaccinations?schedule_type=UIP&view=all`
(or IAP). Parent ownership and connected-doctor access checks remain enforced.
Imported drafts without availability flags now default to visible child plans,
labelled Doctor Review. Explicitly disabled doses stay disabled.


## Integration notes: REALTIME_NOTIFICATIONS.md

### Customer and doctor realtime notifications

Local gateway: `ws://127.0.0.1:5002/ws/notifications`.
Production uses `wss://<host>/ws/notifications`; set `VITE_NOTIFICATION_WS_URL`
when the gateway is hosted separately. The proxy must support WebSocket upgrades.
Run the gateway from backend with `venv/Scripts/python.exe -m scripts.notification_socket`.

1. Sign in to the matching patient or approved doctor portal.
2. `POST /api/v1/notifications/socket-ticket` with `{}` and authenticated credentials.
   Cookie clients include their portal header and CSRF token. Response:
   `{"ticket":"<short-lived ticket>","expires_in":60}`.
3. Connect to the gateway and send `{"type":"auth","ticket":"<ticket>"}`.
   Keep the ticket out of URLs and logs.
4. A `ready` event triggers inbox resync. `notification` and `unread_count` events
   trigger updates; reconnect with a fresh ticket after disconnect.

Customer uses the shared `/api/v1/notifications` inbox. Doctor socket events
refresh the existing `/api/v1/doctors/notifications` inbox so its unread/read
state, links and browser-push preferences stay compatible. Doctor events are
mirrored into the shared notification stream by the backend.

Doctor bell panel displays Live / Reconnecting / Sign in required. Both portals
retain 30-second REST resync while visible. Doctor reconnect uses backoff up to
30 seconds and session refresh for socket close code 4401; logout revokes access.
Pending doctors retain their account inbox polling until clinical access approval.

WebSocket alerts require an open connected web/app session. They do not provide
closed-app mobile background push. Doctor browser Web Push is a separate option.


## Integration notes: woman_adule_api.md

### Adult and women family invitations: API request and response guide

Base API: `http://127.0.0.1:5001`. Invite page: `http://127.0.0.1:5173/customer/family-invite`.
All examples use synthetic identities and abbreviated IDs. Replace placeholders. This is implemented API behavior, not a proposal. Delivery tests mock SMTP; inbox delivery is not established by a unit test.

#### Who receives which email?

| Step | Destination | Result |
| --- | --- | --- |
| Family sends adult/women invitation | Invited member's email | One-use setup link with family name/email, relationship and care area |
| Member submits name/email/mobile/DOB/password form | Inviting family's email | Six-digit setup approval OTP; family shares it with the member |
| Member enters correct family approval OTP | No extra OTP email | Creates member PATIENT account, linked profile and authenticated member session atomically |
| Member signs in | No login OTP | Member's own email and password |
| Member chooses forgot password | Member's own email | Password reset OTP; never routed to the inviting family |

`relationship` is from the inviting family's perspective; default is `Family member`. Send a value such as `Mother`, `Father`, `Spouse`, `Sister`, `Brother`, `Son` or `Daughter`. The API accepts a nonblank relationship up to 50 characters.
`module` is exactly `adult` or `women` (not `woman`). These areas accept age 13–120, matching the existing product split after Child Care (0–12). No gender is inferred from an email address.

There is no shared family password. Each member gets their own password hash and user ID. A random 256-bit invitation secret is generated; only its SHA-256 hash is stored. The secret is not a hash of the family's email and is not returned in the create/list responses. It is delivered in the invite email link, in a URL fragment. Keep the secret and API paths containing it out of application/access logs and analytics. Set an appropriate Referrer-Policy at the production web host.

#### Authentication and configuration

Family create/list/revoke: authenticated `PATIENT` access token:

```http
X-Auth-Transport: bearer
Authorization: Bearer <family_access_token>
Content-Type: application/json
```

Browser family clients use HttpOnly cookies, `credentials: include`, `X-Auth-Transport: cookie`, `X-FamilyCare-Portal: patient`, `X-Requested-With: FamilyCare`, plus the login/refresh `X-CSRF-Token` on authenticated mutations.
Preview/setup/verify/resend use the secret link, not a family access token. Browser clients still send the cookie transport guard headers; no authenticated session is required. Do not send or ask members for the family's password.

Deployment:

- Run `venv/Scripts/python.exe -m alembic upgrade head` from `backend` to install migration `0018_family_invitations`.
- Configure SMTP via the existing ignored backend `.env` settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, TLS and credentials).
- Set `FAMILY_INVITE_FRONTEND_URL` to the trusted frontend origin, e.g. `https://your-familycare-host.example`. Local default: `http://127.0.0.1:5173`.
- Invite and approval OTP emails are sent synchronously. `email_status: sent` means SMTP accepted delivery, not proof that it arrived in Inbox.
- Existing forgot-password emails are queued: run `venv/Scripts/python.exe -m scripts.mail_worker` from `backend`.
- Run the notification socket gateway separately for live family-bell updates. A persistent `family_member_joined` notification is created after successful verification.

#### 1. Family creates an invitation

`POST /api/v1/patients/family-invitations`

```json
{
  "full_name": "Example Member",
  "email": "member@example.com",
  "module": "women",
  "relationship": "Mother"
}
```

For adult, send `"module": "adult"`. Omitting `relationship` uses `Family member`.
Do not send member password, DOB or OTP at this step.

HTTP 201:

```json
{
  "invitation": {
    "id": "<invitation UUID>",
    "full_name": "Example Member",
    "email": "member@example.com",
    "module": "women",
    "relationship": "Mother",
    "status": "PENDING",
    "expires_at": "<UTC timestamp, 24 hours later>",
    "profile_id": null
  },
  "email_status": "sent"
}
```

Member email contains `http://127.0.0.1:5173/customer/family-invite#token=<secret>`. Name/email are stored from the family invitation and cannot be replaced during acceptance. Existing account emails return 409; this flow does not silently attach an existing account. Duplicate active invites from the same family/email return 409. Revoke and send again to replace an invite.

#### 2. Family lists or revokes invitations

`GET /api/v1/patients/family-invitations?page=1&per_page=25`

No request body. HTTP 200:

```json
{
  "items": [
    {
      "id": "<invitation UUID>",
      "full_name": "Example Member",
      "email": "member@example.com",
      "module": "women",
      "relationship": "Mother",
      "status": "PENDING",
      "expires_at": "<UTC timestamp>",
      "profile_id": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Statuses: `PENDING`, `ACCEPTED`, `REVOKED`, `EXPIRED`. Accepted entries include `profile_id`.

`DELETE /api/v1/patients/family-invitations/{invite_id}`

No request body. HTTP 200: `{"message":"Invitation revoked"}`.
Only the inviting family can revoke. Already accepted returns 409; this is not an endpoint for removing an accepted member or deleting their account.

#### 3. Member opens the link

Frontend reads the secret from the URL fragment and calls:

`GET /api/v1/family-invitations/{token}`

No request body or login required. HTTP 200:

```json
{
  "invitation": {
    "id": "<invitation UUID>",
    "full_name": "Example Member",
    "email": "member@example.com",
    "module": "women",
    "relationship": "Mother",
    "status": "PENDING",
    "expires_at": "<UTC timestamp>",
    "profile_id": null
  },
  "family": {"full_name": "Example Family", "email": "family@example.com"},
  "form": {"full_name": "Example Member", "email": "member@example.com", "readonly": ["full_name", "email"]},
  "otp_destination": "inviting_family_email",
  "shared_profile": true
}
```

The page clearly names the inviting family and explains shared-profile access before submission. Invalid secret returns 404. Expired, revoked or consumed link returns 410. Invite lifetime: 24 hours; only one successful acceptance.

#### 4. Member submits profile setup

`POST /api/v1/family-invitations/{token}/setup`

```json
{
  "full_name": "Example Member",
  "email": "member@example.com",
  "mobile_number": "+919876543211",
  "date_of_birth": "1995-02-28",
  "password": "Choose-Your-Password8!",
  "confirm_password": "Choose-Your-Password8!"
}
```

HTTP 202:

```json
{
  "message": "Approval OTP sent to the inviting family email.",
  "email_status": "sent",
  "otp_destination": "inviting_family_email",
  "expires_in": 300,
  "resend_after": 60
}
```

Name/email must match the invitation. Mobile is 8–15 digits with optional leading `+`; password is 8–128 characters and confirmation must match. The form requires explicit acceptance of the family/profile sharing relationship. Before OTP verification, no member User or CareProfile is created. Pending setup stores an Argon2 password hash and HMAC OTP hash, never plaintext password/OTP. Link possession proves access to the member's invitation inbox; the approval OTP proves the family's approval. There is no second member-email signup OTP in this flow.

#### 5. Resend family approval OTP

`POST /api/v1/family-invitations/{token}/resend-otp`

Body: `{}`. Response: same HTTP 202 shape as setup. Destination is still `family@example.com`, not member email. Wait 60 seconds; a fresh OTP replaces the previous one. The setup form must have been submitted first (otherwise 409). Resubmitting setup after the cooldown also replaces pending values and OTP.

#### 6. Member enters the OTP shared by the family

`POST /api/v1/family-invitations/{token}/verify-otp`

```json
{"otp":"123456"}
```

HTTP 201 (representative response):

```json
{
  "message": "Profile setup complete. Opening your profile.",
  "access_token": "<member JWT; bearer mode only>",
  "refresh_token": "<member refresh token; bearer mode only>",
  "token_type": "Bearer",
  "expires_in": 900,
  "redirect_url": "/customer/women/dashboard",
  "user": {
    "id": "<member UUID>",
    "public_id": "C000002",
    "full_name": "Example Member",
    "email": "member@example.com",
    "phone_number": "+919876543211",
    "role": "PATIENT",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false,
    "referred_doctor": null
  },
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "women",
    "full_name": "Example Member",
    "date_of_birth": "1995-02-28",
    "member_email": "member@example.com",
    "relationship": "Mother",
    "linked_member": true,
    "parent_profile_id": null,
    "guardian_contact": "",
    "guardian_name": "",
    "emergency_contacts": [],
    "doctor": null,
    "created_at": "<UTC timestamp>"
  },
  "family": {"full_name":"Example Family", "relationship":"Mother"}
}
```

The account, profile and membership are committed together. Five wrong OTP attempts exhaust the current code. OTP expiry: five minutes. Used links cannot be replayed. Verification immediately signs the member in. Cookie mode sets the member's HttpOnly patient cookies and returns csrf_token; bearer mode returns member tokens. The UI saves the new CSRF token and replaces the invite page with redirect_url, removing the secret link from the current page. The setup password remains unchanged and no immediate password change is required. If the browser was signed in as the inviting family, this browser's patient cookies now belong to the member; the family can sign in again to its own account. Other independent family sessions are not revoked.

The care profile belongs to the inviting family and is accessible by both family and the accepted member. The member only gains access to that specific profile, not the family's children, other adults, women, invitation list or family account settings. Doctor access still requires an explicit referral. Shared server records/reports use the existing APIs. Existing women's diary entries remain browser-local; this change does not convert those entries into server-synced data.

#### 7. Member login and own care profile

`POST /api/v1/patients/login`

```json
{"email":"member@example.com","password":"Choose-Your-Password8!"}
```

HTTP 200 for bearer mode (user fields as above):

```json
{
  "access_token":"<member access JWT>",
  "refresh_token":"<member refresh token>",
  "token_type":"Bearer",
  "expires_in":900,
  "user":{"id":"<member UUID>","public_id":"C000002","role":"PATIENT","email":"member@example.com"}
}
```

User object above is abbreviated. Cookie mode omits tokens from JSON, sets HttpOnly cookies and returns `csrf_token`. Login has no OTP. After login:

- `GET /api/v1/patients/profiles?module=women` (or `adult`) returns the linked profile under `items` with pagination.
- `GET /api/v1/patients/profiles/{profile_id}` returns `{"profile":{...}}`.
- Existing `/patients/profiles/{profile_id}/reports` APIs work for this shared profile.
- Existing `/patients/adults/{profile_id}/records` APIs work for adult profiles. Methods/bodies are detailed in ALL_APIS.md.
- `GET /api/v1/patients/me` identifies the member's own account.

#### 8. Forgot password: OTP to member email

`POST /api/v1/auth/forgot-password`

```json
{"email":"member@example.com"}
```

HTTP 202:

```json
{
  "message":"If an eligible account exists, reset instructions are queued.",
  "challenge_token":"<reset challenge JWT>",
  "expires_in":300,
  "resend_after":60,
  "email_status":"queued"
}
```

The existing mail worker resolves the member account's email. It does not use the family invite's owner email. Unknown/unavailable emails receive an indistinguishable API response.

`POST /api/v1/auth/reset-password`

```json
{
  "challenge_token":"<reset challenge JWT>",
  "otp":"123456",
  "new_password":"New-Password8!",
  "confirm_password":"New-Password8!"
}
```

HTTP 200: `{"message":"Password reset. Sign in again."}`. Existing sessions are revoked. Sign in again using the member's email and new password. To resend reset OTP use existing `POST /api/v1/auth/resend-otp` with `{"challenge_token":"<reset challenge JWT>"}`.

#### Error responses

| HTTP | Examples / behavior |
| --- | --- |
| 400 | `invalid_otp`, `otp_unavailable` (expired/exhausted code) |
| 401/403 | Family token/session missing, wrong role, account suspended or cookie CSRF denied |
| 404 | Invalid invite secret, inaccessible profile or another family's invite |
| 409 | `account_exists`, `invite_exists`, `setup_required`, `invite_accepted` |
| 410 | `invite_unavailable` (expired/revoked/accepted link or unavailable family) |
| 422 | Validation, name/email mismatch, age outside 13–120, bad mobile or password confirmation |
| 429 | `otp_cooldown` or public endpoint request throttling |
| 503 | `email_delivery_failed`; no successful account creation is reported |

```json
{"error":{"code":"invalid_otp","message":"Invalid OTP"}}
```

#### UI entry points and validation

Family dashboard includes an invite form and invitation list with revoke/refresh actions. Adding another adult/women member uses this invite form. Self profiles and child profiles preserve existing flows. The email link opens the prefilled member form and OTP step. Successful OTP verification automatically opens the member?s adult/women dashboard. Once accepted, the shared profile appears in the matching adult/women workspace for both accounts.

Automated tests: `venv/Scripts/python.exe -m pytest tests/test_family_invitations.py -q` from `backend`. Tests use isolated database fixtures and mocked SMTP, covering both modules, locked invite identity, OTP destinations, expiry, attempts, resend, replay, shared access, unrelated-family denial and member password reset.


## Integration notes: Growth_Nutrition_API.md

### Growth & Nutrition API: age-based child guidance

Base URL: `http://127.0.0.1:5001`. JSON examples use synthetic identities.

#### Implemented behavior

- Your supplied Growth & Nutrition text is preserved in `backend/content/child_growth_nutrition_source.md` and converted into structured, versioned educational content in `backend/content/child_growth_nutrition.json`.
- Every existing/new child gets the guide **active by default**. No batch assignment, doctor connection, or manual activation is required for initial visibility.
- Age is calculated from the child's saved DOB using the India product calendar on every read. Clients do not submit or override age.
- There are 24 continuous, nonoverlapping age bands: 12 monthly bands in the first year, then one yearly band for each completed age 1 through 12. Exactly age 13 returns `OUT_OF_SCOPE` and no guide. The supplied 11–12-year content also covers completed age 12 until the 13th birthday.
- Only the currently connected doctor can activate/deactivate **this child's educational guide**. A change does not change another child's guide or the global source content.
- Deactivation returns `guide: null`; it does not delete or disable saved growth measurements, meal notes, existing diary APIs or doctor notes.
- Parent/other doctors/admins cannot use the doctor visibility endpoint. A doctor who is disconnected immediately loses this permission.
- Parents see the guidance on Child Care → Growth & nutrition. Doctors see it with Activate/Deactivate controls under Child Care → Growth or Nutrition.

#### Authentication

Bearer/mobile:

```http
X-Auth-Transport: bearer
Authorization: Bearer <patient_or_doctor_access_token>
Content-Type: application/json
```

Browser: HttpOnly cookies, `credentials: include`, `X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare`, and `X-FamilyCare-Portal: patient` or `doctor`. Doctor PATCH additionally requires that doctor's `X-CSRF-Token` from login/refresh.

`profile_id` is the child's CareProfile UUID. Parent access requires ownership; doctor access requires the current referral connection. Public/unauthenticated access is not provided.

#### 1. Parent reads the child's current guide

`GET /api/v1/children/{profile_id}/growth-nutrition-guide`

Request body: none. No age, module or active parameter is accepted from the client.

HTTP 200 (abbreviated representative body):

```json
{
  "child": {
    "id": "<child UUID>",
    "full_name": "Example Child",
    "date_of_birth": "2026-02-28",
    "age": {
      "completed_years": 0,
      "remaining_months": 8,
      "remaining_days": 3,
      "total_completed_months": 8,
      "total_days": 245,
      "display": "0 years 8 months 3 days",
      "primary_category": "INFANT",
      "secondary_categories": [],
      "in_child_module_scope": true
    }
  },
  "active": true,
  "default_active": true,
  "status": "AVAILABLE",
  "updated_at": null,
  "updated_by": null,
  "version": "2026-10-31.v1",
  "age_band": {
    "id": "month-8",
    "label": "8–9 Months",
    "min_months": 8,
    "max_months_exclusive": 9
  },
  "guide": {
    "title": "Growth & Nutrition Guide for Children (0–12 Years)",
    "nutrition": {
      "id": "month-8",
      "min_months": 8,
      "max_months_exclusive": 9,
      "label": "8–9 Months",
      "foods": "Soft rice, lentils, fully cooked eggs, and fruits",
      "meal_frequency": "2–3 meals daily",
      "blocks": [{"type":"paragraph","text":"Example educational paragraph from the supplied guide."}]
    },
    "growth_monitoring": [],
    "food_safety": [],
    "sources": [
      {"title":"WHO infant and young child feeding","url":"https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding"}
    ],
    "provenance": "User-supplied educational guide; not an individual diagnosis or prescribed meal plan.",
    "notice": "General educational guidance. Your clinician adapts it for allergies, feeding difficulties, prematurity or other needs. Growth needs age- and sex-appropriate charts, not adult BMI cutoffs. No supplement dose or individual calorie target is generated."
  }
}
```

The actual response includes the complete matching age content, growth-monitoring guidance, food-safety sections and references. Empty arrays and the example paragraph above abbreviate those parts; see the full generated response in `ALL_APIS.md`, `all-api.md` or OpenAPI JSON. `default_active` describes initial policy; `active` is the child's saved effective setting.

##### Block format for rendering

No raw HTML is required. Render these structured block types:

```json
[
  {"type":"heading","text":"Recommended foods"},
  {"type":"paragraph","text":"Educational text"},
  {"type":"list","items":["First item","Second item"]},
  {"type":"table","headers":["Food","Preparation"],"rows":[["Lentils","Cook thoroughly"]]}
]
```

Content contains the supplied text; inline `**bold**` markers may occur. The UI safely renders text, lists and tables; it does not inject HTML.

#### 2. Connected doctor reads the same child guide

`GET /api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide`

Request body: none. Doctor access token/cookie required.
HTTP 200: identical response shape and age selection as the parent endpoint. A doctor cannot read an unconnected child's guide.

#### 3. Doctor deactivates or activates for the selected child

`PATCH /api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide/visibility`

Deactivate request:

```json
{"active":false}
```

Activate request:

```json
{"active":true}
```

Use a JSON boolean; strings such as `"false"` or numeric values are rejected.
No POST endpoint is needed: use PATCH to change the setting and GET to read guidance.

HTTP 200 after deactivation (child object abbreviated):

```json
{
  "child": {"id":"<child UUID>","full_name":"Example Child","date_of_birth":"2026-02-28","age":{"total_completed_months":8}},
  "active": false,
  "default_active": true,
  "status": "INACTIVE",
  "updated_at": "<UTC timestamp>",
  "updated_by": "<connected doctor UUID>",
  "version": "2026-10-31.v1"
}
```

The PATCH response includes the complete child/age object but no content payload. Fetch either GET endpoint again to see effective guidance:

```json
{
  "child": {"id":"<child UUID>"},
  "active": false,
  "default_active": true,
  "status": "INACTIVE",
  "updated_at": "<UTC timestamp>",
  "updated_by": "<connected doctor UUID>",
  "version": "2026-10-31.v1",
  "age_band": null,
  "guide": null
}
```

Reactivation exposes the content for the child's **current** age, not a cached age at the time of deactivation. Setting persists across restarts. The family receives a persistent in-app `growth_nutrition_updated` notice with `profile_id` and `area: growth`; live delivery uses the existing notification gateway. An audit action records the doctor change.

#### Statuses and errors

| Status / HTTP | Meaning |
| --- | --- |
| `AVAILABLE` / 200 | Active and age is under 13; guide included |
| `INACTIVE` / 200 | Doctor deactivated this child's guide; no educational content returned |
| `OUT_OF_SCOPE` / 200 | Active child profile has reached age 13; no guide returned |
| 401 | Invalid/missing session or token |
| 403 | Wrong role or cookie CSRF failure |
| 404 | Child missing/deleted, owned by another family, not a child profile, or not connected to this doctor |
| 422 | Missing/invalid active boolean, extra fields or invalid JSON |
| 503 | Database unavailable or migration not installed |

```json
{"error":{"code":"child_not_found","message":"Child profile not found"}}
```

An inaccessible profile can instead return `profile_not_found` to avoid exposing its existence. There is no global activate/deactivate API in this feature.

#### Supplied text and scope

The source guide's age-wise foods, meal ideas, nutrients, food preparation, safety and growth-monitoring information are available as educational content. For the eight-month infant row, the supplied quantity note is supplemented with the WHO 6–8-month meal-frequency guidance. Source references are included in the response. Breastfeeding/food-safety and growth-reference sources were checked; the guide is not marked as an individual doctor's prescription.

App feature suggestions in section 15 of the pasted text are preserved in the source file. They are not automatically represented as already implemented nutrient calculations, WHO percentiles, sex-specific growth curves, dietary prescriptions, allergy tracking or new head-circumference APIs. Existing diary/measurement routes remain documented separately. There is no automatic malnutrition diagnosis, supplement dose or calorie prescription.

References:

- [WHO infant and young child feeding](https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding)
- [ICMR–NIN Dietary Guidelines for Indians 2024](https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf)
- [WHO Child Growth Standards](https://www.who.int/tools/child-growth-standards)
- [WHO growth reference 5–19 years](https://www.who.int/tools/growth-reference-data-for-5to19-years)

#### Setup and regeneration

From `backend`:

1. `venv/Scripts/python.exe -m alembic upgrade head` applies `0019_child_growth_nutrition`.
2. Restart the API.
3. Rebuild content after an intentional source edit: `venv/Scripts/python.exe scripts/build_growth_nutrition_content.py`.
4. Regenerate API docs: `venv/Scripts/python.exe scripts/export_full_api.py`.

Tests: `venv/Scripts/python.exe -m pytest tests/test_growth_nutrition_guide.py -q` from `backend`. Tests cover all 24 age bands, default-active behavior, age 13 boundary, doctor scope, strict booleans, toggles, cross-family denial and continued measurement access while disabled.


## Complete validation schema appendix

All referenced component schemas are included below so this Markdown file can be shared on its own. `$ref` values point to another named schema in this appendix.

### Schema: AdultInput

```json
{
  "additionalProperties": false,
  "properties": {
    "kind": {
      "enum": [
        "bp",
        "glucose",
        "lipids",
        "medicine",
        "lifestyle",
        "screening",
        "history",
        "consultation_request",
        "reminder"
      ],
      "title": "Kind",
      "type": "string"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "status": {
      "default": "Recorded",
      "enum": [
        "Recorded",
        "Planned",
        "Completed"
      ],
      "title": "Status",
      "type": "string"
    },
    "systolic": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 400,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Systolic"
    },
    "diastolic": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 300,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Diastolic"
    },
    "pulse": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 350,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Pulse"
    },
    "glucose": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 2000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Glucose"
    },
    "total": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 3000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Total"
    },
    "ldl": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 3000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Ldl"
    },
    "hdl": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 1000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Hdl"
    },
    "triglycerides": {
      "anyOf": [
        {
          "exclusiveMinimum": 0,
          "maximum": 5000,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Triglycerides"
    },
    "minutes": {
      "anyOf": [
        {
          "maximum": 1440,
          "minimum": 0,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minutes"
    },
    "context": {
      "default": "",
      "maxLength": 160,
      "title": "Context",
      "type": "string"
    }
  },
  "required": [
    "kind",
    "title",
    "date"
  ],
  "title": "AdultInput",
  "type": "object"
}
```

### Schema: AssignReview

```json
{
  "additionalProperties": false,
  "properties": {
    "reviewer_id": {
      "format": "uuid",
      "title": "Reviewer Id",
      "type": "string"
    }
  },
  "required": [
    "reviewer_id"
  ],
  "title": "AssignReview",
  "type": "object"
}
```

### Schema: CareProfileCreate

```json
{
  "additionalProperties": false,
  "properties": {
    "profile_type": {
      "enum": [
        "self",
        "member"
      ],
      "title": "Profile Type",
      "type": "string"
    },
    "module": {
      "enum": [
        "child",
        "adult",
        "women"
      ],
      "title": "Module",
      "type": "string"
    },
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "date_of_birth": {
      "format": "date",
      "title": "Date Of Birth",
      "type": "string"
    },
    "parent_profile_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Parent Profile Id"
    },
    "guardian_name": {
      "default": "",
      "maxLength": 120,
      "title": "Guardian Name",
      "type": "string"
    },
    "guardian_contact": {
      "default": "",
      "maxLength": 20,
      "pattern": "^(?:\\+?[1-9][0-9]{7,14})?$",
      "title": "Guardian Contact",
      "type": "string"
    },
    "emergency_contacts": {
      "items": {
        "$ref": "#/components/schemas/EmergencyContact"
      },
      "maxItems": 5,
      "title": "Emergency Contacts",
      "type": "array"
    },
    "referral_id": {
      "anyOf": [
        {
          "maxLength": 160,
          "minLength": 1,
          "pattern": "^[A-Za-z0-9]+$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Referral Id"
    }
  },
  "required": [
    "profile_type",
    "module",
    "full_name",
    "date_of_birth"
  ],
  "title": "CareProfileCreate",
  "type": "object"
}
```

### Schema: CareProfileEdit

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "guardian_contact": {
      "default": "",
      "maxLength": 20,
      "pattern": "^(?:\\+?[1-9][0-9]{7,14})?$",
      "title": "Guardian Contact",
      "type": "string"
    }
  },
  "required": [
    "full_name"
  ],
  "title": "CareProfileEdit",
  "type": "object"
}
```

### Schema: CareProfileReferral

```json
{
  "additionalProperties": false,
  "properties": {
    "referral_id": {
      "maxLength": 160,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9]+$",
      "title": "Referral Id",
      "type": "string"
    }
  },
  "required": [
    "referral_id"
  ],
  "title": "CareProfileReferral",
  "type": "object"
}
```

### Schema: CareProfileUpdate

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "date_of_birth": {
      "format": "date",
      "title": "Date Of Birth",
      "type": "string"
    },
    "guardian_name": {
      "default": "",
      "maxLength": 120,
      "title": "Guardian Name",
      "type": "string"
    },
    "guardian_contact": {
      "default": "",
      "maxLength": 20,
      "pattern": "^(?:\\+?[1-9][0-9]{7,14})?$",
      "title": "Guardian Contact",
      "type": "string"
    },
    "emergency_contacts": {
      "items": {
        "$ref": "#/components/schemas/EmergencyContact"
      },
      "maxItems": 5,
      "title": "Emergency Contacts",
      "type": "array"
    }
  },
  "required": [
    "full_name",
    "date_of_birth"
  ],
  "title": "CareProfileUpdate",
  "type": "object"
}
```

### Schema: Challenge

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    }
  },
  "required": [
    "challenge_token"
  ],
  "title": "Challenge",
  "type": "object"
}
```

### Schema: ChangePassword

```json
{
  "additionalProperties": false,
  "properties": {
    "current_password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Current Password",
      "type": "string"
    },
    "new_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "New Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    }
  },
  "required": [
    "current_password",
    "new_password",
    "confirm_password"
  ],
  "title": "ChangePassword",
  "type": "object"
}
```

### Schema: ChildContextInput

```json
{
  "additionalProperties": false,
  "properties": {
    "country": {
      "const": "IN",
      "title": "Country",
      "type": "string"
    },
    "state": {
      "default": "",
      "maxLength": 120,
      "title": "State",
      "type": "string"
    },
    "district": {
      "default": "",
      "maxLength": 120,
      "title": "District",
      "type": "string"
    },
    "gender": {
      "default": "Unknown",
      "enum": [
        "Unknown",
        "Girls",
        "Boys"
      ],
      "title": "Gender",
      "type": "string"
    },
    "history_status": {
      "default": "UNKNOWN",
      "enum": [
        "UNKNOWN",
        "PARENT_REPORTED"
      ],
      "title": "History Status",
      "type": "string"
    },
    "email_reminders": {
      "default": false,
      "title": "Email Reminders",
      "type": "boolean"
    }
  },
  "required": [
    "country"
  ],
  "title": "ChildContextInput",
  "type": "object"
}
```

### Schema: ConnectDoctor

```json
{
  "additionalProperties": false,
  "properties": {
    "referral_id": {
      "maxLength": 160,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9]+$",
      "title": "Referral Id",
      "type": "string"
    }
  },
  "required": [
    "referral_id"
  ],
  "title": "ConnectDoctor",
  "type": "object"
}
```

### Schema: Decision

```json
{
  "additionalProperties": false,
  "properties": {
    "schedule_id": {
      "format": "uuid",
      "title": "Schedule Id",
      "type": "string"
    },
    "decision": {
      "enum": [
        "CONFIRM",
        "NOT_APPLICABLE"
      ],
      "title": "Decision",
      "type": "string"
    },
    "notes": {
      "maxLength": 2000,
      "minLength": 20,
      "title": "Notes",
      "type": "string"
    },
    "attestation": {
      "title": "Attestation",
      "type": "boolean"
    }
  },
  "required": [
    "schedule_id",
    "decision",
    "notes",
    "attestation"
  ],
  "title": "Decision",
  "type": "object"
}
```

### Schema: DoctorProfileSetup

```json
{
  "additionalProperties": false,
  "properties": {
    "setup_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Setup Token",
      "type": "string"
    },
    "qualification": {
      "maxLength": 200,
      "minLength": 2,
      "title": "Qualification",
      "type": "string"
    },
    "medical_registration_number": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$",
      "title": "Medical Registration Number",
      "type": "string"
    },
    "registering_council": {
      "maxLength": 200,
      "minLength": 2,
      "title": "Registering Council",
      "type": "string"
    },
    "specialization": {
      "anyOf": [
        {
          "maxLength": 200,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Specialization"
    },
    "nmr_id": {
      "anyOf": [
        {
          "maxLength": 100,
          "minLength": 1,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Nmr Id"
    },
    "address": {
      "maxLength": 1000,
      "minLength": 5,
      "title": "Address",
      "type": "string"
    },
    "clinic_address": {
      "maxLength": 1000,
      "minLength": 5,
      "title": "Clinic Address",
      "type": "string"
    },
    "years_of_experience": {
      "maximum": 80,
      "minimum": 0,
      "title": "Years Of Experience",
      "type": "integer"
    }
  },
  "required": [
    "setup_token",
    "qualification",
    "medical_registration_number",
    "registering_council",
    "address",
    "clinic_address",
    "years_of_experience"
  ],
  "title": "DoctorProfileSetup",
  "type": "object"
}
```

### Schema: DoctorRegistration

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    },
    "qualification": {
      "anyOf": [
        {
          "maxLength": 200,
          "minLength": 2,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Qualification"
    },
    "medical_registration_number": {
      "anyOf": [
        {
          "pattern": "^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Medical Registration Number"
    },
    "registering_council": {
      "anyOf": [
        {
          "maxLength": 200,
          "minLength": 2,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Registering Council"
    },
    "specialization": {
      "anyOf": [
        {
          "maxLength": 200,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Specialization"
    },
    "nmr_id": {
      "anyOf": [
        {
          "maxLength": 100,
          "minLength": 1,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Nmr Id"
    }
  },
  "required": [
    "full_name",
    "email",
    "mobile_number",
    "password",
    "confirm_password"
  ],
  "title": "DoctorRegistration",
  "type": "object"
}
```

### Schema: EligibilityInput

```json
{
  "additionalProperties": false,
  "properties": {
    "gender": {
      "default": "All",
      "enum": [
        "All",
        "Girls",
        "Boys"
      ],
      "title": "Gender",
      "type": "string"
    },
    "country": {
      "const": "IN",
      "default": "IN",
      "title": "Country",
      "type": "string"
    },
    "states": {
      "items": {
        "type": "string"
      },
      "maxItems": 40,
      "title": "States",
      "type": "array"
    },
    "districts": {
      "items": {
        "type": "string"
      },
      "maxItems": 200,
      "title": "Districts",
      "type": "array"
    },
    "programme": {
      "default": "",
      "maxLength": 160,
      "title": "Programme",
      "type": "string"
    },
    "requires_clinical_review": {
      "default": true,
      "title": "Requires Clinical Review",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    }
  },
  "title": "EligibilityInput",
  "type": "object"
}
```

### Schema: EmergencyContact

```json
{
  "additionalProperties": false,
  "properties": {
    "name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Name",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "relationship": {
      "maxLength": 50,
      "minLength": 1,
      "title": "Relationship",
      "type": "string"
    }
  },
  "required": [
    "name",
    "mobile_number",
    "relationship"
  ],
  "title": "EmergencyContact",
  "type": "object"
}
```

### Schema: FamilyInvite

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "module": {
      "enum": [
        "adult",
        "women"
      ],
      "title": "Module",
      "type": "string"
    },
    "relationship": {
      "default": "Family member",
      "maxLength": 50,
      "minLength": 1,
      "title": "Relationship",
      "type": "string"
    }
  },
  "required": [
    "full_name",
    "email",
    "module"
  ],
  "title": "FamilyInvite",
  "type": "object"
}
```

### Schema: FamilyOTP

```json
{
  "additionalProperties": false,
  "properties": {
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    }
  },
  "required": [
    "otp"
  ],
  "title": "FamilyOTP",
  "type": "object"
}
```

### Schema: FamilySetup

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    },
    "date_of_birth": {
      "format": "date",
      "title": "Date Of Birth",
      "type": "string"
    }
  },
  "required": [
    "full_name",
    "email",
    "mobile_number",
    "password",
    "confirm_password",
    "date_of_birth"
  ],
  "title": "FamilySetup",
  "type": "object"
}
```

### Schema: ForgotPassword

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    }
  },
  "required": [
    "email"
  ],
  "title": "ForgotPassword",
  "type": "object"
}
```

### Schema: GuideVisibility

```json
{
  "additionalProperties": false,
  "properties": {
    "active": {
      "title": "Active",
      "type": "boolean"
    }
  },
  "required": [
    "active"
  ],
  "title": "GuideVisibility",
  "type": "object"
}
```

### Schema: InitialPassword

```json
{
  "additionalProperties": false,
  "properties": {
    "current_password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Current Password",
      "type": "string"
    },
    "new_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "New Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    },
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    }
  },
  "required": [
    "current_password",
    "new_password",
    "confirm_password",
    "challenge_token"
  ],
  "title": "InitialPassword",
  "type": "object"
}
```

### Schema: Login

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    }
  },
  "required": [
    "email",
    "password"
  ],
  "title": "Login",
  "type": "object"
}
```

### Schema: MedicalReview

```json
{
  "additionalProperties": false,
  "properties": {
    "decision": {
      "enum": [
        "APPROVE",
        "REJECT"
      ],
      "title": "Decision",
      "type": "string"
    },
    "notes": {
      "maxLength": 2000,
      "minLength": 20,
      "title": "Notes",
      "type": "string"
    },
    "attestation": {
      "title": "Attestation",
      "type": "boolean"
    }
  },
  "required": [
    "decision",
    "notes",
    "attestation"
  ],
  "title": "MedicalReview",
  "type": "object"
}
```

### Schema: Options

```json
{
  "additionalProperties": false,
  "properties": {
    "source_language": {
      "default": "hi",
      "maxLength": 8,
      "title": "Source Language",
      "type": "string"
    },
    "translate_to_english": {
      "default": false,
      "title": "Translate To English",
      "type": "boolean"
    },
    "external_translation_consent": {
      "default": false,
      "title": "External Translation Consent",
      "type": "boolean"
    }
  },
  "title": "Options",
  "type": "object"
}
```

### Schema: PatientRegistration

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    },
    "referral_id": {
      "anyOf": [
        {
          "maxLength": 160,
          "minLength": 1,
          "pattern": "^[A-Za-z0-9]+$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Referral Id"
    }
  },
  "required": [
    "full_name",
    "email",
    "mobile_number",
    "password",
    "confirm_password"
  ],
  "title": "PatientRegistration",
  "type": "object"
}
```

### Schema: PreferencesInput

```json
{
  "additionalProperties": false,
  "properties": {
    "in_app": {
      "title": "In App",
      "type": "boolean"
    }
  },
  "required": [
    "in_app"
  ],
  "title": "PreferencesInput",
  "type": "object"
}
```

### Schema: RecordInput

```json
{
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "anyOf": [
        {
          "pattern": "^[a-fA-F0-9-]{36}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Source Id"
    },
    "title": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "date": {
      "format": "date",
      "title": "Date",
      "type": "string"
    },
    "status": {
      "default": "",
      "maxLength": 32,
      "title": "Status",
      "type": "string"
    },
    "nextDate": {
      "default": "",
      "maxLength": 10,
      "title": "Nextdate",
      "type": "string"
    },
    "provider": {
      "default": "",
      "maxLength": 160,
      "title": "Provider",
      "type": "string"
    },
    "notes": {
      "default": "",
      "maxLength": 2000,
      "title": "Notes",
      "type": "string"
    },
    "category": {
      "default": "",
      "maxLength": 160,
      "title": "Category",
      "type": "string"
    },
    "weight": {
      "default": "",
      "maxLength": 12,
      "title": "Weight",
      "type": "string"
    },
    "height": {
      "default": "",
      "maxLength": 12,
      "title": "Height",
      "type": "string"
    },
    "meal": {
      "default": "",
      "maxLength": 160,
      "title": "Meal",
      "type": "string"
    },
    "vaccine_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Vaccine Id"
    },
    "schedule_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Schedule Id"
    },
    "dose_code": {
      "default": "",
      "maxLength": 40,
      "title": "Dose Code",
      "type": "string"
    },
    "schedule_type": {
      "default": "",
      "maxLength": 8,
      "title": "Schedule Type",
      "type": "string"
    },
    "vaccinator": {
      "default": "",
      "maxLength": 160,
      "title": "Vaccinator",
      "type": "string"
    },
    "batch_number": {
      "default": "",
      "maxLength": 100,
      "title": "Batch Number",
      "type": "string"
    },
    "certificate_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Certificate Id"
    }
  },
  "required": [
    "title",
    "date"
  ],
  "title": "RecordInput",
  "type": "object"
}
```

### Schema: RefreshRequest

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "refresh_token"
  ],
  "properties": {
    "refresh_token": {
      "type": "string",
      "maxLength": 512
    }
  }
}
```

### Schema: Registration

```json
{
  "additionalProperties": false,
  "properties": {
    "full_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Full Name",
      "type": "string"
    },
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "mobile_number": {
      "pattern": "^\\+?[1-9][0-9]{7,14}$",
      "title": "Mobile Number",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    }
  },
  "required": [
    "full_name",
    "email",
    "mobile_number",
    "password",
    "confirm_password"
  ],
  "title": "Registration",
  "type": "object"
}
```

### Schema: Rejection

```json
{
  "additionalProperties": false,
  "properties": {
    "reason": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Reason",
      "type": "string"
    }
  },
  "required": [
    "reason"
  ],
  "title": "Rejection",
  "type": "object"
}
```

### Schema: ReminderInput

```json
{
  "additionalProperties": false,
  "properties": {
    "before_days": {
      "items": {
        "type": "integer"
      },
      "maxItems": 12,
      "title": "Before Days",
      "type": "array"
    },
    "on_due": {
      "default": true,
      "title": "On Due",
      "type": "boolean"
    },
    "overdue_days": {
      "items": {
        "type": "integer"
      },
      "maxItems": 12,
      "title": "Overdue Days",
      "type": "array"
    },
    "language": {
      "default": "en",
      "enum": [
        "en",
        "hi"
      ],
      "title": "Language",
      "type": "string"
    },
    "in_app": {
      "default": true,
      "title": "In App",
      "type": "boolean"
    },
    "email": {
      "default": false,
      "title": "Email",
      "type": "boolean"
    },
    "enabled": {
      "default": true,
      "title": "Enabled",
      "type": "boolean"
    }
  },
  "title": "ReminderInput",
  "type": "object"
}
```

### Schema: ResetPassword

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    },
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    },
    "new_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "New Password",
      "type": "string"
    },
    "confirm_password": {
      "maxLength": 128,
      "minLength": 8,
      "title": "Confirm Password",
      "type": "string"
    }
  },
  "required": [
    "challenge_token",
    "otp",
    "new_password",
    "confirm_password"
  ],
  "title": "ResetPassword",
  "type": "object"
}
```

### Schema: Resubmission

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    },
    "qualification": {
      "maxLength": 200,
      "minLength": 2,
      "title": "Qualification",
      "type": "string"
    },
    "medical_registration_number": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$",
      "title": "Medical Registration Number",
      "type": "string"
    },
    "registering_council": {
      "maxLength": 200,
      "minLength": 2,
      "title": "Registering Council",
      "type": "string"
    }
  },
  "required": [
    "email",
    "password",
    "qualification",
    "medical_registration_number",
    "registering_council"
  ],
  "title": "Resubmission",
  "type": "object"
}
```

### Schema: RetireInput

```json
{
  "additionalProperties": false,
  "properties": {
    "reason": {
      "maxLength": 1000,
      "minLength": 10,
      "title": "Reason",
      "type": "string"
    }
  },
  "required": [
    "reason"
  ],
  "title": "RetireInput",
  "type": "object"
}
```

### Schema: ScheduleInput

```json
{
  "additionalProperties": false,
  "properties": {
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    },
    "vaccine_id": {
      "format": "uuid",
      "title": "Vaccine Id",
      "type": "string"
    },
    "schedule_type": {
      "enum": [
        "UIP",
        "IAP"
      ],
      "title": "Schedule Type",
      "type": "string"
    },
    "dose_code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Dose Code",
      "type": "string"
    },
    "dose_name": {
      "maxLength": 120,
      "minLength": 1,
      "title": "Dose Name",
      "type": "string"
    },
    "version": {
      "maxLength": 80,
      "minLength": 1,
      "title": "Version",
      "type": "string"
    },
    "age_label": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Age Label",
      "type": "string"
    },
    "age_unit": {
      "enum": [
        "days",
        "weeks",
        "months",
        "years"
      ],
      "title": "Age Unit",
      "type": "string"
    },
    "age_start": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age Start",
      "type": "integer"
    },
    "age_end": {
      "maximum": 10000,
      "minimum": 0,
      "title": "Age End",
      "type": "integer"
    },
    "minimum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Age"
    },
    "maximum_age": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Maximum Age"
    },
    "previous_dose_code": {
      "default": "",
      "maxLength": 40,
      "pattern": "^(?:[A-Z0-9][A-Z0-9_-]{0,39})?$",
      "title": "Previous Dose Code",
      "type": "string"
    },
    "minimum_interval_days": {
      "anyOf": [
        {
          "maximum": 3650,
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Minimum Interval Days"
    },
    "route": {
      "enum": [
        "Oral",
        "IM",
        "ID",
        "SC",
        "Other"
      ],
      "title": "Route",
      "type": "string"
    },
    "injection_site": {
      "default": "",
      "maxLength": 160,
      "title": "Injection Site",
      "type": "string"
    },
    "instructions": {
      "default": "",
      "maxLength": 2000,
      "title": "Instructions",
      "type": "string"
    },
    "source_url": {
      "format": "uri",
      "maxLength": 2083,
      "minLength": 1,
      "title": "Source Url",
      "type": "string"
    },
    "source_reference": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Source Reference",
      "type": "string"
    },
    "effective_from": {
      "format": "date",
      "title": "Effective From",
      "type": "string"
    },
    "effective_to": {
      "anyOf": [
        {
          "format": "date",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Effective To"
    },
    "eligibility": {
      "$ref": "#/components/schemas/EligibilityInput"
    },
    "reminders": {
      "$ref": "#/components/schemas/ReminderInput"
    }
  },
  "required": [
    "vaccine_id",
    "schedule_type",
    "dose_code",
    "dose_name",
    "version",
    "age_label",
    "age_unit",
    "age_start",
    "age_end",
    "route",
    "source_url",
    "source_reference",
    "effective_from"
  ],
  "title": "ScheduleInput",
  "type": "object"
}
```

### Schema: ScheduleVisibility

```json
{
  "additionalProperties": false,
  "properties": {
    "active": {
      "title": "Active",
      "type": "boolean"
    },
    "child_visible": {
      "default": true,
      "title": "Child Visible",
      "type": "boolean"
    }
  },
  "required": [
    "active"
  ],
  "title": "ScheduleVisibility",
  "type": "object"
}
```

### Schema: SuperLogin

```json
{
  "additionalProperties": false,
  "properties": {
    "email": {
      "anyOf": [
        {
          "format": "email",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Email"
    },
    "username": {
      "anyOf": [
        {
          "maxLength": 80,
          "minLength": 1,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Username"
    },
    "password": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Password",
      "type": "string"
    }
  },
  "required": [
    "password"
  ],
  "title": "SuperLogin",
  "type": "object"
}
```

### Schema: VaccineInput

```json
{
  "additionalProperties": false,
  "properties": {
    "code": {
      "pattern": "^[A-Z0-9][A-Z0-9_-]{0,39}$",
      "title": "Code",
      "type": "string"
    },
    "name_en": {
      "maxLength": 160,
      "minLength": 1,
      "title": "Name En",
      "type": "string"
    },
    "name_hi": {
      "default": "",
      "maxLength": 160,
      "title": "Name Hi",
      "type": "string"
    },
    "category": {
      "enum": [
        "Government",
        "Optional"
      ],
      "title": "Category",
      "type": "string"
    },
    "protects_against": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Protects Against",
      "type": "string"
    },
    "description_en": {
      "default": "",
      "maxLength": 2000,
      "title": "Description En",
      "type": "string"
    },
    "description_hi": {
      "default": "",
      "maxLength": 2000,
      "title": "Description Hi",
      "type": "string"
    },
    "active": {
      "default": true,
      "title": "Active",
      "type": "boolean"
    }
  },
  "required": [
    "code",
    "name_en",
    "category",
    "protects_against"
  ],
  "title": "VaccineInput",
  "type": "object"
}
```

### Schema: VerifyOTP

```json
{
  "additionalProperties": false,
  "properties": {
    "challenge_token": {
      "maxLength": 4096,
      "minLength": 1,
      "title": "Challenge Token",
      "type": "string"
    },
    "otp": {
      "pattern": "^\\d{6}$",
      "title": "Otp",
      "type": "string"
    }
  },
  "required": [
    "challenge_token",
    "otp"
  ],
  "title": "VerifyOTP",
  "type": "object"
}
```

## Operational endpoints outside the versioned REST inventory

- `GET /health`: liveness; example `{"auth":"flask-jwt","service":"familycare-backend","status":"ok"}`.
- `GET /api/v1/health/ready`: database/schema readiness; documented in the inventory.
- `GET /api/docs`: JSON route inventory.
- `GET /api/openapi.json`: OpenAPI JSON contract.
- WebSocket `/ws/notifications`: see realtime integration above; not a REST method.

## Files and regeneration

- `ALL_APIS.md`: this complete single-file human-readable reference.
- `openapi.json`: machine-readable companion.
- `postman_collection.json`: importable request collection.
- Regenerate: from backend, `venv/Scripts/python.exe scripts/export_full_api.py`.

Total registered API method operations: **220**.
