# Local backend update — 5 November 2026

Source: `https://github.com/coreoutsourcingservices/family-care.git`, branch `main`, commit `f03ad53f235bbad73a9971295af0708fff238a62`.

The changes between local base `8100b8b` and that source commit were applied only to `backend/` and `api-reference/`. This is a selective source update, not a full branch merge. Local backend edits in `patient/care_controller.py` and `patient/controller.py` were preserved. No commits were created or pushed.

All 375 inventoried frontend files under `app/`, `customer/`, `doctor/` and `admin/` were checked by SHA-256 before and after applying the update. Their contents were unchanged. Root/frontend package manifests were also left unchanged.

## Database activation

Migration files 0028 through 0031 are included. A read-only `alembic current` check reported `0031_health_articles`, which already matches the new head. This update did not run migrations or modify application data. For another environment that is behind, run from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic upgrade head
```

The new head is `0031_health_articles`. These migrations add recycle-bin retention, activity deletion markers, confirmed appointment fields, availability/prescription tables, report titles, pregnancy metadata and health articles. Test database creation does not establish that application migrations have been applied.

The updated launcher starts a recycle cleanup worker. Newly deleted content is retained for 30 days and later purged; this update did not start the launcher or run cleanup against application data. See `ADMIN_RECYCLE_ACTIVITY.md` for the exact retention and restore rules.

## Integrations to add to the existing frontend

Keep the current layout and components. The following are missing integrations or opportunities to expose the new backend; they do not require replacing the frontend with the remote version.

| Priority | Area | Current local frontend and required integration |
| --- | --- | --- |
| Already at head locally | Database | The configured database reports 0031. Other environments must reach 0031 before running the updated backend. A revision check does not independently validate every table/column. |
| Behavior alignment | Report OCR | Upload-triggered OCR now defaults to `auto_import: false`, while `app/src/components/ReportTextPanel.tsx` explicitly sends `true`. Decide whether extraction should create unreviewed records or require explicit review/import, then align the existing component and its messaging. |
| Data preservation | Adult edit forms | New record fields include glucose units/context, medicine strength/dose/frequency/dates/adherence, BP context, screening follow-up, sleep and linked reports. Existing `AdultRecords.tsx` builds a limited replacement payload. Extend the model/form and preserve structured values on edit; send the returned `version` to detect concurrent changes. Avoid displaying mmol/L data under a fixed mg/dL label. |
| Feature UI | Appointments | Existing doctor Appointments shows the old requested-date agenda. Add availability CRUD through `/doctors/appointment-slots`, patient slot selection through `/patients/doctor-directory/{doctor_id}/slots`, and confirmed-time/duration/reschedule controls. Consultation status responses now include `confirmed_at`, `duration_minutes` and `version`; include `version` on updates. Legacy status-only requests remain accepted, with confirmation defaulting to requested time. |
| Feature UI | Prescriptions | Existing doctor Prescriptions lists shared documents. Add structured draft/edit/issue/void controls using `/doctors/care-profiles/{profile_id}/prescriptions` and the decision route. Add issued/voided patient history using `/patients/profiles/{profile_id}/prescriptions`. Honor returned versions, attestation and report-tab permissions. |
| Feature UI | Admin recycle/activity | Add local pages/navigation for recycle listing, restore, confirmed emptying and recent-activity filters/deletion. Admin and Superadmin namespaces have distinct authorization. Preserve confirmations and selection tokens from the API. |
| Feature UI | Doctor network | Add doctor-scoped family/member navigation using `/admin/doctors/{doctor}/families` and equivalent Superadmin endpoints. These return directory metadata, not clinical access. |
| Feature UI | Health articles | Add Admin-only article draft/publish/schedule/archive controls through `/admin/health-articles`; display public Child/Women articles through `/health-articles?audience=child` or `women`. The remote update itself supplies these APIs without an article-management UI. |
| Optional structured inputs | Women/pregnancy | Expose new validated diary fields and pregnancy lifecycle/due-date source fields. Existing versioned diary APIs remain; account for overlap/date validation and ended/postpartum guide behavior. |
| UI accuracy | Reports and reminders | Expose optional multipart report `title` and returned title metadata while retaining filenames. Display personal reminder delivery state returned by the API; do not promise email or push for in-app-only reminders. |

API details: `AUDIT_IMPLEMENTATION.md`, `ADMIN_RECYCLE_ACTIVITY.md`, `DOCTOR_NETWORK_DIRECTORY.md` and `../../api-reference/HEALTH_ARTICLES_API.md`.

## Verification results

- Full backend suite: `217 passed, 6 skipped` in 180.93 seconds using the isolated SQLite test configuration. PostgreSQL-specific tests were skipped; this is not live PostgreSQL workflow validation.
- An additional in-memory SQLite API smoke check passed for health article draft creation, scheduled publication exclusion, immediate publication, audience filtering, unauthorized Admin access, archival and missing-audience validation.
- Read-only application database revision check: `0031_health_articles`.
- All 56 imported paths match the fetched source commit, allowing CRLF/LF differences.
- All 375 inventoried frontend files remain byte-for-byte unchanged. Both pre-existing backend controller edits remain byte-for-byte unchanged.
- The preserved frontend was inspected for integration gaps, but no browser/end-to-end compatibility run was performed. Third-party SMTP, Cloudinary, OCR/translation and real-device push were not exercised against live services.

## Backup

Pre-update copies, the original local diff, the applied remote patch and frontend hashes are stored outside the repository:

`C:\Users\AMANKI~1\AppData\Local\Temp\family-care-before-backend-update-bb3_ub09`

Keep that directory if you need the original state; operating-system temporary-file cleanup may eventually remove it.
