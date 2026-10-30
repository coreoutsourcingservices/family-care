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
- In-app child reminders refresh while the page is visible. This does not implement a child WebSocket/background mobile push channel.

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
| `/api/v1/doctors/approval-status` | — | Yes | — | — | — |
| `/api/v1/doctors/care-profiles` | Yes | — | — | — | — |
| `/api/v1/doctors/care-profiles/{profile_id}` | Yes | — | — | — | — |
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
| `/api/v1/health` | Yes | — | — | — | — |
| `/api/v1/health/ready` | Yes | — | — | — | — |
| `/api/v1/patients/adults/{profile_id}/records` | Yes | Yes | — | — | — |
| `/api/v1/patients/adults/{profile_id}/records/{record_id}` | Yes | Yes | — | Yes | Yes |
| `/api/v1/patients/adults/{profile_id}/records/{record_id}/delete` | — | Yes | — | — | — |
| `/api/v1/patients/connect-doctor` | — | Yes | — | — | — |
| `/api/v1/patients/doctor` | Yes | — | — | — | — |
| `/api/v1/patients/login` | — | Yes | — | — | — |
| `/api/v1/patients/me` | Yes | — | — | — | — |
| `/api/v1/patients/profiles` | Yes | Yes | — | — | — |
| `/api/v1/patients/profiles/{profile_id}` | Yes | — | Yes | — | — |
| `/api/v1/patients/profiles/{profile_id}/connect-doctor` | — | Yes | — | — | — |
| `/api/v1/patients/profiles/{profile_id}/doctor` | — | — | — | — | Yes |
| `/api/v1/patients/profiles/{profile_id}/reports` | Yes | Yes | — | — | — |
| `/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download` | Yes | — | — | — | — |
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
| `/api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw` | — | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/vaccines` | Yes | Yes | — | — | — |
| `/api/v1/superadmin/vaccination/vaccines/{vaccine_id}` | — | — | Yes | — | — |
| `/api/v1/vaccination-schedules` | Yes | — | — | — | — |
| `/api/v1/vaccination-schedules/{schedule_id}` | Yes | — | — | — | — |
| `/api/v1/vaccines` | Yes | — | — | — | — |

## GET /api/v1/admin/dashboard

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/doctor-requests

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/doctors

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/doctors/{user_id}

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/doctors/{user_id}/check

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/doctors/{user_id}/profiles

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/doctors/{user_id}/reject

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/doctors/{user_id}/suspend

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/login

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/me

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/patients

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/patients/{user_id}

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/patients/{user_id}/profiles/{profile_id}

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/register

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/resend-otp

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/admin/vaccination/audit

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
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

HTTP 201 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/withdraw

Required roles: ADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `vaccine_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/admin/verify-login-otp

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/change-password

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/forgot-password

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/initial-password

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/logout

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "Logged out"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/logout-all

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success

```json
{
  "message": "All sessions revoked"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/refresh

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/request-email-verification

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/resend-otp

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/auth/reset-password

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/auth/sessions

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/auth/sessions/{session_id}

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `session_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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
        "remaining_days": 29,
        "total_completed_months": 81,
        "total_days": 2494,
        "display": "6 years 9 months 29 days",
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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
      "remaining_days": 29,
      "total_completed_months": 81,
      "total_days": 2494,
      "display": "6 years 9 months 29 days",
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success; example uses synthetic values

```json
{
  "age": {
    "completed_years": 6,
    "remaining_months": 9,
    "remaining_days": 29,
    "total_completed_months": 81,
    "total_days": 2494,
    "display": "6 years 9 months 29 days",
    "primary_category": "SCHOOL_AGE",
    "secondary_categories": [],
    "in_child_module_scope": true
  },
  "as_of_date": "2026-10-30"
}
```

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/care-notes

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/children/{child_id}/growth

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `child_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

## POST /api/v1/doctors/approval-status

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles

Required roles: DOCTOR

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}

Required roles: DOCTOR

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/records

Required roles: DOCTOR

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download

Required roles: DOCTOR

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `report_id` | path | True | `{"type": "string"}` |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/care-profiles/{profile_id}/vaccination-plan

Required roles: DOCTOR

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/login

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/me

Required roles: DOCTOR

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `notification_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/profile-photo

Required roles: DOCTOR

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/register

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/resend-otp

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/resubmit

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/doctors/setup-images

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/doctors/vaccination-reviews

Required roles: DOCTOR

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/health

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/health/ready

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/adults/{profile_id}/records

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `record_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/doctor

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/login

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/me

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/profiles

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## PUT /api/v1/patients/profiles/{profile_id}

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/profiles/{profile_id}/connect-doctor

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## DELETE /api/v1/patients/profiles/{profile_id}/doctor

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

## POST /api/v1/patients/profiles/{profile_id}/reports

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}/reports

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `profile_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}/reports/{report_id}/download

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `report_id` | path | True | `{"type": "string"}` |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/profiles/{profile_id}/reports/{report_id}/text

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `report_id` | path | True | `{"type": "string"}` |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `report_id` | path | True | `{"type": "string"}` |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/patients/report-text/options

Required roles: PATIENT

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/verify-email

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/patients/verify-login-otp

Required roles: public / limited challenge

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/admin-requests

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/admins

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/admins/{user_id}/approve

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/admins/{user_id}/reactivate

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/admins/{user_id}/reject

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## POST /api/v1/superadmin/admins/{user_id}/suspend

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/audit-logs

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/dashboard

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/doctors

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/doctors/{user_id}

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/me

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/patients

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/patients/{user_id}

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `page` | query | False | `{"type": "integer", "minimum": 1, "default": 1}` |
| `per_page` | query | False | `{"type": "integer", "minimum": 1, "maximum": 100, "default": 25}` |
| `module` | query | False | `{"type": "string", "enum": ["child", "adult", "women"]}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/patients/{user_id}/profiles/{profile_id}

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | `{"type": "string"}` |
| `profile_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.

```json
{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}
```

## GET /api/v1/superadmin/vaccination/audit

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
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

HTTP 201 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |

Request: **application/json**

```json
{
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw

Required roles: SUPERADMIN

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `vaccine_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `schedule_id` | path | True | `{"type": "string"}` |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

HTTP 200 — Success; example uses synthetic values

```json
{
  "schedule": {
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

| Parameter | Location | Required | Schema |
| --- | --- | --- | --- |
| `X-Auth-Transport` | header | False | `{"type": "string", "enum": ["bearer", "cookie"], "default": "bearer"}` |
| `X-Requested-With` | header | False | `{"type": "string"}` |
| `X-CSRF-Token` | header | False | `{"type": "string"}` |
Request body: none, or `{}` for a bodyless POST action.

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

## Files and regeneration

- `openapi.json`: full machine-readable schema and response examples.
- `postman_collection.json`: importable request collection.
- Live contract: `/api/openapi.json`; route inventory: `/api/docs`.
- Regenerate: from backend, `venv/Scripts/python.exe scripts/export_full_api.py`.

Total registered API method operations: **192**.
