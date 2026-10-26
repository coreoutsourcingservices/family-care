# Flutter API integration (no UI)

Add `dio` and `flutter_secure_storage` to your Flutter application and use
`examples/flutter_api.dart`. The constructor takes a configurable API base URL.
The example saves access/refresh tokens only in secure storage and serializes refresh.
It requires platform plugin configuration from the package documentation in your app.

```dart
final api = FamilyCareApi('http://127.0.0.1:5001');
final pending = await api.post('/api/v1/patients/register', {
  'full_name': 'Example', 'email': 'user@example.com',
  'mobile_number': '+919876543210',
  'password': 'Choose-Password8!', 'confirm_password': 'Choose-Password8!',
});
await api.post('/api/v1/patients/verify-email', {
  'challenge_token': pending['challenge_token'], 'otp': enteredCode,
});
final profile = await api.dio.get('/api/v1/patients/me');
await api.logout();
```

For patient/admin login, submit email/password, retain the challenge (not an access token),
then call the matching verify-login-otp endpoint with the email code. Resend returns a
NEW challenge token; replace the old one. Doctor verification only queues review.
Doctor login issues credentials after approval. Treat HTTP 202 as an intermediate
workflow state; never treat it as dashboard authentication.

Android emulator base is normally `http://10.0.2.2:5001`; physical devices cannot use
their own localhost to reach the PC. Bind an explicitly authorized LAN address and
configure the firewall for LAN tests; current server binds only to host loopback.
Use HTTPS on deployment. This repo does not contain or generate Flutter screens.
