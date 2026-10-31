# Customer and doctor realtime notifications

Local gateway: `ws://127.0.0.1:5002/ws/notifications`.
Production uses `wss://<host>/ws/notifications`; set `VITE_NOTIFICATION_WS_URL`
when the gateway is hosted separately. The proxy must support WebSocket upgrades.
Run the gateway from backend with `venv/Scripts/python.exe -m scripts.notification_socket`.

1. Sign in to the matching patient or approved doctor portal.
2. `POST /api/v1/notifications/socket-ticket` with `{}` and authenticated credentials.
   Cookie clients include their portal header and CSRF token. Response:
   `{"ticket":"<short-lived ticket>","expires_in":60}`.
3. Connect to the gateway and send `{"type":"auth","ticket":"<ticket>"}`.
   Keep the ticket out of URLs and logs.
4. A `ready` event triggers inbox resync. `notification` and `unread_count` events
   trigger updates; reconnect with a fresh ticket after disconnect.

Customer uses the shared `/api/v1/notifications` inbox. Doctor socket events
refresh the existing `/api/v1/doctors/notifications` inbox so its unread/read
state, links and browser-push preferences stay compatible. Doctor events are
mirrored into the shared notification stream by the backend.

Doctor bell panel displays Live / Reconnecting / Sign in required. Both portals
retain 30-second REST resync while visible. Doctor reconnect uses backoff up to
30 seconds and session refresh for socket close code 4401; logout revokes access.
Pending doctors retain their account inbox polling until clinical access approval.

WebSocket alerts require an open connected web/app session. They do not provide
closed-app mobile background push. Doctor browser Web Push is a separate option.
