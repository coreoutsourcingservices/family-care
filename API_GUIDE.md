# Familycare: all APIs aur complete working flow

- Backend: `http://127.0.0.1:5001`
- Admin UI: `http://localhost:3005/`
- Admin signup UI: `http://localhost:3005/register`
- Superadmin UI: `http://localhost:3005/superadmin`

Ye guide testing order aur complete API list batati hai. Har endpoint ke field
validations, request JSON, example responses aur error codes:
**[Full API reference](backend/docs/API_DOCUMENTATION.md)**.

- [OpenAPI JSON](backend/docs/openapi.json): Swagger-compatible contract.
- [Postman collection](backend/docs/postman_collection.json): Postman/Insomnia mein import karo.
- [Patient self/member/report guide](backend/docs/PATIENT_CARE_API.md).
- [Doctor referral guide](backend/docs/REFERRALS.md).
- [Next.js admin setup](admin/README.md).

## 1. Abhi kya ready hai

- Sab roles ka normal login **email + password** se hai. Login OTP nahi hai.
- Registration par email OTP aata hai; OTP verify hone se pehle account PostgreSQL
  mein save nahi hota. Signup details temporary cache mein rehti hain.
- Patient email verify hone par session milta hai. Doctor/admin ko verification
  ke baad approval chahiye.
- Superadmin ka public signup nahi hai; private seed command se account banta hai.
  First login par password change challenge mil sakta hai; ye email OTP nahi hai.
- Doctor referral auto-generated hai. Patient account aur individual care profiles
  alag-alag doctor referral connections rakh sakte hain.
- Self, child, adult aur women member profiles; parent links; report metadata ready hain.
- **Cloudinary credentials local-only hain; live upload abhi verify nahi hua.**
  Missing keys par HTTP 503 `cloudinary_not_configured` aayega. Upload tests mocked hain.
- Admin/superadmin frontend ka source `admin/` mein hai. Separate `frontend/` folder nahi hai.

## 2. Local start aur health check

Backend terminal:

```powershell
cd "D:\my data\core outsourcing services pvt\familycare\backend"
.\venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe server.py
```

Email worker, second terminal (approval/reset mail ke liye):

```powershell
cd "D:\my data\core outsourcing services pvt\familycare\backend"
.\venv\Scripts\python.exe -m scripts.mail_worker
```

Admin frontend, third terminal:

```powershell
cd "D:\my data\core outsourcing services pvt\familycare\admin"
npm ci
npm run dev
```

| GET URL | Kya check karta hai |
| --- | --- |
| `http://127.0.0.1:5001/health` | Server running; database check nahi |
| `http://127.0.0.1:5001/api/v1/health/ready` | Real database/schema readiness |
| `http://127.0.0.1:5001/api/docs` | Live API index |
| `http://127.0.0.1:5001/api/openapi.json` | Live OpenAPI contract |

Readiness success:

```json
{"database":"postgresql","status":"ready"}
```

Secrets sirf ignored `backend/.env` mein rakho. Supabase Session Pooler uses port 5432
and project-qualified username. Password URI-encoded hona chahiye. Exact connection
details apne Supabase Connect popup se lo; repository mein real credentials nahi hain.

## 3. Insomnia/Postman headers aur IDs

JSON request:

```http
Content-Type: application/json
```

Protected endpoint par login ka access token add karo:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Register/login public endpoints par Authorization nahi chahiye. Authenticated role
endpoint ke required role se match hona chahiye. Admin ka token superadmin actions
ya doctor-only APIs ko access nahi deta.

| Value | Kahan se milegi | Kahan use hogi |
| --- | --- | --- |
| `challenge_token` | Signup/resend/reset response | OTP verification; access token nahi hai |
| `access_token` | Successful bearer login/session | Protected APIs |
| `refresh_token` | Successful bearer login/session | `/auth/refresh` |
| `user.id` / `user.public_id` | Verified account/session/list | Approval/account actions |
| `profile.id` | Self/member create response | Parent link aur profile/report URLs |
| `report.id` | Report upload/list response | Report download URL |
| Doctor `referral_id` | Doctor login, `/doctors/referral`, admin directory | Patient/profile connection |

Examples mein `PROFILE_UUID`, `PARENT_PROFILE_UUID`, `ACCESS_TOKEN` placeholders hain.
Inhe actual API response values se replace karo. Example referral ID bhi actual
approved doctor ki ID se replace karo; referral nahi chahiye to optional field hata do.

## 4. Registration: patient, doctor, admin

### Patient signup

`POST /api/v1/patients/register`

```json
{
  "full_name": "Amit Kumar",
  "email": "patient@example.com",
  "mobile_number": "+919876543210",
  "password": "Example-Patient8!",
  "confirm_password": "Example-Patient8!"
}
```

Optional `referral_id` add kar sakte ho. OTP ke liye `example.com` email ko apne
accessible real email se replace karo.

### Doctor signup

`POST /api/v1/doctors/register`

```json
{
  "full_name": "Dr Rahul Kumar",
  "email": "doctor@example.com",
  "mobile_number": "+919876543211",
  "password": "Example-Doctor8!",
  "confirm_password": "Example-Doctor8!",
  "qualification": "MBBS",
  "medical_registration_number": "TEST-MCI-12345",
  "registering_council": "Delhi Medical Council",
  "specialization": "General Physician"
}
```

`specialization` aur `nmr_id` optional hain. Referral ID server generate karega;
doctor registration input mein apni `referral_id` mat bhejo.

### Admin signup

`POST /api/v1/admin/register`

```json
{
  "full_name": "Example Admin",
  "email": "admin@example.com",
  "mobile_number": "+919876543212",
  "password": "Example-Admin8!",
  "confirm_password": "Example-Admin8!"
}
```

Teeno signup APIs: HTTP 202, `email_status: "sent"`, challenge token aur null
`user_id`/`public_id`. Sent ka matlab SMTP ne message accept kiya; inbox guarantee
nahi. SMTP failure par HTTP 503 `email_delivery_failed` aata hai.

### Registration OTP verify

Apne role ka endpoint:

```http
POST /api/v1/patients/verify-email
POST /api/v1/doctors/verify-email
POST /api/v1/admin/verify-email
```

```json
{"challenge_token":"REGISTER_RESPONSE_TOKEN","otp":"123456"}
```

Actual six-digit email OTP use karo. Validity 5 minutes, maximum 5 attempts.
OTP verify hone par account/profile save hota hai:

- Patient: HTTP 200 + session, account approved.
- Doctor/admin: HTTP 202 + user, `PENDING_APPROVAL`.

Resend: same role ka `POST /resend-otp`, body `{"challenge_token":"CURRENT_TOKEN"}`.
60-second cooldown hai; response ka **naya token** use karo. API restart par local
in-memory pending signup clear hota hai; register again. Multi-process production
same Redis cache use karta hai.

## 5. Approval flow aur login

### Superadmin login

`POST /api/v1/superadmin/login`

```json
{"email":"superadmin@example.com","password":"YOUR_SUPERADMIN_PASSWORD"}
```

Actual seeded email/password use karo. Legacy `username` login compatible hai;
email aur username dono ek saath mat bhejo. Initial password change required ho to
HTTP 202 `requires_password_change` aur challenge milega:

`POST /api/v1/auth/initial-password`

```json
{
  "challenge_token":"LOGIN_RESPONSE_CHALLENGE",
  "current_password":"YOUR_INITIAL_PASSWORD",
  "new_password":"Your-New-Password8!",
  "confirm_password":"Your-New-Password8!"
}
```

### Admin approval by superadmin

1. Superadmin token ke saath `GET /api/v1/superadmin/admin-requests`.
2. Pending admin ka UUID ya public ID lo.
3. `POST /api/v1/superadmin/admins/ADMIN_ID/approve`, body `{}`.
4. Reject ke liye same path par `/reject`, body `{"reason":"Correction needed"}`.

### Doctor approval by admin

1. Approved admin email/password se login kare.
2. `GET /api/v1/admin/doctor-requests`.
3. `POST /api/v1/admin/doctors/DOCTOR_ID/approve`, body `{}`.
4. Reject: `/reject`, body `{"reason":"Registration document correction needed"}`.

Admin/superadmin apni relevant directory mein `/suspend` aur `/reactivate` actions
bhi kar sakte hain. Suspension active sessions revoke karta hai. Reactivation
purane tokens restore nahi karta; login again.

### Normal login: all roles, no OTP

```http
POST /api/v1/patients/login
POST /api/v1/doctors/login
POST /api/v1/admin/login
POST /api/v1/superadmin/login
```

```json
{"email":"YOUR_ACCOUNT_EMAIL","password":"YOUR_PASSWORD"}
```

Approved/verified/active account ko HTTP 200 session milta hai. Pending/rejected/
suspended accounts blocked rahenge. **Legacy `/verify-login-otp` routes HTTP 410
return karti hain; unhe call mat karo.**

## 6. Doctor referral aur patient connection

`Dr Rahul Kumar` + actual public ID `D000001` = `rahulkumarD000001`.
Naam ka Dr prefix/spaces/punctuation remove hote hain; name lowercase hota hai.
Public ID exactly preserve hota hai. Referral ID naam change hone par stable rahegi.

Doctor token se `GET /api/v1/doctors/referral`: referral ID, public ID, full name,
email aur mobile number milenge. `GET /api/v1/doctors/me` bhi referral ID deta hai.

Patient signup par optional referral, ya existing patient token ke saath:

`POST /api/v1/patients/connect-doctor`

```json
{"referral_id":"rahulkumarD000001"}
```

- `GET /api/v1/patients/doctor`: connected doctor.
- `GET /api/v1/doctors/patients`: doctor ke connected patient accounts only.
- One doctor per patient account; same connection repeat safe hai. Different doctor
  connection returns 409. Invalid/unapproved/suspended doctor referral returns 422.

## 7. Self aur family members: child/adult/women

Patient token se `POST /api/v1/patients/profiles`.

Self example:

```json
{"profile_type":"self","module":"adult","full_name":"Amit Kumar","date_of_birth":"1990-04-12"}
```

Response ka `profile.id` parent link mein use karo. Child example:

```json
{
  "profile_type":"member",
  "module":"child",
  "full_name":"Aarav Kumar",
  "date_of_birth":"2018-05-14",
  "parent_profile_id":"PARENT_PROFILE_UUID",
  "guardian_contact":"+919876543210",
  "emergency_contacts":[
    {"name":"Amit Kumar","mobile_number":"+919876543210","relationship":"father"}
  ],
  "referral_id":"rahulkumarD000001"
}
```

Adult/women ke liye same input with `profile_type: "member"`, `module: "adult"`
ya `"women"`. Parent link sirf child member ke liye hai; own account ka older
adult/women profile chahiye. Parent/guardian/emergency/referral fields optional hain.
Ek account mein ek self profile aur multiple members ho sakte hain.

- List: `GET /api/v1/patients/profiles?page=1&per_page=25`.
- Module filter: `?module=child`, `adult`, ya `women`.
- Details: `GET /api/v1/patients/profiles/PROFILE_UUID`.
- Profile doctor connection: `POST /api/v1/patients/profiles/PROFILE_UUID/connect-doctor`
  with referral JSON above.

Patient account referral aur care-profile referral alag hain. Family reports tabhi
doctor ko visible hain jab **us care profile** par doctor explicitly connect ho.
Dusre patient's profile/parent/report IDs access nahi kiye ja sakte.

## 8. Medical report photo/PDF: Cloudinary

`POST /api/v1/patients/profiles/PROFILE_UUID/reports`

Insomnia/Postman mein **Multipart Form**, `file` field ko **File** type set karke
photo/PDF select karo. Authorization header rakho; JSON Content-Type hata do.
One file per request: JPEG, PNG, WebP ya PDF, maximum 10 MB.

Backend stores original `name`, detected `content_type`, size, Cloudinary `public_id`,
`asset_id`, `secure_url`, `folder`, resource and authenticated delivery type. Response
ka `url` short-lived signed download link hai, with `url_expires_in: 300`.

```text
familycare/C000001/profiles/PROFILE_UUID/child/reports/REPORT_UUID_blood-test.pdf
```

Folder module `child`, `adult` ya `women` hoga. IDs backend generate karega; client
arbitrary Cloudinary URL/public ID/folder save nahi kar sakta.

- List: `GET /api/v1/patients/profiles/PROFILE_UUID/reports`.
- New signed link: `GET /api/v1/patients/profiles/PROFILE_UUID/reports/REPORT_UUID/download`.
- Purani database-stored reports ka download attachment bytes deta hai; automatic
  migration un files ko delete ya Cloudinary par upload nahi karti.
- Referred doctor uses `/api/v1/doctors/care-profiles` and nested profile/report paths.
  Unrelated doctors ko access nahi milta.

Backend `.env` mein privately set karke restart karo:

```dotenv
CLOUDINARY_CLOUD_NAME=""
CLOUDINARY_API_KEY=""
CLOUDINARY_API_SECRET=""
```

**Keys missing hon to upload 503 dega. Real Cloudinary upload abhi verify nahi hua.** Profile/member APIs independent
hain. Cloudinary errors 502, unsupported/empty file 422, oversized file 413.
Canonical `secure_url` protected hai; display/download ke liye signed `url` use karo.

## 9. Sessions, password reset aur browser integration

- `GET /api/v1/{role}/me`: current user (role namespace admin/superadmin/doctors/patients).
- `POST /api/v1/auth/refresh`: `{"refresh_token":"CURRENT_REFRESH_TOKEN"}` in bearer mode.
  Response ke new access/refresh tokens save karo. Refresh calls serialize karo;
  old refresh token reuse session revoke karta hai.
- `POST /api/v1/auth/logout`, body `{}`: current session revoke.
- `POST /api/v1/auth/logout-all`, body `{}`: all sessions revoke.
- `GET /api/v1/auth/sessions`: active session list.
- `DELETE /api/v1/auth/sessions/SESSION_UUID`: one session revoke.
- `POST /api/v1/auth/forgot-password`, `{"email":"YOUR_EMAIL"}`: reset challenge.
  Unknown email ko bhi generic response milta hai.
- `POST /api/v1/auth/reset-password`: reset `challenge_token`, email `otp`,
  `new_password`, `confirm_password`.
- `POST /api/v1/auth/change-password`: logged-in token + `current_password`,
  `new_password`, `confirm_password`. Existing sessions revoke ho jaati hain.
- `POST /api/v1/auth/request-email-verification`: email/password se pending signup
  verification restart. Cache expired/cleared ho to register again.

Next.js uses same-origin proxy `/api/v1/*`, HttpOnly access/refresh cookies and CSRF
checks. Browser JSON mein access/refresh tokens nahi aate. Proxy CSRF token ko bhi
HttpOnly cookie mein rakhta hai. Direct Flask browser integration mein cookie transport,
credentials, trusted Origin, `X-Requested-With: FamilyCare` and authenticated mutations
par `X-CSRF-Token` chahiye. Bearer API examples above Insomnia/mobile ke liye hain.

## 10. Errors ka matlab

| HTTP | Meaning / next action |
| --- | --- |
| 200 | Successful read/login/action |
| 201 | Self/member profile ya report created |
| 202 | Signup OTP ya pending approval/initial password step; normal login session nahi |
| 400 | Invalid/expired/replayed OTP or invalid state |
| 401 | Wrong credentials, missing/expired/revoked token; sign in/refresh |
| 403 | Wrong role, pending approval, suspension or CSRF/origin failure |
| 404 | Resource absent ya is account ko accessible nahi |
| 409 | Duplicate account/self profile, approval conflict or different doctor already connected |
| 410 | Login OTP endpoint retired; email/password login use karo |
| 413 | Report/body too large |
| 415 | Report upload needs multipart/form-data |
| 422 | Invalid fields, date, referral, parent connection or file type |
| 429 | OTP cooldown / request rate limit |
| 502 | Cloudinary unavailable/upload failed |
| 503 | Database/schema, SMTP signup delivery or Cloudinary configuration unavailable |

Error body: `{"error":{"code":"machine_readable_code","message":"Readable explanation"}}`.
Validation errors can also include a `fields` list. Never log passwords, tokens or OTPs.

## 11. Complete API inventory

Table actual Flask route metadata se generated hai. Body schema ka full JSON/validation
[full API reference](backend/docs/API_DOCUMENTATION.md) mein diya hai. Listed paths
backend base URL ke relative hain. Normal GET routes ko request JSON nahi chahiye.

<!-- API_TABLE_START -->

| Method | API path | Access | Request body |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/refresh` | public / limited challenge | `RefreshRequest` |
| POST | `/api/v1/auth/logout` | SUPERADMIN, ADMIN, DOCTOR, PATIENT | `None` |
| POST | `/api/v1/auth/logout-all` | SUPERADMIN, ADMIN, DOCTOR, PATIENT | `None` |
| POST | `/api/v1/auth/forgot-password` | public / limited challenge | `ForgotPassword` |
| POST | `/api/v1/auth/reset-password` | public / limited challenge | `ResetPassword` |
| POST | `/api/v1/auth/change-password` | SUPERADMIN, ADMIN, DOCTOR, PATIENT | `ChangePassword` |
| POST | `/api/v1/auth/initial-password` | public / limited challenge | `InitialPassword` |
| GET | `/api/v1/auth/sessions` | SUPERADMIN, ADMIN, DOCTOR, PATIENT | `None` |
| DELETE | `/api/v1/auth/sessions/{session_id}` | SUPERADMIN, ADMIN, DOCTOR, PATIENT | `None` |
| POST | `/api/v1/auth/request-email-verification` | public / limited challenge | `Login` |
| POST | `/api/v1/auth/resend-otp` | public / limited challenge | `Challenge` |
| POST | `/api/v1/doctors/login` | public / limited challenge | `Login` |
| GET | `/api/v1/doctors/me` | DOCTOR | `None` |
| POST | `/api/v1/doctors/register` | public / limited challenge | `DoctorRegistration` |
| POST | `/api/v1/doctors/verify-email` | public / limited challenge | `VerifyOTP` |
| POST | `/api/v1/doctors/resend-otp` | public / limited challenge | `Challenge` |
| POST | `/api/v1/doctors/approval-status` | public / limited challenge | `Login` |
| POST | `/api/v1/doctors/resubmit` | public / limited challenge | `Resubmission` |
| GET | `/api/v1/doctors/referral` | DOCTOR | `None` |
| GET | `/api/v1/doctors/patients` | DOCTOR | `None` |
| GET | `/api/v1/doctors/care-profiles` | DOCTOR | `None` |
| GET | `/api/v1/doctors/care-profiles/{profile_id}` | DOCTOR | `None` |
| GET | `/api/v1/doctors/care-profiles/{profile_id}/reports` | DOCTOR | `None` |
| GET | `/api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download` | DOCTOR | `None` |
| POST | `/api/v1/patients/login` | public / limited challenge | `Login` |
| GET | `/api/v1/patients/me` | PATIENT | `None` |
| POST | `/api/v1/patients/register` | public / limited challenge | `PatientRegistration` |
| POST | `/api/v1/patients/verify-email` | public / limited challenge | `VerifyOTP` |
| POST | `/api/v1/patients/resend-otp` | public / limited challenge | `Challenge` |
| POST | `/api/v1/patients/verify-login-otp` | RETIRED: HTTP 410 | `VerifyOTP` |
| POST | `/api/v1/patients/connect-doctor` | PATIENT | `ConnectDoctor` |
| GET | `/api/v1/patients/doctor` | PATIENT | `None` |
| POST | `/api/v1/patients/profiles` | PATIENT | `CareProfileCreate` |
| GET | `/api/v1/patients/profiles` | PATIENT | `None` |
| GET | `/api/v1/patients/profiles/{profile_id}` | PATIENT | `None` |
| POST | `/api/v1/patients/profiles/{profile_id}/connect-doctor` | PATIENT | `CareProfileReferral` |
| POST | `/api/v1/patients/profiles/{profile_id}/reports` | PATIENT | `multipart: file` |
| GET | `/api/v1/patients/profiles/{profile_id}/reports` | PATIENT | `None` |
| GET | `/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download` | PATIENT | `None` |
| POST | `/api/v1/admin/login` | public / limited challenge | `Login` |
| GET | `/api/v1/admin/me` | ADMIN | `None` |
| POST | `/api/v1/admin/register` | public / limited challenge | `Registration` |
| POST | `/api/v1/admin/verify-email` | public / limited challenge | `VerifyOTP` |
| POST | `/api/v1/admin/resend-otp` | public / limited challenge | `Challenge` |
| POST | `/api/v1/admin/verify-login-otp` | RETIRED: HTTP 410 | `VerifyOTP` |
| GET | `/api/v1/admin/dashboard` | ADMIN | `None` |
| GET | `/api/v1/admin/doctor-requests` | ADMIN | `None` |
| GET | `/api/v1/admin/doctors` | ADMIN | `None` |
| POST | `/api/v1/admin/doctors/{user_id}/approve` | ADMIN | `None` |
| POST | `/api/v1/admin/doctors/{user_id}/reject` | ADMIN | `Rejection` |
| POST | `/api/v1/admin/doctors/{user_id}/suspend` | ADMIN | `None` |
| POST | `/api/v1/admin/doctors/{user_id}/reactivate` | ADMIN | `None` |
| GET | `/api/v1/admin/patients` | ADMIN | `None` |
| POST | `/api/v1/superadmin/login` | public / limited challenge | `SuperLogin` |
| GET | `/api/v1/superadmin/me` | SUPERADMIN | `None` |
| GET | `/api/v1/superadmin/dashboard` | SUPERADMIN | `None` |
| GET | `/api/v1/superadmin/admin-requests` | SUPERADMIN | `None` |
| GET | `/api/v1/superadmin/admins` | SUPERADMIN | `None` |
| POST | `/api/v1/superadmin/admins/{user_id}/approve` | SUPERADMIN | `None` |
| POST | `/api/v1/superadmin/admins/{user_id}/reject` | SUPERADMIN | `Rejection` |
| POST | `/api/v1/superadmin/admins/{user_id}/suspend` | SUPERADMIN | `None` |
| POST | `/api/v1/superadmin/admins/{user_id}/reactivate` | SUPERADMIN | `None` |
| GET | `/api/v1/superadmin/doctors` | SUPERADMIN | `None` |
| GET | `/api/v1/superadmin/patients` | SUPERADMIN | `None` |
| GET | `/api/v1/superadmin/audit-logs` | SUPERADMIN | `None` |
| GET | `/api/v1/health` | public / limited challenge | `None` |
| GET | `/api/v1/health/ready` | public / limited challenge | `None` |

<!-- API_TABLE_END -->

## 12. Database checks aur deployment state

New users `public.profiles` mein nahi, `familycare.users` mein save hote hain:

```sql
SELECT public_id, full_name, email, role, email_verified, approval_status, created_at
FROM familycare.users
ORDER BY created_at DESC;

SELECT u.public_id, u.full_name, d.referral_id
FROM familycare.users u
JOIN familycare.doctor_profiles d ON d.user_id = u.id;

SELECT id, owner_id, profile_type, module, name, dob, parent_profile_id, referred_doctor_id
FROM familycare.care_profiles
ORDER BY created_at DESC;

SELECT id, profile_id, name, storage_provider, cloudinary_public_id, folder
FROM familycare.care_reports
ORDER BY created_at DESC;
```

Latest migration: `0004_members_cloudinary`. Existing care records/report bytes were
preserved. The `0002_care_profiles` compatibility marker represents an earlier deployed
extension whose source was missing; `0004` now adopts and extends those care tables.

Checks:

```powershell
# In backend/
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m scripts.export_api_docs

# In admin/
npm run build
node tests/smoke.mjs
```

Backend workflow tests use isolated SQLite by default; optional PostgreSQL tests need
a dedicated loopback `_test` database. They never use Supabase production data. The
admin smoke test starts its own isolated API/database and sends no email. Live
Cloudinary transfer still needs real keys and a separate verification upload.
