# Complete doctor APIs: request and output JSON

Synthetic examples captured from isolated SQLite. Credentials, tokens, IDs and links are examples, not live patient data. Scenarios have separate preconditions; do not run this file as one linear workflow.

Base: `http://127.0.0.1:5001/api/v1`. Protected requests use `Authorization: Bearer DOCTOR_ACCESS_TOKEN`. PATIENT actions require the patient token. GET has no body. Refresh requires its refresh-token credential in JSON.

Doctor login uses email/password; no doctor login-OTP endpoint exists. Email verification and password-reset OTP are separate. Cookie-mode login sets HttpOnly cookies and omits access/refresh tokens from JSON.

## API index

| # | Method | Endpoint | Auth | HTTP |
| --- | --- | --- | --- | --- |
| 1 | POST | `/doctors/register` | PUBLIC | 202 |
| 2 | POST | `/doctors/resend-otp` | PUBLIC | 200 |
| 3 | POST | `/auth/request-email-verification` | PUBLIC | 202 |
| 4 | POST | `/doctors/verify-email` | PUBLIC | 202 |
| 5 | POST | `/doctors/approval-status` | PUBLIC | 200 |
| 6 | POST | `/doctors/resubmit` | PUBLIC | 202 |
| 7 | POST | `/doctors/login` | PUBLIC | 200 |
| 8 | GET | `/doctors/me` | DOCTOR | 200 |
| 9 | GET | `/doctors/referral` | DOCTOR | 200 |
| 10 | POST | `/patients/register` | PUBLIC | 202 |
| 11 | POST | `/patients/verify-email` | PUBLIC | 200 |
| 12 | POST | `/patients/connect-doctor` | PATIENT | 200 |
| 13 | GET | `/patients/doctor` | PATIENT | 200 |
| 14 | POST | `/patients/profiles` | PATIENT | 201 |
| 15 | POST | `/patients/profiles/33333333-3333-4333-8333-333333333333/connect-doctor` | PATIENT | 200 |
| 16 | GET | `/doctors/patients?page=1&per_page=25` | DOCTOR | 200 |
| 17 | GET | `/doctors/care-profiles?module=child&page=1&per_page=25` | DOCTOR | 200 |
| 18 | GET | `/doctors/care-profiles/33333333-3333-4333-8333-333333333333` | DOCTOR | 200 |
| 19 | GET | `/doctors/care-profiles/33333333-3333-4333-8333-333333333333/reports?page=1&per_page=25` | DOCTOR | 200 |
| 20 | GET | `/doctors/care-profiles/33333333-3333-4333-8333-333333333333/reports/44444444-4444-4444-8444-444444444444/download` | DOCTOR | 200 |
| 21 | POST | `/children/33333333-3333-4333-8333-333333333333/consultation-requests` | PATIENT | 201 |
| 22 | GET | `/doctors/consultation-requests?page=1&per_page=25` | DOCTOR | 200 |
| 23 | GET | `/children/33333333-3333-4333-8333-333333333333/consultation-requests?page=1&per_page=25` | DOCTOR | 200 |
| 24 | GET | `/doctors/vaccination-reviews?page=1&per_page=25` | DOCTOR | 200 |
| 25 | POST | `/doctors/vaccination-reviews/55555555-5555-4555-8555-555555555555` | DOCTOR | 200 |
| 26 | POST | `/auth/refresh` | PUBLIC | 200 |
| 27 | GET | `/auth/sessions` | DOCTOR | 200 |
| 28 | DELETE | `/auth/sessions/b7ef7110-27b7-4d66-985e-9845284a76e8` | DOCTOR | 200 |
| 29 | POST | `/auth/change-password` | DOCTOR | 200 |
| 30 | POST | `/auth/forgot-password` | PUBLIC | 202 |
| 31 | POST | `/auth/resend-otp` | PUBLIC | 200 |
| 32 | POST | `/auth/reset-password` | PUBLIC | 200 |
| 33 | POST | `/auth/logout` | DOCTOR | 200 |
| 34 | POST | `/auth/logout-all` | DOCTOR | 200 |

## 1. Doctor registration

`POST http://127.0.0.1:5001/api/v1/doctors/register`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "full_name": "Dr New Example",
  "email": "new-doctor@example.com",
  "mobile_number": "+919876543219",
  "password": "ExamplePass8!",
  "confirm_password": "ExamplePass8!",
  "qualification": "MBBS",
  "medical_registration_number": "DEMO-12345",
  "registering_council": "Example Council",
  "specialization": "Pediatrics"
}
```

Output JSON - HTTP 202:

```json
{
  "approval_status": "PENDING_EMAIL_VERIFICATION",
  "challenge_token": "{{challenge_token}}",
  "email_status": "sent",
  "expires_in": 300,
  "message": "OTP sent to your email. Verify OTP to complete registration.",
  "public_id": null,
  "resend_after": 60,
  "user_id": null
}
```

## 2. Doctor resend email OTP

`POST http://127.0.0.1:5001/api/v1/doctors/resend-otp`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "challenge_token": "{{challenge_token}}"
}
```

Output JSON - HTTP 200:

```json
{
  "challenge_token": "{{challenge_token}}",
  "email_status": "sent",
  "expires_in": 300,
  "message": "OTP sent to your email. Verify OTP to complete registration.",
  "resend_after": 60
}
```

## 3. Restart pending email verification

`POST http://127.0.0.1:5001/api/v1/auth/request-email-verification`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "email": "new-doctor@example.com",
  "password": "ExamplePass8!"
}
```

Output JSON - HTTP 202:

```json
{
  "challenge_token": "{{challenge_token}}",
  "email_status": "sent",
  "expires_in": 300,
  "message": "OTP sent to your email. Verify OTP to complete registration.",
  "resend_after": 60
}
```

## 4. Verify doctor email

`POST http://127.0.0.1:5001/api/v1/doctors/verify-email`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "challenge_token": "{{challenge_token}}",
  "otp": "123456"
}
```

Output JSON - HTTP 202:

```json
{
  "message": "Email verified. Waiting for approval.",
  "user": {
    "account_status": "ACTIVE",
    "approval_status": "PENDING_APPROVAL",
    "email": "new-doctor@example.com",
    "email_verified": true,
    "full_name": "Dr New Example",
    "id": "cf5c4ef0-50b2-454b-823f-e42dab16c2c5",
    "must_change_password": false,
    "phone_number": "+919876543219",
    "public_id": "D6b75fdcd6046",
    "referral_id": "newexampleD6b75fdcd6046",
    "role": "DOCTOR"
  }
}
```

## 5. Doctor approval status

`POST http://127.0.0.1:5001/api/v1/doctors/approval-status`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "email": "new-doctor@example.com",
  "password": "ExamplePass8!"
}
```

Output JSON - HTTP 200:

```json
{
  "account_status": "ACTIVE",
  "approval_status": "PENDING_APPROVAL",
  "email_verified": true,
  "public_id": "D6b75fdcd6046",
  "rejection_reason": null
}
```

## 6. Resubmit rejected doctor application

`POST http://127.0.0.1:5001/api/v1/doctors/resubmit`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "email": "new-doctor@example.com",
  "password": "ExamplePass8!",
  "qualification": "MBBS",
  "medical_registration_number": "DEMO-12345-CORRECTED",
  "registering_council": "Example Council"
}
```

Output JSON - HTTP 202:

```json
{
  "message": "Resubmitted for review",
  "user": {
    "account_status": "ACTIVE",
    "approval_status": "PENDING_APPROVAL",
    "email": "new-doctor@example.com",
    "email_verified": true,
    "full_name": "Dr New Example",
    "id": "cf5c4ef0-50b2-454b-823f-e42dab16c2c5",
    "must_change_password": false,
    "phone_number": "+919876543219",
    "public_id": "D6b75fdcd6046",
    "referral_id": "newexampleD6b75fdcd6046",
    "role": "DOCTOR"
  }
}
```

## 7. Doctor login - Bearer response

`POST http://127.0.0.1:5001/api/v1/doctors/login`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "email": "doctor@example.com",
  "password": "SmokePassword8!"
}
```

Output JSON - HTTP 200:

```json
{
  "access_token": "{{access_token}}",
  "expires_in": 86400,
  "refresh_token": "{{refresh_token}}",
  "token_type": "Bearer",
  "user": {
    "account_status": "ACTIVE",
    "approval_status": "APPROVED",
    "email": "doctor@example.com",
    "email_verified": true,
    "full_name": "Dr Example Kumar",
    "id": "11111111-1111-4111-8111-111111111111",
    "must_change_password": false,
    "phone_number": null,
    "public_id": "D000001",
    "referral_id": "examplekumarD000001",
    "role": "DOCTOR"
  }
}
```

## 8. Doctor profile

`GET http://127.0.0.1:5001/api/v1/doctors/me`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "user": {
    "account_status": "ACTIVE",
    "approval_status": "APPROVED",
    "doctor": {
      "medical_registration_number": "TEST-1",
      "nmr_id": null,
      "qualification": "MBBS",
      "registering_council": "Test Council",
      "specialization": null,
      "verification_status": "APPROVED"
    },
    "email": "doctor@example.com",
    "email_verified": true,
    "full_name": "Dr Example Kumar",
    "id": "11111111-1111-4111-8111-111111111111",
    "must_change_password": false,
    "phone_number": null,
    "public_id": "D000001",
    "referral_id": "examplekumarD000001",
    "role": "DOCTOR"
  }
}
```

## 9. Own doctor referral ID

`GET http://127.0.0.1:5001/api/v1/doctors/referral`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "doctor": {
    "account_status": "ACTIVE",
    "approval_status": "APPROVED",
    "email": "doctor@example.com",
    "full_name": "Dr Example Kumar",
    "mobile_number": null,
    "public_id": "D000001",
    "referral_id": "examplekumarD000001"
  }
}
```

## 10. New patient signup with doctor referral

`POST http://127.0.0.1:5001/api/v1/patients/register`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "full_name": "New Example Parent",
  "email": "new-parent@example.com",
  "mobile_number": "+919876543218",
  "password": "ExampleParent8!",
  "confirm_password": "ExampleParent8!",
  "referral_id": "examplekumarD000001"
}
```

Output JSON - HTTP 202:

```json
{
  "approval_status": "PENDING_EMAIL_VERIFICATION",
  "challenge_token": "{{challenge_token}}",
  "email_status": "sent",
  "expires_in": 300,
  "message": "OTP sent to your email. Verify OTP to complete registration.",
  "public_id": null,
  "resend_after": 60,
  "user_id": null
}
```

## 11. Verify referred patient signup

`POST http://127.0.0.1:5001/api/v1/patients/verify-email`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "challenge_token": "{{challenge_token}}",
  "otp": "123456"
}
```

Output JSON - HTTP 200:

```json
{
  "access_token": "{{access_token}}",
  "expires_in": 86400,
  "refresh_token": "{{refresh_token}}",
  "token_type": "Bearer",
  "user": {
    "account_status": "ACTIVE",
    "approval_status": "APPROVED",
    "email": "new-parent@example.com",
    "email_verified": true,
    "full_name": "New Example Parent",
    "id": "4c712819-4d84-4133-a2b9-a6fbae14a20f",
    "must_change_password": false,
    "phone_number": "+919876543218",
    "public_id": "Ce1417d884420",
    "referred_doctor": {
      "account_status": "ACTIVE",
      "approval_status": "APPROVED",
      "email": "doctor@example.com",
      "full_name": "Dr Example Kumar",
      "mobile_number": null,
      "public_id": "D000001",
      "referral_id": "examplekumarD000001"
    },
    "role": "PATIENT"
  }
}
```

## 12. Connect parent account using referral

`POST http://127.0.0.1:5001/api/v1/patients/connect-doctor`

Authentication: **PATIENT**.

Request JSON:

```json
{
  "referral_id": "examplekumarD000001"
}
```

Output JSON - HTTP 200:

```json
{
  "doctor": {
    "account_status": "ACTIVE",
    "approval_status": "APPROVED",
    "email": "doctor@example.com",
    "full_name": "Dr Example Kumar",
    "mobile_number": null,
    "public_id": "D000001",
    "referral_id": "examplekumarD000001"
  },
  "message": "Patient connected to doctor"
}
```

## 13. Parent connected doctor

`GET http://127.0.0.1:5001/api/v1/patients/doctor`

Authentication: **PATIENT**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "doctor": {
    "account_status": "ACTIVE",
    "approval_status": "APPROVED",
    "email": "doctor@example.com",
    "full_name": "Dr Example Kumar",
    "mobile_number": null,
    "public_id": "D000001",
    "referral_id": "examplekumarD000001"
  }
}
```

## 14. Create child profile with referral

`POST http://127.0.0.1:5001/api/v1/patients/profiles`

Authentication: **PATIENT**.

Request JSON:

```json
{
  "profile_type": "member",
  "module": "child",
  "full_name": "Example Child",
  "date_of_birth": "2020-03-01",
  "guardian_contact": "+919876543210",
  "emergency_contacts": [],
  "referral_id": "examplekumarD000001"
}
```

Output JSON - HTTP 201:

```json
{
  "profile": {
    "created_at": "2026-10-28T10:48:32.500474Z",
    "date_of_birth": "2020-03-01",
    "doctor": {
      "account_status": "ACTIVE",
      "approval_status": "APPROVED",
      "email": "doctor@example.com",
      "full_name": "Dr Example Kumar",
      "mobile_number": null,
      "public_id": "D000001",
      "referral_id": "examplekumarD000001"
    },
    "emergency_contacts": [],
    "full_name": "Example Child",
    "guardian_contact": "+919876543210",
    "id": "33333333-3333-4333-8333-333333333333",
    "module": "child",
    "parent_profile_id": null,
    "profile_type": "member"
  }
}
```

## 15. Connect existing family profile using referral

`POST http://127.0.0.1:5001/api/v1/patients/profiles/33333333-3333-4333-8333-333333333333/connect-doctor`

Authentication: **PATIENT**.

Request JSON:

```json
{
  "referral_id": "examplekumarD000001"
}
```

Output JSON - HTTP 200:

```json
{
  "profile": {
    "created_at": "2026-10-28T10:48:32.500474Z",
    "date_of_birth": "2020-03-01",
    "doctor": {
      "account_status": "ACTIVE",
      "approval_status": "APPROVED",
      "email": "doctor@example.com",
      "full_name": "Dr Example Kumar",
      "mobile_number": null,
      "public_id": "D000001",
      "referral_id": "examplekumarD000001"
    },
    "emergency_contacts": [],
    "full_name": "Example Child",
    "guardian_contact": "+919876543210",
    "id": "33333333-3333-4333-8333-333333333333",
    "module": "child",
    "parent_profile_id": null,
    "profile_type": "member"
  }
}
```

## 16. Doctor connected patient accounts

`GET http://127.0.0.1:5001/api/v1/doctors/patients?page=1&per_page=25`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "items": [
    {
      "account_status": "ACTIVE",
      "approval_status": "APPROVED",
      "email": "patient@example.com",
      "email_verified": true,
      "full_name": "Example Parent",
      "id": "22222222-2222-4222-8222-222222222222",
      "must_change_password": false,
      "phone_number": null,
      "public_id": "C000001",
      "referred_doctor": {
        "account_status": "ACTIVE",
        "approval_status": "APPROVED",
        "email": "doctor@example.com",
        "full_name": "Dr Example Kumar",
        "mobile_number": null,
        "public_id": "D000001",
        "referral_id": "examplekumarD000001"
      },
      "role": "PATIENT"
    },
    {
      "account_status": "ACTIVE",
      "approval_status": "APPROVED",
      "email": "new-parent@example.com",
      "email_verified": true,
      "full_name": "New Example Parent",
      "id": "4c712819-4d84-4133-a2b9-a6fbae14a20f",
      "must_change_password": false,
      "phone_number": "+919876543218",
      "public_id": "Ce1417d884420",
      "referred_doctor": {
        "account_status": "ACTIVE",
        "approval_status": "APPROVED",
        "email": "doctor@example.com",
        "full_name": "Dr Example Kumar",
        "mobile_number": null,
        "public_id": "D000001",
        "referral_id": "examplekumarD000001"
      },
      "role": "PATIENT"
    }
  ],
  "page": 1,
  "per_page": 25,
  "total": 2
}
```

## 17. Doctor connected child care profiles

`GET http://127.0.0.1:5001/api/v1/doctors/care-profiles?module=child&page=1&per_page=25`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "items": [
    {
      "created_at": "2026-10-28T10:48:32.500474Z",
      "date_of_birth": "2020-03-01",
      "doctor": {
        "account_status": "ACTIVE",
        "approval_status": "APPROVED",
        "email": "doctor@example.com",
        "full_name": "Dr Example Kumar",
        "mobile_number": null,
        "public_id": "D000001",
        "referral_id": "examplekumarD000001"
      },
      "emergency_contacts": [],
      "full_name": "Example Child",
      "guardian_contact": "+919876543210",
      "id": "33333333-3333-4333-8333-333333333333",
      "module": "child",
      "parent_profile_id": null,
      "profile_type": "member"
    }
  ],
  "page": 1,
  "per_page": 25,
  "total": 1
}
```

## 18. Doctor care profile detail

`GET http://127.0.0.1:5001/api/v1/doctors/care-profiles/33333333-3333-4333-8333-333333333333`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "profile": {
    "created_at": "2026-10-28T10:48:32.500474Z",
    "date_of_birth": "2020-03-01",
    "doctor": {
      "account_status": "ACTIVE",
      "approval_status": "APPROVED",
      "email": "doctor@example.com",
      "full_name": "Dr Example Kumar",
      "mobile_number": null,
      "public_id": "D000001",
      "referral_id": "examplekumarD000001"
    },
    "emergency_contacts": [],
    "full_name": "Example Child",
    "guardian_contact": "+919876543210",
    "id": "33333333-3333-4333-8333-333333333333",
    "module": "child",
    "parent_profile_id": null,
    "profile_type": "member"
  }
}
```

## 19. Doctor reports list

`GET http://127.0.0.1:5001/api/v1/doctors/care-profiles/33333333-3333-4333-8333-333333333333/reports?page=1&per_page=25`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "items": [
    {
      "asset_id": null,
      "content_type": "application/pdf",
      "created_at": "2026-10-28T10:48:32.581971Z",
      "delivery_type": "authenticated",
      "folder": null,
      "id": "44444444-4444-4444-8444-444444444444",
      "name": "Example report.pdf",
      "profile_id": "33333333-3333-4333-8333-333333333333",
      "public_id": "synthetic/example.pdf",
      "resource_type": "raw",
      "secure_url": "https://res.cloudinary.com/example-cloud/raw/authenticated/synthetic/example.pdf",
      "size_bytes": 1024,
      "storage_provider": "cloudinary",
      "url": "https://api.cloudinary.com/v1_1/example-cloud/raw/download?SIGNED_PARAMETERS",
      "url_expires_in": 300
    }
  ],
  "page": 1,
  "per_page": 25,
  "total": 1
}
```

## 20. Doctor report download JSON

`GET http://127.0.0.1:5001/api/v1/doctors/care-profiles/33333333-3333-4333-8333-333333333333/reports/44444444-4444-4444-8444-444444444444/download`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "report": {
    "asset_id": null,
    "content_type": "application/pdf",
    "created_at": "2026-10-28T10:48:32.581971Z",
    "delivery_type": "authenticated",
    "folder": null,
    "id": "44444444-4444-4444-8444-444444444444",
    "name": "Example report.pdf",
    "profile_id": "33333333-3333-4333-8333-333333333333",
    "public_id": "synthetic/example.pdf",
    "resource_type": "raw",
    "secure_url": "https://res.cloudinary.com/example-cloud/raw/authenticated/synthetic/example.pdf",
    "size_bytes": 1024,
    "storage_provider": "cloudinary",
    "url": "https://api.cloudinary.com/v1_1/example-cloud/raw/download?SIGNED_PARAMETERS",
    "url_expires_in": 300
  }
}
```

## 21. Parent sends consultation request

`POST http://127.0.0.1:5001/api/v1/children/33333333-3333-4333-8333-333333333333/consultation-requests`

Authentication: **PATIENT**.

Request JSON:

```json
{
  "title": "Routine review request",
  "date": "2026-10-28",
  "notes": "Synthetic request only"
}
```

Output JSON - HTTP 201:

```json
{
  "record": {
    "batch_number": "",
    "category": "",
    "certificate_id": null,
    "date": "2026-10-28",
    "doctor_id": "11111111-1111-4111-8111-111111111111",
    "dose_code": "",
    "height": "",
    "id": "7f7afb1b-dfd3-47a6-9aed-0a484142fec2",
    "kind": "consultation_request",
    "meal": "",
    "nextDate": "",
    "notes": "Synthetic request only",
    "provider": "",
    "schedule_id": null,
    "schedule_type": "",
    "source_id": null,
    "status": "REQUESTED",
    "title": "Routine review request",
    "vaccinator": "",
    "vaccine_id": null,
    "verification_status": "PARENT_REPORTED",
    "weight": ""
  }
}
```

## 22. Doctor consultation requests

`GET http://127.0.0.1:5001/api/v1/doctors/consultation-requests?page=1&per_page=25`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "items": [
    {
      "batch_number": "",
      "category": "",
      "certificate_id": null,
      "child_id": "33333333-3333-4333-8333-333333333333",
      "date": "2026-10-28",
      "doctor_id": "11111111-1111-4111-8111-111111111111",
      "dose_code": "",
      "height": "",
      "id": "7f7afb1b-dfd3-47a6-9aed-0a484142fec2",
      "kind": "consultation_request",
      "meal": "",
      "nextDate": "",
      "notes": "Synthetic request only",
      "provider": "",
      "schedule_id": null,
      "schedule_type": "",
      "source_id": null,
      "status": "REQUESTED",
      "title": "Routine review request",
      "vaccinator": "",
      "vaccine_id": null,
      "verification_status": "PARENT_REPORTED",
      "weight": ""
    }
  ],
  "page": 1,
  "per_page": 25,
  "total": 1
}
```

## 23. Doctor requests for connected child

`GET http://127.0.0.1:5001/api/v1/children/33333333-3333-4333-8333-333333333333/consultation-requests?page=1&per_page=25`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "items": [
    {
      "batch_number": "",
      "category": "",
      "certificate_id": null,
      "date": "2026-10-28",
      "doctor_id": "11111111-1111-4111-8111-111111111111",
      "dose_code": "",
      "height": "",
      "id": "7f7afb1b-dfd3-47a6-9aed-0a484142fec2",
      "kind": "consultation_request",
      "meal": "",
      "nextDate": "",
      "notes": "Synthetic request only",
      "provider": "",
      "schedule_id": null,
      "schedule_type": "",
      "source_id": null,
      "status": "REQUESTED",
      "title": "Routine review request",
      "vaccinator": "",
      "vaccine_id": null,
      "verification_status": "PARENT_REPORTED",
      "weight": ""
    }
  ],
  "page": 1,
  "per_page": 25,
  "total": 1
}
```

## 24. Assigned doctor vaccination reviews

`GET http://127.0.0.1:5001/api/v1/doctors/vaccination-reviews?page=1&per_page=25`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "items": [
    {
      "age_end": 7,
      "age_label": "Synthetic example only",
      "age_start": 6,
      "age_unit": "years",
      "dose_code": "D1",
      "dose_name": "Synthetic dose",
      "effective_from": "2026-01-01",
      "effective_to": null,
      "eligibility": {
        "active": true,
        "country": "IN",
        "districts": [],
        "gender": "All",
        "programme": "",
        "requires_clinical_review": true,
        "states": []
      },
      "id": "55555555-5555-4555-8555-555555555555",
      "injection_site": "",
      "instructions": "",
      "maximum_age": null,
      "minimum_age": null,
      "minimum_interval_days": null,
      "previous_dose_code": "",
      "published_at": null,
      "reminders": {
        "before_days": [
          7
        ],
        "email": false,
        "enabled": true,
        "in_app": true,
        "language": "en",
        "on_due": true,
        "overdue_days": [
          7
        ]
      },
      "route": "Other",
      "schedule_type": "UIP",
      "source_reference": "Synthetic fixture, not a clinical guideline",
      "source_url": "https://example.org/synthetic-guideline",
      "status": "IN_REVIEW",
      "vaccine": {
        "active": true,
        "category": "Government",
        "code": "EXAMPLE",
        "description_en": "",
        "description_hi": "",
        "id": "b103a2b7-4c93-4275-8e05-1d9384a1bc37",
        "name_en": "Synthetic vaccine",
        "name_hi": "",
        "protects_against": "Synthetic example only"
      },
      "vaccine_id": "b103a2b7-4c93-4275-8e05-1d9384a1bc37",
      "version": "demo-v1"
    }
  ],
  "page": 1,
  "per_page": 25,
  "total": 1
}
```

## 25. Doctor approves assigned review

`POST http://127.0.0.1:5001/api/v1/doctors/vaccination-reviews/55555555-5555-4555-8555-555555555555`

Authentication: **DOCTOR**.

Request JSON:

```json
{
  "decision": "APPROVE",
  "notes": "Synthetic fixture review, not a clinical approval of real patient care.",
  "attestation": true
}
```

Output JSON - HTTP 200:

```json
{
  "schedule": {
    "age_end": 7,
    "age_label": "Synthetic example only",
    "age_start": 6,
    "age_unit": "years",
    "dose_code": "D1",
    "dose_name": "Synthetic dose",
    "effective_from": "2026-01-01",
    "effective_to": null,
    "eligibility": {
      "active": true,
      "country": "IN",
      "districts": [],
      "gender": "All",
      "programme": "",
      "requires_clinical_review": true,
      "states": []
    },
    "id": "55555555-5555-4555-8555-555555555555",
    "injection_site": "",
    "instructions": "",
    "maximum_age": null,
    "medical_review": {
      "council": "Test Council",
      "name": "Dr Example Kumar",
      "notes": "Synthetic fixture review, not a clinical approval of real patient care.",
      "qualification": "MBBS",
      "registration": "TEST-1",
      "reviewed_at": "2026-10-28T10:48:33.150282Z"
    },
    "minimum_age": null,
    "minimum_interval_days": null,
    "previous_dose_code": "",
    "published_at": null,
    "reminders": {
      "before_days": [
        7
      ],
      "email": false,
      "enabled": true,
      "in_app": true,
      "language": "en",
      "on_due": true,
      "overdue_days": [
        7
      ]
    },
    "route": "Other",
    "schedule_type": "UIP",
    "source_reference": "Synthetic fixture, not a clinical guideline",
    "source_url": "https://example.org/synthetic-guideline",
    "status": "APPROVED",
    "vaccine": {
      "active": true,
      "category": "Government",
      "code": "EXAMPLE",
      "description_en": "",
      "description_hi": "",
      "id": "b103a2b7-4c93-4275-8e05-1d9384a1bc37",
      "name_en": "Synthetic vaccine",
      "name_hi": "",
      "protects_against": "Synthetic example only"
    },
    "vaccine_id": "b103a2b7-4c93-4275-8e05-1d9384a1bc37",
    "version": "demo-v1"
  }
}
```

## 26. Refresh doctor Bearer session

`POST http://127.0.0.1:5001/api/v1/auth/refresh`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "refresh_token": "{{refresh_token}}"
}
```

Output JSON - HTTP 200:

```json
{
  "access_token": "{{access_token}}",
  "expires_in": 86400,
  "refresh_token": "{{refresh_token}}",
  "token_type": "Bearer",
  "user": {
    "account_status": "ACTIVE",
    "approval_status": "APPROVED",
    "email": "doctor@example.com",
    "email_verified": true,
    "full_name": "Dr Example Kumar",
    "id": "11111111-1111-4111-8111-111111111111",
    "must_change_password": false,
    "phone_number": null,
    "public_id": "D000001",
    "referral_id": "examplekumarD000001",
    "role": "DOCTOR"
  }
}
```

## 27. Doctor active sessions

`GET http://127.0.0.1:5001/api/v1/auth/sessions`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "items": [
    {
      "created_at": "2026-10-28T10:48:31.663144Z",
      "current": true,
      "expires_at": "2026-11-27T10:48:31.660233Z",
      "id": "e4f25ce8-b1c6-4512-81fd-dee2fadfba5a"
    }
  ]
}
```

## 28. Revoke another doctor session

`DELETE http://127.0.0.1:5001/api/v1/auth/sessions/b7ef7110-27b7-4d66-985e-9845284a76e8`

Authentication: **DOCTOR**.

Request body: **none**.

Output JSON - HTTP 200:

```json
{
  "message": "Session revoked"
}
```

## 29. Doctor password change

`POST http://127.0.0.1:5001/api/v1/auth/change-password`

Authentication: **DOCTOR**.

Request JSON:

```json
{
  "current_password": "SmokePassword8!",
  "new_password": "ChangedExample8!",
  "confirm_password": "ChangedExample8!"
}
```

Output JSON - HTTP 200:

```json
{
  "message": "Password changed. All sessions revoked; sign in again."
}
```

## 30. Doctor forgot password

`POST http://127.0.0.1:5001/api/v1/auth/forgot-password`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "email": "doctor@example.com"
}
```

Output JSON - HTTP 202:

```json
{
  "challenge_token": "{{challenge_token}}",
  "email_status": "queued",
  "expires_in": 300,
  "message": "If an eligible account exists, reset instructions are queued.",
  "resend_after": 60
}
```

## 31. Resend password reset OTP

`POST http://127.0.0.1:5001/api/v1/auth/resend-otp`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "challenge_token": "{{challenge_token}}"
}
```

Output JSON - HTTP 200:

```json
{
  "challenge_token": "{{challenge_token}}",
  "email_status": "queued",
  "expires_in": 300,
  "resend_after": 60
}
```

## 32. Doctor reset password

`POST http://127.0.0.1:5001/api/v1/auth/reset-password`

Authentication: **PUBLIC**.

Request JSON:

```json
{
  "challenge_token": "{{challenge_token}}",
  "otp": "123456",
  "new_password": "ResetExample8!",
  "confirm_password": "ResetExample8!"
}
```

Output JSON - HTTP 200:

```json
{
  "message": "Password reset. Sign in again."
}
```

## 33. Doctor logout

`POST http://127.0.0.1:5001/api/v1/auth/logout`

Authentication: **DOCTOR**.

Request JSON:

```json
{}
```

Output JSON - HTTP 200:

```json
{
  "message": "Logged out"
}
```

## 34. Doctor logout all devices

`POST http://127.0.0.1:5001/api/v1/auth/logout-all`

Authentication: **DOCTOR**.

Request JSON:

```json
{}
```

Output JSON - HTTP 200:

```json
{
  "message": "All sessions revoked"
}
```

## Access and workflow notes

- Account referral and family-profile referral are separate. `/doctors/patients` lists account referrals; `/doctors/care-profiles` lists profile referrals.
- Doctor report endpoints read/download only. OCR/translation requires the patient owner; no doctor OCR endpoint exists.
- Consultation endpoints list requests. No doctor consultation accept/reject/book endpoint is implemented.
- Review decision may be APPROVE or REJECT. REJECT returns a schedule to DRAFT. Do not automate professional attestation from these synthetic examples. Admin publication is separate.
- `/auth/initial-password` is superadmin bootstrap, not a doctor flow. Password changes/reset revoke sessions; resend has a 60-second cooldown.
- Pagination: page >= 1, per_page 1-100. Errors: 401 invalid session, 403 role/account/CSRF restriction, 404 inaccessible record, 409 invalid state, 422 invalid fields, 429 cooldown/rate limit.

```json
{"error":{"code":"forbidden","message":"Insufficient permissions"}}
```
