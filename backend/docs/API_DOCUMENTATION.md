# Family Care API reference

Base URL: `http://127.0.0.1:5001` (local only).

API only: no website, dashboard UI or mobile UI is included.

OpenAPI: `GET /api/openapi.json`. JSON API index: `GET /api/docs`.

All JSON requests use `Content-Type: application/json`.
Mobile/CLI: `Authorization: Bearer <access_token>` for protected endpoints.
Browser: `X-Auth-Transport: cookie`, credentials enabled, `X-Requested-With: FamilyCare` on mutations;
also send the returned `csrf_token` as `X-CSRF-Token` on authenticated mutations and refresh.
Cookie sessions return no access/refresh tokens in JSON. Refresh rotates the CSRF token too.

Passwords: 8–128 characters; `confirm_password` must match. Roles/public IDs/status are server owned.
All dates are stored as UTC. Public IDs or UUIDs may be used for `{user_id}`.
List routes support `page=1&per_page=25` (maximum 100); user lists accept `status` approval filter.

Signup sends email OTP synchronously and stores temporary details in a TTL cache, not PostgreSQL.
No user/profile/OTP/audit/outbox rows are inserted until signup OTP verification succeeds.
Register returns null public_id/user_id; IDs are assigned only after verification.
SMTP acceptance returns email_status sent; delivery failure returns 503 email_delivery_failed.
Patient verification issues a JWT session; admin/doctor verification queues approval.
Admin and patient login: password → OTP → session. Doctor login: password → session after approval.
Superadmin first login: password → initial-password challenge → password rotation → session.

OTP: 6 digits, 5 minutes, 60-second resend cooldown, 5 attempts, one-time use.
After a consumed/exhausted signup challenge, restart with `/auth/request-email-verification`.
Forgot password is generic for unknown accounts. Registration conflicts can reveal existing accounts.
Signup mail is sent directly; sent means SMTP accepted it, not a guarantee of inbox placement.
Login/reset/approval mail still uses the outbox and requires the separate SMTP worker.

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
| POST | `http://127.0.0.1:5001/api/v1/patients/login` | Required roles: public / limited challenge |
| GET | `http://127.0.0.1:5001/api/v1/patients/me` | Required roles: PATIENT |
| POST | `http://127.0.0.1:5001/api/v1/patients/register` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/verify-email` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/resend-otp` | Required roles: public / limited challenge |
| POST | `http://127.0.0.1:5001/api/v1/patients/verify-login-otp` | Required roles: public / limited challenge |
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 202: Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "queued",
  "requires_otp": true
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/patients/register', data: {"full_name": "Example User", "email": "user@example.com", "mobile_number": "+919876543210", "password": "Choose-Your-Password8!", "confirm_password": "Choose-Your-Password8!"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/patients/register', 'POST', {"full_name": "Example User", "email": "user@example.com", "mobile_number": "+919876543210", "password": "Choose-Your-Password8!", "confirm_password": "Choose-Your-Password8!"});
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 202: Success

```json
{
  "challenge_token": "<limited-purpose JWT>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "queued",
  "requires_otp": true
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

## POST /api/v1/superadmin/login

Required roles: public / limited challenge

Request fields:

| Field | Required | Validation |
|---|---|---|
| `username` | yes | `{"maxLength": 80, "minLength": 1, "type": "string"}` |
| `password` | yes | `{"maxLength": 128, "minLength": 1, "type": "string"}` |

Request JSON:

```json
{
  "username": "superadmin",
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
    "public_id": "C000001",
    "role": "PATIENT"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
  }
}
```

Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):

```dart
await dio.request('/api/v1/superadmin/login', data: {"username": "superadmin", "password": "superadmin@2026"}, options: Options(method: 'POST'));
```

Web (use the cookie/CSRF client in `examples/web_api.js`):

```javascript
await api('/api/v1/superadmin/login', 'POST', {"username": "superadmin", "password": "superadmin@2026"});
```

## GET /api/v1/superadmin/me

Required roles: SUPERADMIN

No JSON body required.

HTTP 200: Success

```json
{
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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

HTTP 503: Database unavailable/not configured

```json
{
  "error": {
    "code": "error_code",
    "message": "Database unavailable/not configured"
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
