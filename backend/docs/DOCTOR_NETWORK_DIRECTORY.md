# Administrative doctor network

Admin and Super Admin share the doctor detail component. Existing portal navigation stays unchanged. The six sections are Dashboard, Family, Connected Members, Professional Info, Verification and Settings. Family and member pages remain under the selected doctor URL.

## Routes

For each prefix `/api/v1/admin` and `/api/v1/superadmin`:

| GET path | Result |
| --- | --- |
| `/doctors/{doctor}/profiles` | Connected member metadata; supports `search`, `module`, `page`, `per_page` |
| `/doctors/{doctor}/families` | Distinct connected families with connected-member counts; supports `search`, `page`, `per_page` |
| `/doctors/{doctor}/families/{family}` | Only that family's members connected to this doctor; supports pagination |
| `/doctors/{doctor}/families/{family}/profiles/{member}` | One connected member's directory metadata |

Pagination defaults to 25, with a maximum of 100. The frontend uses 12 rows per page. Counts are computed across all matching records, independently of pagination. An unknown, disconnected, deleted, or mismatched member/family returns 404. Each namespace requires its own staff role.

Connection means a nondeleted `CareProfile` whose `referred_doctor_id` matches the selected doctor. This association is not a clinical sharing grant. These directory endpoints return no medical reports, files, diary content or clinical records. Family/member links do not fall through to the general patient directory.

Professional and verification values come from saved doctor data. No mock compliance scores, visits, consultations, appointments or follow-ups are shown. The existing registry check is offered only to Admin for pending applications. Settings displays saved account values and links to existing account management; this change does not create new role permissions or unsupported settings writes.

## Verification

`python -m pytest backend/tests/test_doctor_network.py backend/tests/test_patient_directory.py -q`

`npm run typecheck --workspace admin`

`npm run test:doctor-network --workspace admin`

The browser test renders the actual shared component with synthetic API records for both roles at 360, 390, 768, 1366, 1920 and 2560 pixels. It checks tabs, filters, empty search, scoped navigation, error/retry and page overflow. It performs no live data writes. Mobile member tables become cards with every action visible. Desktop retains the table layout.
