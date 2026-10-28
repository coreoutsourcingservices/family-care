# Doctor API and request JSON

Base: `http://127.0.0.1:5001/api/v1`.
Examples use synthetic credentials. Do not hardcode real passwords or tokens in frontend source.

## Endpoints

| Method | Path | Body / purpose |
| --- | --- | --- |
| POST | `/doctors/register` | Registration JSON below |
| POST | `/doctors/verify-email` | `challenge_token`, six-digit `otp` |
| POST | `/doctors/resend-otp` | `challenge_token` |
| POST | `/doctors/login` | `email`, `password` |
| POST | `/doctors/approval-status` | `email`, `password` |
| POST | `/doctors/resubmit` | Rejected-doctor corrected registration details |
| GET | `/doctors/me` | Current doctor account and professional profile |
| GET | `/doctors/referral` | Doctor's own referral information |
| GET | `/doctors/patients?page=1&per_page=25` | Connected patients |
| GET | `/doctors/care-profiles?page=1&per_page=25&module=child` | Connected care profiles; module optional |
| GET | `/doctors/care-profiles/{profile_id}` | Accessible care-profile details |
| GET | `/doctors/care-profiles/{profile_id}/reports?page=1&per_page=25` | Accessible profile's reports |
| GET | `/doctors/care-profiles/{profile_id}/reports/{report_id}/download` | Download accessible report |
| GET | `/doctors/consultation-requests?page=1&per_page=25` | Requests for profiles connected to this doctor |
| GET | `/doctors/vaccination-reviews?page=1&per_page=25` | Assigned medical reviews; qualified verified doctor required |
| POST | `/doctors/vaccination-reviews/{schedule_id}` | Approve/reject assigned dose version |
| POST | `/auth/forgot-password` | `email` |
| POST | `/auth/reset-password` | `challenge_token`, `otp`, `new_password`, `confirm_password` |
| POST | `/auth/refresh` | Existing refresh-token flow |
| POST | `/auth/logout` | Sign out current session |

GET requests have no JSON body. List pagination is page >= 1, per_page 1–100.
Doctor access is restricted to connected profiles and assigned reviews, not all patient medical records.

## Registration

`POST http://127.0.0.1:5001/api/v1/doctors/register`

```json
{
  "full_name": "Dr Example Kumar",
  "email": "doctor@example.com",
  "mobile_number": "+919876543210",
  "password": "ExamplePass8!",
  "confirm_password": "ExamplePass8!",
  "qualification": "MBBS",
  "medical_registration_number": "EXAMPLE-12345",
  "registering_council": "Example Medical Council",
  "specialization": "Pediatrics"
}
```

Optional `nmr_id` may also be supplied. Email verification and administrative approval are separate steps. Follow the returned challenge token; do not invent an OTP or mark an account approved in the frontend.

## Verify email and resend

`POST /doctors/verify-email`

```json
{"challenge_token":"TOKEN_FROM_REGISTRATION","otp":"123456"}
```

OTP above is a format example only; use the actual emailed OTP.

`POST /doctors/resend-otp`

```json
{"challenge_token":"CURRENT_CHALLENGE_TOKEN"}
```

## Login / approval status

Use this body for `POST /doctors/login` or `POST /doctors/approval-status`:

```json
{"email":"doctor@example.com","password":"ExamplePass8!"}
```

Approval-status response contains `public_id`, `email_verified`, `approval_status`, `account_status` and `rejection_reason`.

## Resubmit a rejected application

`POST /doctors/resubmit`

```json
{
  "email":"doctor@example.com",
  "password":"ExamplePass8!",
  "qualification":"MBBS",
  "medical_registration_number":"EXAMPLE-12345",
  "registering_council":"Example Medical Council"
}
```

Only verified, active, rejected doctors can resubmit. This returns the application to review; it does not approve it.

## Protected GET example

```sh
curl 'http://127.0.0.1:5001/api/v1/doctors/me' \
  -H 'Authorization: Bearer DOCTOR_ACCESS_TOKEN'
```

For existing browser cookie auth use the shared `authApi` / `careApi` helpers with credentials included, `X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare` and the login-issued CSRF header for mutations. Do not send patient or admin credentials as a doctor session.

## Vaccination review decision

`POST /doctors/vaccination-reviews/{schedule_id}`

```json
{
  "decision":"APPROVE",
  "notes":"I verified the cited guideline, age window, intervals and eligibility within my professional competence.",
  "attestation":true
}
```

Use `REJECT` to return corrections. Notes require at least 20 meaningful characters. Only the assigned qualified reviewer can decide. Approval does not publish the version; an administrator must separately publish it. Never automatically tick professional attestation in the frontend.

## Password reset

`POST /auth/forgot-password`

```json
{"email":"doctor@example.com"}
```

`POST /auth/reset-password`

```json
{
  "challenge_token":"RESET_CHALLENGE_TOKEN",
  "otp":"123456",
  "new_password":"AnotherExample8!",
  "confirm_password":"AnotherExample8!"
}
```

## Report OCR boundary

The doctor API currently supports reading/downloading accessible reports. Report OCR/translation endpoints are **patient-owner-only**:

`POST/GET /patients/profiles/{profile_id}/reports/{report_id}/text`

A doctor token cannot call this endpoint; it returns 403. There is currently no `/doctors/.../text` OCR endpoint. Do not bypass ownership by sending a patient token from a doctor interface. See [report OCR API](REPORT_OCR_API.md) for the existing owner flow.

## Common errors

Responses use `{ "error": { "code": "...", "message": "..." } }`.
401: absent/invalid session; 403: role/account/CSRF restriction; 404: inaccessible profile/report; 409: invalid application/review state; 422: invalid request fields. The frontend must display the server response rather than treating access errors as an empty patient list.
