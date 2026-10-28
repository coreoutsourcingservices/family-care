# Patient accounts and their family profiles

Admin `/patients` and superadmin `/superadmin/patients` now show each patient's
family member count and total profile count. Click the patient name or member
count to open the account, then click a member to inspect their profile details.

`members` counts profiles whose `profile_type` is `member`; `self` counts the
account owner's own profile. `total` includes both. Module counts include self
profiles. Zero means no profiles were added, not that the API failed to load.

Read-only APIs (use the matching ADMIN or SUPERADMIN session):

- `GET /api/v1/{admin|superadmin}/patients`: existing list plus `profile_counts`.
- `GET /api/v1/{admin|superadmin}/patients/{user_id}`: account and profile counts.
- `GET /api/v1/{admin|superadmin}/patients/{user_id}/profiles`: paginated profiles;
  optional `module=child|adult|women`, `page`, `per_page` (maximum 100).
- `GET /api/v1/{admin|superadmin}/patients/{user_id}/profiles/{profile_id}`:
  member details, owner, guardian/emergency contacts, linked doctor and report count.

Patient account UUIDs and public IDs are accepted. Profile identifiers are UUIDs.
The selected profile must belong to the selected account, otherwise 404 is returned.
Patient/doctor roles cannot access these administrative endpoints. Password hashes,
uploaded report content and private care diary entries are not returned here.

These changes require no database migration. Counts use grouped database queries
for the current page of patient accounts.

Validation: `venv/Scripts/python.exe -m pytest tests/test_patient_directory.py -q`.
For isolated browser validation run `tests/admin_members_fixture.py`, start the
built admin app on 3006 with `BACKEND_URL=http://127.0.0.1:5501`, then run
`node tests/patient-members.mjs` from `admin`. Tests use synthetic SQLite data only.
