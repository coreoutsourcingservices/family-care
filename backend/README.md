# Family Care Flask backend

Python virtual environment, Flask API and hosted Supabase Auth/Postgres. No Docker.

## Windows PowerShell

```powershell
cd "D:\my data\core outsourcing services pvt\familycare\backend"
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If activation is blocked, use `venv\Scripts\python.exe` directly; activation is optional.
Edit `.env` with your Supabase project URL and publishable/anon key. Do not commit `.env`.
No service role key is needed. The virtual environment is local and excluded from Git.

## Supabase setup (online)

1. Create/select your hosted Supabase project.
2. Run `supabase/schema.sql` once in its SQL Editor, before registering users.
3. Enable email/password authentication and email confirmation. Configure your Site URL
   for your frontend. Use a confirmed account when testing signin.
4. Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`.
5. Register your own account, confirm its email, then run the following in SQL Editor,
   replacing the email. This bootstraps the first super admin:

```sql
update public.profiles
set role = 'super_admin'
where id = (select id from auth.users where email = 'your-email@example.com');
```

The app cannot create or configure your hosted project without its connection details.
Passwords are managed by Supabase Auth. Profiles and roles are stored in Postgres.
Doctor signup creates an account; it does not verify medical qualifications.

## Run

```powershell
.\venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

Health: `http://127.0.0.1:5000/health`

For serving without the Flask development server (Windows supported):

```powershell
.\venv\Scripts\waitress-serve.exe --host=127.0.0.1 --port=5000 app:app
```

For public deployment, put HTTPS in front of the server and use a same-origin frontend
or an explicit CORS allowlist. Configure Supabase Auth rate limits/SMTP for production.
No frontend UI is included in this backend setup.

## API

Send JSON with `Content-Type: application/json`. Protected requests require
`Authorization: Bearer <access_token>`. Never log or put tokens in URLs.

| Method | Path | Access / body |
| --- | --- | --- |
| POST | `/api/auth/signup` | `email`, `password` (12–128 chars), `full_name`, `role`: `patient` or `doctor` |
| POST | `/api/auth/signin` | `email`, `password`; shared by all four roles |
| POST | `/api/auth/refresh` | `refresh_token` |
| POST | `/api/auth/signout` | Signed-in user; client must discard tokens |
| GET | `/api/auth/me` | Signed-in user; authoritative role from database |
| GET | `/api/admin/users?offset=0` | Admin or super admin; 100 users per page |
| PATCH | `/api/admin/users/<user UUID>/role` | Super admin only; body `{"role":"admin"}` |

Public signup cannot grant admin/super admin. A super admin can promote an existing
registered user through the role endpoint. Admins can list profiles but cannot change roles.
The last super admin cannot be demoted through the API. Direct database owners retain control.
Supabase signout revokes refresh tokens; an issued access token can remain valid until expiry.

PowerShell signup example:

```powershell
$body = @{email='doctor@example.com'; password='Choose-A-Unique-Password-123!'; full_name='Dr Example'; role='doctor'} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/auth/signup -ContentType application/json -Body $body
```

For a patient, use `role='patient'`. After confirming email:

```powershell
$login = @{email='doctor@example.com'; password='Choose-A-Unique-Password-123!'} | ConvertTo-Json
$session = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/auth/signin -ContentType application/json -Body $login
$headers = @{Authorization="Bearer $($session.access_token)"}
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/auth/me -Headers $headers
```

## Tests

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests mock Supabase HTTP responses. Real signup/email delivery, SQL policies and hosted
database connectivity require your configured project and must also be verified there.
