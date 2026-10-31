# Growth & Nutrition API: age-based child guidance

Base URL: `http://127.0.0.1:5001`. JSON examples use synthetic identities.

## Implemented behavior

- Your supplied Growth & Nutrition text is preserved in `backend/content/child_growth_nutrition_source.md` and converted into structured, versioned educational content in `backend/content/child_growth_nutrition.json`.
- Every existing/new child gets the guide **active by default**. No batch assignment, doctor connection, or manual activation is required for initial visibility.
- Age is calculated from the child's saved DOB using the India product calendar on every read. Clients do not submit or override age.
- There are 24 continuous, nonoverlapping age bands: 12 monthly bands in the first year, then one yearly band for each completed age 1 through 12. Exactly age 13 returns `OUT_OF_SCOPE` and no guide. The supplied 11–12-year content also covers completed age 12 until the 13th birthday.
- Only the currently connected doctor can activate/deactivate **this child's educational guide**. A change does not change another child's guide or the global source content.
- Deactivation returns `guide: null`; it does not delete or disable saved growth measurements, meal notes, existing diary APIs or doctor notes.
- Parent/other doctors/admins cannot use the doctor visibility endpoint. A doctor who is disconnected immediately loses this permission.
- Parents see the guidance on Child Care → Growth & nutrition. Doctors see it with Activate/Deactivate controls under Child Care → Growth or Nutrition.

## Authentication

Bearer/mobile:

```http
X-Auth-Transport: bearer
Authorization: Bearer <patient_or_doctor_access_token>
Content-Type: application/json
```

Browser: HttpOnly cookies, `credentials: include`, `X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare`, and `X-FamilyCare-Portal: patient` or `doctor`. Doctor PATCH additionally requires that doctor's `X-CSRF-Token` from login/refresh.

`profile_id` is the child's CareProfile UUID. Parent access requires ownership; doctor access requires the current referral connection. Public/unauthenticated access is not provided.

## 1. Parent reads the child's current guide

`GET /api/v1/children/{profile_id}/growth-nutrition-guide`

Request body: none. No age, module or active parameter is accepted from the client.

HTTP 200 (abbreviated representative body):

```json
{
  "child": {
    "id": "<child UUID>",
    "full_name": "Example Child",
    "date_of_birth": "2026-02-28",
    "age": {
      "completed_years": 0,
      "remaining_months": 8,
      "remaining_days": 3,
      "total_completed_months": 8,
      "total_days": 245,
      "display": "0 years 8 months 3 days",
      "primary_category": "INFANT",
      "secondary_categories": [],
      "in_child_module_scope": true
    }
  },
  "active": true,
  "default_active": true,
  "status": "AVAILABLE",
  "updated_at": null,
  "updated_by": null,
  "version": "2026-10-31.v1",
  "age_band": {
    "id": "month-8",
    "label": "8–9 Months",
    "min_months": 8,
    "max_months_exclusive": 9
  },
  "guide": {
    "title": "Growth & Nutrition Guide for Children (0–12 Years)",
    "nutrition": {
      "id": "month-8",
      "min_months": 8,
      "max_months_exclusive": 9,
      "label": "8–9 Months",
      "foods": "Soft rice, lentils, fully cooked eggs, and fruits",
      "meal_frequency": "2–3 meals daily",
      "blocks": [{"type":"paragraph","text":"Example educational paragraph from the supplied guide."}]
    },
    "growth_monitoring": [],
    "food_safety": [],
    "sources": [
      {"title":"WHO infant and young child feeding","url":"https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding"}
    ],
    "provenance": "User-supplied educational guide; not an individual diagnosis or prescribed meal plan.",
    "notice": "General educational guidance. Your clinician adapts it for allergies, feeding difficulties, prematurity or other needs. Growth needs age- and sex-appropriate charts, not adult BMI cutoffs. No supplement dose or individual calorie target is generated."
  }
}
```

The actual response includes the complete matching age content, growth-monitoring guidance, food-safety sections and references. Empty arrays and the example paragraph above abbreviate those parts; see the full generated response in `ALL_APIS.md`, `all-api.md` or OpenAPI JSON. `default_active` describes initial policy; `active` is the child's saved effective setting.

### Block format for rendering

No raw HTML is required. Render these structured block types:

```json
[
  {"type":"heading","text":"Recommended foods"},
  {"type":"paragraph","text":"Educational text"},
  {"type":"list","items":["First item","Second item"]},
  {"type":"table","headers":["Food","Preparation"],"rows":[["Lentils","Cook thoroughly"]]}
]
```

Content contains the supplied text; inline `**bold**` markers may occur. The UI safely renders text, lists and tables; it does not inject HTML.

## 2. Connected doctor reads the same child guide

`GET /api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide`

Request body: none. Doctor access token/cookie required.
HTTP 200: identical response shape and age selection as the parent endpoint. A doctor cannot read an unconnected child's guide.

## 3. Doctor deactivates or activates for the selected child

`PATCH /api/v1/doctors/care-profiles/{profile_id}/growth-nutrition-guide/visibility`

Deactivate request:

```json
{"active":false}
```

Activate request:

```json
{"active":true}
```

Use a JSON boolean; strings such as `"false"` or numeric values are rejected.
No POST endpoint is needed: use PATCH to change the setting and GET to read guidance.

HTTP 200 after deactivation (child object abbreviated):

```json
{
  "child": {"id":"<child UUID>","full_name":"Example Child","date_of_birth":"2026-02-28","age":{"total_completed_months":8}},
  "active": false,
  "default_active": true,
  "status": "INACTIVE",
  "updated_at": "<UTC timestamp>",
  "updated_by": "<connected doctor UUID>",
  "version": "2026-10-31.v1"
}
```

The PATCH response includes the complete child/age object but no content payload. Fetch either GET endpoint again to see effective guidance:

```json
{
  "child": {"id":"<child UUID>"},
  "active": false,
  "default_active": true,
  "status": "INACTIVE",
  "updated_at": "<UTC timestamp>",
  "updated_by": "<connected doctor UUID>",
  "version": "2026-10-31.v1",
  "age_band": null,
  "guide": null
}
```

Reactivation exposes the content for the child's **current** age, not a cached age at the time of deactivation. Setting persists across restarts. The family receives a persistent in-app `growth_nutrition_updated` notice with `profile_id` and `area: growth`; live delivery uses the existing notification gateway. An audit action records the doctor change.

## Statuses and errors

| Status / HTTP | Meaning |
| --- | --- |
| `AVAILABLE` / 200 | Active and age is under 13; guide included |
| `INACTIVE` / 200 | Doctor deactivated this child's guide; no educational content returned |
| `OUT_OF_SCOPE` / 200 | Active child profile has reached age 13; no guide returned |
| 401 | Invalid/missing session or token |
| 403 | Wrong role or cookie CSRF failure |
| 404 | Child missing/deleted, owned by another family, not a child profile, or not connected to this doctor |
| 422 | Missing/invalid active boolean, extra fields or invalid JSON |
| 503 | Database unavailable or migration not installed |

```json
{"error":{"code":"child_not_found","message":"Child profile not found"}}
```

An inaccessible profile can instead return `profile_not_found` to avoid exposing its existence. There is no global activate/deactivate API in this feature.

## Supplied text and scope

The source guide's age-wise foods, meal ideas, nutrients, food preparation, safety and growth-monitoring information are available as educational content. For the eight-month infant row, the supplied quantity note is supplemented with the WHO 6–8-month meal-frequency guidance. Source references are included in the response. Breastfeeding/food-safety and growth-reference sources were checked; the guide is not marked as an individual doctor's prescription.

App feature suggestions in section 15 of the pasted text are preserved in the source file. They are not automatically represented as already implemented nutrient calculations, WHO percentiles, sex-specific growth curves, dietary prescriptions, allergy tracking or new head-circumference APIs. Existing diary/measurement routes remain documented separately. There is no automatic malnutrition diagnosis, supplement dose or calorie prescription.

References:

- [WHO infant and young child feeding](https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding)
- [ICMR–NIN Dietary Guidelines for Indians 2024](https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf)
- [WHO Child Growth Standards](https://www.who.int/tools/child-growth-standards)
- [WHO growth reference 5–19 years](https://www.who.int/tools/growth-reference-data-for-5to19-years)

## Setup and regeneration

From `backend`:

1. `venv/Scripts/python.exe -m alembic upgrade head` applies `0019_child_growth_nutrition`.
2. Restart the API.
3. Rebuild content after an intentional source edit: `venv/Scripts/python.exe scripts/build_growth_nutrition_content.py`.
4. Regenerate API docs: `venv/Scripts/python.exe scripts/export_full_api.py`.

Tests: `venv/Scripts/python.exe -m pytest tests/test_growth_nutrition_guide.py -q` from `backend`. Tests cover all 24 age bands, default-active behavior, age 13 boundary, doctor scope, strict booleans, toggles, cross-family denial and continued measurement access while disabled.
