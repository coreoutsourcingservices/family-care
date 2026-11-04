# Health Articles API

Base URL: `http://127.0.0.1:5001`. These endpoints are API-only; no portal navigation or UI is exposed for article management.

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
