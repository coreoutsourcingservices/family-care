# Connected doctor appointments

Doctor profile (`/doctor/setup-account`) has an **Appointments** tab after approval. The same schedule editor and booked patient list are available at `/doctor/appointments`.

Patients open **Appointments** from Family (`/customer/dashboard?view=appointments`), Adult (`/customer/adult/appointments`) or Women (`/customer/women/appointments`). Family offers the signed-in user's self/child profiles; invited adult/women members book through their own primary account. The server enforces primary-profile ownership and the current doctor connection.

## Schedule

All windows use **Asia/Kolkata (IST)**, independent of browser timezone. A window repeats on its selected weekdays, with a separate patient capacity for each calendar date. A booking reserves a place in the window, not an exact minute. The first editor suggests 10:00–12:00 and 13:00–16:00; they are not published until the doctor saves.

- `GET /api/v1/doctors/appointment-schedule` — approved Doctor; returns `{windows, version, timezone}`. Empty schedule has version `0`.
- `PUT /api/v1/doctors/appointment-schedule` — approved Doctor; replaces windows with optimistic version checking.

```json
{
  "version": 0,
  "windows": [
    {"id":"<new UUID>","start":"10:00","end":"12:00","capacity":20,"days":[0,1,2,3,4,5]},
    {"id":"<new UUID>","start":"13:00","end":"16:00","capacity":30,"days":[0,1,2,3,4,5]}
  ]
}
```

Days are Monday `0` to Sunday `6`. Each window requires a positive whole-number capacity, a unique ID and a nonoverlapping same-day range. There is no fixed two-/three-hour duration, 20-window cap or 500-patient capacity cap. Preserve IDs when editing. Future booked windows cannot be removed/moved or have capacity reduced below their existing per-date occupancy. Stale versions return `409 schedule_changed`; invalid ranges/overlaps return `422`.

## Availability and booking

- `GET /api/v1/patients/appointment-profiles` — profiles for which the patient is primary.
- `GET /api/v1/patients/profiles/{profile_id}/appointment-availability?date=YYYY-MM-DD` — only this profile's currently connected approved doctor; returns `doctor`, `date`, `timezone`, and `items` with `id`, `start`, `end`, `capacity`, `booked`, `remaining`, and `status` (`AVAILABLE`, `FULL`, `CLOSED`). No doctor connection returns `doctor:null` and no windows.
- `GET /api/v1/patients/profiles/{profile_id}/appointments` — up to 200 recent bookings made by this patient for the profile, including previous-doctor history.
- `POST /api/v1/patients/profiles/{profile_id}/appointments` — books a capacity place immediately (`BOOKED`).

```json
{"window_id":"<schedule window UUID>","appointment_date":"2026-11-10","request_id":"<client-generated UUID>"}
```

Choose today through 90 days ahead; a window that has started cannot be booked. No doctor ID is accepted: it is derived from the current profile connection. A PostgreSQL doctor-row lock serializes bookings, cancellations and schedule updates. A full window returns `409 window_full`; duplicates for the same profile/date/window return `409 already_booked`. Repeating an identical `request_id` returns the original booking (`200`) without consuming another place or queuing another email. A changed payload with the same request ID returns `409 booking_key_reused`.

## Doctor list and changes

- `GET /api/v1/doctors/booked-appointments?date=YYYY-MM-DD` — Doctor's bookings for that date, ordered by time and booking creation. Includes patient name, date/window, status and `email_status`.
- `PATCH /api/v1/doctors/booked-appointments/{booking_id}/status` with `{"status":"CANCELLED"}` or `{"status":"COMPLETED"}` — only that doctor; completion is blocked before the window starts.
- `PATCH /api/v1/patients/profiles/{profile_id}/appointments/{booking_id}/status` with `{"status":"CANCELLED"}` — only the primary patient who booked; blocked once the window starts.

Cancelled places become available again. Completed bookings still consume that day's capacity. Existing individual consultation requests/appointments retain their separate workflow; the new capacity windows are shown separately.

## Email and notifications

A successful booking atomically queues one `EmailNotification` (`appointment_booked`) to the connected doctor's account email and a doctor inbox notification linking to Appointments. Email includes patient, booking user, appointment date, start/end and IST timezone. Booking does not wait on SMTP. Failed delivery is retried by the existing outbox with backoff, up to eight attempts; the booking remains saved. Cancelling an unsent booking cancels its pending email.

The local `server.py` starts an appointment-only outbox worker when `SMTP_HOST` and `SMTP_FROM` are configured. It does not drain unrelated queued emails. Production uses the existing `python scripts/mail_worker.py` process. SMTP TLS and credentials follow the existing backend configuration. `PENDING` means queued, `SENT` means handed to SMTP, and `FAILED` means retries exhausted; none of these proves inbox placement.

All endpoints require approved active sessions of the stated role. Cookie writes require the normal FamilyCare portal and CSRF headers. Apply migration `0033_capacity_appointments` and restart the API before use.


## Consultation modes, fees and documents

`GET /api/v1/doctors/consultation-settings` returns `doctor_id`, `referral_id` and
`consultation_options`. `PUT` saves the options for the signed-in doctor:

```json
{"physical_enabled":true,"physical_fee_paise":50000,"video_enabled":true,"video_fee_paise":35000}
```

Amounts are integer INR paise; zero means a free consultation. At least one mode
must be enabled. Profile setup also accepts `consultation_options`.

Availability accepts optional `doctor_id` so a profile owner may book an approved
doctor from the directory without changing the profile's doctor connection or
record-sharing permissions. Booking accepts `doctor_id`, `mode` (`physical` or
`video`), `expected_fee_paise`, `notes` (up to 2,000 characters), and up to ten
`report_ids` belonging to the same profile, in addition to the window, date and
idempotency key. A changed fee returns 409; disabled or unpriced modes return 422.
The selected mode and current fee are snapshotted in `appointment.details`.
No payment collection or video room is created.

Upload optional files individually through the profile report upload endpoint,
then send the resulting report IDs. This grants the booked doctor access to these
specific attachments, without sharing the rest of the profile. Doctor booking
responses include document IDs and filenames. The booked doctor may download via
`GET /api/v1/doctors/booked-appointments/{booking_id}/documents/{report_id}`.
Other doctors receive 404. Patient and doctor booking lists include saved notes,
mode and fee; cancellations continue to use the status endpoint.
