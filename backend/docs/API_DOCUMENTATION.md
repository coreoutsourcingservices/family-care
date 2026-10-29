# Family Care API reference

Base URL: `http://127.0.0.1:5001` (local only).

Backend API reference. Next.js admin/superadmin UI is in admin/ on port 3005; patient/doctor UI is not included.

OpenAPI: `GET /api/openapi.json`. JSON API index: `GET /api/docs`.

All JSON requests use `Content-Type: application/json`.
Mobile/CLI: `Authorization: Bearer <access_token>` for protected endpoints.
Browser: `X-Auth-Transport: cookie`, credentials enabled, `X-Requested-With: FamilyCare` on mutations;
also send the returned `csrf_token` as `X-CSRF-Token` on authenticated mutations and refresh.
Cookie sessions return no access/refresh tokens in JSON. Refresh rotates the CSRF token too.

Passwords: 8-128 characters; `confirm_password` must match. Roles/public IDs/status are server owned.
All dates are stored as UTC. Public IDs or UUIDs may be used for `{user_id}`.
List routes support `page=1&per_page=25` (maximum 100); user lists accept `status` approval filter.

Signup sends email OTP synchronously and stores temporary details in a TTL cache, not PostgreSQL.
No user/profile/OTP/audit/outbox rows are inserted until signup OTP verification succeeds.
Register returns null public_id/user_id; IDs are assigned only after verification.
SMTP acceptance returns email_status sent; delivery failure returns 503 email_delivery_failed.
Patient verification issues a JWT session; admin/doctor verification queues approval.
All roles sign in with email + password; no login OTP. Approval/verification requirements still apply.
Superadmin supports email login (legacy username remains accepted); first login requires password rotation.
OTP: 6 digits, 5 minutes, 60-second resend cooldown, 5 attempts, one-time use.
After a consumed/exhausted signup challenge, restart with `/auth/request-email-verification`.
Forgot password is generic for unknown accounts. Registration conflicts can reveal existing accounts.
Signup mail is sent directly; sent means SMTP accepted it, not a guarantee of inbox placement.
Reset/approval mail still uses the outbox and requires the separate SMTP worker.

Access JWT default: 15 minutes. Refresh session: 7 days with rotation and replay revocation.
Logout, suspension and password change revoke sessions; reactivation does not restore old sessions.
On concurrent refresh, only one succeeds; reuse revokes that session. Clients must serialize refresh.

## All API URLs

| Method | Local URL | Access |
|---|---|---|
| POST | `http://127.0.0.1:5001/api/v1/auth/refresh` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/auth/logout` | Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/auth/logout-all` | Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/auth/forgot-password` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/auth/reset-password` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/auth/change-password` | Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/auth/initial-password` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/auth/sessions` | Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/auth/sessions/{session_id}` | Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/auth/request-email-verification` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/auth/resend-otp` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/doctors/login` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/doctors/me` | Required roles: DOCTOR |
| POST | `http://127.0.0.1:5001/api/v1/doctors/register` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/doctors/verify-email` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/doctors/resend-otp` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/doctors/approval-status` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/doctors/resubmit` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/doctors/referral` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/doctors/patients` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/doctors/care-profiles` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/reports` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/doctors/practice-profile` | Required roles: DOCTOR |
| PUT | `http://127.0.0.1:5001/api/v1/doctors/practice-profile` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/doctors/care-profiles/{profile_id}/records` | Required roles: DOCTOR |
| POST | `http://127.0.0.1:5001/api/v1/patients/login` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/patients/me` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/register` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/verify-email` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/resend-otp` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/verify-login-otp` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/connect-doctor` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/doctor` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/patients/doctor` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/profiles` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/connect-doctor` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/report-text/options` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/doctor` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/import` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/imported-records` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/admin/login` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/admin/me` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/register` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/admin/verify-email` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/admin/resend-otp` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/admin/verify-login-otp` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/admin/dashboard` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/doctor-requests` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/doctors` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/approve` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/reject` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/suspend` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/doctors/{user_id}/reactivate` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/patients` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/patients/{user_id}` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/patients/{user_id}/profiles` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/patients/{user_id}/profiles/{profile_id}` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/login` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/me` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/dashboard` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/admin-requests` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/admins` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/admins/{user_id}/approve` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/admins/{user_id}/reject` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/admins/{user_id}/suspend` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/admins/{user_id}/reactivate` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/doctors` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/patients` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/patients/{user_id}` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/patients/{user_id}/profiles` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/patients/{user_id}/profiles/{profile_id}` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/audit-logs` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/children` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/age` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/records` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/dashboard` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/health-guide` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/upcoming` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/reminders` | Required roles: PATIENT |
| PUT | `http://127.0.0.1:5001/api/v1/children/{child_id}/reminder-preferences` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/vaccines` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/doctors/consultation-requests` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/vaccination-schedules` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history/{record_id}` | Required roles: PATIENT |
| PATCH | `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccinations/history/{record_id}` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history/{record_id}` | Required roles: PATIENT |
| PATCH | `http://127.0.0.1:5001/api/v1/children/{child_id}/medical-history/{record_id}` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/growth` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/children/{child_id}/growth` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/children/{child_id}/growth/{record_id}` | Required roles: PATIENT |
| PATCH | `http://127.0.0.1:5001/api/v1/children/{child_id}/growth/{record_id}` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition/{record_id}` | Required roles: PATIENT |
| PATCH | `http://127.0.0.1:5001/api/v1/children/{child_id}/nutrition/{record_id}` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations/{record_id}` | Required roles: PATIENT |
| PATCH | `http://127.0.0.1:5001/api/v1/children/{child_id}/consultations/{record_id}` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes/{record_id}` | Required roles: PATIENT |
| PATCH | `http://127.0.0.1:5001/api/v1/children/{child_id}/care-notes/{record_id}` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests` | Required roles: PATIENT, DOCTOR |
| POST | `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests` | Required roles: PATIENT |
| DELETE | `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests/{record_id}` | Required roles: PATIENT |
| PATCH | `http://127.0.0.1:5001/api/v1/children/{child_id}/consultation-requests/{record_id}` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/vaccination-schedules/{schedule_id}` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccination-context` | Required roles: PATIENT |
| PUT | `http://127.0.0.1:5001/api/v1/children/{child_id}/vaccination-context` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/doctors/vaccination-reviews` | Required roles: DOCTOR |
| POST | `http://127.0.0.1:5001/api/v1/doctors/vaccination-reviews/{schedule_id}` | Required roles: DOCTOR |
| GET | `http://127.0.0.1:5001/api/v1/admin/vaccination/vaccines` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/vaccination/vaccines` | Required roles: ADMIN |
| PUT | `http://127.0.0.1:5001/api/v1/admin/vaccination/vaccines/{vaccine_id}` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules` | Required roles: ADMIN |
| PUT | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}` | Required roles: ADMIN |
| PUT | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/eligibility` | Required roles: ADMIN |
| PUT | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/reminders` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/vaccination/reviewers` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/submit-review` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/withdraw` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/publish` | Required roles: ADMIN |
| POST | `http://127.0.0.1:5001/api/v1/admin/vaccination/schedules/{schedule_id}/retire` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/admin/vaccination/audit` | Required roles: ADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/vaccines` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/vaccines` | Required roles: SUPERADMIN |
| PUT | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/vaccines/{vaccine_id}` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules` | Required roles: SUPERADMIN |
| PUT | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}` | Required roles: SUPERADMIN |
| PUT | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/eligibility` | Required roles: SUPERADMIN |
| PUT | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/reminders` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/reviewers` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/submit-review` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/publish` | Required roles: SUPERADMIN |
| POST | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/schedules/{schedule_id}/retire` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/superadmin/vaccination/audit` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/health` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/health/ready` | Required roles: public / limited challenge |

## POST /api/v1/auth/refresh

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `refresh_token` | yes | `{"type": "string", "maxLength": 512}` |

Request JSON:

```json
{
  "refresh_token": "<refresh_token>"
}
```

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/refresh', data: {"refresh_token": "<refresh_token>"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/refresh', 'POST', {"refresh_token": "<refresh_token>"});
```

## POST /api/v1/auth/logout

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Logged out"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/logout', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/logout', 'POST', undefined);
```

## POST /api/v1/auth/logout-all

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "All sessions revoked"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/logout-all', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/logout-all', 'POST', undefined);
```

## POST /api/v1/auth/forgot-password

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `email` | yes | `{"format": "email", "type": "string"}` |

Request JSON:

```json
{
  "email": "user@example.com"
}
```

HTTP 202: Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "queued",
  "message": "If an eligible account exists, reset instructions are queued."
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/forgot-password', data: {"email": "user@example.com"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/forgot-password', 'POST', {"email": "user@example.com"});
```

## POST /api/v1/auth/reset-password

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |
| `otp` | yes | `{"pattern": "^\\d{6}$", "type": "string"}` |
| `new_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `confirm_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456",
  "new_password": "New-Password8!",
  "confirm_password": "New-Password8!"
}
```

HTTP 200: Success

```json
{
  "message": "Password reset. Sign in again."
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/reset-password', data: {"challenge_token": "<challenge_token>", "otp": "123456", "new_password": "New-Password8!", "confirm_password": "New-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/reset-password', 'POST', {"challenge_token": "<challenge_token>", "otp": "123456", "new_password": "New-Password8!", "confirm_password": "New-Password8!"});
```

## POST /api/v1/auth/change-password

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

Request fields:

| Field | Required | Validation |
|---|---|---|
| `current_password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |
| `new_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `confirm_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |

Request JSON:

```json
{
  "current_password": "Old-Password8!",
  "new_password": "New-Password8!",
  "confirm_password": "New-Password8!"
}
```

HTTP 200: Success

```json
{
  "message": "Password changed. All sessions revoked; sign in again."
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/change-password', data: {"current_password": "Old-Password8!", "new_password": "New-Password8!", "confirm_password": "New-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/change-password', 'POST', {"current_password": "Old-Password8!", "new_password": "New-Password8!", "confirm_password": "New-Password8!"});
```

## POST /api/v1/auth/initial-password

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `current_password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |
| `new_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `confirm_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "current_password": "Old-Password8!",
  "new_password": "New-Password8!",
  "confirm_password": "New-Password8!",
  "challenge_token": "<challenge_token>"
}
```

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/initial-password', data: {"current_password": "Old-Password8!", "new_password": "New-Password8!", "confirm_password": "New-Password8!", "challenge_token": "<challenge_token>"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/initial-password', 'POST', {"current_password": "Old-Password8!", "new_password": "New-Password8!", "confirm_password": "New-Password8!", "challenge_token": "<challenge_token>"});
```

## GET /api/v1/auth/sessions

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/sessions', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/sessions', 'GET', undefined);
```

## DELETE /api/v1/auth/sessions/{session_id}

Required roles: SUPERADMIN, ADMIN, DOCTOR, PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/sessions/{session_id}', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/sessions/{session_id}', 'DELETE', undefined);
```

## POST /api/v1/auth/request-email-verification

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `email` | yes | `{"format": "email", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

HTTP 202: Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/request-email-verification', data: {"email": "user@example.com", "password": "Choose-Your-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/request-email-verification', 'POST', {"email": "user@example.com", "password": "Choose-Your-Password8!"});
```

## POST /api/v1/auth/resend-otp

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>"
}
```

HTTP 200: Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/auth/resend-otp', data: {"challenge_token": "<challenge_token>"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/auth/resend-otp', 'POST', {"challenge_token": "<challenge_token>"});
```

## POST /api/v1/doctors/login

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `email` | yes | `{"format": "email", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/login', data: {"email": "user@example.com", "password": "Choose-Your-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/login', 'POST', {"email": "user@example.com", "password": "Choose-Your-Password8!"});
```

## GET /api/v1/doctors/me

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

```json
{
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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/me', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/me', 'GET', undefined);
```

## POST /api/v1/doctors/register

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `full_name` | yes | `{"maxLength": 120, "minLength": 1, "type": "string"}` |
| `email` | yes | `{"format": "email", "type": "string"}` |
| `mobile_number` | yes | `{"pattern": "^\\+?[1-9][0-9]{7,14}$", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `confirm_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `qualification` | no | `{"anyOf": [{"maxLength": 200, "minLength": 2, "type": "string"}, {"type": "null"}], "default": null}` |
| `medical_registration_number` | yes | `{"pattern": "^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$", "type": "string"}` |
| `registering_council` | yes | `{"maxLength": 200, "minLength": 2, "type": "string"}` |
| `specialization` | no | `{"anyOf": [{"maxLength": 200, "type": "string"}, {"type": "null"}], "default": null}` |
| `nmr_id` | no | `{"anyOf": [{"maxLength": 100, "minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` |

Request JSON:

```json
{
  "full_name": "Example User",
  "email": "user@example.com",
  "mobile_number": "+919876543210",
  "password": "Choose-Your-Password8!",
  "confirm_password": "Choose-Your-Password8!",
  "qualification": "MBBS",
  "medical_registration_number": "EXAMPLE-12345",
  "registering_council": "Example Medical Council",
  "specialization": "General Medicine"
}
```

HTTP 202: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/register', data: {"full_name": "Example User", "email": "user@example.com", "mobile_number": "+919876543210", "password": "Choose-Your-Password8!", "confirm_password": "Choose-Your-Password8!", "qualification": "MBBS", "medical_registration_number": "EXAMPLE-12345", "registering_council": "Example Medical Council", "specialization": "General Medicine"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/register', 'POST', {"full_name": "Example User", "email": "user@example.com", "mobile_number": "+919876543210", "password": "Choose-Your-Password8!", "confirm_password": "Choose-Your-Password8!", "qualification": "MBBS", "medical_registration_number": "EXAMPLE-12345", "registering_council": "Example Medical Council", "specialization": "General Medicine"});
```

## POST /api/v1/doctors/verify-email

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |
| `otp` | yes | `{"pattern": "^\\d{6}$", "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

HTTP 202: Success

```json
{
  "message": "Email verified. Waiting for approval.",
  "user": {
    "approval_status": "PENDING_APPROVAL"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/verify-email', data: {"challenge_token": "<challenge_token>", "otp": "123456"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/verify-email', 'POST', {"challenge_token": "<challenge_token>", "otp": "123456"});
```

## POST /api/v1/doctors/resend-otp

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>"
}
```

HTTP 200: Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/resend-otp', data: {"challenge_token": "<challenge_token>"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/resend-otp', 'POST', {"challenge_token": "<challenge_token>"});
```

## POST /api/v1/doctors/approval-status

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `email` | yes | `{"format": "email", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

HTTP 200: Success

```json
{
  "public_id": "D000001",
  "email_verified": true,
  "approval_status": "PENDING_APPROVAL",
  "account_status": "ACTIVE",
  "rejection_reason": null
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/approval-status', data: {"email": "user@example.com", "password": "Choose-Your-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/approval-status', 'POST', {"email": "user@example.com", "password": "Choose-Your-Password8!"});
```

## POST /api/v1/doctors/resubmit

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `email` | yes | `{"format": "email", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |
| `qualification` | no | `{"anyOf": [{"maxLength": 200, "minLength": 2, "type": "string"}, {"type": "null"}], "default": null}` |
| `medical_registration_number` | yes | `{"pattern": "^[A-Za-z0-9][A-Za-z0-9/ ._-]{1,99}$", "type": "string"}` |
| `registering_council` | yes | `{"maxLength": 200, "minLength": 2, "type": "string"}` |

Request JSON:

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!",
  "qualification": "MBBS",
  "medical_registration_number": "EXAMPLE-12345",
  "registering_council": "Example Medical Council"
}
```

HTTP 202: Success

```json
{
  "message": "Resubmitted for review",
  "user": {
    "approval_status": "PENDING_APPROVAL"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/resubmit', data: {"email": "user@example.com", "password": "Choose-Your-Password8!", "qualification": "MBBS", "medical_registration_number": "EXAMPLE-12345", "registering_council": "Example Medical Council"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/resubmit', 'POST', {"email": "user@example.com", "password": "Choose-Your-Password8!", "qualification": "MBBS", "medical_registration_number": "EXAMPLE-12345", "registering_council": "Example Medical Council"});
```

## GET /api/v1/doctors/referral

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/referral', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/referral', 'GET', undefined);
```

## GET /api/v1/doctors/patients

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/patients', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/patients', 'GET', undefined);
```

## GET /api/v1/doctors/care-profiles

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/care-profiles', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/care-profiles', 'GET', undefined);
```

## GET /api/v1/doctors/care-profiles/{profile_id}

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/care-profiles/{profile_id}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/care-profiles/{profile_id}', 'GET', undefined);
```

## GET /api/v1/doctors/care-profiles/{profile_id}/reports

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/care-profiles/{profile_id}/reports', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/care-profiles/{profile_id}/reports', 'GET', undefined);
```

## GET /api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download', 'GET', undefined);
```

## GET /api/v1/doctors/practice-profile

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/practice-profile', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/practice-profile', 'GET', undefined);
```

## PUT /api/v1/doctors/practice-profile

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/practice-profile', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/practice-profile', 'PUT', undefined);
```

## GET /api/v1/doctors/care-profiles/{profile_id}/records

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/care-profiles/{profile_id}/records', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/care-profiles/{profile_id}/records', 'GET', undefined);
```

## POST /api/v1/patients/login

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `email` | yes | `{"format": "email", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/login', data: {"email": "user@example.com", "password": "Choose-Your-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/login', 'POST', {"email": "user@example.com", "password": "Choose-Your-Password8!"});
```

## GET /api/v1/patients/me

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/me', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/me', 'GET', undefined);
```

## POST /api/v1/patients/register

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `full_name` | yes | `{"maxLength": 120, "minLength": 1, "type": "string"}` |
| `email` | yes | `{"format": "email", "type": "string"}` |
| `mobile_number` | yes | `{"pattern": "^\\+?[1-9][0-9]{7,14}$", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `confirm_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `referral_id` | no | `{"anyOf": [{"maxLength": 160, "minLength": 1, "pattern": "^[A-Za-z0-9]+$", "type": "string"}, {"type": "null"}], "default": null}` |

Request JSON:

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

HTTP 202: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/register', data: {"full_name": "Example User", "email": "user@example.com", "mobile_number": "+919876543210", "password": "Choose-Your-Password8!", "confirm_password": "Choose-Your-Password8!", "referral_id": "rahulkumarD000001"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/register', 'POST', {"full_name": "Example User", "email": "user@example.com", "mobile_number": "+919876543210", "password": "Choose-Your-Password8!", "confirm_password": "Choose-Your-Password8!", "referral_id": "rahulkumarD000001"});
```

## POST /api/v1/patients/verify-email

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |
| `otp` | yes | `{"pattern": "^\\d{6}$", "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/verify-email', data: {"challenge_token": "<challenge_token>", "otp": "123456"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/verify-email', 'POST', {"challenge_token": "<challenge_token>", "otp": "123456"});
```

## POST /api/v1/patients/resend-otp

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>"
}
```

HTTP 200: Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/resend-otp', data: {"challenge_token": "<challenge_token>"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/resend-otp', 'POST', {"challenge_token": "<challenge_token>"});
```

## POST /api/v1/patients/verify-login-otp

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |
| `otp` | yes | `{"pattern": "^\\d{6}$", "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

HTTP 410: Success

```json
{
  "error": {
    "code": "login_otp_disabled",
    "message": "Sign in with email and password; login OTP is no longer required"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/verify-login-otp', data: {"challenge_token": "<challenge_token>", "otp": "123456"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/verify-login-otp', 'POST', {"challenge_token": "<challenge_token>", "otp": "123456"});
```

## POST /api/v1/patients/connect-doctor

Required roles: PATIENT

Request fields:

| Field | Required | Validation |
|---|---|---|
| `referral_id` | yes | `{"maxLength": 160, "minLength": 1, "pattern": "^[A-Za-z0-9]+$", "type": "string"}` |

Request JSON:

```json
{
  "referral_id": "rahulkumarD000001"
}
```

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/connect-doctor', data: {"referral_id": "rahulkumarD000001"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/connect-doctor', 'POST', {"referral_id": "rahulkumarD000001"});
```

## GET /api/v1/patients/doctor

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/doctor', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/doctor', 'GET', undefined);
```

## DELETE /api/v1/patients/doctor

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/doctor', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/doctor', 'DELETE', undefined);
```

## POST /api/v1/patients/profiles

Required roles: PATIENT

Request fields:

| Field | Required | Validation |
|---|---|---|
| `profile_type` | yes | `{"enum": ["self", "member"], "type": "string"}` |
| `module` | yes | `{"enum": ["child", "adult", "women"], "type": "string"}` |
| `full_name` | yes | `{"maxLength": 120, "minLength": 1, "type": "string"}` |
| `date_of_birth` | yes | `{"format": "date", "type": "string"}` |
| `parent_profile_id` | no | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "default": null}` |
| `guardian_contact` | no | `{"default": "", "maxLength": 20, "pattern": "^(?:\\+?[1-9][0-9]{7,14})?$", "type": "string"}` |
| `emergency_contacts` | no | `{"items": {"$ref": "#/components/schemas/EmergencyContact"}, "maxItems": 5, "type": "array"}` |
| `referral_id` | no | `{"anyOf": [{"maxLength": 160, "minLength": 1, "pattern": "^[A-Za-z0-9]+$", "type": "string"}, {"type": "null"}], "default": null}` |

Request JSON:

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

HTTP 201: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles', data: {"profile_type": "member", "module": "child", "full_name": "Aarav Kumar", "date_of_birth": "2018-05-14", "guardian_contact": "+919876543210", "emergency_contacts": [], "referral_id": "rahulkumarD000001"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles', 'POST', {"profile_type": "member", "module": "child", "full_name": "Aarav Kumar", "date_of_birth": "2018-05-14", "guardian_contact": "+919876543210", "emergency_contacts": [], "referral_id": "rahulkumarD000001"});
```

## GET /api/v1/patients/profiles

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles', 'GET', undefined);
```

## GET /api/v1/patients/profiles/{profile_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}', 'GET', undefined);
```

## POST /api/v1/patients/profiles/{profile_id}/connect-doctor

Required roles: PATIENT

Request fields:

| Field | Required | Validation |
|---|---|---|
| `referral_id` | yes | `{"maxLength": 160, "minLength": 1, "pattern": "^[A-Za-z0-9]+$", "type": "string"}` |

Request JSON:

```json
{
  "referral_id": "rahulkumarD000001"
}
```

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}/connect-doctor', data: {"referral_id": "rahulkumarD000001"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}/connect-doctor', 'POST', {"referral_id": "rahulkumarD000001"});
```

## POST /api/v1/patients/profiles/{profile_id}/reports

Required roles: PATIENT

Request: multipart/form-data. Field `file`: one PDF/JPEG/PNG/WebP, max 10 MB. Do not manually set the multipart Content-Type boundary.

HTTP 201: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Use Postman/Insomnia multipart file input, or curl:

```bash
curl -X POST http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports -H "Authorization: Bearer ACCESS_TOKEN" -F "file=@blood-test.pdf"
```

## GET /api/v1/patients/profiles/{profile_id}/reports

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}/reports', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}/reports', 'GET', undefined);
```

## GET /api/v1/patients/profiles/{profile_id}/reports/{report_id}/download

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download', 'GET', undefined);
```

## GET /api/v1/patients/report-text/options

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/report-text/options', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/report-text/options', 'GET', undefined);
```

## GET /api/v1/patients/profiles/{profile_id}/reports/{report_id}/text

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text', 'GET', undefined);
```

## POST /api/v1/patients/profiles/{profile_id}/reports/{report_id}/text

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}/reports/{report_id}/text', 'POST', undefined);
```

## DELETE /api/v1/patients/profiles/{profile_id}/doctor

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}/doctor', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}/doctor', 'DELETE', undefined);
```

## POST /api/v1/patients/profiles/{profile_id}/reports/{report_id}/import

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}/reports/{report_id}/import', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}/reports/{report_id}/import', 'POST', undefined);
```

## GET /api/v1/patients/profiles/{profile_id}/imported-records

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/profiles/{profile_id}/imported-records', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/profiles/{profile_id}/imported-records', 'GET', undefined);
```

## POST /api/v1/admin/login

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `email` | yes | `{"format": "email", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "email": "user@example.com",
  "password": "Choose-Your-Password8!"
}
```

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/login', data: {"email": "user@example.com", "password": "Choose-Your-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/login', 'POST', {"email": "user@example.com", "password": "Choose-Your-Password8!"});
```

## GET /api/v1/admin/me

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/me', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/me', 'GET', undefined);
```

## POST /api/v1/admin/register

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `full_name` | yes | `{"maxLength": 120, "minLength": 1, "type": "string"}` |
| `email` | yes | `{"format": "email", "type": "string"}` |
| `mobile_number` | yes | `{"pattern": "^\\+?[1-9][0-9]{7,14}$", "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |
| `confirm_password` | yes | `{"maxLength": 128, "minLength": 8, "type": "string"}` |

Request JSON:

```json
{
  "full_name": "Example User",
  "email": "user@example.com",
  "mobile_number": "+919876543210",
  "password": "Choose-Your-Password8!",
  "confirm_password": "Choose-Your-Password8!"
}
```

HTTP 202: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/register', data: {"full_name": "Example User", "email": "user@example.com", "mobile_number": "+919876543210", "password": "Choose-Your-Password8!", "confirm_password": "Choose-Your-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/register', 'POST', {"full_name": "Example User", "email": "user@example.com", "mobile_number": "+919876543210", "password": "Choose-Your-Password8!", "confirm_password": "Choose-Your-Password8!"});
```

## POST /api/v1/admin/verify-email

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |
| `otp` | yes | `{"pattern": "^\\d{6}$", "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

HTTP 202: Success

```json
{
  "message": "Email verified. Waiting for approval.",
  "user": {
    "approval_status": "PENDING_APPROVAL"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/verify-email', data: {"challenge_token": "<challenge_token>", "otp": "123456"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/verify-email', 'POST', {"challenge_token": "<challenge_token>", "otp": "123456"});
```

## POST /api/v1/admin/resend-otp

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>"
}
```

HTTP 200: Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/resend-otp', data: {"challenge_token": "<challenge_token>"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/resend-otp', 'POST', {"challenge_token": "<challenge_token>"});
```

## POST /api/v1/admin/verify-login-otp

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `challenge_token` | yes | `{"maxLength": 4096, "minLength": 1, "type": "string"}` |
| `otp` | yes | `{"pattern": "^\\d{6}$", "type": "string"}` |

Request JSON:

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

HTTP 410: Success

```json
{
  "error": {
    "code": "login_otp_disabled",
    "message": "Sign in with email and password; login OTP is no longer required"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/verify-login-otp', data: {"challenge_token": "<challenge_token>", "otp": "123456"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/verify-login-otp', 'POST', {"challenge_token": "<challenge_token>", "otp": "123456"});
```

## GET /api/v1/admin/dashboard

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/dashboard', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/dashboard', 'GET', undefined);
```

## GET /api/v1/admin/doctor-requests

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/doctor-requests', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/doctor-requests', 'GET', undefined);
```

## GET /api/v1/admin/doctors

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/doctors', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/doctors', 'GET', undefined);
```

## POST /api/v1/admin/doctors/{user_id}/approve

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "user": {
    "approval_status": "APPROVED"
  },
  "email_status": "queued"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/doctors/{user_id}/approve', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/doctors/{user_id}/approve', 'POST', undefined);
```

## POST /api/v1/admin/doctors/{user_id}/reject

Required roles: ADMIN

Request fields:

| Field | Required | Validation |
|---|---|---|
| `reason` | yes | `{"maxLength": 500, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "reason": "Registration details require correction"
}
```

HTTP 200: Success

```json
{
  "user": {
    "approval_status": "REJECTED"
  },
  "email_status": "queued"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/doctors/{user_id}/reject', data: {"reason": "Registration details require correction"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/doctors/{user_id}/reject', 'POST', {"reason": "Registration details require correction"});
```

## POST /api/v1/admin/doctors/{user_id}/suspend

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "user": {
    "account_status": "SUSPENDED"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/doctors/{user_id}/suspend', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/doctors/{user_id}/suspend', 'POST', undefined);
```

## POST /api/v1/admin/doctors/{user_id}/reactivate

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "user": {
    "account_status": "ACTIVE"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/doctors/{user_id}/reactivate', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/doctors/{user_id}/reactivate', 'POST', undefined);
```

## GET /api/v1/admin/patients

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/patients', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/patients', 'GET', undefined);
```

## GET /api/v1/admin/patients/{user_id}

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/patients/{user_id}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/patients/{user_id}', 'GET', undefined);
```

## GET /api/v1/admin/patients/{user_id}/profiles

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/patients/{user_id}/profiles', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/patients/{user_id}/profiles', 'GET', undefined);
```

## GET /api/v1/admin/patients/{user_id}/profiles/{profile_id}

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/patients/{user_id}/profiles/{profile_id}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/patients/{user_id}/profiles/{profile_id}', 'GET', undefined);
```

## POST /api/v1/superadmin/login

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `email` | no | `{"anyOf": [{"format": "email", "type": "string"}, {"type": "null"}], "default": null}` |
| `username` | no | `{"anyOf": [{"maxLength": 80, "minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` |
| `password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "email": "superadmin@example.com",
  "password": "superadmin@2026"
}
```

HTTP 200: Success

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

HTTP 202: Success

```json
{
  "requires_password_change": true,
  "challenge_token": "<challenge JWT>",
  "expires_in": 600
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/login', data: {"email": "superadmin@example.com", "password": "superadmin@2026"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/login', 'POST', {"email": "superadmin@example.com", "password": "superadmin@2026"});
```

## GET /api/v1/superadmin/me

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/me', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/me', 'GET', undefined);
```

## GET /api/v1/superadmin/dashboard

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/dashboard', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/dashboard', 'GET', undefined);
```

## GET /api/v1/superadmin/admin-requests

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/admin-requests', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/admin-requests', 'GET', undefined);
```

## GET /api/v1/superadmin/admins

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/admins', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/admins', 'GET', undefined);
```

## POST /api/v1/superadmin/admins/{user_id}/approve

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "user": {
    "approval_status": "APPROVED"
  },
  "email_status": "queued"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/admins/{user_id}/approve', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/admins/{user_id}/approve', 'POST', undefined);
```

## POST /api/v1/superadmin/admins/{user_id}/reject

Required roles: SUPERADMIN

Request fields:

| Field | Required | Validation |
|---|---|---|
| `reason` | yes | `{"maxLength": 500, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "reason": "Registration details require correction"
}
```

HTTP 200: Success

```json
{
  "user": {
    "approval_status": "REJECTED"
  },
  "email_status": "queued"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/admins/{user_id}/reject', data: {"reason": "Registration details require correction"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/admins/{user_id}/reject', 'POST', {"reason": "Registration details require correction"});
```

## POST /api/v1/superadmin/admins/{user_id}/suspend

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "user": {
    "account_status": "SUSPENDED"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/admins/{user_id}/suspend', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/admins/{user_id}/suspend', 'POST', undefined);
```

## POST /api/v1/superadmin/admins/{user_id}/reactivate

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "user": {
    "account_status": "ACTIVE"
  }
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/admins/{user_id}/reactivate', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/admins/{user_id}/reactivate', 'POST', undefined);
```

## GET /api/v1/superadmin/doctors

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/doctors', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/doctors', 'GET', undefined);
```

## GET /api/v1/superadmin/patients

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/patients', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/patients', 'GET', undefined);
```

## GET /api/v1/superadmin/patients/{user_id}

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/patients/{user_id}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/patients/{user_id}', 'GET', undefined);
```

## GET /api/v1/superadmin/patients/{user_id}/profiles

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/patients/{user_id}/profiles', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/patients/{user_id}/profiles', 'GET', undefined);
```

## GET /api/v1/superadmin/patients/{user_id}/profiles/{profile_id}

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/patients/{user_id}/profiles/{profile_id}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/patients/{user_id}/profiles/{profile_id}', 'GET', undefined);
```

## GET /api/v1/superadmin/audit-logs

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/audit-logs', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/audit-logs', 'GET', undefined);
```

## GET /api/v1/children

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children', 'GET', undefined);
```

## GET /api/v1/children/{child_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/age

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/age', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/age', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/records

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/records', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/records', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/dashboard

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

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

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/dashboard', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/dashboard', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/health-guide

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/health-guide', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/health-guide', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/vaccinations

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/vaccinations', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/vaccinations', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/vaccinations/upcoming

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/vaccinations/upcoming', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/vaccinations/upcoming', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/reminders

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/reminders', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/reminders', 'GET', undefined);
```

## PUT /api/v1/children/{child_id}/reminder-preferences

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/reminder-preferences', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/reminder-preferences', 'PUT', undefined);
```

## GET /api/v1/vaccines

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/vaccines', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/vaccines', 'GET', undefined);
```

## GET /api/v1/doctors/consultation-requests

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/consultation-requests', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/consultation-requests', 'GET', undefined);
```

## GET /api/v1/vaccination-schedules

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/vaccination-schedules', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/vaccination-schedules', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/vaccinations/history

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/vaccinations/history', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/vaccinations/history', 'GET', undefined);
```

## POST /api/v1/children/{child_id}/vaccinations/history

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/vaccinations/history', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/vaccinations/history', 'POST', undefined);
```

## DELETE /api/v1/children/{child_id}/vaccinations/history/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/vaccinations/history/{record_id}', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/vaccinations/history/{record_id}', 'DELETE', undefined);
```

## PATCH /api/v1/children/{child_id}/vaccinations/history/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/vaccinations/history/{record_id}', data: {}, options: Options(method: 'PATCH'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/vaccinations/history/{record_id}', 'PATCH', undefined);
```

## GET /api/v1/children/{child_id}/medical-history

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/medical-history', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/medical-history', 'GET', undefined);
```

## POST /api/v1/children/{child_id}/medical-history

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/medical-history', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/medical-history', 'POST', undefined);
```

## DELETE /api/v1/children/{child_id}/medical-history/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/medical-history/{record_id}', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/medical-history/{record_id}', 'DELETE', undefined);
```

## PATCH /api/v1/children/{child_id}/medical-history/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/medical-history/{record_id}', data: {}, options: Options(method: 'PATCH'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/medical-history/{record_id}', 'PATCH', undefined);
```

## GET /api/v1/children/{child_id}/growth

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/growth', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/growth', 'GET', undefined);
```

## POST /api/v1/children/{child_id}/growth

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/growth', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/growth', 'POST', undefined);
```

## DELETE /api/v1/children/{child_id}/growth/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/growth/{record_id}', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/growth/{record_id}', 'DELETE', undefined);
```

## PATCH /api/v1/children/{child_id}/growth/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/growth/{record_id}', data: {}, options: Options(method: 'PATCH'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/growth/{record_id}', 'PATCH', undefined);
```

## GET /api/v1/children/{child_id}/nutrition

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/nutrition', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/nutrition', 'GET', undefined);
```

## POST /api/v1/children/{child_id}/nutrition

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/nutrition', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/nutrition', 'POST', undefined);
```

## DELETE /api/v1/children/{child_id}/nutrition/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/nutrition/{record_id}', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/nutrition/{record_id}', 'DELETE', undefined);
```

## PATCH /api/v1/children/{child_id}/nutrition/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/nutrition/{record_id}', data: {}, options: Options(method: 'PATCH'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/nutrition/{record_id}', 'PATCH', undefined);
```

## GET /api/v1/children/{child_id}/consultations

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/consultations', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/consultations', 'GET', undefined);
```

## POST /api/v1/children/{child_id}/consultations

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/consultations', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/consultations', 'POST', undefined);
```

## DELETE /api/v1/children/{child_id}/consultations/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/consultations/{record_id}', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/consultations/{record_id}', 'DELETE', undefined);
```

## PATCH /api/v1/children/{child_id}/consultations/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/consultations/{record_id}', data: {}, options: Options(method: 'PATCH'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/consultations/{record_id}', 'PATCH', undefined);
```

## GET /api/v1/children/{child_id}/care-notes

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/care-notes', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/care-notes', 'GET', undefined);
```

## POST /api/v1/children/{child_id}/care-notes

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/care-notes', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/care-notes', 'POST', undefined);
```

## DELETE /api/v1/children/{child_id}/care-notes/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/care-notes/{record_id}', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/care-notes/{record_id}', 'DELETE', undefined);
```

## PATCH /api/v1/children/{child_id}/care-notes/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/care-notes/{record_id}', data: {}, options: Options(method: 'PATCH'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/care-notes/{record_id}', 'PATCH', undefined);
```

## GET /api/v1/children/{child_id}/consultation-requests

Required roles: PATIENT, DOCTOR

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/consultation-requests', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/consultation-requests', 'GET', undefined);
```

## POST /api/v1/children/{child_id}/consultation-requests

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "items": [],
  "total": 0
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/consultation-requests', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/consultation-requests', 'POST', undefined);
```

## DELETE /api/v1/children/{child_id}/consultation-requests/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/consultation-requests/{record_id}', data: {}, options: Options(method: 'DELETE'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/consultation-requests/{record_id}', 'DELETE', undefined);
```

## PATCH /api/v1/children/{child_id}/consultation-requests/{record_id}

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/consultation-requests/{record_id}', data: {}, options: Options(method: 'PATCH'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/consultation-requests/{record_id}', 'PATCH', undefined);
```

## GET /api/v1/vaccination-schedules/{schedule_id}

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/vaccination-schedules/{schedule_id}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/vaccination-schedules/{schedule_id}', 'GET', undefined);
```

## GET /api/v1/children/{child_id}/vaccination-context

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/vaccination-context', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/vaccination-context', 'GET', undefined);
```

## PUT /api/v1/children/{child_id}/vaccination-context

Required roles: PATIENT

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/children/{child_id}/vaccination-context', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/children/{child_id}/vaccination-context', 'PUT', undefined);
```

## GET /api/v1/doctors/vaccination-reviews

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/vaccination-reviews', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/vaccination-reviews', 'GET', undefined);
```

## POST /api/v1/doctors/vaccination-reviews/{schedule_id}

Required roles: DOCTOR

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/doctors/vaccination-reviews/{schedule_id}', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/doctors/vaccination-reviews/{schedule_id}', 'POST', undefined);
```

## GET /api/v1/admin/vaccination/vaccines

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/vaccines', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/vaccines', 'GET', undefined);
```

## POST /api/v1/admin/vaccination/vaccines

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/vaccines', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/vaccines', 'POST', undefined);
```

## PUT /api/v1/admin/vaccination/vaccines/{vaccine_id}

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/vaccines/{vaccine_id}', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/vaccines/{vaccine_id}', 'PUT', undefined);
```

## GET /api/v1/admin/vaccination/schedules

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules', 'GET', undefined);
```

## POST /api/v1/admin/vaccination/schedules

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules', 'POST', undefined);
```

## PUT /api/v1/admin/vaccination/schedules/{schedule_id}

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules/{schedule_id}', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules/{schedule_id}', 'PUT', undefined);
```

## PUT /api/v1/admin/vaccination/schedules/{schedule_id}/eligibility

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules/{schedule_id}/eligibility', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules/{schedule_id}/eligibility', 'PUT', undefined);
```

## PUT /api/v1/admin/vaccination/schedules/{schedule_id}/reminders

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules/{schedule_id}/reminders', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules/{schedule_id}/reminders', 'PUT', undefined);
```

## GET /api/v1/admin/vaccination/reviewers

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/reviewers', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/reviewers', 'GET', undefined);
```

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/submit-review

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules/{schedule_id}/submit-review', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules/{schedule_id}/submit-review', 'POST', undefined);
```

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/withdraw

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules/{schedule_id}/withdraw', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules/{schedule_id}/withdraw', 'POST', undefined);
```

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/publish

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules/{schedule_id}/publish', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules/{schedule_id}/publish', 'POST', undefined);
```

## POST /api/v1/admin/vaccination/schedules/{schedule_id}/retire

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/schedules/{schedule_id}/retire', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/schedules/{schedule_id}/retire', 'POST', undefined);
```

## GET /api/v1/admin/vaccination/audit

Required roles: ADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/admin/vaccination/audit', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/admin/vaccination/audit', 'GET', undefined);
```

## GET /api/v1/superadmin/vaccination/vaccines

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/vaccines', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/vaccines', 'GET', undefined);
```

## POST /api/v1/superadmin/vaccination/vaccines

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/vaccines', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/vaccines', 'POST', undefined);
```

## PUT /api/v1/superadmin/vaccination/vaccines/{vaccine_id}

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/vaccines/{vaccine_id}', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/vaccines/{vaccine_id}', 'PUT', undefined);
```

## GET /api/v1/superadmin/vaccination/schedules

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules', 'GET', undefined);
```

## POST /api/v1/superadmin/vaccination/schedules

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules', 'POST', undefined);
```

## PUT /api/v1/superadmin/vaccination/schedules/{schedule_id}

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules/{schedule_id}', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules/{schedule_id}', 'PUT', undefined);
```

## PUT /api/v1/superadmin/vaccination/schedules/{schedule_id}/eligibility

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules/{schedule_id}/eligibility', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules/{schedule_id}/eligibility', 'PUT', undefined);
```

## PUT /api/v1/superadmin/vaccination/schedules/{schedule_id}/reminders

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules/{schedule_id}/reminders', data: {}, options: Options(method: 'PUT'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules/{schedule_id}/reminders', 'PUT', undefined);
```

## GET /api/v1/superadmin/vaccination/reviewers

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/reviewers', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/reviewers', 'GET', undefined);
```

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/submit-review

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules/{schedule_id}/submit-review', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules/{schedule_id}/submit-review', 'POST', undefined);
```

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules/{schedule_id}/withdraw', 'POST', undefined);
```

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/publish

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules/{schedule_id}/publish', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules/{schedule_id}/publish', 'POST', undefined);
```

## POST /api/v1/superadmin/vaccination/schedules/{schedule_id}/retire

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/schedules/{schedule_id}/retire', data: {}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/schedules/{schedule_id}/retire', 'POST', undefined);
```

## GET /api/v1/superadmin/vaccination/audit

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
  "message": "Operation completed"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/vaccination/audit', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/vaccination/audit', 'GET', undefined);
```

## GET /api/v1/health

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "status": "ok",
  "service": "familycare-backend",
  "auth": "flask-jwt"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/health', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/health', 'GET', undefined);
```

## GET /api/v1/health/ready

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "status": "ready",
  "database": "postgresql"
}
```

HTTP 400: Invalid challenge/OTP/state

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid challenge/OTP/state"
  }
}
```

HTTP 401: Invalid credentials/token/session

```json
{
  "error": {
    "code": "error_code",
    "message": "Invalid credentials/token/session"
  }
}
```

HTTP 403: Role, approval, status, transport or CSRF denied

```json
{
  "error": {
    "code": "error_code",
    "message": "Role, approval, status, transport or CSRF denied"
  }
}
```

HTTP 404: Not found

```json
{
  "error": {
    "code": "error_code",
    "message": "Not found"
  }
}
```

HTTP 409: Duplicate data or invalid approval state

```json
{
  "error": {
    "code": "error_code",
    "message": "Duplicate data or invalid approval state"
  }
}
```

HTTP 422: Validation failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Validation failed"
  }
}
```

HTTP 429: Rate limit or OTP cooldown

```json
{
  "error": {
    "code": "error_code",
    "message": "Rate limit or OTP cooldown"
  }
}
```

HTTP 413: Report exceeds size limit

```json
{
  "error": {
    "code": "error_code",
    "message": "Report exceeds size limit"
  }
}
```

HTTP 415: Multipart upload required

```json
{
  "error": {
    "code": "error_code",
    "message": "Multipart upload required"
  }
}
```

HTTP 502: Cloudinary upload failed

```json
{
  "error": {
    "code": "error_code",
    "message": "Cloudinary upload failed"
  }
}
```

HTTP 503: Database or Cloudinary unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database or Cloudinary unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/health/ready', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/health/ready', 'GET', undefined);
```
