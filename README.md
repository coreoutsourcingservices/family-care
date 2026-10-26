# Family Care

Project folders:

- `admin/`
- `app/`
- `backend/`
- `customer/`
- `doctor/`

The Flask API backend is implemented in `backend/`. The other product folders remain placeholders.

See [backend setup](backend/README.md), [all API URLs and examples](backend/docs/API_DOCUMENTATION.md),
and [Supabase setup SQL](backend/supabase/0001_identity.sql).

The v1 backend owns JWT authentication, email OTP and role approval workflows using
Supabase PostgreSQL. No UI or Docker is included. Local API base: `http://127.0.0.1:5001`.
