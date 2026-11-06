# Women Health Articles API — Admin, Doctor and patient reader

Verified against registered backend routes and schemas on 6 November 2026.
Base URL: `http://127.0.0.1:5001`. All article examples below are synthetic; the screenshot's DEMO title is an illustration, not a live database record capture.
See [Language API](LOCALIZATION_API.md) for language selection and localized system messages.

## Screenshot flow

The women workspace section headed **Health articles — Guidance from FamilyCare Admin and your connected doctor** calls:

`GET /api/v1/women/profiles/{profile_id}/health-articles?category=fertility&per_page=100`

The request category follows the current women tab. The UI displays each returned `title` in an expandable row, `author.role` as Admin/Doctor, optional month/time labels, and full `content` after expansion. The current reader refreshes every 30 seconds and clears old items when the profile/category changes. It shows loading, retry and empty states.

## Authentication

- Protected routes require the specified approved/active role and an accessible profile where applicable.
- Bearer clients send `Authorization: Bearer <access_token>` and JSON requests use `Content-Type: application/json`.
- Cookie clients use `X-Auth-Transport: cookie`, credentials included, `X-Requested-With: FamilyCare` on mutations and `X-CSRF-Token` on authenticated mutations.
- Public customer/doctor cookie clients send `X-FamilyCare-Portal: patient` or `doctor`. Admin's Next proxy handles its portal cookies; Doctor calls the `/doctor/` article namespace, while doctor authentication endpoints use `/doctors/`.
- `Accept-Language` localizes known system messages; it does not translate stored article content.
- Superadmin does not have article-management access. Do not use a Superadmin session on the Admin article endpoints.

## All endpoints

| Method | Path | Role / purpose |
| --- | --- | --- |
| GET | `/api/v1/admin/health-articles` | ADMIN: list articles |
| POST | `/api/v1/admin/health-articles` | ADMIN: create |
| GET | `/api/v1/admin/health-articles/{article_id}` | ADMIN: full detail |
| PUT | `/api/v1/admin/health-articles/{article_id}` | ADMIN: replace editable fields |
| DELETE | `/api/v1/admin/health-articles/{article_id}` | ADMIN: archive, not hard delete |
| GET | `/api/v1/doctor/women-health-articles` | DOCTOR: own and published Admin articles |
| POST | `/api/v1/doctor/women-health-articles` | DOCTOR: create own women article |
| GET | `/api/v1/doctor/women-health-articles/{article_id}` | DOCTOR: own article detail |
| PUT | `/api/v1/doctor/women-health-articles/{article_id}` | DOCTOR: replace own article fields |
| PUT | `/api/v1/doctor/women-health-articles/{article_id}/visibility` | DOCTOR: own visibility override on a published Admin article |
| GET | `/api/v1/women/profiles/{profile_id}/health-articles` | PATIENT or DOCTOR: permission-checked reader |
| GET | `/api/v1/health-articles` | Public: published Admin articles for an audience |

`article_id` and `profile_id` are UUIDs. No Doctor DELETE endpoint exists; use a full PUT with `status: DRAFT` to deactivate an owned article.

## Categories and publication

| Category | Women section |
| --- | --- |
| `cycle` | Period & cycle |
| `pcos` | PCOS & hormonal |
| `pregnancy` | Pregnancy care |
| `fertility` | Fertility & reproductive |
| `symptoms` | Symptoms & wellness |
| `nutrition` | Nutrition & lifestyle |
| `screening` | Screening & preventive |

`DRAFT` means inactive/private. `PUBLISHED` with no date publishes now; a future timezone-aware publication date is returned as `SCHEDULED` until it arrives. `SCHEDULED` and `ARCHIVED` are response/filter states, not valid POST/PUT `status` values. Draft updates clear publication time. Dates are returned in UTC.

## POST / PUT request schema

Both Admin and Doctor POST/PUT use these fields. PUT requires the full editable request, including required fields; omitted optional fields reset to their defaults. It is not a partial PATCH.

| Field | Required | Validation / default |
| --- | --- | --- |
| `title` | Yes | Trimmed, 3–180 characters, not blank |
| `audience` | Yes | `child` or `women`; Doctor routes require `women` |
| `content` | Yes | Trimmed, 20–30,000 characters, not blank; the UI Description field |
| `category` | No in shared schema | One of seven categories or null; Doctor women routes require a valid category; use the matching category for the women reader |
| `stage_month` | No | Strict integer 1–9 or null; non-null allowed only for women/pregnancy |
| `time_label` | No | At most 100 characters; default empty string |
| `summary` | No | Trimmed, at most 600 characters; default empty string |
| `cover_image_url` | No | Complete http/https URL, at most 1,000 characters, or null |
| `tags` | No | At most 12 entries, each trimmed 1–32 characters; case-insensitive duplicates removed; default [] |
| `status` | No | `DRAFT` (default) or `PUBLISHED` |
| `published_at` | No | ISO 8601 datetime including timezone, or null |

Example request:

```json
{
  "title": "DEMO - Build a reproductive health question list",
  "audience": "women",
  "category": "fertility",
  "stage_month": null,
  "time_label": "Before your appointment",
  "summary": "Prepare questions for your next consultation.",
  "content": "Write down the questions you want to discuss with your clinician at your next consultation.",
  "cover_image_url": null,
  "tags": [
    "consultation"
  ],
  "status": "PUBLISHED",
  "published_at": "2026-11-06T06:30:00Z"
}
```

## Admin APIs

### GET /api/v1/admin/health-articles

Example: `/api/v1/admin/health-articles?audience=women&category=fertility&status=PUBLISHED&page=1&per_page=25`

| Query | Default / meaning |
| --- | --- |
| `page` | 1; positive integer |
| `per_page` | 25; integer 1–100 |
| `audience` | Optional `child` / `women` |
| `category` | Optional category filter |
| `status` | Optional `DRAFT`, `PUBLISHED`, `SCHEDULED`, `ARCHIVED` |
| `q` | Optional title/summary search; backend uses first 120 characters |

Lists articles across authors, newest update first. This endpoint omits `content`; load detail before displaying/editing the full description. HTTP 200:

```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "title": "DEMO - Build a reproductive health question list",
      "audience": "women",
      "summary": "Prepare questions for your next consultation.",
      "category": "fertility",
      "stage_month": null,
      "time_label": "Before your appointment",
      "cover_image_url": null,
      "tags": [
        "consultation"
      ],
      "status": "PUBLISHED",
      "published_at": "2026-11-06T06:30:00Z",
      "created_at": "2026-11-06T06:00:00Z",
      "updated_at": "2026-11-06T06:30:00Z",
      "author": {
        "id": "22222222-2222-4222-8222-222222222222",
        "role": "ADMIN",
        "full_name": "Example Admin"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

### POST /api/v1/admin/health-articles

Send the full request example above. The author is the authenticated Admin; do not send `author` or `id`. HTTP 201:

```json
{
  "article": {
    "id": "11111111-1111-4111-8111-111111111111",
    "title": "DEMO - Build a reproductive health question list",
    "audience": "women",
    "summary": "Prepare questions for your next consultation.",
    "category": "fertility",
    "stage_month": null,
    "time_label": "Before your appointment",
    "content": "Write down the questions you want to discuss with your clinician at your next consultation.",
    "cover_image_url": null,
    "tags": [
      "consultation"
    ],
    "status": "PUBLISHED",
    "published_at": "2026-11-06T06:30:00Z",
    "created_at": "2026-11-06T06:00:00Z",
    "updated_at": "2026-11-06T06:30:00Z",
    "author": {
      "id": "22222222-2222-4222-8222-222222222222",
      "role": "ADMIN",
      "full_name": "Example Admin"
    }
  }
}
```

### GET /api/v1/admin/health-articles/{article_id}

No JSON body. HTTP 200 returns `{ "article": ... }` with the full article object including `content`, as above. An unknown UUID returns 404.

### PUT /api/v1/admin/health-articles/{article_id}

Send the same full request schema. HTTP 200 returns `{ "article": ... }` with saved values. Use `status: DRAFT` to deactivate, or `PUBLISHED` to activate/schedule. Archived articles return 409 and cannot be edited.

### DELETE /api/v1/admin/health-articles/{article_id}

No JSON body. Archives the article and returns HTTP 200 with the full article object, now `status: ARCHIVED`. Stored content is retained. It is excluded from public/profile readers. No unarchive endpoint is implemented.

## Doctor APIs

### GET /api/v1/doctor/women-health-articles

Example: `/api/v1/doctor/women-health-articles?category=fertility&page=1&per_page=25`

Supported queries: optional `category`, `page` (default 1), `per_page` (default 25, maximum 100). Unlike the Admin list, this route does not implement `q`, `audience` or `status` filters.

Includes this Doctor's own women articles (including inactive states) and currently published Admin women articles. List items include full `content` plus `can_edit` and `doctor_active`. HTTP 200 example for an Admin article:

```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "title": "DEMO - Build a reproductive health question list",
      "audience": "women",
      "summary": "Prepare questions for your next consultation.",
      "category": "fertility",
      "stage_month": null,
      "time_label": "Before your appointment",
      "content": "Write down the questions you want to discuss with your clinician at your next consultation.",
      "cover_image_url": null,
      "tags": [
        "consultation"
      ],
      "status": "PUBLISHED",
      "published_at": "2026-11-06T06:30:00Z",
      "created_at": "2026-11-06T06:00:00Z",
      "updated_at": "2026-11-06T06:30:00Z",
      "author": {
        "id": "22222222-2222-4222-8222-222222222222",
        "role": "ADMIN",
        "full_name": "Example Admin"
      },
      "can_edit": false,
      "doctor_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

`can_edit: true` means the article belongs to this Doctor. Read published Admin content from this list; Doctor detail GET is restricted to owned articles. `doctor_active` reports the explicit visibility override when present, otherwise true; it is not a substitute for checking the article's `status`.

### POST /api/v1/doctor/women-health-articles

Send the shared request with `audience: women` and a valid category. HTTP 201 returns `{ "article": ... }`. The author is the authenticated Doctor (`author.role: DOCTOR`), not a client-supplied Admin. Content is available only to that Doctor's currently connected women profiles when published and otherwise eligible.

### GET /api/v1/doctor/women-health-articles/{article_id}

No JSON body. HTTP 200 returns `{ "article": ... }` including full content, restricted to this Doctor's own women article. Another author's article returns 404 even when that Admin article appears in the Doctor list.

### PUT /api/v1/doctor/women-health-articles/{article_id}

Send the full schema; ownership and women category rules apply. HTTP 200 returns `{ "article": ... }`. Set `status: DRAFT` to deactivate, `PUBLISHED` to activate/schedule. Cannot edit Admin/another Doctor's content. Archived articles return 409.

### PUT /api/v1/doctor/women-health-articles/{article_id}/visibility

Only for an active/published Admin women article. Request:

```json
{
  "active": false
}
```

HTTP 200:

```json
{
  "active": false
}
```

Send `active: true` to restore it. The value must be a JSON boolean, not a string. This changes availability for this Doctor's currently connected women profiles only; it does not change Admin publication status or other Doctors' patients. Unknown/ineligible articles return 404. For an owned Doctor article, change publication state through full PUT instead.

## Women profile reader — screenshot API

### GET /api/v1/women/profiles/{profile_id}/health-articles

`category` is required and must be one of the seven women categories. `page` defaults to 1; `per_page` defaults to 25, maximum 100. No JSON body. The current UI requests `per_page=100` and has no pagination controls; API clients that need more than 100 results must fetch subsequent pages.

HTTP 200 (general fertility category):

```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "title": "DEMO - Build a reproductive health question list",
      "audience": "women",
      "summary": "Prepare questions for your next consultation.",
      "category": "fertility",
      "stage_month": null,
      "time_label": "Before your appointment",
      "content": "Write down the questions you want to discuss with your clinician at your next consultation.",
      "cover_image_url": null,
      "tags": [
        "consultation"
      ],
      "status": "PUBLISHED",
      "published_at": "2026-11-06T06:30:00Z",
      "created_at": "2026-11-06T06:00:00Z",
      "updated_at": "2026-11-06T06:30:00Z",
      "author": {
        "id": "22222222-2222-4222-8222-222222222222",
        "role": "ADMIN",
        "full_name": "Example Admin"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 100,
  "stage_month": null
}
```

An empty valid result has `items: []` and `total: 0`; it is not an authentication error.

Reader access and visibility:

1. Caller must be a Patient or Doctor. The women profile must exist and not be deleted.
2. The owner has tab access. Shared family members/Doctors need an effective, unexpired, unrevoked grant for the requested category and must still be connected. A connected Doctor relationship alone does not replace the category permission check.
3. Reader includes currently published articles from active Admin accounts and from this profile's currently connected, active, approved Doctor. No connected Doctor is required to read eligible Admin articles.
4. Draft, archived and future publication dates are excluded.
5. This connected Doctor's disabled Admin article overrides are excluded. Disconnecting or changing Doctor stops the old Doctor's articles/overrides from applying.
6. General articles (`stage_month: null`) remain eligible. Month-specific articles require the matching saved, active, ongoing pregnancy stage. An absent, ended, inactive or out-of-range stage returns no month-specific guidance. `stage_month` at the response root is the calculated current month (or null), not a value supplied by the client.

## Public read

### GET /api/v1/health-articles?audience=women

No authentication. `audience` is required (`child` or `women`). Optional `page`, `per_page`, `q` (first 120 characters; title/summary/content search). This endpoint does not implement category or pregnancy-month filtering.

HTTP 200 shape:

```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "title": "DEMO - Build a reproductive health question list",
      "audience": "women",
      "summary": "Prepare questions for your next consultation.",
      "category": "fertility",
      "stage_month": null,
      "time_label": "Before your appointment",
      "content": "Write down the questions you want to discuss with your clinician at your next consultation.",
      "cover_image_url": null,
      "tags": [
        "consultation"
      ],
      "status": "PUBLISHED",
      "published_at": "2026-11-06T06:30:00Z",
      "created_at": "2026-11-06T06:00:00Z",
      "updated_at": "2026-11-06T06:30:00Z",
      "author": {
        "id": "22222222-2222-4222-8222-222222222222",
        "role": "ADMIN",
        "full_name": "Example Admin"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25,
  "audience": "women"
}
```

Only published Admin-authored content whose publication time has arrived is returned. Doctor content is excluded. This public API does not perform the profile/category/month/Doctor-override filtering used by the screenshot; use the women-profile reader for that interface.

## Errors

| HTTP | Code / condition |
| --- | --- |
| 400 / 403 | Invalid request origin/CSRF or transport, when applicable |
| 401 | Missing, expired or invalid session/token |
| 403 | Wrong role, missing/expired sharing, or denied women-category permission |
| 404 | `health_article_not_found`, `profile_not_found`, unknown/ineligible or non-owned article |
| 409 | `health_article_archived` |
| 422 | `validation_error`, `invalid_category`, `invalid_article_stage`, `invalid_pagination`, `invalid_audience`, `invalid_status` |
| 503 | Database/schema unavailable |

Representative JSON error (message can be localized):

```json
{
  "error": {
    "code": "health_article_not_found",
    "message": "Health article not found"
  }
}
```

## Setup and source of truth

Apply the current Alembic migrations before using article endpoints, including `0031_health_articles` and `0032_women_articles`. The latter adds category/month fields and per-Doctor visibility overrides.

Source: `backend/admin/routes.py`, `backend/services/health_articles.py`, `backend/core/article_schemas.py`, `backend/services/women_workspace.py` and `customer/src/modules/women/WomenHealthArticles.tsx`.

The DEMO title in the screenshot follows the same reader contract. Documentation examples do not create, activate, seed, edit or delete any real article.
