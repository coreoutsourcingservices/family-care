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

## Frontend integration

The shared application retains only registration number and council in the doctor
signup professional step. Remaining information is collected after email
verification in `doctor/src/pages/AccountSetup.tsx`, mounted at
`/doctor/setup-account`. Incomplete/rejected login responses resume this same
page; pending responses show under review and approved sessions open the dashboard.
Setup tokens are passed in memory, not stored in browser storage or URLs.
The form displays verified name/email/mobile read-only and submits only the
documented setup fields. No certificate upload is included.

The configured database already recorded `0010_optional_doctor_degree` while main
was missing that file. A compatibility revision restores the inspected nullable
qualification change without resetting deployed migration history.

## Setup photos and older accounts

Apply migration `0013_doctor_onboarding_images`. `POST /api/v1/doctors/setup-images`
accepts multipart `setup_token`, `kind` (`profile_photo` or `degree_photo`) and `file`.
Both photos are optional; JPEG, PNG and WebP are accepted up to 5 MB per image.
Cloudinary credentials must be configured. Assets use authenticated delivery; setup
and admin-directory responses include five-minute signed URLs under `doctor.images`.
Uploads preserve PROFILE_REQUIRED/REJECTED and never create approval requests.
The existing JSON setup-profile request remains compatible.

A verified legacy PENDING_APPROVAL account with missing address/clinic/experience
and an unreviewed pending request resumes setup on login. The premature request is
removed with an audit entry; complete pending and approved applications are preserved.
Restart the backend and frontend dev servers after updating; old processes may keep
serving the pre-onboarding flow.

The frontend now opens a basic doctor dashboard after OTP verification or an
incomplete-profile login. Set My Profile opens account setup; Proceed for Approval
submits it and returns to the dashboard with a review status. This basic dashboard
does not issue a clinical session or load patient APIs. Clinical access remains
restricted to approved accounts.
