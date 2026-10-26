# Family Care: final development prompt

Implement the detailed specification below in the existing backend at:
D:\my data\core outsourcing services pvt\familycare\backend

Inspect the existing code and schema before changing them. The following requirements
resolve ambiguities and take precedence over conflicting wording in the specification.
This is a development prompt; none of these new workflows should be assumed implemented.

## Mandatory clarifications

1. NO DOCKER. Use backend/venv, Flask, Supabase PostgreSQL, SQLAlchemy/Alembic,
   Flask-owned JWT authentication, Argon2id and real configurable email delivery.
   Windows: Waitress, separate server.py. Linux: Gunicorn. Local port is 5001.
2. Separate doctor, patient, admin and superadmin folders. Each module must contain
   working model.py, controller.py, routes.py plus service/repository/schema as needed.
3. PostgreSQL generates public IDs through independent sequences: A000001 (admin),
   D000001 (doctor), C000001 (patient/customer). Internal primary keys are UUIDs.
   Enforce uniqueness and immutability. Allow sequence gaps; never reuse IDs. Values
   above 999999 must grow in length without truncation or collision.
4. Passwords: MINIMUM 8 CHARACTERS, not exactly eight numeric digits. Allow letters,
   numbers and symbols, document maximum length, require matching confirm_password,
   and store only Argon2id hashes. Never return hashes.
5. Development bootstrap: username superadmin, password superadmin@2026. Seed this
   account in Supabase Postgres through an idempotent Python command. Do not overwrite
   an existing account/password. Configure notification email. Store only the hash.
   Production rejects this default password. First login issues only a short-lived
   password-change challenge; dashboard access/refresh tokens come after rotation.
6. Admin signup requires name, EMAIL, mobile, password, confirm_password. Verify email
   through OTP, then queue superadmin approval. Only approved active verified admins
   may authenticate: email + password THEN email OTP. Persist dashboard notification,
   approve/reject decision, reviewer, timestamps and reason; send decision email.
7. Doctor signup requires name, email, mobile, password, qualification, medical
   registration number and issuing council/authority. Optional specialization/NMR ID.
   D... is the app ID, not a professional registration number. Verify email OTP first,
   then admin reviews and approves/rejects. Email the doctor on decision. Only approved,
   verified active doctors log in with email/password. No automatic medical validation.
8. Patient/customer signup requires name, email, mobile, password, confirm_password.
   Email OTP verification activates account and returns JWT access + refresh session.
   No manual approval. Subsequent login requires email/password THEN email OTP.
   Do not issue dashboard JWTs before verification/approval. Limited challenge tokens
   must have a separate purpose/audience and cannot authorize protected APIs.
9. Existing backend currently uses Supabase Auth. New architecture must use Supabase
   as managed PostgreSQL with Flask owning auth. Implement a deliberate migration,
   not two conflicting auth systems. Do not delete public.profiles or auth.users.
   Use a private familycare schema for new tables, inaccessible to anon/authenticated
   Data API roles. Explain migration/enrollment/password resets for old accounts.
   Do not assume old password hashes can be extracted or reused. Old Supabase JWTs
   must not silently authenticate to the new Flask JWT system.
10. DATABASE_URL is required; an API key is not a PostgreSQL password. Known host:
    db.gludrdsinkyptcvixggd.supabase.co, port 5432, database postgres. Never invent the
    missing database password. Percent-encode connection password characters. Require
    TLS. If direct connectivity fails, obtain exact session-pooler details from the
    dashboard. Use a least-privilege app DB role and separate migration role.
    Keep DATABASE_URL, JWT_SECRET_KEY, OTP_HMAC_SECRET and SMTP credentials only in
    ignored .env/server secrets. JWT_SECRET_KEY is a signing secret, not a static token.
    Never copy current secrets into source, docs, logs or test fixtures.
11. OTP: cryptographic 6 digits, TTL 5 minutes, resend cooldown 60 seconds, at most
    5 attempts, keyed HMAC storage, atomic single-use verification and attempt counting.
    Bind challenge to user and purpose; invalidate old code on resend. Concurrent
    verification cannot issue multiple sessions. No OTP before password validation
    for login. Never log OTPs. Apply shared rate limits by account and IP.
12. Real email delivery uses configurable SMTP/provider and a durable transactional
    outbox. Include a runnable worker with retries/backoff and idempotency. Approval
    and email enqueue must commit atomically. Distinguish queued from delivered email.
13. Check current role, active status, approval state and session on protected requests.
    Admins cannot approve admins or promote themselves. Only superadmin approves
    admins; admins review doctors. Use transactions and locks against double decisions.
    Persist audit logs. Suspension/password change invalidates sessions.
14. Access JWT default TTL 15 minutes, refresh session default TTL 7 days. Use refresh
    rotation, hashed storage, token families, replay detection and revocation. Validate
    issuer/audience/type/algorithm/expiry. First-login and OTP challenges must never
    be treated as normal sessions. Logout revokes the server-side session.
15. Flutter uses Bearer tokens in platform secure storage; web uses HttpOnly cookies
    with CSRF, SameSite and production HTTPS. Define transport selection explicitly,
    use a CORS allowlist, avoid exposing browser refresh tokens in JSON. Same workflow
    for both clients; no duplicate client-side authentication/approval decisions.
16. Provide executable Supabase SQL Editor scripts matching Alembic revisions, indexes,
    sequence/trigger functions, grants and schema. Explain alternative install paths:
    migrations on empty DB OR SQL bootstrap + equivalent migration stamp, not both.
    Superadmin seed hashes passwords in Python; never insert a plaintext SQL password.
17. API docs: docs/API_DOCUMENTATION.md, /api/docs, /api/openapi.json. List EVERY method,
    full local URL, role, request JSON, response JSON, challenge/token requirements,
    error codes and Flutter/web examples. Local base http://127.0.0.1:5001. Production
    base is configurable; never invent a deployed domain. Include missing operational
    endpoints for password change, suspension/reactivation and session management.
18. Performance target: 100 concurrent active clients and 200 HTTP requests/second for
    a clearly documented realistic route mix. This is not a guarantee of 200 Argon2
    password checks or OTP emails/second. Use asynchronous mail delivery, Redis-backed
    shared rate limits, bounded DB pools across workers, indexes and pagination.
    Provide Locust/k6 scripts and report hardware, dataset/mix, actual RPS, p50/p95/p99,
    unexpected error rate, CPU/memory and DB pool saturation. Initial read/profile
    target: p95 below 500 ms and unexpected errors below 1%; email latency separate.
    Never weaken password hashing to hit throughput. Do not load-test hosted Supabase
    or send bulk email without a separate explicit benchmark instruction. Use isolated
    test data and a local mail sink. Never claim capacity without measured evidence.
19. Tests must cover entire approval/auth workflow, sequence concurrency and overflow,
    role isolation, OTP attempts/expiry/resend/replay/races, pending-account restrictions,
    refresh replay, password change, suspension, and migration/bootstrap idempotency.
    Report which live tests are blocked by missing database/SMTP credentials.
20. Scope is a complete working identity/authentication foundation for a large product;
    appointments, prescriptions, billing and medical records are separate future work.
    Do not claim healthcare certification or full production readiness without evidence.

## Detailed implementation specification

# Build a Large-Scale Doctor & Patient Management Backend — Flask + Supabase

Act as a Senior Python Backend Architect, Database Architect, and API Security Engineer.

I want to build a large-scale, modular, production-ready healthcare management backend using Flask and Supabase PostgreSQL.

This backend will serve:

1. A Flutter mobile application
2. A web frontend
3. An Admin Dashboard
4. A Super Admin Dashboard
5. A Doctor Dashboard
6. A Patient Dashboard

Build the backend as a scalable Flask modular monolith with clean separation of concerns.

Do not create only a basic Flask demo. Generate a professional, working project foundation that can support a large application.

# 1. Technology Stack

Use:

- Python 3.12+
- Flask
- Flask Blueprints
- Flask Application Factory
- Supabase PostgreSQL
- SQLAlchemy
- Flask-Migrate / Alembic
- PostgreSQL UUID
- PostgreSQL sequences
- PyJWT / Flask-JWT-Extended
- Argon2 password hashing
- Email OTP using SMTP or a configurable email provider
- Marshmallow or Pydantic for validation
- Flask-Limiter
- Swagger / OpenAPI
- Pytest
- Gunicorn
- Nginx
- Environment variables

Use Supabase primarily as a managed PostgreSQL database. Flask must own the authentication, authorization, OTP and approval workflows.

Do not mix Flask JWT authentication with Supabase Auth unless a complete and consistent integration is deliberately designed.

All Flutter and web clients must call the Flask REST API.

# 2. Role System

Create four roles:

- SUPERADMIN
- ADMIN
- DOCTOR
- PATIENT

Each role must have separate permissions.

Use secure Role-Based Access Control (RBAC).

Users must not be able to change their own role, approval status or public ID through an API request.

# 3. Dynamic User ID Generation

Create a PostgreSQL-backed, concurrency-safe ID generator.

Required format:

SUPERADMIN:
- Username: superadmin

ADMIN:
- A000001
- A000002
- A000003

DOCTOR:
- D000001
- D000002
- D000003

PATIENT / CUSTOMER:
- C000001
- C000002
- C000003

Requirements:

1. IDs must be generated automatically by PostgreSQL.
2. Use dedicated sequences for each role.
3. Never generate sequential IDs in Flutter or JavaScript.
4. Prevent duplicate IDs, including under concurrent registrations.
5. Use UUID primary keys internally for relationships.
6. Keep public IDs unique and immutable.
7. Create SQLAlchemy models and Alembic migrations.
8. Explain how PostgreSQL generates IDs.
9. Show the generated ID in API responses.
10. Do not reuse deleted user IDs.

# 4. Password Policy

All regular users must have passwords containing at least 8 characters.

Requirements:

- Minimum 8 characters
- Allow letters, numbers and special characters
- Use Argon2 password hashing
- Never save plaintext passwords
- Implement password confirmation
- Support forgot/reset password using verified email OTP
- Rate-limit failed login attempts
- Never return password hashes in API responses

Do not restrict passwords to exactly eight numeric digits.

# 5. Super Admin Authentication

Create the initial Super Admin using a secure, idempotent database seed script.

Development bootstrap credentials:

Username: superadmin
Password: superadmin@2026

Requirements:

1. Store the Super Admin account in Supabase PostgreSQL.
2. Store only the Argon2 password hash, never the plaintext password.
3. Set role = SUPERADMIN.
4. Set email_verified = true for the trusted bootstrap account.
5. Set approval_status = APPROVED.
6. Prevent public Super Admin registration.
7. Create the Super Admin only if it does not exist.
8. Require a password change on first login.
9. Require a deployment-specific strong secret in production. The provided bootstrap password must not remain usable in production.
10. Make credentials configurable through environment variables or a secure bootstrap command.
11. Implement Super Admin login and logout with JWT authentication.
12. Protect every Super Admin API with role-based permissions.

Super Admin login:

POST /api/v1/superadmin/login

Request:

{
  "username": "superadmin",
  "password": "superadmin@2026"
}

Return a valid session only after successful authentication and required first-login password rotation.

Super Admin Dashboard:

- View total admins
- View pending admin requests
- Approve admins
- Reject admins
- View approved admins
- Suspend or reactivate admins
- View doctors and patients
- View audit logs

# 6. Admin Registration

Create the Admin signup form with:

- Full Name
- Gmail / Email
- Mobile Number
- Password
- Confirm Password

Email is mandatory because OTP verification and email-based login are required.

Admin registration workflow:

STEP 1:
Admin submits signup information.

STEP 2:
Backend validates all fields and checks for duplicates.

STEP 3:
Generate a unique public Admin ID, such as A000001.

STEP 4:
Create an Admin record in Supabase PostgreSQL.

Initial status:
- email_verified = false
- approval_status = PENDING_EMAIL_VERIFICATION

STEP 5:
Generate a secure 6-digit email OTP.

STEP 6:
Send OTP to the Admin's email.

STEP 7:
Admin enters OTP and clicks Verify.

STEP 8:
Backend validates OTP.

STEP 9:
After successful verification:
- email_verified = true
- approval_status = PENDING_APPROVAL

STEP 10:
Send an approval request notification to the Super Admin Dashboard.

STEP 11:
Super Admin can Approve or Reject.

If approved:
- approval_status = APPROVED
- Send approval email to Admin
- Allow Admin to log in

If rejected:
- approval_status = REJECTED
- Store rejection reason
- Send rejection email
- Do not allow Admin login

# 7. Admin Login

After Super Admin approval, Admin must log in using:

- Gmail / Email
- Password
- Email OTP

Admin login flow:

1. Enter email and password.
2. Validate credentials.
3. Check email verification status.
4. Check Super Admin approval status.
5. If approved, send login OTP.
6. Display OTP verification screen.
7. Verify OTP.
8. Issue access token and refresh token.
9. Redirect to Admin Dashboard.

Implement:

- Login OTP
- Resend OTP
- OTP expiry
- Maximum OTP attempts
- Invalid OTP handling
- Expired OTP handling
- JWT token refresh
- Logout
- Password reset
- Session revocation

Pending or rejected admins must not receive authenticated dashboard access.

# 8. Doctor Registration

Create the Doctor signup form with these fields:

- Full Name
- Email / Gmail
- Mobile Number
- Password
- Confirm Password
- Qualification
- Specialization (optional)
- Medical Registration Number
- State Medical Council / Registering Authority
- NMR ID, if available
- Medical Registration Certificate (optional, configurable private storage)

Important:

Medical Registration Number is the professional registration number issued by the relevant medical council.

For Indian allopathic doctors, capture the State Medical Council registration number and the council name. An NMR ID may also be recorded when available.

Do not confuse this professional registration number with the application's automatically generated Doctor ID.

Example:

Application Doctor ID: D000001

Medical Registration Number: Provided by the doctor

Doctor registration workflow:

1. Doctor submits registration form.
2. Validate all required fields.
3. Validate email and mobile number format.
4. Check duplicate email and medical registration records.
5. Generate dynamic Doctor ID.
6. Save Doctor information in Supabase.
7. Generate email OTP.
8. Send OTP to Doctor Gmail.
9. Doctor verifies email OTP.
10. Update email_verified = true.
11. Change approval status to PENDING_APPROVAL.
12. Display the Doctor request in Admin Dashboard.
13. Admin reviews doctor qualification and registration details.
14. Admin approves or rejects the request.

On approval:

- Update status to APPROVED.
- Save approving Admin ID and approval timestamp.
- Send confirmation email to the Doctor.
- Allow Doctor to log in.

Approval email should communicate:

"Your doctor registration has been approved. You can now log in to your Doctor Dashboard."

On rejection:

- Store rejection reason.
- Notify Doctor by email.
- Restrict dashboard access.
- Support a controlled resubmission process.

Medical registration verification must be a review process, not an assumption that submitting a number proves medical eligibility.

# 9. Doctor Login

Doctor login form:

- Email
- Password

Login workflow:

1. Doctor enters email and password.
2. Verify password hash.
3. Check email_verified.
4. Check approval_status = APPROVED.
5. Check account status is ACTIVE.
6. Generate JWT access and refresh tokens.
7. Return doctor profile and public ID.
8. Open Doctor Dashboard.

Do not allow pending, rejected or suspended doctors to access protected APIs.

Design optional doctor login OTP / MFA support for future enablement.

# 10. Patient / Customer Registration

Patient signup fields:

- Full Name
- Email
- Mobile Number
- Password
- Confirm Password

Registration process:

1. Patient submits signup form.
2. Validate data.
3. Generate public ID beginning with C.
4. Store patient details in Supabase.
5. Generate email OTP.
6. Send OTP to Gmail/email.
7. Verify OTP.
8. Mark email_verified = true.
9. Activate patient account.
10. Issue JWT access and refresh tokens.
11. Allow Patient Dashboard access.

Example patient ID:

C000001

Patient registration does not require manual Admin approval.

# 11. Patient Login

Implement email, password and OTP-based login.

Steps:

1. Patient enters email and password.
2. Verify credentials.
3. Send login OTP to registered email.
4. Display OTP input.
5. Verify OTP.
6. Issue JWT access and refresh tokens.
7. Redirect to Patient Dashboard.

Include:

- Resend OTP
- Forgot password
- Reset password
- Token refresh
- Logout
- Profile details

# 12. Universal Email OTP System

Create one reusable OTP service for all roles.

OTP purposes:

- Email verification
- Login verification
- Password reset
- Sensitive account changes

Requirements:

- Secure random 6-digit OTP
- OTP valid for 5 minutes
- Resend cooldown of 60 seconds
- Maximum 5 verification attempts
- One-time use
- Store only secure OTP hashes
- Expiration timestamps
- OTP purpose and user association
- Secure resend flow
- Rate limiting per account and IP
- Prevent OTP replay
- Prevent email enumeration where possible
- Log security events without logging OTP values

All email templates must be stored separately.

Create templates for:

- Signup OTP
- Login OTP
- Password reset OTP
- Admin approval
- Admin rejection
- Doctor approval
- Doctor rejection

Email sender settings must come from environment variables.

# 13. Supabase PostgreSQL Database Schema

Design a normalized and scalable PostgreSQL schema.

Required tables:

1. users
2. admin_profiles
3. doctor_profiles
4. patient_profiles
5. otp_challenges
6. approval_requests
7. refresh_tokens
8. user_sessions
9. password_reset_events
10. email_notifications
11. audit_logs

Users table must include:

- id: UUID primary key
- public_id: unique string
- username: optional unique string
- full_name
- email: unique
- phone_number
- password_hash
- role
- email_verified
- approval_status
- account_status
- must_change_password
- created_at
- updated_at
- last_login_at

Doctor profiles must include:

- user_id
- qualification
- specialization
- medical_registration_number
- registering_council
- nmr_id
- verification_status
- approved_by
- approved_at

Approval requests must include:

- id
- applicant_id
- applicant_role
- requested_at
- status
- reviewed_by
- reviewed_at
- rejection_reason

Implement:

- Foreign keys
- Unique constraints
- Database indexes
- Transactions
- Pagination
- Filtering
- Database migrations
- Database-generated IDs
- Consistent status enums
- Safe audit logging

Generate complete SQLAlchemy models and Alembic migrations.

Also provide equivalent PostgreSQL SQL scripts compatible with Supabase SQL Editor.

# 14. Supabase Connection

Use Supabase PostgreSQL with SQLAlchemy and a PostgreSQL driver.

Provide:

- Environment configuration
- Secure PostgreSQL connection string
- SSL configuration
- Appropriate connection pooling
- Session handling
- Transaction management
- Migration configuration
- Database connectivity health check

Document when to use a direct connection versus the Supabase session pooler.

Never expose PostgreSQL credentials, secret API keys, service-role keys, or JWT signing keys in Flutter or web frontend code.

Keep sensitive healthcare and authentication tables inaccessible to direct public database APIs.

Access protected data through authenticated Flask endpoints.

Document database grants and Row Level Security settings if Supabase Data API access remains enabled.

# 15. Flask Project Folder Structure

Create this scalable architecture:

```text
backend/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── extensions.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   ├── exceptions.py
│   │   └── logging_config.py
│   │
│   ├── api/
│   │   └── v1/
│   │       └── __init__.py
│   │
│   ├── modules/
│   │   ├── superadmin/
│   │   ├── admin/
│   │   ├── doctor/
│   │   ├── patient/
│   │   ├── authentication/
│   │   ├── otp/
│   │   ├── approvals/
│   │   ├── notifications/
│   │   └── users/
│   │
│   ├── middleware/
│   │   ├── auth.py
│   │   ├── roles.py
│   │   ├── rate_limit.py
│   │   └── errors.py
│   │
│   ├── services/
│   │   ├── jwt_service.py
│   │   ├── email_service.py
│   │   └── id_generator.py
│   │
│   ├── utils/
│   │   ├── responses.py
│   │   └── validators.py
│   │
│   └── templates/
│       └── emails/
│
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── security/
├── scripts/
│   └── seed_superadmin.py
├── docs/
│   ├── API_DOCUMENTATION.md
│   ├── DATABASE_SCHEMA.md
│   ├── AUTH_FLOW.md
│   ├── FLUTTER_INTEGRATION.md
│   ├── WEB_INTEGRATION.md
│   ├── SUPABASE_SETUP.md
│   └── DEPLOYMENT.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── alembic.ini
├── wsgi.py
├── run.py
└── README.md
```

Each major module must contain:

- routes.py
- controller.py
- service.py
- repository.py
- model.py
- schema.py

Create working implementations wherever needed.

# 16. REST API Endpoints

Implement and document the following endpoints.

Super Admin:

POST /api/v1/superadmin/login

GET /api/v1/superadmin/dashboard

GET /api/v1/superadmin/admin-requests

POST /api/v1/superadmin/admins/{admin_id}/approve

POST /api/v1/superadmin/admins/{admin_id}/reject

GET /api/v1/superadmin/admins

Admin:

POST /api/v1/admin/register

POST /api/v1/admin/verify-email

POST /api/v1/admin/login

POST /api/v1/admin/verify-login-otp

POST /api/v1/admin/resend-otp

GET /api/v1/admin/dashboard

GET /api/v1/admin/doctor-requests

POST /api/v1/admin/doctors/{doctor_id}/approve

POST /api/v1/admin/doctors/{doctor_id}/reject

Doctor:

POST /api/v1/doctors/register

POST /api/v1/doctors/verify-email

POST /api/v1/doctors/login

POST /api/v1/doctors/resend-otp

GET /api/v1/doctors/me

GET /api/v1/doctors/approval-status

Patient:

POST /api/v1/patients/register

POST /api/v1/patients/verify-email

POST /api/v1/patients/login

POST /api/v1/patients/verify-login-otp

POST /api/v1/patients/resend-otp

GET /api/v1/patients/me

Common:

POST /api/v1/auth/refresh

POST /api/v1/auth/logout

POST /api/v1/auth/forgot-password

POST /api/v1/auth/reset-password

GET /api/v1/health

Provide consistent JSON structures, appropriate HTTP status codes and reusable response helpers.

# 17. JWT and Session Security

Implement:

- Short-lived access tokens
- Rotating refresh tokens
- Refresh token revocation
- Logout from current session
- Server-side session tracking
- Session expiry
- Role and approval-status enforcement
- JWT signature and expiry verification
- Password-change session invalidation
- Protection against replay and brute-force attacks

For web:
- Use secure HTTP-only cookies
- SameSite configuration
- CSRF protection
- HTTPS in production

For Flutter:
- Use secure platform-backed token storage
- Never use ordinary SharedPreferences for sensitive tokens
- Never embed database credentials

# 18. Flutter and Website API Integration

The backend must support both Flutter mobile applications and a website frontend.

Use one shared versioned REST API.

Provide complete examples of:

Flutter:
- Dio HTTP client
- API service class
- Registration request
- OTP verification
- Login request
- Refresh-token handling
- Logout
- Protected API requests

Website:
- Next.js or JavaScript API client
- Login form request
- OTP verification request
- Approval status handling
- Cookie-based authenticated requests
- Logout

Do not duplicate authentication logic between clients.

The Flask backend must remain the source of truth.

# 19. API Documentation

Create complete OpenAPI/Swagger documentation.

Provide local API documentation endpoints such as:

/api/docs

/api/openapi.json

Also generate:

docs/API_DOCUMENTATION.md

For every endpoint include:

1. HTTP method
2. Complete route
3. Required role
4. Request fields
5. Example request JSON
6. Example successful response
7. Error responses
8. Authentication requirements
9. Flutter integration example
10. Web frontend integration example

Clearly distinguish example local API URLs from deployed production URLs.

Do not invent a live domain.

# 20. Testing Requirements

Write automated tests for:

- Dynamic ID generation
- Concurrent registration without duplicate IDs
- Super Admin login
- Admin registration
- Admin OTP verification
- Admin approval and rejection
- Admin login before and after approval
- Doctor registration
- Doctor registration-number validation
- Doctor approval and rejection
- Patient registration
- Patient login OTP
- OTP expiration
- OTP resend
- OTP replay prevention
- Expired JWT
- Invalid JWT
- Role-based access restrictions
- Refresh token rotation
- Password reset
- SQL injection defenses
- Rate limiting

# 21. Installation and Deployment

Provide step-by-step instructions for:

Windows 11 local development:

- Python virtual environment
- Package installation
- Environment configuration
- Supabase database connection
- Database migrations
- Initial Super Admin creation
- Flask server startup
- API testing

Ubuntu VPS production:

- Gunicorn
- Nginx
- HTTPS
- Environment secrets
- Supabase production database
- Database migrations
- Email service configuration
- Logging and monitoring

# 22. Final Output Rules

Generate a complete working Flask starter project.

Output:

1. Full folder structure
2. Every necessary starter file
3. Complete working source code
4. SQLAlchemy models
5. PostgreSQL migrations and SQL scripts
6. Supabase connection setup
7. Super Admin bootstrap script
8. Admin signup/login/approval
9. Doctor signup/login/approval
10. Patient signup/login
11. Email OTP system
12. JWT authentication
13. RBAC permissions
14. API documentation
15. Flutter integration examples
16. Website integration examples
17. Automated tests
18. Local and production run commands

Do not provide only pseudocode or an empty project skeleton.

Do not leave core authentication, OTP, approval, database or authorization logic as TODO placeholders.

Use safe defaults, clear module boundaries and production-grade security practices.

Build this as the foundation of a large healthcare product.