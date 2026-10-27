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

All roles log in with email/password and receive sessions directly after verification
and approval. No login OTP is sent. Registration OTP still uses a challenge token;
resend replaces that token. HTTP 202 is an intermediate registration/approval state
or initial superadmin password change, not dashboard authentication.

Android emulator base is normally `http://10.0.2.2:5001`; physical devices cannot use
their own localhost to reach the PC. Bind an explicitly authorized LAN address and
configure the firewall for LAN tests; current server binds only to host loopback.
Use HTTPS on deployment. This repo does not contain or generate Flutter screens.

Current login flow: all roles use email + password without login OTP. Signup email OTP,
password-reset OTP, account approval and first-login password change are preserved.
Legacy superadmin username login remains compatible. Legacy verify-login-otp routes return HTTP 410.
