# Customer frontend

Run `npm run dev:customer` from the repository root, then open
http://127.0.0.1:5174. The public app on port 5173 also mounts these customer routes.
The backend must be running on 5001 with both local frontend origins allowed.

Sign in, create/select a child profile, then open `/customer/child/dashboard`.
Growth, nutrition, vaccination records, medical history, consultation journal and
care notes now save to the authenticated account. Records support editing,
removal and reload persistence. Settings has an in-app reminder preference and
explicit import for existing device-only diary entries.

Vaccination schedules and health guides display an unavailable state until approved
clinical content is published. Parent-reported records do not establish verified
vaccination status. Consultation requests remain requests, not accepted appointments;
vaccination email reminders require opt-in and an enabled published policy. SMS and doctor-facing appointment acceptance are not implemented.

See [backend integration details](../backend/docs/CHILD_FRONTEND_INTEGRATION.md)
for endpoints, schema migration and isolated tests.

See [Vaccination management](../backend/docs/VACCINATION_MANAGEMENT.md) for catalog, medical review, certificates and reminders.

Child vaccination list integration: [Frontend API contract](../backend/docs/CHILD_VACCINATION_FRONTEND_API.md). Uses server-calculated age views and published dose references.
