# Health Articles API

Base URL: `http://127.0.0.1:5001`. Admin UI: `/women-health-articles`. Doctor UI: `/doctor/women-health-articles`. Both sidebars include Women Health Articles.

## Women categories and timing

Admin's published articles are visible by default to every women profile (including profiles with no connected doctor), within the matching category and pregnancy month rules. Doctors also see published Admin articles by default. Only an explicit doctor visibility override hides an Admin article for that doctor's currently connected women patients.

To add the ten labelled active demo articles, run `python scripts/seed_women_articles.py` from `backend` with `PYTHONPATH=.`. It uses an existing active approved Admin account (or `--admin-id`), creates no account, and preserves existing articles. Repeated runs skip the same deterministic sample IDs. Nine samples are general; the pregnancy month-3 sample requires a matching saved stage.

Women articles accept `category`: `cycle`, `pcos`, `pregnancy`, `fertility`, `symptoms`, `nutrition`, or `screening`; `time_label` (up to 100 characters); and optional `stage_month` (integer 1–9, only for women/pregnancy). `content` is the Description input. The existing title, content, publication date, tags and audience contracts remain supported. Inactive maps to `DRAFT`; Active maps to `PUBLISHED`. Future publication remains scheduled. Deactivation is reversible; archival retains its existing behavior.

`GET /api/v1/admin/health-articles` also accepts `category`.

Example women article:

```json
{"title":"Third month care","audience":"women","category":"pregnancy","stage_month":3,"time_label":"Daily care","content":"Enter the complete clinician-reviewed article description here.","status":"PUBLISHED"}
```

## Connected doctor management

All following endpoints require an approved Doctor session and standard CSRF protection for cookie mutations:

- `GET /api/v1/doctor/women-health-articles?category=pregnancy`: paginated list of the doctor's own women articles plus currently published Admin women articles. Items contain `can_edit` and `doctor_active`.
- `POST /api/v1/doctor/women-health-articles`: create an article using the article schema, requiring women audience and one of the seven categories.
- `GET /api/v1/doctor/women-health-articles/{article_id}` and `PUT` on the same URL: read/edit only this doctor's own articles. Another author's article returns 404.
- `PUT /api/v1/doctor/women-health-articles/{article_id}/visibility` with `{"active":false}` or `{"active":true}`: hide/restore an active Admin article for this doctor's connected women profiles. This leaves Admin publication status and other doctors' patients unchanged.

Doctor articles are visible only to profiles currently connected to their author; disconnecting or switching doctors immediately removes the previous doctor's articles and visibility overrides. Doctor articles are excluded from unauthenticated public reads.

## Women profile article reader

`GET /api/v1/women/profiles/{profile_id}/health-articles?category=pregnancy`

Requires Patient or Doctor authentication and the profile's existing permission for that category. Returns paginated `items` including full article content, plus `stage_month`. Includes only currently published Admin articles and the currently connected approved doctor's articles, minus that doctor's disabled Admin articles. Draft, archived and future articles are excluded.

Pregnancy month is calculated from the existing active ongoing Pregnancy Care stage, using the same month/week ranges. General articles (`stage_month:null`) always qualify. Month-specific articles appear only when the saved stage matches; an absent/inactive/ended/stale stage does not reveal month-specific guidance. The UI shows articles within each of the seven existing women pages, with expandable descriptions and author attribution. It refreshes every 30 seconds.

Apply migration `0032_women_articles` after `0031_health_articles`; it adds category/timing columns and per-doctor visibility overrides. Restart the API after migrating.

Articles have one required audience tag: `child` or `women`. Additional tags are optional. Admins can save drafts, publish immediately, schedule a publication time, edit articles, and archive them. Superadmins do not have access to the article-management routes.

All stored publication timestamps are UTC. The Admin form accepts the browser's local date and time and sends an ISO 8601 timestamp with timezone. Public reads include only published articles whose publication time has arrived.

## Admin endpoints

Admin endpoints require an approved Admin session or an Admin bearer token. Cookie mutations also require the standard FamilyCare CSRF headers.

### `GET /api/v1/admin/health-articles`

List articles, newest updates first.

| Query | Required | Values |
| --- | --- | --- |
| `page` | No | Positive integer; default `1` |
| `per_page` | No | `1` to `100`; default `25` |
| `audience` | No | `child` or `women` |
| `status` | No | `DRAFT`, `PUBLISHED`, `SCHEDULED`, `ARCHIVED` |
| `q` | No | Search title or summary |

Response: `{ "items": [], "total": 0, "page": 1, "per_page": 25 }`. The list includes title, summary, tags, audience, publication time, status, author, and update timestamps. Article body is returned by the detail endpoint.

### `POST /api/v1/admin/health-articles`

Create an article. Use `status: "DRAFT"` to save it privately. Use `status: "PUBLISHED"` and omit `published_at` to publish now, or pass a future timestamp to schedule publication.

```json
{
  "title": "Healthy sleep habits for children",
  "audience": "child",
  "summary": "Age-appropriate routines that support healthy sleep.",
  "content": "Write the complete article content here. Use plain text paragraphs.",
  "cover_image_url": "https://example.org/child-sleep.jpg",
  "tags": ["sleep", "wellness"],
  "status": "DRAFT",
  "published_at": null
}
```

`audience` is `child` or `women`. `title` is required (3-180 characters), `content` is required (20-30,000 characters), `summary` may be empty (up to 600 characters), `cover_image_url` is optional (http/https), and up to 12 additional tags are accepted (32 characters each). A successful create returns `201` with `{ "article": { ... } }`.

### `GET /api/v1/admin/health-articles/{article_id}`

Get a single article including full content.

### `PUT /api/v1/admin/health-articles/{article_id}`

Replace the editable article fields using the same JSON schema as `POST`. Archived articles cannot be edited (`409`). A scheduled article becomes public automatically when its publication timestamp is reached.

### `DELETE /api/v1/admin/health-articles/{article_id}`

Archive an article. Archived articles no longer appear in public reads; their content remains in the Admin archive filter.

## Public article read

### `GET /api/v1/health-articles?audience=child`

Return published articles for one audience. The required `audience` query value is `child` or `women`. Optional query parameters are `page`, `per_page` (up to 100), and `q` (search title, summary, or content). No authentication is required. Drafts, archived articles, and scheduled articles whose publication time has not arrived are excluded.

Example response:

```json
{
  "items": [
    {
      "id": "<article UUID>",
      "title": "Healthy sleep habits for children",
      "audience": "child",
      "summary": "Age-appropriate routines that support healthy sleep.",
      "content": "Full article text...",
      "cover_image_url": null,
      "tags": ["sleep", "wellness"],
      "status": "PUBLISHED",
      "published_at": "2026-10-30T10:00:00Z",
      "created_at": "2026-10-29T10:00:00Z",
      "updated_at": "2026-10-30T10:00:00Z",
      "author": { "id": "<admin UUID>", "full_name": "Example Admin" }
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25,
  "audience": "child"
}
```

`422 invalid_audience` is returned for a missing or unsupported audience. Standard authorization, validation, and database errors use the API error format documented in `ALL_APIS.md`.

## Database setup

Apply migration `0031_health_articles` using the project's Alembic migration command before using these endpoints. The migration creates the `familycare.health_articles` table and its audience, status, author, and publication-time fields.
