# Location and language API

These public GET endpoints need no login, Bearer token, database write, or request body.

| Purpose | URL |
| --- | --- |
| Detect caller IP and suggest languages | `http://127.0.0.1:5001/api/v1/localization` |
| Preview Maharashtra locally | `http://127.0.0.1:5001/api/v1/localization?state=Maharashtra` |
| Preview Tamil Nadu | `http://127.0.0.1:5001/api/v1/localization?state=Tamil%20Nadu` |
| Preview Gujarat | `http://127.0.0.1:5001/api/v1/localization?state=Gujarat` |
| All 28 states and 8 union territories | `http://127.0.0.1:5001/api/v1/localization/states` |
| All languages (Other languages selector) | `http://127.0.0.1:5001/api/v1/localization/languages` |
| Hindi i18next catalog | `http://127.0.0.1:5001/api/v1/localization/messages/hi` |
| English i18next catalog | `http://127.0.0.1:5001/api/v1/localization/messages/en`
http://127.0.0.1:5001/api/v1/localization/languages|
all list othguages

Example Maharashtra response:

```json
{
  "location": {"country_code":"IN","state":"Maharashtra","status":"manual","approximate":true},
  "languages": [
    {"code":"mr","name":"Marathi","translation_status":"available","fallback_language":"en","direction":"ltr"},
    {"code":"hi","name":"Hindi","translation_status":"available","fallback_language":"en","direction":"ltr"},
    {"code":"en","name":"English","translation_status":"available","fallback_language":"en","direction":"ltr"}
  ],
  "recommended_language":"mr",
  "fallback_language":"en",
  "manual_state_selection":true
}
```

The supplied state list is a product recommendation list, not a claim about official languages. The response includes up to three regional options plus Hindi and English, deduplicated: three to five total. All supplied regional names remain in `regional_languages` on `/states`, including fourth choices. Uncommon language codes are stable application slugs, not claimed ISO codes.

## Detection and fallback

The API validates the caller address and sends only a public IP to the fixed HTTPS [ipwho.is endpoint](https://ipwhois.io/documentation). It requests country/state only, uses a three-second timeout, and caches at most 2,048 lookups per process with hourly expiry. No IP or precise coordinates are returned or stored in the database. The provider receives the IP; location is approximate, can reflect VPN/mobile routing, and is not used for authorization. Provider errors/rate limits return usable Hindi/English options with `lookup_unavailable`.

Loopback/private addresses return `private_ip`: localhost cannot identify the user's Indian state. Use the manual state dropdown or `?state=` for local testing. Outside India or an unmapped state returns `outside_supported_region`. Invalid manual state returns 400; unknown language code returns 404.

## Admin app, port 3005

Admin and superadmin login, registration, dashboard, directories, settings and audit screens use react-i18next. The selector appears on login screens and the panel header. First visit uses the recommended language; a manual language selection is remembered in `localStorage` and wins over later IP detection. Changing the state changes suggestions, not the saved language. No authentication tokens are saved by this feature.

There are 27 complete static UI catalogs: English, Hindi, Marathi, Tamil, Gujarati, Telugu, Bengali, Kannada, Malayalam, Punjabi, Urdu, Odia, Assamese, Nepali, French, Bhojpuri, Maithili, Konkani, Manipuri, Mizo, Dogri, Awadhi, Marwari, Khasi, Santali, Tulu and Kokborok. Each covers all 289 current UI/known API-message keys, including story copy, login/session messages, navigation, dashboards, directories, dialogs, settings, known audit event labels and loading/error pages. Language changes retranslate already-visible notices immediately. Manual translations were retained where present; the added catalogs are machine-generated from public English interface copy and need native-speaker review. No user, credential, patient or medical data was sent for translation. At runtime the app only reads these local JSON catalogs; there is no translation-service dependency.

Untranslated regional languages remain in the API recommendation list, with `english_fallback` status; the admin selector disables them and displays a translated unavailable label. They are not presented as working translations. First-visit recommendations choose the first fully translated language, falling back to Hindi/English. Names, email addresses, IDs, user-entered medical text and unknown/new server/audit data remain as supplied. See `backend/locales/README.md` for catalog maintenance.

Catalogs live in `backend/locales/<code>.json`. `/messages/<code>` returns merged fallback messages suitable for `i18next.addResourceBundle(code, 'translation', data.messages)`. Add missing keys to complete a language; translation status is computed from key coverage. Restart backend workers after changing cached catalog files. The initial English catalog is bundled at `admin/src/locales/en.json`; update both English copies when adding keys. i18next uses `fallbackLng: 'en'`, literal phrase keys and React-safe interpolation. See [i18next fallback](https://www.i18next.com/principles/fallback).

## Reverse proxy deployment

By default, arbitrary `X-Forwarded-For` headers are ignored. Backend `GEO_TRUSTED_PROXIES` accepts comma-separated CIDRs of known reverse proxies and walks their forwarding chain from right to left until the first untrusted peer. Keep it empty when accessing Flask directly.

The Next.js proxy forwards no caller IP by default, so local admin requests correctly return private-IP fallback. For production IP detection, the ingress proxy must overwrite `X-Forwarded-For`; set admin server environment `GEO_FORWARD_CLIENT_IP=true` only behind that ingress and configure backend `GEO_TRUSTED_PROXIES` with the actual Next/ingress proxy networks. Do not use unrestricted CIDRs. Without that deployment setup the selector still works through manual state selection.


## Other languages (additional API)

`GET /api/v1/localization/languages` returns `{ "items": [...], "total": N }`. Each item uses the existing language-option fields (`code`, `name`, `native_name`, `translation_status`, `fallback_language`, `direction`). The list contains every configured language once, sorted by English name, including languages not in the current state's recommendations. Untranslated options keep their support status. This endpoint does not detect an IP or change any saved preference.

In both portals, choose **Other languages** at the end of the language dropdown to load this list; choose **Regional languages** to return to state recommendations. Existing localization/recommendation, states, messages and authentication routes are unchanged.
