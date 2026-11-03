# FamilyCare audit implementation and verification

Source: user-supplied Complete Project Audit, 3 November 2026. Existing role boundaries, optional doctor images and authenticated APIs are retained. Files that already implement a workflow are verified rather than rewritten solely to match the audit file list.

## Implemented changes

| Area | Result | Main files |
| --- | --- | --- |
| Session protection | Failed or missing patient sessions never render protected children; invalid sessions redirect; network failures offer retry | app/src/components/MemberRouteGuard.tsx |
| Invitations | Removed relationship-word gender assumptions; member-email OTP preserved | app/src/components/FamilyInvitations.tsx |
| Public information | Replaced false preview-only claims with actual storage, sharing, processing, retention and account behavior | app/src/pages/Information.tsx |
| Child vaccination | All/Completed/Upcoming/Overdue filters; no local Read/Unread state; linked doses rendered once; fixed age-group order; doctor attribution | customer/src/modules/child/Vaccination.tsx |
| Doctor vaccination | Select the scheduled dose when recording an administered vaccine; derive vaccine identity server-side; reject duplicate completed linked doses | doctor/src/pages/ChildCare.tsx, backend/services/vaccination.py |
| Child summaries | Independent request outcomes and partial errors; clear stale profile data; chart counts combine schedule and unlinked records | ChildApiPanels.tsx, ChildDashboardCharts.tsx |
| Medical history | Document-first upload/review entry point; manual notes preserved | MedicalHistory.tsx |
| Reports | Descriptive titles and categories; original filenames retained; OCR extraction defaults to no automatic record import; reviewed import stays explicit | care_uploads.py, ReportTextPanel.tsx, ChildHealthReports.tsx, WomenReportUpload.tsx, AdultReports.tsx |
| Women records | Optional structured PCOS source/treatment, symptoms/pain, fertility observations, screening statuses, due-date sources; overlap and date checks | womenRecords.ts, women_workspace.py |
| Pregnancy | Due date/source and ongoing/ended/postpartum state; ended pregnancies stop the weekly guide; version checks retained | pregnancy_guide.py, PregnancyCareGuide.tsx |
| Adult records | BP context, glucose units/context, medicine schedule/adherence, screening follow-up, history type, sleep, linked lipid report and optimistic edit checks | adult_routes.py, AdultRecords.tsx |
| Charts | Separate glucose units rather than mixing measurements; self-reported labels and no invented diagnoses | AdultCharts.tsx, GrowthOverview.tsx |
| Shared access | Correct medicine/lifestyle labels; clear prior profile state; expiry clears Adult shared records; server revocation checks retained | SharedAdultWorkspace.tsx, womenRecords.ts, adult_workspace.py |
| Appointments | Published availability; request is separate from confirmed time; confirm/reschedule/cancel/complete; overlap checks under doctor lock; version checks | appointment_slots.py, consultation_directory.py, Appointments.tsx |
| Prescriptions | Structured medicines, draft editing, doctor-attested immutable issue, issuer registration snapshot, reasoned void, patient issued-history view | prescriptions.py, Prescriptions.tsx, IssuedPrescriptions.tsx |
| Notifications | Due personal reminders become private in-app inbox alerts, deduplicated by record/date; saved and available-in-inbox states distinguished | personal_reminders.py, notifications.py, WomenCalendar.tsx |
| Responsive layout | Shared sizing, bounded large-screen content, mobile forms/tables/dialogs, keyboard focus and touch targets; no CSS page zoom | app/src/audit-responsive.css |
| Admin/Superadmin | Existing approval reasons, private patient-directory boundaries, reviewed vaccine publication, named audit history, recycle/restore/delete flows preserved under regression tests | admin components, existing backend services |

## New API contracts

- GET/POST `/api/v1/doctors/appointment-slots`; DELETE `/<slot_id>` removes unbooked availability.
- GET `/api/v1/patients/doctor-directory/<doctor_id>/slots` lists future, unbooked availability. A slot selection requests a time; it does not automatically confirm a booking.
- PATCH `/api/v1/doctors/consultation-visits/<id>/status` accepts `status`, optional timezone-aware `confirmed_at`, `duration_minutes` (5-240) and current `version`. Overlaps or stale versions return 409. Future appointments cannot be marked completed.
- GET/POST `/api/v1/doctors/care-profiles/<profile_id>/prescriptions`; PUT `/<id>` updates a draft with its version.
- POST `/<id>/decision` accepts `action: ISSUE|VOID`, current `version`, `attestation: true`; VOID requires a reason. Issued content cannot be edited.
- GET `/api/v1/patients/profiles/<profile_id>/prescriptions` returns issued/voided documents only, subject to profile permissions. Adult/Women creation and issuing require edit access to their report tab; view-only grants cannot write prescriptions.
- Adult records accept optional structured context fields; all existing input fields/routes remain compatible. Edit clients send the returned `version`.
- Report multipart uploads accept optional `title` up to 160 characters. New UI uploads require one; legacy clients can continue sending filenames/categories.

## Database and startup

Run `backend/venv/Scripts/python.exe -m alembic upgrade head` from backend. Migration `0030_clinical_workflows` adds confirmed appointment/version fields, availability/prescription tables, report title and pregnancy lifecycle metadata. Existing documents remain intact.

## Verification

- Full backend suite: 211 passed, 6 skipped before the separately added private reminder test. Skipped cases are excluded from the passing count and are not considered verified.
- Seven focused audit workflow tests passed; additional focused runs cover reminder delivery/privacy, prescription edit-scope/expiry and dose identity across schedule versions.
- `npm run typecheck --workspaces --if-present` passed.
- `node app/tests/audit-workflows.mjs`: actual React components with synthetic API responses, five screens at 360/390/768/1366/1920/2560px, overflow checks, vaccination reconciliation, structured fields, appointment payload, prescription draft UI and failed-session guard.
- Public app, customer, doctor and admin production builds passed. Local API readiness and live page/layout checks are verified separately.
- No real patient data was deleted or shared during verification.

## Clinical and operational boundaries

Growth charts show actual recorded values and arithmetic BMI. Age-at-measurement and recorded-sex context link to the appropriate official WHO reference resource. No automatically calculated age/sex percentile, Z-score, diagnosis, fertility guarantee or medicine recommendation is invented without a validated clinical reference and review. Official WHO growth standards and 5-19 reference resources are linked below. IAP-specific reference data, clinical thresholds and clinician approval are not inferred from UI code.

- https://www.who.int/tools/child-growth-standards
- https://www.who.int/tools/growth-reference-data-for-5to19-years

Diary reminders deliver in-app when the notifications refresh; this does not claim email/browser-push delivery. Existing vaccine email consent/published-policy workflows remain separate. SMTP, external translation/OCR, provider approvals and real-device push require their configured runtime services. Factual product privacy copy is not a substitute for the organization's legal review or published support contact details.
