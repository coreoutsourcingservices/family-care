# Women: doctor-to-doctor referrals

Base API: `http://127.0.0.1:5001/api/v1`. Doctor UI: `http://127.0.0.1:5175/doctor/referrals`.
The first doctor opens Patients → shared Women profile → Refer to another doctor.
The woman reviews requests in Women → Access & Sharing → Doctor referral approvals.

The first doctor must be the currently connected, approved doctor and hold active Medical records tab permission. A referral does not replace that doctor or give the second doctor general access to the woman's workspace. No AI service receives medical text: the referring doctor writes the bullet summary.

## App doctor

1. GET `/doctors/women/{profile_id}/handoff-options` returns `patient_name` and accessible `reports` (`id`, `name`, `category`).
2. POST `/doctors/women/{profile_id}/handoffs`:

```json
{
  "doctor_identifier": "D000002",
  "summary": ["Reason for referral: specialist review", "Please review the attached laboratory report."],
  "report_ids": ["<report UUID>"],
  "expires_in_days": 7
}
```

`doctor_identifier` accepts the exact referral ID or doctor public ID, case-insensitively. Recipient must be active, approved and different from the first doctor. The response is HTTP 201 `{"handoff": {..., "status": "PENDING"}}`. No reports are released yet.

3. The woman GETs `/women/profiles/{profile_id}/handoffs`, reviews recipient, bullets and filenames, then PUTs `/women/profiles/{profile_id}/handoffs/{handoff_id}`:

```json
{"decision": "APPROVED"}
```

Use `DECLINED` to reject a pending referral, or `REVOKED` to stop an approved referral. Only the profile's primary woman account can decide; an inviting family account cannot decide for an accepted member. Decisions return HTTP 200 `{"handoff": {...}}`.

4. GET `/doctors/handoffs` returns sent requests and approved incoming referrals. Pending/declined referrals are not disclosed to the recipient. Each row includes `direction`, `status`, source/recipient identity, expiry and (when authorized) patient name, summary and selected report filenames.
5. GET `/doctors/handoffs/{handoff_id}/download` returns an authenticated `application/zip` attachment with original selected reports and `referral-summary.txt` containing the doctor-authored bullets. Never put access tokens or private report links in message URLs.

## External doctor

Omit `doctor_identifier` and send:

```json
{
  "external_name": "External specialist",
  "external_email": "specialist@example.com",
  "external_phone": "+919876543210",
  "summary": ["Reason for referral: specialist review"],
  "report_ids": ["<report UUID>"],
  "expires_in_days": 7
}
```

Provide at least an email or phone. The woman's approval identifies this recipient and authorizes the first doctor to download the selected files. After approval, the first doctor downloads the ZIP; Share report files opens the device file share sheet where supported. Otherwise it downloads the file. Open WhatsApp and Compose email open drafts; the doctor attaches the ZIP and sends it manually. These links do not attach files automatically. No external email/WhatsApp is sent by the backend.

## Limits and revocation

- 1–20 selected reports from the same profile, 1–20 bullets of 1–500 characters each, access duration 1–30 days, default seven days from request creation.
- ZIP is limited to 50 MiB of original report content; individual report limits still apply.
- Download rechecks patient approval, expiry, active doctors, source doctor's current connection and Medical records permission, and report membership/existence. Losing source permission or connection stops subsequent downloads.
- Revocation stops further authenticated access. Already downloaded or externally sent copies cannot be recalled.
- Notifications and audit events record requests, decisions and downloads. No schema or report storage is copied to a second doctor account.
- Errors include 403 for missing consent/access, 404 for unrelated referrals, 409 for unavailable reports or invalid decisions, 413 for an oversized ZIP, 422 for invalid recipient/input, and 502 for report storage download failures.
- Cookies use `X-Auth-Transport: cookie`, `X-FamilyCare-Portal: doctor|patient`, credentials include and CSRF for mutations. Bearer API clients use `X-Auth-Transport: bearer` and `Authorization: Bearer <role access token>`.

Install migration: from backend, `venv/Scripts/python.exe -m alembic upgrade head`.
Tests: `venv/Scripts/python.exe -m pytest tests/test_doctor_handoffs.py tests/test_women_workspace.py -q`.
