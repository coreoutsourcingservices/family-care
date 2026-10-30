# Patient and doctor browser sessions

Cookie clients send `X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare`
and `X-FamilyCare-Portal: patient` or `doctor` on login, reads, refresh and logout.
Use the same portal throughout a workflow. Cookies are HttpOnly:

| Portal | Access cookie | Refresh cookie |
| --- | --- | --- |
| Patient | fc_patient_access | fc_patient_refresh |
| Doctor | fc_doctor_access | fc_doctor_refresh |

Access cookies use `/api/v1`; refresh cookies use `/api/v1/auth`.
Authenticated mutations and refresh require the portal's `X-CSRF-Token`.
Login/refresh returns `csrf_token` without exposing session tokens in JSON.
The web client stores CSRF values separately per portal.

Doctor login/logout no longer replaces the patient's cookie. An old shared
cookie is accepted only for its matching role. If it belongs to another portal,
the API returns HTTP 401 with `error.code: portal_session_changed`; the web app
opens the appropriate login page. Sign in once if an old tab has this error.
Legacy clients without this header and bearer-token app clients keep their
existing contract. Admin/superadmin continue using their existing proxy cookies.

After login, patient vaccination reads use
`GET /api/v1/children/{child_id}/vaccinations?schedule_type=UIP&view=all`
(or IAP). Parent ownership and connected-doctor access checks remain enforced.
Imported drafts without availability flags now default to visible child plans,
labelled Doctor Review. Explicitly disabled doses stay disabled.
