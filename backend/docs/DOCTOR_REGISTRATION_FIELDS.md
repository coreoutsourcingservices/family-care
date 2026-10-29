# Doctor registration fields

`POST /api/v1/doctors/register` accepts:

| Field | Required | Notes |
| --- | --- | --- |
| `full_name` | Yes | Doctor's full name |
| `email` | Yes | Signup OTP is delivered by email |
| `mobile_number` | Yes | International format, such as `+919876543210` |
| `password`, `confirm_password` | Yes | Matching passwords |
| `medical_registration_number` | Yes | Professional registration number |
| `registering_council` | Yes | Trimmed and normalized to uppercase |
| `qualification` | No | Degree; omitted, null or blank becomes null. Supplied values are trimmed, uppercase and 2–200 characters |
| `specialization` | No | Up to 200 characters |
| `nmr_id` | No | NMR ID, 1–100 characters when supplied |

The public doctor's Professional Information step includes these professional fields. Registering Council uses a required dropdown based on the [NMC state council directory](https://nmc.org.in/information-desk/state-medical-councils), with Other / Council not listed opening a required custom-name input. The API still receives the full council name as `registering_council`, not an option ID. There is no certificate upload.

Registration still requires email verification and admin approval. Optional degree at signup does not bypass existing eligibility checks for clinical-content review. On rejected-doctor resubmission, omitting degree preserves an existing degree.

For an existing database, apply migration `0010_optional_doctor_degree`:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Restart the running backend after code changes. No existing doctor records are deleted or rewritten by this migration.
