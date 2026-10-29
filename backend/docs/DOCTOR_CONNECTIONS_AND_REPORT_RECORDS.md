# Doctor onboarding, connections and reviewed report records

Doctor signup, email verification, approval and generated referral IDs are unchanged.
`GET /api/v1/doctors/practice-profile` returns `{profile, complete, professional}`.
`PUT` saves clinic name, city, address, experience years (0–80), languages, consultation
hours and optional bio. Only the logged-in DOCTOR can save this row. Verified
qualifications, registration number, approval and referral ID cannot be changed here.
Run `python -m alembic upgrade head` for `0009_doctor_practice`.

Patient controls:

- `DELETE /api/v1/patients/profiles/{profile_id}/doctor`: disconnect just this owned
  profile. Doctor read/download/clinical-record endpoints recheck this connection.
- `DELETE /api/v1/patients/doctor`: remove the account referral and this owner's
  profile connections to that same doctor. Connections to other doctors stay intact.
- Existing referral POST routes reconnect an approved active doctor. They do not
  grant access to every family member automatically.

`GET /api/v1/doctors/care-profiles/{profile_id}/records` returns paginated shared
medical history, measurements, vaccination, nutrition and consultation notes.
Private care notes and other profiles are excluded. Patient-only OCR endpoints
remain patient-only; doctors do not queue OCR using patient credentials.
Already-issued signed report links retain their existing short expiry.

After OCR completes, the owner can review and edit suggestions from explicit
weight/height labels and units. Date and confirmation must be supplied by the
owner. Vaccine mentions do not prove administration; the administration checkbox
is never preselected. No diagnosis or clinical certification is generated.

`POST /api/v1/patients/profiles/{profile_id}/reports/{report_id}/import`:

```json
{
  "kind": "growth",
  "reviewed": true,
  "record": {"title":"Reviewed report measurement","date":"2026-10-28","weight":"20"}
}
```

Kinds: `growth`, `history`, `vaccination`, `nutrition`. Readable saved COMPLETED or
PARTIAL OCR is required. The report must belong to this profile and patient.
One report/kind import is idempotent. Saves remain PARENT_REPORTED with
`source_report_id`; vaccine imports also attach `certificate_id`. Partial growth
measurements preserve unknown values rather than inventing height/weight or BMI.
Existing child record APIs and charts read these saved records.

`GET /api/v1/patients/profiles/{profile_id}/imported-records` lists owner-reviewed
report records (paginated) for all three modules. Women/adult report/profile flows
show these separately from their local diaries.

Extraction needs the local OCR interpreter and running report worker documented
in REPORT_OCR_API.md. English translation still requires explicit consent before
sending medical text to MyMemory. A file upload alone does not create health facts.
