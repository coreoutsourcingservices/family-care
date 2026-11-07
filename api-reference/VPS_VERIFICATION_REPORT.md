# VPS verification — 7 November 2026

The release working tree was tested before committing, including its new files.
The results apply to these reviewed changes, not to older versions of `main`.

## Result

Local functional, build and responsive-design checks passed. A staging deployment
is reasonable once the verified local changes are included in the release.
Production infrastructure and external-service delivery still need verification
on the actual VPS/domain; this report is not an unconditional production sign-off.

| Check | Result | Scope |
| --- | --- | --- |
| Full backend suite | 249 passed, 6 skipped | Isolated test database; the six skipped tests require an isolated local PostgreSQL test database for locks/sequences |
| Localization after proxy-config fix | 13 passed | Includes reading the trusted-proxy environment setting |
| Fresh critical-flow recheck | 26 passed | Booking/cancellation, sharing, localization and report upload/extraction test flows |
| Workspace production builds | Passed | Public app, customer, doctor and Next.js admin |
| Final public-app build | Passed | Rebuilt after the mobile profile-selector fix |
| Production static-app smoke | Passed | Built `app/dist`, direct URL reloads and JS/CSS assets; 390/1366px |
| Public-page layout | Passed | Home, services, privacy, terms and both login screens; 360–2560px |
| Doctor pages | Passed | Dashboard, patients, consultations, appointments, clinical records, reports, prescriptions and subscription; 255/320/390/1366/1440px |
| Admin/Superadmin | Passed | Dashboard, doctors, patients, doctor details, vaccination, settings, administrators and audit screens; desktop/tablet/mobile navigation |
| Booking | Passed | Adult, Women and Child; mode/fee selection, full-slot handling, notes, document upload payload, compact calendar and missing legacy fee fields |
| Sharing/loading | Passed | Adult/Women scoped records/reports, persistent doctor sidebar/session, cached data during slow background fetches |
| Language/guidance | Passed | English/Hindi, IP-state metadata, more-language picker, page-specific reference cards, saved BP reading, child age-based API guide |
| Python dependency consistency | Passed | `pip check` |
| Current PostgreSQL connectivity | Passed | Server readiness check; migration head `0034_consultation_booking` |

Protected browser-flow tests use synthetic API fixtures. They verify the real UI
components and request payloads without changing real medical records. Backend
tests separately exercise permission enforcement and persistence. Actual SMTP
inbox delivery, Cloudinary upload/download, OCR extraction and concurrency on the
VPS were not end-to-end verified by these browser checks.

## Issues found and corrected

- On narrow screens the language selector squeezed the Adult profile dropdown
  until its name was unreadable. The actions row now has enough width, and the
  booking regression test asserts a readable profile-selector width.
- `GEO_TRUSTED_PROXIES` was used by localization but not loaded from environment
  configuration. It is now loaded, documented in `.env.example`, and tested.
  The default remains empty: forwarding headers are not trusted automatically.
- The standalone Admin UI test did not define Next.js build-time public portal
  URLs. Its fixture now supplies synthetic URLs, and all portal-page checks pass.

## Required release steps

1. Deploy the release containing the verified frontend/backend changes and new
   files. In particular, include migration
   `backend/migrations/versions/0034_consultation_booking_details.py` and the new
   booking, guidance and language components. Do not deploy an older `main` commit.
2. Create a fresh Linux Python environment on the VPS; do not copy the Windows
   `.venv`. Install backend dependencies and build the frontends from the release
   lockfile. No VPS commands were executed during this local review.
3. Configure production environment values privately:
   - `APP_ENV=production`, `COOKIE_SECURE=true` and a reachable Redis
     `RATELIMIT_STORAGE_URI` are required by backend startup validation.
   - Use distinct strong JWT/OTP secrets and correct database credentials.
   - Set `CORS_ORIGINS` and `FAMILY_INVITE_FRONTEND_URL` to the real HTTPS origins.
   - Set the Admin build-time `NEXT_PUBLIC_DOCTOR_PORTAL_URL` and
     `NEXT_PUBLIC_CUSTOMER_PORTAL_URL` to deployed portal origins; local defaults
     point to localhost. Set its server-side `BACKEND_URL` appropriately.
   - Leave the public app's API base relative when using a same-origin reverse
     proxy. Never build a VPS release with a localhost API URL exposed to clients.
4. Back up the database and run `python -m alembic upgrade head` using the intended
   database. Confirm head `0034_consultation_booking` before starting the new API.
5. Configure HTTPS and the reverse proxy: serve `app/dist`, use SPA fallback for
   customer/doctor URLs, and proxy `/api/` to the Python API. Vite's development
   proxy is not included in the static production build. Allow multipart report
   requests slightly larger than the backend's 10 MiB file limit (for example
   `client_max_body_size 12m` in Nginx).
6. Run the API and required workers as supervised services. Email outbox processing
   uses `python -m scripts.mail_worker`; report extraction uses
   `python -m scripts.report_worker` plus a Linux OCR environment configured via
   `OCR_PYTHON`. Install/cache the OCR dependencies and models on that machine.
7. If IP-state detection is required behind a proxy, configure
   `GEO_TRUSTED_PROXIES` with only the actual ingress proxy CIDRs. The ingress must
   overwrite `X-Forwarded-For`. For the separate Admin proxy, enable
   `GEO_FORWARD_CLIENT_IP` only after that trust chain is configured. Local/private
   IPs cannot identify an Indian state and retain language/state-picker fallbacks.
8. On the HTTPS staging domain verify login/session refresh, owner-to-doctor share
   and revoke, one booking and cancellation, one original report upload/download,
   OCR result, actual email receipt and notification delivery. Then repeat the
   six PostgreSQL-specific checks against an isolated `_test` database, never a
   live patient database.

## Current account/configuration notes

- The doctor `gqwyrew` now has both mode-wise consultation fees saved and two
  appointment windows. Fresh real-database handler checks verified patient
  availability, patient booking history and the doctor's booking list. Eight
  original demo PDFs were also downloaded through their scoped services. Zero is
  a valid free-consultation fee; disabled or unpriced modes cannot be booked.
- The local environment remains development mode with non-secure cookies and
  in-memory rate limiting. Do not reuse it unchanged as production configuration.
- SMTP and Cloudinary configuration are present locally, and the OCR interpreter
  exists; their presence does not prove delivery or extraction on a different VPS.
- Existing demo records remain labeled as demo. No records were deleted by this
  audit and no VPS deployment was performed. Commit/push is a separate release step.
- Builds still warn about a large JavaScript chunk and ignored dependency
  `use client` directives. They did not fail builds or smoke tests. Production
  latency and load capacity have not been benchmarked here.

Screenshots are under ignored `app/.preview`, `.preview`, and
`test-results/portal`. Local command logs were retained in the system temporary
directory `familycare-vps-audit-20261107`; they are not deployment assets.
