# Medical report OCR and English translation

Base URL: `http://127.0.0.1:5001/api/v1`. Requires the owning PATIENT account.
Works with the existing report-upload screens for child, adult and women profiles.
Original files remain private. Admin catalog privileges do not grant report access.

## API list

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/patients/profiles/{profile_id}/reports` | Upload one image/PDF in multipart `file`; returns `report.id` |
| GET | `/patients/report-text/options` | Supported OCR languages and runtime configuration |
| POST | `/patients/profiles/{profile_id}/reports/{report_id}/text` | Queue OCR and optional English translation |
| GET | `/patients/profiles/{profile_id}/reports/{report_id}/text` | Poll status and read saved results |
| GET | `/patients/profiles/{profile_id}/reports/{report_id}/download` | Read original report |

`profile_id` is the selected care-profile UUID, not the parent account ID.
`report_id` must belong to that profile and authenticated patient.

## Queue extraction

```http
POST /api/v1/patients/profiles/PROFILE_UUID/reports/REPORT_UUID/text
Content-Type: application/json
Authorization: Bearer PATIENT_ACCESS_TOKEN
```

```json
{
  "source_language": "hi",
  "translate_to_english": true,
  "external_translation_consent": true
}
```

Choose the main printed language. Initial supported codes: `hi`, `en`, `mr`, `ne`,
`sa`, `ta`, `te`, `ur`, `ar`, `fr`, `de`, `es`, `pt`, `ru`. Query options for the
authoritative list. OCR does not automatically detect the document's language.

For local OCR only, send `translate_to_english: false` and
`external_translation_consent: false`. Non-English translation requires explicit
consent because extracted medical text is sent to MyMemory through
deep-translator. Consent must not be preselected in the UI. Selecting English
copies the extracted English text without an external translation request.

New/in-progress jobs return HTTP **202**:

```json
{
  "analysis": {
    "report_id": "REPORT_UUID",
    "status": "QUEUED",
    "options": {
      "source_language": "hi",
      "translate_to_english": true,
      "external_translation_consent": true
    },
    "result": null,
    "error": null,
    "updated_at": "2026-10-28T10:00:00Z"
  }
}
```

Repeated requests while queued/processing reuse the current job. A completed
result with identical options returns HTTP 200 from the saved result. Failed or
partial jobs can be retried through POST. Changing options replaces that report's
previous extracted-result cache; the original uploaded file is preserved.

## Read results

Poll GET every 3 seconds while status is `QUEUED` or `PROCESSING`. Stop polling
when the panel closes or status finishes. Results can be reopened after reload.

```json
{
  "analysis": {
    "report_id": "REPORT_UUID",
    "status": "COMPLETED",
    "result": {
      "engine": "PaddleOCR",
      "source_language": "hi",
      "page_count": 1,
      "original_text": "परीक्षण रिपोर्ट",
      "english_text": "Test report",
      "translation_status": "COMPLETED",
      "pages": [{
        "page": 1,
        "text": "परीक्षण रिपोर्ट",
        "lines": [{"text": "परीक्षण रिपोर्ट", "confidence": 0.95}]
      }],
      "warnings": ["Machine extraction and translation require verification against the original."]
    },
    "error": null
  }
}
```

Example is synthetic. `english_text` is null when translation was not requested or
failed. Translation statuses: `NOT_REQUESTED`, `NO_TEXT`, `COMPLETED`, `FAILED`.
OCR status `PARTIAL` preserves original text when only translation fails.
`NOT_REQUESTED` means no extraction exists. `FAILED` includes a safe error code
and message. No readable text is a completed extraction with a warning, not
invented content.

## Frontend integration

The existing `ReportTextPanel` component is mounted next to saved reports in
`MemberProfiles` and the child Health reports screen. It uses the shared
`careApi` helper for cookie auth, refresh and CSRF handling.

```ts
const path = `/patients/profiles/${profileId}/reports/${reportId}/text`;
await careApi(path, {
  source_language: 'hi',
  translate_to_english: wantsTranslation,
  external_translation_consent: explicitConsent
});
const {analysis} = await careApi(path);
```

For a Next.js client using the same authenticated backend, call the full base URL
with `credentials: 'include'`, `X-Auth-Transport: cookie`,
`X-Requested-With: FamilyCare` and the login-issued `X-CSRF-Token` for POST. Its
origin must be in Flask's CORS configuration. Never embed JWTs or service secrets
in frontend source. Render OCR output as plain text, not HTML.

## Runtime setup

The existing Flask venv can remain on Python 3.14. PaddleOCR runs in a separate
Python 3.12 environment, avoiding incompatible Paddle wheels in the API runtime.

```powershell
# From backend; use a Python 3.12 installation to create .ocr-venv.
python3.12 -m venv .ocr-venv
.ocr-venv/Scripts/python.exe -m pip install -r requirements-ocr.txt
venv/Scripts/python.exe -m alembic upgrade head
venv/Scripts/python.exe -m scripts.report_worker
```

Default processor interpreter: `backend/.ocr-venv/Scripts/python.exe` on Windows
or `.ocr-venv/bin/python` on Linux. Override with `OCR_PYTHON`. Worker runs with
Flask's existing venv and database configuration. Keep it running alongside the
API. First use of each script downloads its model; `.ocr-models` caches models
inside the workspace and is excluded from Git. Warm models before production
traffic; the processor timeout is 360 seconds. Serve with a single OCR worker on
small CPU machines. Expired processing leases become retryable after 10 minutes.

Migration `0008_report_text` adds a private RLS-protected result table. Temporary
document and result files are cleaned after processing. Do not place patient
document contents or translations in application logs. Signed Cloudinary downloads
are restricted to the configured cloud and trusted HTTPS hosts, including redirects.

## Limits and error handling

- PDF/JPEG/PNG/WebP, 10 MB maximum; PDF must be unencrypted and at most 5 pages.
- Scanned PDF pages are rendered to bounded images; image pixel and extracted
  text limits prevent excessive memory use. Long documents must be split.
- 401: sign in; 403: wrong role/CSRF; 404: inaccessible profile/report;
  422: invalid language or missing translation consent; 503: OCR runtime missing.
- Background failures include `processor_timeout`, `invalid_document`,
  `too_many_pages`, `image_too_large`, `text_too_large`, `report_download_failed`.
- Printed text works best. Handwriting, tables, mixed scripts, medicine names,
  doses and units may be misread. Confidence is not a clinical verification score.
  This feature does not diagnose, prescribe or interpret medical findings.

## Verification

Run the Flask suite from `backend`: `venv/Scripts/python.exe -m pytest -q`.
`tests/report_text_fixture.py` plus test Vite on 5175 and
`node admin/tests/report-text.mjs` exercise the UI using synthetic mocked results.
Real model tests should use synthetic reports, never an unconsented patient report.

## Free translation provider

This application uses `deep-translator==1.11.4` with **MyMemoryTranslator**,
not GoogleTranslator. No paid API key is required. OCR stays local; English
translation sends extracted text to MyMemory only after explicit consent.

The package's default MyMemory URL is HTTP, so our adapter explicitly uses
`https://api.mymemory.translated.net/get`, rejects redirects and restricts the
request to that provider. Requests are split into at most 450 UTF-8 bytes to
respect MyMemory's 500-byte limit, including Hindi/other multibyte scripts.

Anonymous free usage is limited to 5000 characters/day by the provider; this is
shared by the deployment, not guaranteed per patient. We cap one translation at
4000 characters. A daily quota or network failure keeps original OCR text and
returns PARTIAL with a structured translation error. HTTP 429 blocks immediate
retries for at least 60 seconds. No automatic fallback sends text to another
provider. Larger reports can still be OCR-extracted without translation.

References: [deep-translator MyMemory usage](https://deep-translator.readthedocs.io/en/latest/usage.html#mymemory-translator),
[MyMemory API](https://mymemory.translated.net/doc/spec.php),
[free usage limits](https://mymemory.translated.net/doc/usagelimits.php).
