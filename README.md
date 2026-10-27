# Family Care

Start here: [All API documentation and working flows](API_GUIDE.md).

Child profile APIs, child data examples and the proposed vaccination/dashboard API list: [English Child Healthcare API Guide](backend/CHILD_HEALTHCARE_API_GUIDE.md). The guide distinguishes existing routes from proposed additions.

IP/state language suggestions, i18next catalogs and admin language selector: [Localization API](backend/LOCALIZATION_API.md).

Project folders:

- `admin/`
- `app/`
- `backend/`
- `customer/`
- `doctor/`

The Flask API backend is implemented in `backend/`. The Next.js admin/superadmin frontend is in `admin/` (port 3005); the other product folders remain placeholders.

See [backend setup](backend/README.md), [all API URLs and examples](backend/docs/API_DOCUMENTATION.md),
and [Supabase setup SQL](backend/supabase/0001_identity.sql).

The v1 backend owns JWT authentication, email OTP and role approval workflows using
Supabase PostgreSQL. The API has no UI or Docker. See [admin frontend](admin/README.md) for the Next.js portals. Local API base: `http://127.0.0.1:5001`.

Care profiles now have automatic [CH / AD / WO public IDs](backend/PROFILE_PUBLIC_IDS.md); existing UUID URLs remain supported.
