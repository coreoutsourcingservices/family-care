# Doctor onboarding frontend

The account setup UI is implemented inside the doctor workspace:

- `src/pages/AccountSetup.tsx` — verified identity, professional/practice fields and submit-for-approval status.
- `src/pages/account-setup.css` — desktop/mobile layout.
- `src/onboarding/setupSession.ts` — temporary onboarding-token handoff, held in memory only.
- `src/onboarding/types.ts` — doctor setup/response types.
- `src/pages/DoctorAuth.tsx` — doctor login/signup response routing, using the common auth form controls.
- `src/components/RegistrationFields.tsx` — doctor-only registration number/council/qualification inputs and signup progress.
- `src/data/medicalCouncils.ts` — council dropdown options.
- `src/pages/DoctorDashboard.tsx`, `VaccineReviews.tsx` — doctor pages.
- `src/components/DoctorPatientDirectory.tsx`, `DoctorClinicalRecords.tsx` — doctor-only dashboard components.

The shared public application mounts this module at `/doctor/setup-account`. Run the root `npm run dev`, then enter through `/doctor/signup` or `/doctor/login`. Alternatively, root `npm run dev:doctor` starts the doctor workspace on port 5175 and opens Doctor Login at `/`. Its entry reuses the common router, public assets and API proxy. All doctor-specific pages, components and onboarding state stay inside `doctor/src/`; shared form controls, navbar and HTTP transport remain shared.

## Flow

1. Signup basic details, followed by registration number, council and qualification.
2. Verify the email OTP through the existing API.
3. A `requires_profile_setup` response opens the basic doctor dashboard with Set My Profile. This opens the Account Setup page with the returned `setup_token`, `user`, `doctor` and rejection reason.
4. Complete qualification, personal address, clinic address and years of experience. Specialization and NMR ID are optional. Registration number and council are prefilled and editable for corrections.
5. Proceed for Approval submits `/doctors/setup-profile` and show under review only after the API confirms `PENDING_APPROVAL`.

Name, email and phone are read-only and are not posted back in the setup request. Optional doctor profile and degree photos can be uploaded privately (JPEG/PNG/WebP, up to 5 MB each). Uploads use a setup token and do not request approval; only Proceed for Approval submits the completed profile. Qualification is collected at signup and remains editable during setup.

Incomplete/rejected logins resume setup. Rejected profiles display the reason and saved fields. Pending accounts see the review state, and only approved sessions navigate to the doctor dashboard. The obsolete post-approval practice-completion widget is no longer mounted in that dashboard.

Setup tokens are never saved to URLs, browser storage, history state, or used as dashboard credentials. After reload/expiry, sign in again for a fresh setup response. The server enforces the real token lifetime and approval state. Field validation/network errors preserve the form for retry; expired token errors require re-authentication.

## Verification

From the repository root against a running frontend:

```powershell
node app/scripts/check-doctor-setup.mjs
```

This uses mock API responses in an isolated browser; it sends no real emails or approval applications. It checks signup/OTP/setup, read-only identity, payloads, mobile/desktop layouts, rejection/resubmission, approval gating and recovery from expiry or reload.

The required backend migration is `0013_doctor_onboarding_images`. Cloudinary credentials are required for photo uploads. See `backend/docs/DOCTOR_ONBOARDING_API.md`.

## Purple and pink workspace

`src/components/DoctorWorkspaceLayout.tsx` is the shared dashboard/setup shell.
`DoctorProfileSummary.tsx` shows actual profile completeness. The purple sidebar
shows all clinical menu items as disabled before approval; it has no bottom illustration.
`src/pages/doctor-home.css` supplies responsive desktop/mobile styling. Backend approval
checks remain mandatory for clinical access; disabled controls are not authorization.

## Doctor pages

All routes use the same purple/pink workspace shell:

- `/doctor/dashboard`: onboarding dashboard or approved practice overview.
- `/doctor/setup-account`: editable onboarding profile, or submitted read-only profile.
- `/doctor/patients`: connected family profiles, search and care-area filtering.
- `/doctor/consultations`: family consultation requests and guardian contact links.
- `/doctor/clinical-records`: read-only family-reported history, selected per patient.
- `/doctor/appointments`: requested-date agenda and date filtering (not confirmed bookings).
- `/doctor/prescriptions`: original shared reports with prescription/Rx filenames, not prescription issuance.
- `/doctor/reports`: original shared documents with authenticated downloads.
- `/doctor/settings`: account identity, password change and revoke-all-sessions action.
- `/doctor/vaccination-reviews`: existing assigned medical guideline review flow.

`src/DoctorRoutes.tsx` owns doctor routing. `DoctorSessionGate` restores approved
cookie sessions on direct navigation/reload; `DoctorApprovalGate` blocks clinical
routes for incomplete/pending accounts before their components mount. The backend
also enforces approval and profile ownership. No patient data is persisted in browser storage.

`GET /api/v1/doctors/care-profiles/:id/records` supplies paginated family-reported
history for profiles referred to the current doctor only. POST/PATCH are not enabled.

Browser verification with mocked APIs (no real medical changes):

```powershell
node doctor/scripts/check-workspace.mjs
node app/scripts/check-doctor-setup.mjs
```

## Dashboard charts and notifications

`src/components/DashboardCharts.tsx` renders Chart.js line, doughnut and bar charts
from real connected-profile and consultation data. Required approval and empty-data
states never fabricate chart readings.

`src/notifications/` owns the global inbox, cross-page toast, device permission
controls and subscription API. The shared header bell works on every doctor page;
Settings also exposes device notification preferences. Background delivery uses
the doctor service worker and durable backend push queue. See
`backend/docs/DOCTOR_NOTIFICATIONS.md` for setup, privacy, worker operation and
HTTPS / iPhone Home Screen requirements.

```powershell
node doctor/scripts/check-charts-notifications.mjs
```
