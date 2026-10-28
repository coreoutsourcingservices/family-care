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
| POST | `http://127.0.0.1:5001/api/v1/patients/login` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/patients/me` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/register` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/verify-email` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/resend-otp` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/verify-login-otp` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/connect-doctor` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/doctor` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/profiles` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/connect-doctor` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports` | Required roles: PATIENT |
| GET | `http://127.0.0.1:5001/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download` | Required roles: PATIENT |
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
| GET | `http://127.0.0.1:5001/api/v1/superadmin/audit-logs` | Required roles: SUPERADMIN |
| GET | `http://127.0.0.1:5001/api/v1/localization` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/localization/states` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/localization/languages` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/localization/messages/{language}` | Required roles: public / limited challenge |
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
| `qualification` | yes | `{"maxLength": 200, "minLength": 2, "type": "string"}` |
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
| `qualification` | yes | `{"maxLength": 200, "minLength": 2, "type": "string"}` |
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
      "public_id": "CH000001",
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
    "public_id": "CH000001",
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
    "public_id": "CH000001",
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
      "public_id": "CH000001",
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
    "public_id": "CH000001",
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
    "public_id": "CH000001",
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

## GET /api/v1/localization

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "location": {
    "country_code": "IN",
    "state": "Maharashtra",
    "status": "detected",
    "approximate": true
  },
  "languages": [
    {
      "code": "mr",
      "name": "Marathi",
      "native_name": "\u092e\u0930\u093e\u0920\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "hi",
      "name": "Hindi",
      "native_name": "\u0939\u093f\u0928\u094d\u0926\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "en",
      "name": "English",
      "native_name": "English",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    }
  ],
  "recommended_language": "mr",
  "fallback_language": "en",
  "manual_state_selection": true
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
await dio.request('/api/v1/localization', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/localization', 'GET', undefined);
```

## GET /api/v1/localization/states

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "items": [
    {
      "name": "Maharashtra",
      "type": "state",
      "languages": [
        {
          "code": "mr",
          "name": "Marathi",
          "native_name": "\u092e\u0930\u093e\u0920\u0940",
          "translation_status": "available",
          "fallback_language": "en",
          "direction": "ltr"
        },
        {
          "code": "hi",
          "name": "Hindi",
          "native_name": "\u0939\u093f\u0928\u094d\u0926\u0940",
          "translation_status": "available",
          "fallback_language": "en",
          "direction": "ltr"
        },
        {
          "code": "en",
          "name": "English",
          "native_name": "English",
          "translation_status": "available",
          "fallback_language": "en",
          "direction": "ltr"
        }
      ],
      "regional_languages": [
        "Marathi"
      ]
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
await dio.request('/api/v1/localization/states', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/localization/states', 'GET', undefined);
```

## GET /api/v1/localization/languages

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "items": [
    {
      "code": "adi",
      "name": "Adi",
      "native_name": "Adi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "angami",
      "name": "Angami",
      "native_name": "Angami",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "ao",
      "name": "Ao",
      "native_name": "Ao",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "apatani",
      "name": "Apatani",
      "native_name": "Apatani",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "as",
      "name": "Assamese",
      "native_name": "\u0985\u09b8\u09ae\u09c0\u09af\u09bc\u09be",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "awadhi",
      "name": "Awadhi",
      "native_name": "\u0905\u0935\u0927\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "bagheli",
      "name": "Bagheli",
      "native_name": "Bagheli",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "balti",
      "name": "Balti",
      "native_name": "Balti",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "bn",
      "name": "Bengali",
      "native_name": "\u09ac\u09be\u0982\u09b2\u09be",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "bhojpuri",
      "name": "Bhojpuri",
      "native_name": "\u092d\u094b\u091c\u092a\u0941\u0930\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "bhutia",
      "name": "Bhutia",
      "native_name": "Bhutia",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "bodo",
      "name": "Bodo",
      "native_name": "Bodo",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "braj",
      "name": "Braj",
      "native_name": "Braj",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "bundeli",
      "name": "Bundeli",
      "native_name": "Bundeli",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "chhattisgarhi",
      "name": "Chhattisgarhi",
      "native_name": "Chhattisgarhi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "dhundhari",
      "name": "Dhundhari",
      "native_name": "Dhundhari",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "dogri",
      "name": "Dogri",
      "native_name": "\u0921\u094b\u0917\u0930\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "en",
      "name": "English",
      "native_name": "English",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "fr",
      "name": "French",
      "native_name": "Fran\u00e7ais",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "garhwali",
      "name": "Garhwali",
      "native_name": "Garhwali",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "garo",
      "name": "Garo",
      "native_name": "Garo",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "gondi",
      "name": "Gondi",
      "native_name": "Gondi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "gu",
      "name": "Gujarati",
      "native_name": "\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "haryanvi",
      "name": "Haryanvi",
      "native_name": "Haryanvi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "hi",
      "name": "Hindi",
      "native_name": "\u0939\u093f\u0928\u094d\u0926\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "jeseri",
      "name": "Jeseri",
      "native_name": "Jeseri",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "kangri",
      "name": "Kangri",
      "native_name": "Kangri",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "kn",
      "name": "Kannada",
      "native_name": "\u0c95\u0ca8\u0ccd\u0ca8\u0ca1",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "kashmiri",
      "name": "Kashmiri",
      "native_name": "Kashmiri",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "khasi",
      "name": "Khasi",
      "native_name": "Khasi",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "kokborok",
      "name": "Kokborok",
      "native_name": "Kokborok",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "konkani",
      "name": "Konkani",
      "native_name": "\u0915\u094b\u0902\u0915\u0923\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "kumaoni",
      "name": "Kumaoni",
      "native_name": "Kumaoni",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "kutchi",
      "name": "Kutchi",
      "native_name": "Kutchi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "ladakhi",
      "name": "Ladakhi",
      "native_name": "Ladakhi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "lepcha",
      "name": "Lepcha",
      "native_name": "Lepcha",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "magahi",
      "name": "Magahi",
      "native_name": "Magahi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "mahl",
      "name": "Mahl",
      "native_name": "Mahl",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "maithili",
      "name": "Maithili",
      "native_name": "\u092e\u0948\u0925\u093f\u0932\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "ml",
      "name": "Malayalam",
      "native_name": "\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "malvi",
      "name": "Malvi",
      "native_name": "Malvi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "mandeali",
      "name": "Mandeali",
      "native_name": "Mandeali",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "manipuri",
      "name": "Manipuri",
      "native_name": "\uabc3\uabe4\uabc7\uabe9\uabc2\uabe3\uabdf",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "mr",
      "name": "Marathi",
      "native_name": "\u092e\u0930\u093e\u0920\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "marwari",
      "name": "Marwari",
      "native_name": "\u092e\u093e\u0930\u0935\u093e\u0921\u093c\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "mewari",
      "name": "Mewari",
      "native_name": "Mewari",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "mizo",
      "name": "Mizo",
      "native_name": "Mizo",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "monpa",
      "name": "Monpa",
      "native_name": "Monpa",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "mundari",
      "name": "Mundari",
      "native_name": "Mundari",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "nagamese",
      "name": "Nagamese",
      "native_name": "Nagamese",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "nagpuri",
      "name": "Nagpuri",
      "native_name": "Nagpuri",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "ne",
      "name": "Nepali",
      "native_name": "\u0928\u0947\u092a\u093e\u0932\u0940",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "nicobarese",
      "name": "Nicobarese",
      "native_name": "Nicobarese",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "nyishi",
      "name": "Nyishi",
      "native_name": "Nyishi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "or",
      "name": "Odia",
      "native_name": "\u0b13\u0b21\u0b3c\u0b3f\u0b06",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "pahari",
      "name": "Pahari",
      "native_name": "Pahari",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "pa",
      "name": "Punjabi",
      "native_name": "\u0a2a\u0a70\u0a1c\u0a3e\u0a2c\u0a40",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "purgi",
      "name": "Purgi",
      "native_name": "Purgi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "santali",
      "name": "Santali",
      "native_name": "\u1c65\u1c5f\u1c71\u1c5b\u1c5f\u1c72\u1c64",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "sumi",
      "name": "Sumi",
      "native_name": "Sumi",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "ta",
      "name": "Tamil",
      "native_name": "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "tangkhul",
      "name": "Tangkhul",
      "native_name": "Tangkhul",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "te",
      "name": "Telugu",
      "native_name": "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "tulu",
      "name": "Tulu",
      "native_name": "\u0ca4\u0cc1\u0cb3\u0cc1",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "ur",
      "name": "Urdu",
      "native_name": "\u0627\u0631\u062f\u0648",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "rtl"
    },
    {
      "code": "warli",
      "name": "Warli",
      "native_name": "Warli",
      "translation_status": "english_fallback",
      "fallback_language": "en",
      "direction": "ltr"
    }
  ],
  "total": 66
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
await dio.request('/api/v1/localization/languages', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/localization/languages', 'GET', undefined);
```

## GET /api/v1/localization/messages/{language}

Required roles: public / limited challenge

No JSON body required.

HTTP 200: Success

```json
{
  "language": "hi",
  "fallback_language": "en",
  "translation_status": "available",
  "messages": {
    "Sign in": "\u0932\u0949\u0917\u093f\u0928 \u0915\u0930\u0947\u0902"
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
await dio.request('/api/v1/localization/messages/{language}', data: {}, options: Options(method: 'GET'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/localization/messages/{language}', 'GET', undefined);
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
