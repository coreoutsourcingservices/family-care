# Language / Localization API

Verified against backend routes on 6 November 2026. Base URL: `http://127.0.0.1:5001`.
Admin/Superadmin browser proxy: `http://127.0.0.1:3005/api/v1/localization`.
See [Women Health Articles API](HEALTH_ARTICLES_API.md) for Admin, Doctor and women-profile article endpoints.

## Endpoint list

| Method | API | Access | Request data |
| --- | --- | --- | --- |
| GET | `/api/v1/localization` | Public | Optional query `state` |
| GET | `/api/v1/localization/states` | Public | None |
| GET | `/api/v1/localization/languages` | Public | None |
| GET | `/api/v1/localization/messages/{language}` | Public | Language code in path |

These four APIs take no JSON body and do not save a user preference in the database.
The examples below use actual public catalog metadata; the message example is an excerpt, not the complete catalog.

## 1. State recommendations

`GET /api/v1/localization?state=Kerala`

Optional `state` must match a supported state/union territory (known aliases are normalized).
Omit it for approximate IP-based recommendations. Local/private IPs cannot detect the user's Indian state and use Hindi/English with `location.status: private_ip`.

HTTP 200:

```json
{
  "fallback_language": "en",
  "languages": [
    {
      "code": "ml",
      "direction": "ltr",
      "fallback_language": "en",
      "name": "Malayalam",
      "native_name": "മലയാളം",
      "translation_status": "available"
    },
    {
      "code": "hi",
      "direction": "ltr",
      "fallback_language": "en",
      "name": "Hindi",
      "native_name": "हिन्दी",
      "translation_status": "available"
    },
    {
      "code": "en",
      "direction": "ltr",
      "fallback_language": "en",
      "name": "English",
      "native_name": "English",
      "translation_status": "available"
    }
  ],
  "location": {
    "approximate": true,
    "country_code": "IN",
    "state": "Kerala",
    "status": "manual"
  },
  "manual_state_selection": true,
  "recommended_language": "ml"
}
```

Each language has `code`, English `name`, `native_name`, `translation_status`, `fallback_language` and `direction`.
`recommended_language` is the first available regional choice, otherwise Hindi/English. Regional suggestions include at most three regional choices plus Hindi/English, without duplicates; `/states` retains all names in `regional_languages`.

Invalid state: HTTP 400:

```json
{
  "error": {
    "code": "invalid_state",
    "message": "Choose a state from /api/v1/localization/states"
  }
}
```

Other location statuses include `manual`, `detected`, `unknown`, `outside_supported_region` and `lookup_unavailable`. Location is approximate and must not be used for authorization. Public-IP lookup uses the configured trusted-proxy rules; provider failures retain usable language options. No GPS request is made.

## 2. States and union territories

`GET /api/v1/localization/states`

HTTP 200: `items` contains 28 states and 8 union territories. Example excerpt:

```json
{
  "items": [
    {
      "languages": [
        {
          "code": "ml",
          "direction": "ltr",
          "fallback_language": "en",
          "name": "Malayalam",
          "native_name": "മലയാളം",
          "translation_status": "available"
        },
        {
          "code": "hi",
          "direction": "ltr",
          "fallback_language": "en",
          "name": "Hindi",
          "native_name": "हिन्दी",
          "translation_status": "available"
        },
        {
          "code": "en",
          "direction": "ltr",
          "fallback_language": "en",
          "name": "English",
          "native_name": "English",
          "translation_status": "available"
        }
      ],
      "name": "Kerala",
      "regional_languages": [
        "Malayalam"
      ],
      "type": "state"
    }
  ]
}
```

`type` is `state` or `union_territory`; `languages` contains recommendation objects and `regional_languages` contains product recommendation names. This is not a list of legally designated official languages.

## 3. All language choices

`GET /api/v1/localization/languages`

HTTP 200 shape (items excerpted):

```json
{
  "items": [
    {
      "code": "en",
      "name": "English",
      "native_name": "English",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "hi",
      "name": "Hindi",
      "native_name": "हिन्दी",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    },
    {
      "code": "ml",
      "name": "Malayalam",
      "native_name": "മലയാളം",
      "translation_status": "available",
      "fallback_language": "en",
      "direction": "ltr"
    }
  ],
  "total": 66
}
```

The complete response is sorted by English name. It contains 66 configured choices; 27 currently have available catalogs. Admin/Superadmin selectors show only `translation_status: available` choices.

| Status | Meaning |
| --- | --- |
| `available` | Catalog contains all English source keys |
| `partial` | Catalog exists but some keys are missing |
| `english_fallback` | No translated catalog; messages fall back to English |

Available language codes:

| Code | Language | Direction |
| --- | --- | --- |
| `as` | Assamese | ltr |
| `awadhi` | Awadhi | ltr |
| `bhojpuri` | Bhojpuri | ltr |
| `bn` | Bengali | ltr |
| `dogri` | Dogri | ltr |
| `en` | English | ltr |
| `fr` | French | ltr |
| `gu` | Gujarati | ltr |
| `hi` | Hindi | ltr |
| `khasi` | Khasi | ltr |
| `kn` | Kannada | ltr |
| `kokborok` | Kokborok | ltr |
| `konkani` | Konkani | ltr |
| `maithili` | Maithili | ltr |
| `manipuri` | Manipuri | ltr |
| `marwari` | Marwari | ltr |
| `mizo` | Mizo | ltr |
| `ml` | Malayalam | ltr |
| `mr` | Marathi | ltr |
| `ne` | Nepali | ltr |
| `or` | Odia | ltr |
| `pa` | Punjabi | ltr |
| `santali` | Santali | ltr |
| `ta` | Tamil | ltr |
| `te` | Telugu | ltr |
| `tulu` | Tulu | ltr |
| `ur` | Urdu | rtl |

Application slugs such as `manipuri` and `bhojpuri` are the API codes; do not replace them with a translation provider's code.

## 4. Load UI messages

`GET /api/v1/localization/messages/hi`

HTTP 200 shape (message excerpt):

```json
{
  "language": "hi",
  "fallback_language": "en",
  "translation_status": "available",
  "messages": {
    "Dashboard": "डैशबोर्ड",
    "Vaccination": "टीकाकरण",
    "Language": "भाषा",
    "Sign in": "लॉगिन करें"
  }
}
```

The full response contains all 1204 current keys. `messages` merges English fallback keys with the selected static catalog. Known configured languages without a catalog return HTTP 200 with `english_fallback`; an unknown code returns HTTP 404:

```json
{
  "error": {
    "code": "unsupported_language",
    "message": "Unknown language code"
  }
}
```

## Admin / Superadmin integration

1. Load recommendations and `/states`.
2. Load `/languages` for Other languages; show available options.
3. Fetch `/messages/{code}` and add `messages` to i18next; use English fallback.
4. Set document language to the API code and direction from metadata (`ur` is RTL).
5. Send `Accept-Language: hi` (or the selected code) on Admin/Superadmin API requests. The Next proxy forwards this header to Flask.

```javascript
const response = await fetch('/api/v1/localization/messages/hi');
if (!response.ok) throw new Error('Language catalog unavailable');
const data = await response.json();
if (data.translation_status === 'available') {
  i18n.addResourceBundle(data.language, 'translation', data.messages, true, true);
  await i18n.changeLanguage(data.language);
  document.documentElement.lang = data.language;
  document.documentElement.dir = data.language === 'ur' ? 'rtl' : 'ltr';
}
```

Preference storage in the current portals:

| Storage | Key | Data |
| --- | --- | --- |
| localStorage | `familycare-language` | Selected language code |
| localStorage | `familycare-state` | Selected state name |
| sessionStorage | `familycare-language-catalog` | Last selected static UI catalog |

Manual language selection wins over recommendations. Changing state updates suggestions, not the saved language. Cache contains interface text, not patient data or authentication tokens.

### Backend messages

`Accept-Language` translates known static error messages and top-level system messages on Admin/Superadmin/auth responses. Error codes, HTTP statuses, resource IDs and enum values are unchanged. Missing/unsupported headers fall back to English. It is not a translation endpoint for user content. Article descriptions, patient records, names and validation details without a matching catalog entry remain as supplied.

Example request:

```bash
curl "http://127.0.0.1:5001/api/v1/admin/me" -H "Accept-Language: hi"
```

Without authentication, HTTP 401 retains `error.code: invalid_token` and returns a localized `error.message`.

Catalogs are machine-generated translations with existing manual entries retained; they have not all received native-speaker review. No translation service is used to process runtime user content. Restart API workers after changing `backend/locales` because catalogs are cached.
