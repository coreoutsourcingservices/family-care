# Admin doctor verification and three public statuses

The public `doctor_status` field has exactly three values:

| Value | Meaning |
| --- | --- |
| pending | Not yet manually approved. An incomplete profile is not an approval request. |
| verified | An admin approved the submitted application. |
| rejected | An admin rejected the application with a reason. |

Existing `approval_status` and `verification_status` workflow fields remain
compatible for authentication and existing clients. They are not extra public
doctor status labels. Use `doctor_status` to render the three status badges.

## When the doctor reaches the admin page

Signup and email OTP create no approval request. Doctor login creates no request.
An incomplete doctor receives profile setup on login. Only submitting the full
`POST /api/v1/doctors/setup-profile` form creates an approval request. Incomplete
profiles are excluded from the admin doctor directory and dashboard counts.

The submitted doctor row has **Check Doctor**, **Approve**, **Reject** actions.
Check opens the complete submitted profile and supporting reference results.
Approve and Reject each require an explicit admin decision. Reject requires a reason.

## Check Doctor API

```http
POST /api/v1/admin/doctors/D000001/check
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{}
```

Only ADMIN can call it; the application must be submitted and pending. UUIDs are
also supported. Existing cookie transport/CSRF protection applies in the web portal.

Response **200**, abbreviated:

```json
{
  "doctor_status": "pending",
  "cached": false,
  "verification_check": {
    "checked_at": "2026-10-29T10:00:00Z",
    "checked_by": "<admin_uuid>",
    "registration": {
      "provider": "AskMyDoc (third party)",
      "status": "match",
      "comparisons": {"registration": true, "name": true, "council": true},
      "records": [{"name": "Example Kumar", "registration": "12345", "council": "Delhi"}]
    },
    "address": {"status": "area_match", "pincode": "110001"},
    "clinic_postal": {"status": "area_match", "pincode": "110002"},
    "clinic": {"status": "locations_found"},
    "official_registry": {"status": "manual_review", "search_url": "https://www.nmc.org.in/information-desk/indian-medical-register/"},
    "facility_registry": {"status": "manual_review", "search_url": "https://facility.abdm.gov.in/searchV2"},
    "requires_admin_review": true,
    "auto_approved": false
  }
}
```

This is an example response, not a verified real doctor. Evidence is stored on the
profile and exposed in `doctor.verification_check` in admin listings. Results for
the same input are cached for 10 minutes. Corrected/resubmitted profile details
clear old evidence. A concurrent approval/profile change invalidates an in-flight
check with HTTP 409. A provider outage returns a check marked `unavailable`, not a
doctor rejection. A provider's `verified: true` without comparable identity fields
is insufficient to produce even an identity match.

## What each check establishes

| Check | Service | Interpretation |
| --- | --- | --- |
| Name + registration + council | AskMyDoc `/api/verify` | Supporting third-party registry match; all three fields must compare |
| Personal address PIN/state | India Postal PIN API | Postal area only; full personal address is not sent |
| Clinic address PIN/state | India Postal PIN API | Postal area only |
| Clinic location | Nominatim | Possible map locations; not clinic registration or ownership |
| Official doctor registration | NMC / relevant council portal | Manual admin review link |
| Official facility registration | ABDM HFR portal | Manual admin review link; no public HFR API access assumed |

Reference checks never set `doctor_status` to verified. Only
`POST /api/v1/admin/doctors/{id}/approve` sets verified; rejection sets rejected.
List filters accept `?status=pending`, `?status=verified`, `?status=rejected`.
Legacy uppercase filter values are also supported.

Possible check outcomes include `match`, `mismatch`, `manual_review`,
`unavailable`, `not_found`, `area_match`, `locations_found`, `rate_limited`.
These are evidence outcomes, separate from the three doctor statuses. A missing
map/registry record does not prove an invalid doctor or clinic.

## Provider checks and constraints

AskMyDoc documents free access without an API key. During development its health
endpoint returned 200, but a synthetic registration lookup returned 503 with
`Portal returned HTTP 404`. Reliable live registry matching has therefore not
been established; the UI handles the outage and offers official review links.

Public Nominatim use is limited to admin-clicked clinic searches, with a maximum
one request per 1.1 seconds application-wide, result caching, an identifying
User-Agent and visible OpenStreetMap attribution. Production uses the configured
Redis gate across processes. Without Redis, run only one API process when using
the public endpoint. No autocomplete, background bulk lookup, or personal home
address query is implemented.

Configuration:

```dotenv
CLINIC_GEOCODING_ENABLED=true
CLINIC_GEOCODER_URL=https://nominatim.openstreetmap.org/search
VERIFICATION_USER_AGENT=FamilyCareDoctorReview/1.0 (https://github.com/coreoutsourcingservices/family-care)
```

Disable the integration or switch to an appropriate hosted/self-hosted provider
if usage exceeds the public service limits. Apply migration
`0012_doctor_verification_check` before restarting the API. External requests use
fixed service URLs, a five-second per-request timeout and bounded response sizes.

Sources checked for this implementation:

- [AskMyDoc API documentation](https://api.askmydoc.in/)
- [NMC Indian Medical Register](https://www.nmc.org.in/information-desk/indian-medical-register/)
- [India Postal PIN response](https://api.postalpincode.in/pincode/110001)
- [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/)
- [ABDM Health Facility Registry](https://facility.abdm.gov.in/searchV2)
