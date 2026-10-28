# Familycare admin

Patients now show family-member and total-profile counts. Click a patient to see
all self/child/adult/women profiles, then click a profile for member details and its
account owner. The same flow is available in both admin and superadmin portals.
See [patient/member API details](../backend/docs/ADMIN_PATIENT_MEMBERS.md).

Next.js App Router app containing both admin and superadmin portals. All frontend
source lives in `familycare/admin`. Default port: **3005**.

```powershell
cd "D:\my data\core outsourcing services pvt\familycare\admin"
npm install
npm run dev
```

Start the Flask backend on port 5001 and its mail worker in separate terminals.
Optional `.env.local`: `BACKEND_URL=http://127.0.0.1:5001` (server-only).
Flask `CORS_ORIGINS` must include `http://localhost:3005` and, if used,
`http://127.0.0.1:3005`. Restart Flask after changing its `.env`.

Routes:

| URL | Purpose |
| --- | --- |
| `/` | Admin email/password login |
| `/dashboard` | Live network overview and doctor review queue |
| `/doctors` | Paginated doctor directory, approvals, rejection reasons, suspension |
| `/patients` | Paginated patient directory |
| `/settings` | Profile and password change |
| `/superadmin` | Superadmin email/password login and initial password rotation |
| `/superadmin/dashboard` | Organization overview and admin review queue |
| `/superadmin/admins` | Admin approvals and account management |
| `/superadmin/doctors` | Read-only doctor directory |
| `/superadmin/patients` | Read-only patient directory |
| `/superadmin/audit-logs` | Paginated activity log |
| `/superadmin/settings` | Superadmin profile and password change |

Browser requests go through the same-origin `/api/v1/*` Next.js route handler to
Flask. HttpOnly access/refresh cookies are used; tokens are never stored in localStorage.
The proxy validates mutation Origin + X-Requested-With, keeps CSRF material in an
HttpOnly cookie, and injects it only into same-origin backend requests. The access
cookie is scoped to `/` so server-rendered protected layouts can verify the session.
The refresh cookie stays scoped to `/api/v1/auth`. Admin and superadmin have separate HttpOnly cookie namespaces (`fc_admin_*` and
`fc_superadmin_*`). Patient/customer frontend cookies (`fc_access`/`fc_refresh`)
are not forwarded or overwritten by the admin proxy. Each portal refreshes and
logs out independently. Existing shared-cookie sessions require one fresh sign-in.
Backend role checks remain authoritative. No public superadmin signup exists.

Database totals and tables are live; empty/error/loading states do not substitute
sample data. Search filters only the current page. Approval status filtering and
pagination run on the backend. Approve/reject/suspend/reactivate require a confirmation.
The admin patient directory adds `GET /api/v1/admin/patients`; existing APIs are unchanged.

```powershell
npm run typecheck
npm run build
node tests/smoke.mjs
npm start
```

Production: configure `BACKEND_URL` for the Flask service, set Flask production
cookie/Redis settings, and add the actual frontend origin to its allowed origins.
Keep signing keys, SMTP and database credentials exclusively in the backend.

The smoke test starts its own loopback-only API on 5501 and Next.js on 3006.
It uses in-memory SQLite test users, sends no email and never connects to Supabase.

Current login flow: all roles use email + password without login OTP. Signup email OTP,
password-reset OTP, account approval and first-login password change are preserved.
Legacy superadmin username login remains compatible. Legacy verify-login-otp routes return HTTP 410.

Admin signup: `/register` ? email OTP ? pending superadmin approval. The admin login
page links to registration and does not display a superadmin sign-in link.


### Language regression test

After `npm run build`, run `npm run test:localization` with Playwright Chromium installed (`npx playwright install chromium`). To use installed Google Chrome in PowerShell, set `$env:PLAYWRIGHT_CHANNEL="chrome"` first. The test starts isolated SQLite Flask/Next fixtures on ports 5501/3006, checks all 27 login languages for both roles, switches already-visible session notices, and visits authenticated panel routes. It never uses Supabase or sends email.

Catalogs and translation availability: [Localization API](../backend/LOCALIZATION_API.md). New regional catalogs are machine-generated and need native-speaker review.

Session isolation regression: run `node tests/portal-sessions.mjs` against the isolated
member fixture on 5501 and the built admin test server on 3006. It checks frontend
cookie overwrites, both portals in one browser, refresh/logout isolation, stale-role
recovery, API error states and cross-origin rejection.

For authentication-only validation on backend snapshots without localization routes,
run `node tests/smoke.mjs --auth-only`. The default smoke command retains its strict
localization checks; `--auth-only` explicitly excludes only those assertions.

Vaccination management is available at `/vaccination` and `/superadmin/vaccination`. See [workflow and API](../backend/docs/VACCINATION_MANAGEMENT.md).
