# Care-profile public IDs

Each care profile has its existing UUID `id` and a stable, automatically allocated `public_id`.

| Module | First public ID | Next public ID |
| --- | --- | --- |
| child | `CH000001` | `CH000002` |
| adult | `AD000001` | `AD000002` |
| women | `WO000001` | `WO000002` |

Numbers have a minimum of six digits and grow rather than truncate. Numbering is independent per module and shared across accounts. Clients cannot assign IDs. IDs are identifiers, not access credentials; authentication and ownership/explicit doctor connections are still required.

## Existing endpoints, same URLs

Create a child using the existing endpoint:

```http
POST http://127.0.0.1:5001/api/v1/patients/profiles
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

```json
{
  "profile_type": "member",
  "module": "child",
  "full_name": "Aarav Kumar",
  "date_of_birth": "2022-03-01",
  "guardian_contact": "+919876543210",
  "emergency_contacts": []
}
```

The response's `profile` object includes both `id` and `public_id`. Changing `module` to `adult` or `women` selects the corresponding prefix. Do not send `public_id` in the request body. First IDs above are examples; use the value actually returned by the API.

```http
GET http://127.0.0.1:5001/api/v1/patients/profiles?module=child
GET http://127.0.0.1:5001/api/v1/patients/profiles/CH000001
GET http://127.0.0.1:5001/api/v1/patients/profiles/CH000001/reports
POST http://127.0.0.1:5001/api/v1/patients/profiles/CH000001/reports
POST http://127.0.0.1:5001/api/v1/patients/profiles/CH000001/connect-doctor
```

Public IDs also work for protected report download paths and `/api/v1/doctors/care-profiles/{profile_id}` routes. UUID URLs continue working. Report database links and Cloudinary folders retain the original UUID; they are not renamed or moved.

The patient's account public ID (`C…`), doctor's account ID (`D…`) and Cloudinary report asset `public_id` are separate identifiers. `parent_profile_id` in create JSON still expects the parent's care-profile UUID.

## Migration and allocation

Run `venv\Scripts\python.exe -m alembic upgrade head` from `backend/`. Migration `0005_profile_public_ids` backfills existing profiles in creation/UUID order within each module, initializes transactional counters, adds unique/format constraints and prevents changing an assigned ID/module. It leaves UUIDs, parent links, reports and ownership unchanged. A PostgreSQL insert trigger supports older workers while restarting the backend.

The backend allocates numbers with an atomic database upsert, not `MAX(id) + 1`. Counters participate in the profile transaction; failures roll back allocation, and committed profile deletions do not decrement counters. Restart backend workers after applying the migration. Tests cover UUID/public lookup compatibility, independent numbering, upload/list/download using public IDs, client-assigned-ID rejection and cross-account/doctor access denial.
