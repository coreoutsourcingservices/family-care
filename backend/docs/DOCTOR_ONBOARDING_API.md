# Doctor Signup, Profile Setup and Admin Approval API

Base URL: `http://127.0.0.1:5001/api/v1`

Flow: Signup -> Email OTP -> Setup Profile -> Submit -> Admin review -> Approve/Reject.

All POST bodies below use `Content-Type: application/json`. Values and tokens in
examples are placeholders. User objects are shortened to the relevant fields.

## Endpoint summary

| Method | Path | Authentication | Success |
| --- | --- | --- | --- |
| POST | `/doctors/register` | None | 202 |
| POST | `/doctors/verify-email` | OTP challenge in body | 202 |
| POST | `/doctors/resend-otp` | OTP challenge in body | 200 |
| POST | `/doctors/setup-profile` | Setup token in body | 202 |
| POST | `/doctors/login` | Email/password | 200 or 202 |
| POST | `/doctors/approval-status` | Email/password | 200 |
| GET | `/doctors/me` | Approved doctor access token | 200 |
| POST | `/admin/login` | Approved admin email/password | 200 |
| GET | `/admin/doctor-requests?page=1&per_page=15` | Admin access token | 200 |
| GET | `/admin/doctors?status=PENDING_APPROVAL` | Admin access token | 200 |
| POST | `/admin/doctors/{public_id_or_uuid}/approve` | Admin access token | 200 |
| POST | `/admin/doctors/{public_id_or_uuid}/reject` | Admin access token | 200 |

## 1. Basic doctor signup

`POST /doctors/register`

```json
{
  "full_name": "Dr Example Kumar",
  "mobile_number": "+919876543210",
  "email": "doctor@example.com",
  "password": "ExamplePassword8!",
  "confirm_password": "ExamplePassword8!"
}
```

All five fields are required. Qualification, council and registration number are
not required at signup. Password length: 8-128 characters; passwords must match.
Mobile: optional leading `+`, followed by 8-15 digits, starting with 1-9.

Response: **202**

```json
{
  "public_id": null,
  "user_id": null,
  "approval_status": "PENDING_EMAIL_VERIFICATION",
  "challenge_token": "<challenge_token>",
  "expires_in": 300,
  "resend_after": 60,
  "email_status": "sent",
  "message": "OTP sent to your email. Verify OTP to complete registration."
}
```

Save `challenge_token` for verification/resend. No account is persisted before OTP
verification. `sent` means SMTP accepted the email, not confirmed inbox delivery.

## 2. Verify email OTP

`POST /doctors/verify-email`

```json
{
  "challenge_token": "<challenge_token>",
  "otp": "123456"
}
```

Response: **202**, example shortened:

```json
{
  "requires_profile_setup": true,
  "setup_token": "<setup_token>",
  "user": {
    "id": "<doctor_uuid>",
    "public_id": "D000001",
    "full_name": "Dr Example Kumar",
    "email": "doctor@example.com",
    "phone_number": "+919876543210",
    "role": "DOCTOR",
    "email_verified": true,
    "approval_status": "PROFILE_REQUIRED"
  },
  "doctor": {
    "qualification": null,
    "medical_registration_number": null,
    "registering_council": null,
    "specialization": null,
    "nmr_id": null,
    "address": null,
    "clinic_address": null,
    "years_of_experience": null
  },
  "rejection_reason": null,
  "message": "Complete your doctor profile and submit it for approval."
}
```

Open Setup Doctor Profile. Prefill name/email/mobile from `user` as read-only.
The setup token expires in 30 minutes. It is not a dashboard access token.
No admin approval request exists at this stage.

## 3. Resend OTP

`POST /doctors/resend-otp`

```json
{"challenge_token": "<latest_challenge_token>"}
```

Response **200** contains a new `challenge_token`, `expires_in`, `resend_after`
and `email_status`. Replace the previous challenge token with the new one.
Resend cooldown is 60 seconds. OTP validity is 5 minutes, with at most 5 attempts.
If the pending signup expires or the API restarts, register again.

## 4. Complete profile and submit for admin approval

`POST /doctors/setup-profile`

```json
{
  "setup_token": "<setup_token>",
  "qualification": "MBBS",
  "medical_registration_number": "REG-12345",
  "registering_council": "Example Medical Council",
  "specialization": "General Medicine",
  "nmr_id": null,
  "address": "12 Example Street, Delhi, Delhi 110001",
  "clinic_address": "Example Clinic, 21 Clinic Road, Delhi 110002",
  "years_of_experience": 5
}
```

| Field | Required | Validation |
| --- | --- | --- |
| setup_token | Yes | Valid doctor setup token |
| qualification | Yes | 2-200 characters after trimming |
| medical_registration_number | Yes | 2-100 characters; first character alphanumeric; remaining characters alphanumeric, `/`, space, `.`, `_`, `-` |
| registering_council | Yes | 2-200 characters after trimming |
| specialization | No | Up to 200 characters; omit or send null |
| nmr_id | No | 1-100 characters when supplied; omit or send null |
| address | Yes | 5-1000 characters after trimming |
| clinic_address | Yes | 5-1000 characters after trimming |
| years_of_experience | Yes | JSON integer 0-80; use 0 for newly qualified doctors |

Do not send name/email/mobile/password in this request. Unknown body fields are
rejected. Council + registration number must be unique; NMR ID must be unique
when supplied. Qualification, council and registration number are stored uppercase.

Response: **202**, user shortened:

```json
{
  "user": {
    "id": "<doctor_uuid>",
    "public_id": "D000001",
    "role": "DOCTOR",
    "approval_status": "PENDING_APPROVAL"
  },
  "message": "Your profile is under review."
}
```

Now the admin approval request exists. Show the under-review screen. Submitting
again while under review returns 409. Dashboard access remains unavailable.

## 5. Doctor login and resume setup

`POST /doctors/login`

```json
{"email": "doctor@example.com", "password": "ExamplePassword8!"}
```

Handle the result by state:

| State | HTTP | Frontend action |
| --- | --- | --- |
| PROFILE_REQUIRED | 202 | `requires_profile_setup: true`; open setup using returned `setup_token`, `user`, `doctor` |
| REJECTED | 202 | Open setup with previous details and `rejection_reason`; resubmit through `/doctors/setup-profile` |
| PENDING_APPROVAL | 202 | Show `message: "Your profile is under review."`; no access token |
| APPROVED and active | 200 | Receive session; open doctor dashboard |
| Suspended or email unverified | 403 | Display restriction error |
| Wrong credentials | 401 | Display login error |

Approved login response in default bearer mode, user shortened:

```json
{
  "access_token": "<doctor_access_token>",
  "refresh_token": "<refresh_token>",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {"public_id": "D000001", "role": "DOCTOR", "approval_status": "APPROVED"}
}
```

To fetch the approved profile:

```http
GET /api/v1/doctors/me
Authorization: Bearer <doctor_access_token>
```

Response **200** contains `user` with nested `doctor`, including the submitted
professional fields, addresses, experience and verification status.

## 6. Check approval status

`POST /doctors/approval-status`

```json
{"email": "doctor@example.com", "password": "ExamplePassword8!"}
```

Response **200**:

```json
{
  "public_id": "D000001",
  "email_verified": true,
  "approval_status": "PENDING_APPROVAL",
  "account_status": "ACTIVE",
  "rejection_reason": null
}
```

## 7. Admin login

`POST /admin/login`

```json
{"email": "<approved_admin_email>", "password": "<admin_password>"}
```

Response **200** in bearer mode contains `access_token`, `refresh_token`,
`token_type`, `expires_in` and `user`. Use the ADMIN access token for all review
endpoints below. A doctor/setup token cannot review applications.

## 8. Admin pending requests and complete submitted data

```http
GET /api/v1/admin/doctor-requests?page=1&per_page=15
Authorization: Bearer <admin_access_token>
```

Response **200**, item shortened:

```json
{
  "items": [{
    "id": "<doctor_uuid>",
    "public_id": "D000001",
    "full_name": "Dr Example Kumar",
    "email": "doctor@example.com",
    "phone_number": "+919876543210",
    "approval_status": "PENDING_APPROVAL",
    "doctor": {
      "qualification": "MBBS",
      "specialization": "General Medicine",
      "medical_registration_number": "REG-12345",
      "registering_council": "EXAMPLE MEDICAL COUNCIL",
      "nmr_id": null,
      "verification_status": "PENDING",
      "address": "12 Example Street, Delhi, Delhi 110001",
      "clinic_address": "Example Clinic, 21 Clinic Road, Delhi 110002",
      "years_of_experience": 5
    }
  }],
  "total": 1,
  "page": 1,
  "per_page": 15
}
```

Only submitted, verified pending applications appear here. To list other states,
use `/admin/doctors?status=APPROVED`, `REJECTED`, `PROFILE_REQUIRED` or
`PENDING_APPROVAL`. Omit `status` to list all doctors. Page must be >=1;
`per_page` is 1-100 (default 25).

## 9. Approve doctor

```http
POST /api/v1/admin/doctors/D000001/approve
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{}
```

Response **200**, user shortened:

```json
{
  "user": {"public_id": "D000001", "approval_status": "APPROVED"},
  "email_status": "queued"
}
```

The doctor can now log in and receive a dashboard session.

## 10. Reject doctor with reason

```http
POST /api/v1/admin/doctors/D000001/reject
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{"reason": "Please correct your clinic address and registration details."}
```

Reason is required, 1-500 characters. Response **200** contains `user` with
`approval_status: "REJECTED"` and `email_status: "queued"`. On next doctor login,
show the rejection reason and previous profile; submit corrections through the
setup endpoint. Review URLs accept either the public ID or UUID.

Approval/rejection notifications need the mail worker for delivery:
`python -m scripts.mail_worker`. Signup OTP is sent directly, without that worker.

## Authentication transport

The examples above use the default bearer transport, suitable for API clients:

```http
Authorization: Bearer <access_token>
```

The existing website uses cookie transport instead. Send
`X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare` and fetch with
`credentials: 'include'`. Approved login returns HttpOnly session cookies and
`csrf_token`, without access/refresh tokens in JSON. Authenticated cookie writes
also require `X-CSRF-Token: <csrf_token>`. Browser Origin must be allowed by the
backend configuration. Do not mix bearer and cookie sessions.

The setup token is always sent in the `setup_token` JSON field, independent of
session transport. Keep it in memory and obtain a fresh one by logging in if it expires.

## Errors

```json
{"error": {"code": "conflict", "message": "Doctor registration already exists"}}
```

| HTTP | Common codes / meaning |
| --- | --- |
| 400 | `invalid_json`, `invalid_otp`, `otp_unavailable` |
| 401 | `invalid_credentials`, `invalid_token` |
| 403 | `account_restricted`, `forbidden`, `csrf_required`, `csrf_failed` |
| 409 | `account_exists`, `conflict`, `invalid_state` |
| 422 | `validation_error`; `error.fields` identifies invalid fields |
| 429 | `otp_cooldown` or request rate limit |
| 503 | `email_delivery_failed`, database unavailable/not configured |

Signup, login, OTP, status and setup endpoints are rate limited to 10 requests
per minute per account key and 30 per minute per client IP. Setup has no email in
its body, so its account key falls back to client IP.

Live machine-readable API reference: `http://127.0.0.1:5001/api/openapi.json`.
Live API endpoint index: `http://127.0.0.1:5001/api/docs`.
