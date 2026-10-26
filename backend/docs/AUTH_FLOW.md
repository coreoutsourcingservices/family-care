# API authentication flows

## Superadmin
Seed `superadmin` using the private CLI. Initial login with development password
`superadmin@2026` returns only a password-change challenge. Submit that challenge plus
current_password/new_password/confirm_password to `/api/v1/auth/initial-password`.
Only then are access/refresh credentials issued. Subsequent login issues a session.
Production must use a unique bootstrap password and rejects the development default.

## Admin
Register -> queued email OTP -> verify-email -> pending superadmin approval.
Superadmin lists admin-requests and approves/rejects by UUID or public ID.
Approval queues email. Login -> email/password -> queued login OTP -> verify-login-otp
-> session. Pending/rejected/suspended accounts never get dashboard credentials.

## Doctor
Register with professional registration details -> email OTP -> pending admin approval.
Admin sees qualification/council/registration and reviews. Approval queues email and
allows email/password login. Rejected doctors can check status with credentials and
resubmit corrected details through the limited resubmission API.

## Patient/customer
Register -> queued email OTP -> verify-email -> activated account and JWT session.
Subsequent login -> password check -> login OTP -> verify-login-otp -> session.
No full session is issued on the initial unverified registration response.

## Shared
Refresh rotates opaque refresh tokens; replay revokes the session family. Clients must
serialize refresh calls. Logout revokes current session; logout-all revokes every session.
Password reset: forgot-password -> generic challenge -> reset-password with email OTP.
All sessions are revoked on reset/change. `request-email-verification` restarts exhausted
signup OTP using email/password. OTP resend requires the current unused challenge.
Role-specific resend endpoints also enforce the role. Public challenge tokens cannot
be used as access JWTs. JWT expiry, issuer, audience, algorithm and purpose are verified.

Browser JSON contains CSRF token but no access/refresh credentials; those live in
HttpOnly cookies. Browser mutations require trusted Origin (when present), custom
X-Requested-With and, for authenticated requests, X-CSRF-Token bound to the session.
Cookies and Bearer sessions cannot be interchanged. Flutter stores credentials in
platform secure storage. See code-only examples and complete API reference.
