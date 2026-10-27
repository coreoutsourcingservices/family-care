# Patient self, family members and medical reports

Base URL: `http://127.0.0.1:5001`. All APIs below require login.

```http
Authorization: Bearer PATIENT_ACCESS_TOKEN
Content-Type: application/json
```

Signup uses the existing `/api/v1/patients/register` and `/verify-email` flow.
After verification or email/password login, use the returned access token. Do not
send account passwords again when adding members. Member records are care profiles,
not independent login accounts; the patient account owns them.

## 1. Add self profile

`POST /api/v1/patients/profiles`

```json
{
  "profile_type": "self",
  "module": "adult",
  "full_name": "Rahul Kumar",
  "date_of_birth": "1990-04-12",
  "referral_id": "rahulkumarD000001"
}
```

`referral_id` is optional; use an actual approved active doctor's referral ID.
Only one self profile is allowed per patient account (duplicate returns 409).
The response is HTTP 201 with `profile.id`, which is used in subsequent URLs.
Every profile can select its own doctor; an account's signup referral does not
automatically share all family members' reports with that doctor.

## 2. Add child member with parent connection

`POST /api/v1/patients/profiles`

```json
{
  "profile_type": "member",
  "module": "child",
  "full_name": "Aarav Kumar",
  "date_of_birth": "2018-05-14",
  "parent_profile_id": "PARENT_OR_SELF_PROFILE_UUID",
  "guardian_contact": "+919876543210",
  "emergency_contacts": [
    {"name": "Rahul Kumar", "mobile_number": "+919876543210", "relationship": "father"}
  ],
  "referral_id": "rahulkumarD000001"
}
```

`parent_profile_id`, guardian, emergency contacts and referral are optional. Parent
must be an older adult/women profile owned by the same account. Another patient's
profile cannot be linked. Dates cannot be in the future. Names and dates belong to
the member, while the existing patient account controls access.

## 3. Adult and women members

Use the same POST URL with `profile_type: "member"` and `module: "adult"` or `"women"`.

```json
{
  "profile_type": "member",
  "module": "women",
  "full_name": "Priya Kumar",
  "date_of_birth": "1994-08-20",
  "referral_id": "rahulkumarD000001"
}
```

## 4. List, details and doctor connection

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/patients/profiles?page=1&per_page=25` | Own self/member profiles |
| GET | `/api/v1/patients/profiles?module=child` | Filter by child/adult/women |
| GET | `/api/v1/patients/profiles/{profile_id}` | One owned profile |
| POST | `/api/v1/patients/profiles/{profile_id}/connect-doctor` | Connect approved doctor using referral |

Connect body:

```json
{"referral_id":"rahulkumarD000001"}
```

One doctor per profile. A different doctor returns 409; connect is not a reassignment
API. Connecting a profile explicitly allows that doctor to see its details and reports.

## 5. Upload a medical report photo or PDF

`POST /api/v1/patients/profiles/{profile_id}/reports`

In Insomnia/Postman choose **Multipart Form**, add field **file**, change its type to
**File**, and select a JPEG, PNG, WebP or PDF. Keep Authorization. Remove a manually
set JSON Content-Type header; let the client generate the multipart boundary.
One file per request, maximum 10 MB. File type is detected from content, not the filename.

```bash
curl -X POST "http://127.0.0.1:5001/api/v1/patients/profiles/PROFILE_UUID/reports" \
  -H "Authorization: Bearer PATIENT_ACCESS_TOKEN" \
  -F "file=@blood-test.pdf"
```

Example HTTP 201 response (IDs/URLs are placeholders):

```json
{
  "report": {
    "id": "REPORT_UUID",
    "profile_id": "PROFILE_UUID",
    "name": "blood-test.pdf",
    "content_type": "application/pdf",
    "storage_provider": "cloudinary",
    "url": "SHORT_LIVED_SIGNED_CLOUDINARY_DOWNLOAD_URL",
    "secure_url": "AUTHENTICATED_CLOUDINARY_ASSET_URL",
    "url_expires_in": 300,
    "public_id": "familycare/C000001/profiles/PROFILE_UUID/child/reports/REPORT_UUID_blood-test.pdf",
    "folder": "familycare/C000001/profiles/PROFILE_UUID/child/reports",
    "resource_type": "raw",
    "delivery_type": "authenticated",
    "size_bytes": 12345
  }
}
```

Photos use Cloudinary `image` resources; PDF uses `raw` to preserve its original bytes.
Both use authenticated delivery. The original filename is saved in `name`; the
asset public ID includes a random report UUID to prevent collisions/overwrites.
Folders use account/profile identifiers rather than names or email addresses.
`public_id` is an asset identifier, not public authorization. The canonical `secure_url`
is protected; use the signed `url`, valid for 5 minutes. Listing/download APIs issue
fresh links only after checking account ownership or explicit doctor connection.
Do not publish signed URLs; anyone who receives one can use it until expiry.
Cloudinary delivery behavior: https://cloudinary.com/documentation/control_access_to_media

## 6. Reports and downloads

| Method | Path |
| --- | --- |
| GET | `/api/v1/patients/profiles/{profile_id}/reports?page=1&per_page=25` |
| GET | `/api/v1/patients/profiles/{profile_id}/reports/{report_id}/download` |

Cloudinary download returns JSON containing a fresh signed URL. Older database-stored
reports remain downloadable as attachment bytes. Existing data is not uploaded or
deleted automatically by this migration.

## 7. Referred doctor access

Use the doctor's access token:

- `GET /api/v1/doctors/care-profiles`
- `GET /api/v1/doctors/care-profiles/{profile_id}`
- `GET /api/v1/doctors/care-profiles/{profile_id}/reports`
- `GET /api/v1/doctors/care-profiles/{profile_id}/reports/{report_id}/download`

Only explicitly connected profiles are accessible. Doctors cannot add members or
upload reports through the patient APIs. Profile/report UUIDs from another account
return 404 instead of exposing their metadata or files.

## Cloudinary setup (credentials stay local)

The tracked `.env.example` contains blank placeholders; set actual credentials only in the ignored backend `.env`:

```dotenv
CLOUDINARY_CLOUD_NAME=""
CLOUDINARY_API_KEY=""
CLOUDINARY_API_SECRET=""
```

Set these privately and restart the backend. Until then report upload returns HTTP
503 `cloudinary_not_configured`; self/member/profile APIs continue to work. Upload
tests mock Cloudinary, so live cloud delivery is not claimed until real keys are set.
Cloudinary failures return 502; unsupported/empty files 422; oversized uploads 413.
Only explicit file uploads are accepted; clients cannot save arbitrary Cloudinary URLs
or choose another profile's public ID/folder.

Migration: `python -m alembic upgrade head` (`0004_members_cloudinary`). Existing care
profiles become `member` profiles; existing report bytes and metadata are preserved.
