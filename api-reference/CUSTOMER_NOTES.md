# Main-customer private notes

Notes belong to the authenticated main PATIENT account, not a child or family-member profile. Invited-member sessions receive 403 for every notes operation. Other customers cannot view, update or delete the owner's notes. Doctor/admin roles are not authorized by these endpoints.

Cookie clients send `X-Auth-Transport: cookie`, `X-FamilyCare-Portal: patient`, credentials, and the existing requested-with/CSRF headers for mutations. Bearer clients use their own access token.

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| GET | `/api/v1/patients/notes?page=1&per_page=25` | None | `{items: [], total: 0, page: 1, per_page: 25}` |
| POST | `/api/v1/patients/notes` | `{"title":"Question for next visit","body":"Synthetic personal reminder"}` | 201 `{note: {...}}` |
| PUT | `/api/v1/patients/notes/{note_id}` | Complete title/body | 200 `{note: {...}}` |
| DELETE | `/api/v1/patients/notes/{note_id}` | None | 200 `{"message":"Note deleted"}` |

Title is nonblank and at most 160 characters. Body is nonblank and at most 5,000 characters. Unknown fields are rejected. List pagination permits 1–100 items per page. Notes return id, title, body, created_at and updated_at; times are UTC. Inaccessible note IDs return 404. Validation errors return 422.

Apply migration `0021_customer_notes` from backend with `.venv/Scripts/python.exe -m alembic upgrade head`. This also adds the optional profile `gender` field (`Male`, `Female`, `Other`, or empty for existing records). Setup does not infer gender from a name or email. Existing records remain intact.

The main dashboard sidebar separates Dashboard / Self / Add member from health navigation. Add notes opens `/customer/dashboard?view=notes`. Self setup offers Women/Adult; Add member offers Child/Women/Adult. Child creation and self creation use the existing profile API; adult/women invitations retain the email and family-approval OTP flow.
