# Web API integration (no UI)

Use `examples/web_api.js`. Configure exact backend/frontend origins in the server CORS
allowlist; development example allows localhost:3000 and localhost:5173. Same-site
deployment with an HTTPS reverse proxy is recommended; SameSite=Lax will not support
arbitrary cross-site third-party-cookie deployments.

```javascript
restoreCsrf();
const step = await api('/api/v1/admin/login', 'POST', {
  email: 'admin@example.com', password: enteredPassword,
});
// For an approved admin: prompt in your own frontend for the email OTP.
await api('/api/v1/admin/verify-login-otp', 'POST', {
  challenge_token: step.challenge_token, otp: enteredCode,
});
const profile = await api('/api/v1/admin/me');
await api('/api/v1/auth/logout', 'POST');
```

Cookie mode sends `credentials: include`, `X-Auth-Transport: cookie`,
`X-Requested-With: FamilyCare`. The API client stores only the CSRF value in sessionStorage;
auth cookies are HttpOnly. Refresh rotates CSRF; the example replaces it and retries one
failed protected request. Handle failed refresh by showing your own login flow.
Do not auto-refresh or auto-retry login/OTP business errors in application code.
Registration and approval states are backend decisions; clients display HTTP 202 status.
No HTML login/signup/dashboard UI is built by this project.
