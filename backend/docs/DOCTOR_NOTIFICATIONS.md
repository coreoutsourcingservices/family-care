# Doctor charts and notifications

Dashboard charts use Chart.js and existing connected-profile / consultation APIs.
Line: connected profiles grouped by their creation month (last six months). Doughnut: care
areas. Bar: recorded consultation-request statuses. No sample clinical values are
generated. Empty accounts have empty charts; approval-required accounts see locked
chart panels and do not fetch clinical data.

## Inbox and Web Push

Apply migration `0014_doctor_notifications`. It adds an account-scoped inbox,
browser subscriptions and a per-device delivery outbox. New profile connections,
consultation requests, shared reports, profile submissions and admin approval or
rejection queue generic notifications in the same transaction as the event.
There are no patient names, medical notes or report filenames in push payloads.

Doctor email verification/setup, pending login and approved `/doctors/me` responses
include a one-hour `notification_token`. It is held in frontend memory, sent only
in the Authorization header and cannot access clinical APIs. Approved tokens bind
to the cookie/bearer session and are rejected when that session is revoked. All
notification tokens bind to the current password hash and active verified account.

All endpoints below require `Authorization: Bearer <notification_token>`:

| Endpoint | Behavior |
| --- | --- |
| `GET /api/v1/doctors/notifications?page=1&per_page=25` | Paginated owned inbox and total unread count |
| `POST /api/v1/doctors/notifications/:id/read` | Mark one owned item read |
| `GET /api/v1/doctors/notifications/push-config` | Public VAPID key and readiness flag |
| `POST /api/v1/doctors/notifications/subscriptions` | Browser PushSubscription JSON (`endpoint`, `keys.auth`, `keys.p256dh`) |
| `DELETE /api/v1/doctors/notifications/subscriptions` | JSON `{ "endpoint": "..." }`, scoped to the current user |

Only HTTPS endpoints for the supported Chrome/Firefox/Apple/Edge push services are
accepted. EC keys are validated. Subscription endpoints cannot be transferred to
another account. Private signing keys never reach the frontend. Password changes,
logout-all and session revocation clear server subscriptions; regular sign-out also
attempts to remove the current browser subscription.

## Local setup

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/configure_push.py
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe server.py
```

The configuration script preserves existing keys, generates an ignored
`.webpush-private.pem` file once, and uses the configured SMTP_FROM as the VAPID
contact. Back up that private key securely; changing it invalidates existing browser
subscriptions. The public key and private-file path are saved only in the ignored
backend `.env`.

`server.py` starts one daemon delivery worker for local Waitress. Production WSGI
deployments should run a separate process:

```powershell
python scripts/run_doctor_push.py
```

The worker polls every 15 seconds and locks individual outbox rows. Successful
per-device deliveries are not retried; temporary failures back off (up to five
attempts). HTTP 404/410 removes expired subscriptions. Push TTL is one hour.
Stable notification tags let the OS replace retries of the same notification.
An outage between push-provider acceptance and database commit can still repeat a
delivery; clients deduplicate in-app toasts by event ID.

## Browser behavior

The common doctor shell has a bell on every page, an unread badge, persisted read
state and a cross-page toast. The inbox refreshes every 30 seconds while visible,
on focus and when the service worker receives a push. Permission is requested only
after the user clicks **Enable notifications** in the bell panel or Settings.

`/doctor-sw.js` handles background delivery and same-origin notification clicks.
It never caches clinical pages or responses. `/doctor.webmanifest` and touch icons
support installation. Push works without an open doctor page when the browser/OS
permits background delivery; the server and worker must be running.

Mobile requires HTTPS; localhost is a development exception on the same device.
On iPhone/iPad, install the website on the Home Screen and allow notifications from
that installed app (iOS/iPadOS 16.4+). A plain HTTP LAN URL is not a mobile push test.

Primary references: [MDN Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API),
[Apple Web Push](https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers),
[Chart.js responsive charts](https://www.chartjs.org/docs/latest/configuration/responsive.html).

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_doctor_notifications.py -q
node doctor/scripts/check-charts-notifications.mjs
```

Run the Node check from the repository root. Browser tests mock push registration
and HTTP delivery, and execute service-worker handlers in an isolated environment.
They do not send real push messages or display OS notifications. A real phone must
still opt in on its HTTPS origin to verify device delivery.
