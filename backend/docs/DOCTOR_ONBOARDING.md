# Doctor signup and profile review

Complete requests, responses and admin review examples: [Doctor Onboarding API](DOCTOR_ONBOARDING_API.md).

Flow: basic signup → email OTP verification → setup profile → submit → admin review.

`POST /api/v1/doctors/register` needs only `full_name`, `mobile_number`, `email`,
`password` and `confirm_password`. Existing clients may still send professional fields.

`POST /api/v1/doctors/verify-email` returns HTTP 202 with `requires_profile_setup`,
the verified `user`, existing `doctor` details and a 30-minute `setup_token`.
The user is `PROFILE_REQUIRED`; no approval request or dashboard session is created.

`POST /api/v1/doctors/setup-profile` accepts:

| Field | Required |
| --- | --- |
| setup_token | Yes |
| qualification | Yes |
| medical_registration_number | Yes |
| registering_council | Yes |
| address | Yes, 5–1000 characters |
| clinic_address | Yes, 5–1000 characters |
| years_of_experience | Yes, integer 0–80 |
| specialization | No |
| nmr_id | No |

Name, email and mobile are displayed read-only from the verified account.
Submission creates the approval request and returns `PENDING_APPROVAL` (HTTP 202).
The admin doctor directory and request list include all submitted fields.
Admin can approve or reject with a reason. Only approved doctors receive dashboard sessions.

Doctor login with email/password returns setup details and a new setup token for
incomplete/rejected profiles. Rejected profiles include the reason and previous data.
Pending profiles return HTTP 202 with the under-review message and no session.
Setup tokens cannot authenticate dashboard/clinical APIs or edit an application under review.

Apply migration `0011_doctor_onboarding` before restarting the backend.
Existing submitted and approved accounts are preserved.

The configured database already recorded `0010_optional_doctor_degree` while main
was missing that file. A compatibility revision restores the inspected nullable
qualification change without resetting deployed migration history.
