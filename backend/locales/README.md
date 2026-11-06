# Admin and Superadmin translation catalogs

The English source and all 26 enabled translated catalogs contain 1204 keys. The matching English bundle lives in `admin/src/locales/en.json`. These cover portal navigation, dashboard, account settings, directories, approval review, patient/doctor details, vaccination, women health article management, activity/recycle-bin tools and static backend system messages.

The additional translations are machine-generated drafts of public interface text. They have not been reviewed by native speakers. Brand names, technical identifiers, interpolation tokens and API enum values retain their spelling. User names, article content, clinical records and uploaded documents are not submitted for UI translation.

API workers load these static catalogs; restart workers after edits. No translation service is called to render an interface or localize a response. `backend/scripts/translate_ui_catalogs.py` is an explicit build-time helper; it requires `--translate` and a JSON list of public source keys. The admin selector lists the 27 available catalogs; unsupported languages remain identifiable through backend inventory metadata.

`Accept-Language` selects static backend error/system-message translations. Error codes, status fields and record data retain their original values. The admin client sends its selected language through the Next proxy. Missing or unsupported language headers use English.

Validation:

- `node admin/scripts/check-localization.mjs`: all enabled catalogs, source UI keys and interpolation tokens.
- `backend/venv/Scripts/python.exe -m pytest backend/tests/test_localization.py -q` (run from backend with relative paths adjusted).
- `npm run test:all-languages --workspace admin`: isolated browser matrix for both roles, all 27 selections, representative pages in five languages, Urdu RTL and form enum values.

When adding copy, extend the English source and each enabled catalog, then run the checks. The API's `available` status describes catalog coverage, not native-speaker review. Translation build results are recorded in `backend/localization_translation_report.json`.
