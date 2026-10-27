# UI translation catalogs

27 languages currently have all 289 interface/message keys. The source is `en.json`; its bundled frontend copy is `admin/src/locales/en.json`. All catalogs are static files loaded and cached per worker by the existing localization API. Restart backend workers after updating catalogs. No runtime translation requests are made.

Existing human-authored Hindi and common Marathi/Tamil/Gujarati labels were retained. New entries were prepared with machine translation of public English interface labels only. They have not been reviewed by native speakers. Technical IDs, brand names and interpolation tokens are preserved. Review translations before treating them as approved terminology, especially for account approval and security actions.

Languages without a complete catalog remain visible as unavailable, disabled choices in the admin selector. Do not copy Hindi/English into a differently named regional catalog to label that language supported. Supply a real translation file to enable one.

When adding interface text, add the English key/value to both English files and translate it in every enabled catalog. `test_localization.py` verifies complete key coverage, interpolation tokens and translated story/session text. Catalog metadata `available` means complete key coverage, not native-speaker approval.

Run backend tests with `venv\Scripts\python.exe -m pytest tests/test_localization.py -q`. Browser regression tests are in `admin/tests/localization.mjs`; see the admin README for execution.
