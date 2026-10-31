# Adult and women family invitations: API request and response guide

Base API: `http://127.0.0.1:5001`. Invite page: `http://127.0.0.1:5173/customer/family-invite`.
All examples use synthetic identities and abbreviated IDs. Replace placeholders. This is implemented API behavior, not a proposal. Delivery tests mock SMTP; inbox delivery is not established by a unit test.

## Who receives which email?

| Step | Destination | Result |
| --- | --- | --- |
| Family sends adult/women invitation | Invited member's email | One-use setup link with family name/email, relationship and care area |
| Member submits name/email/mobile/DOB/password form | Inviting family's email | Six-digit setup approval OTP; family shares it with the member |
| Member enters correct family approval OTP | No extra OTP email | Creates member PATIENT account and linked adult/women profile atomically |
| Member signs in | No login OTP | Member's own email and password |
| Member chooses forgot password | Member's own email | Password reset OTP; never routed to the inviting family |

`relationship` is from the inviting family's perspective; default is `Family member`. Send a value such as `Mother`, `Father`, `Spouse`, `Sister`, `Brother`, `Son` or `Daughter`. The API accepts a nonblank relationship up to 50 characters.
`module` is exactly `adult` or `women` (not `woman`). These areas accept age 13–120, matching the existing product split after Child Care (0–12). No gender is inferred from an email address.

There is no shared family password. Each member gets their own password hash and user ID. A random 256-bit invitation secret is generated; only its SHA-256 hash is stored. The secret is not a hash of the family's email and is not returned in the create/list responses. It is delivered in the invite email link, in a URL fragment. Keep the secret and API paths containing it out of application/access logs and analytics. Set an appropriate Referrer-Policy at the production web host.

## Authentication and configuration

Family create/list/revoke: authenticated `PATIENT` access token:

```http
X-Auth-Transport: bearer
Authorization: Bearer <family_access_token>
Content-Type: application/json
```

Browser family clients use HttpOnly cookies, `credentials: include`, `X-Auth-Transport: cookie`, `X-FamilyCare-Portal: patient`, `X-Requested-With: FamilyCare`, plus the login/refresh `X-CSRF-Token` on authenticated mutations.
Preview/setup/verify/resend use the secret link, not a family access token. Browser clients still send the cookie transport guard headers; no authenticated session is required. Do not send or ask members for the family's password.

Deployment:

- Run `venv/Scripts/python.exe -m alembic upgrade head` from `backend` to install migration `0018_family_invitations`.
- Configure SMTP via the existing ignored backend `.env` settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, TLS and credentials).
- Set `FAMILY_INVITE_FRONTEND_URL` to the trusted frontend origin, e.g. `https://your-familycare-host.example`. Local default: `http://127.0.0.1:5173`.
- Invite and approval OTP emails are sent synchronously. `email_status: sent` means SMTP accepted delivery, not proof that it arrived in Inbox.
- Existing forgot-password emails are queued: run `venv/Scripts/python.exe -m scripts.mail_worker` from `backend`.
- Run the notification socket gateway separately for live family-bell updates. A persistent `family_member_joined` notification is created after successful verification.

## 1. Family creates an invitation

`POST /api/v1/patients/family-invitations`

```json
{
  "full_name": "Example Member",
  "email": "member@example.com",
  "module": "women",
  "relationship": "Mother"
}
```

For adult, send `"module": "adult"`. Omitting `relationship` uses `Family member`.
Do not send member password, DOB or OTP at this step.

HTTP 201:

```json
{
  "invitation": {
    "id": "<invitation UUID>",
    "full_name": "Example Member",
    "email": "member@example.com",
    "module": "women",
    "relationship": "Mother",
    "status": "PENDING",
    "expires_at": "<UTC timestamp, 24 hours later>",
    "profile_id": null
  },
  "email_status": "sent"
}
```

Member email contains `http://127.0.0.1:5173/customer/family-invite#token=<secret>`. Name/email are stored from the family invitation and cannot be replaced during acceptance. Existing account emails return 409; this flow does not silently attach an existing account. Duplicate active invites from the same family/email return 409. Revoke and send again to replace an invite.

## 2. Family lists or revokes invitations

`GET /api/v1/patients/family-invitations?page=1&per_page=25`

No request body. HTTP 200:

```json
{
  "items": [
    {
      "id": "<invitation UUID>",
      "full_name": "Example Member",
      "email": "member@example.com",
      "module": "women",
      "relationship": "Mother",
      "status": "PENDING",
      "expires_at": "<UTC timestamp>",
      "profile_id": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

Statuses: `PENDING`, `ACCEPTED`, `REVOKED`, `EXPIRED`. Accepted entries include `profile_id`.

`DELETE /api/v1/patients/family-invitations/{invite_id}`

No request body. HTTP 200: `{"message":"Invitation revoked"}`.
Only the inviting family can revoke. Already accepted returns 409; this is not an endpoint for removing an accepted member or deleting their account.

## 3. Member opens the link

Frontend reads the secret from the URL fragment and calls:

`GET /api/v1/family-invitations/{token}`

No request body or login required. HTTP 200:

```json
{
  "invitation": {
    "id": "<invitation UUID>",
    "full_name": "Example Member",
    "email": "member@example.com",
    "module": "women",
    "relationship": "Mother",
    "status": "PENDING",
    "expires_at": "<UTC timestamp>",
    "profile_id": null
  },
  "family": {"full_name": "Example Family", "email": "family@example.com"},
  "form": {"full_name": "Example Member", "email": "member@example.com", "readonly": ["full_name", "email"]},
  "otp_destination": "inviting_family_email",
  "shared_profile": true
}
```

The page clearly names the inviting family and explains shared-profile access before submission. Invalid secret returns 404. Expired, revoked or consumed link returns 410. Invite lifetime: 24 hours; only one successful acceptance.

## 4. Member submits profile setup

`POST /api/v1/family-invitations/{token}/setup`

```json
{
  "full_name": "Example Member",
  "email": "member@example.com",
  "mobile_number": "+919876543211",
  "date_of_birth": "1995-02-28",
  "password": "Choose-Your-Password8!",
  "confirm_password": "Choose-Your-Password8!"
}
```

HTTP 202:

```json
{
  "message": "Approval OTP sent to the inviting family email.",
  "email_status": "sent",
  "otp_destination": "inviting_family_email",
  "expires_in": 300,
  "resend_after": 60
}
```

Name/email must match the invitation. Mobile is 8–15 digits with optional leading `+`; password is 8–128 characters and confirmation must match. The form requires explicit acceptance of the family/profile sharing relationship. Before OTP verification, no member User or CareProfile is created. Pending setup stores an Argon2 password hash and HMAC OTP hash, never plaintext password/OTP. Link possession proves access to the member's invitation inbox; the approval OTP proves the family's approval. There is no second member-email signup OTP in this flow.

## 5. Resend family approval OTP

`POST /api/v1/family-invitations/{token}/resend-otp`

Body: `{}`. Response: same HTTP 202 shape as setup. Destination is still `family@example.com`, not member email. Wait 60 seconds; a fresh OTP replaces the previous one. The setup form must have been submitted first (otherwise 409). Resubmitting setup after the cooldown also replaces pending values and OTP.

## 6. Member enters the OTP shared by the family

`POST /api/v1/family-invitations/{token}/verify-otp`

```json
{"otp":"123456"}
```

HTTP 201 (representative response):

```json
{
  "message": "Profile setup complete. Sign in with your own email and password.",
  "user": {
    "id": "<member UUID>",
    "public_id": "C000002",
    "full_name": "Example Member",
    "email": "member@example.com",
    "phone_number": "+919876543211",
    "role": "PATIENT",
    "email_verified": true,
    "approval_status": "APPROVED",
    "account_status": "ACTIVE",
    "must_change_password": false,
    "referred_doctor": null
  },
  "profile": {
    "id": "<profile UUID>",
    "profile_type": "member",
    "module": "women",
    "full_name": "Example Member",
    "date_of_birth": "1995-02-28",
    "member_email": "member@example.com",
    "relationship": "Mother",
    "linked_member": true,
    "parent_profile_id": null,
    "guardian_contact": "",
    "guardian_name": "",
    "emergency_contacts": [],
    "doctor": null,
    "created_at": "<UTC timestamp>"
  },
  "family": {"full_name":"Example Family", "relationship":"Mother"}
}
```

The account, profile and membership are committed together. Five wrong OTP attempts exhaust the current code. OTP expiry: five minutes. Used links cannot be replayed. Verification does not replace the browser's current patient session; member signs in explicitly.

The care profile belongs to the inviting family and is accessible by both family and the accepted member. The member only gains access to that specific profile, not the family's children, other adults, women, invitation list or family account settings. Doctor access still requires an explicit referral. Shared server records/reports use the existing APIs. Existing women's diary entries remain browser-local; this change does not convert those entries into server-synced data.

## 7. Member login and own care profile

`POST /api/v1/patients/login`

```json
{"email":"member@example.com","password":"Choose-Your-Password8!"}
```

HTTP 200 for bearer mode (user fields as above):

```json
{
  "access_token":"<member access JWT>",
  "refresh_token":"<member refresh token>",
  "token_type":"Bearer",
  "expires_in":900,
  "user":{"id":"<member UUID>","public_id":"C000002","role":"PATIENT","email":"member@example.com"}
}
```

User object above is abbreviated. Cookie mode omits tokens from JSON, sets HttpOnly cookies and returns `csrf_token`. Login has no OTP. After login:

- `GET /api/v1/patients/profiles?module=women` (or `adult`) returns the linked profile under `items` with pagination.
- `GET /api/v1/patients/profiles/{profile_id}` returns `{"profile":{...}}`.
- Existing `/patients/profiles/{profile_id}/reports` APIs work for this shared profile.
- Existing `/patients/adults/{profile_id}/records` APIs work for adult profiles. Methods/bodies are detailed in ALL_APIS.md.
- `GET /api/v1/patients/me` identifies the member's own account.

## 8. Forgot password: OTP to member email

`POST /api/v1/auth/forgot-password`

```json
{"email":"member@example.com"}
```

HTTP 202:

```json
{
  "message":"If an eligible account exists, reset instructions are queued.",
  "challenge_token":"<reset challenge JWT>",
  "expires_in":300,
  "resend_after":60,
  "email_status":"queued"
}
```

The existing mail worker resolves the member account's email. It does not use the family invite's owner email. Unknown/unavailable emails receive an indistinguishable API response.

`POST /api/v1/auth/reset-password`

```json
{
  "challenge_token":"<reset challenge JWT>",
  "otp":"123456",
  "new_password":"New-Password8!",
  "confirm_password":"New-Password8!"
}
```

HTTP 200: `{"message":"Password reset. Sign in again."}`. Existing sessions are revoked. Sign in again using the member's email and new password. To resend reset OTP use existing `POST /api/v1/auth/resend-otp` with `{"challenge_token":"<reset challenge JWT>"}`.

## Error responses

| HTTP | Examples / behavior |
| --- | --- |
| 400 | `invalid_otp`, `otp_unavailable` (expired/exhausted code) |
| 401/403 | Family token/session missing, wrong role, account suspended or cookie CSRF denied |
| 404 | Invalid invite secret, inaccessible profile or another family's invite |
| 409 | `account_exists`, `invite_exists`, `setup_required`, `invite_accepted` |
| 410 | `invite_unavailable` (expired/revoked/accepted link or unavailable family) |
| 422 | Validation, name/email mismatch, age outside 13–120, bad mobile or password confirmation |
| 429 | `otp_cooldown` or public endpoint request throttling |
| 503 | `email_delivery_failed`; no successful account creation is reported |

```json
{"error":{"code":"invalid_otp","message":"Invalid OTP"}}
```

## UI entry points and validation

Family dashboard includes an invite form and invitation list with revoke/refresh actions. Adding another adult/women member uses this invite form. Self profiles and child profiles preserve existing flows. The email link opens the prefilled member form and OTP step. Once accepted, the shared profile appears in the matching adult/women workspace for both accounts.

Automated tests: `venv/Scripts/python.exe -m pytest tests/test_family_invitations.py -q` from `backend`. Tests use isolated database fixtures and mocked SMTP, covering both modules, locked invite identity, OTP destinations, expiry, attempts, resend, replay, shared access, unrelated-family denial and member password reset.
