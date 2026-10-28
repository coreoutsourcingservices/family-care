# Customer module-selection localization

The selector is mounted only on `/customer/dashboard`, after login. Recommendations, states, all languages and common message catalogs use the existing Flask localization API. Loopback/private-IP responses show Hindi/English and an optional state picker; there is no browser public-IP lookup or GPS permission.

`source/en.json` contains public static interface copy only. The 26 additional catalogs are machine-generated draft translations and should receive native-speaker review. Patient names, records, credentials and medical text were never submitted for translation. No translation service is called at runtime.

The requested `i18n` package runs in `scripts/compile-locales.mjs`, producing browser-safe JSON under `compiled/`. React updates static copy from these catalogs without bundling Node filesystem dependencies. Run `npm run locales:compile --workspace customer` after editing source catalogs; the customer prebuild also runs it. Commit source and compiled catalogs together because the shared app consumes the compiled assets too.

Language choice is remembered in `familycare.customer.language`. Changing the manual state changes suggestions only. Non-translated configured languages are listed but disabled. Urdu sets RTL direction on the module-selection dashboard. Names, IDs and backend values are never translated. The backend remains responsible for trusted-proxy IP handling after deployment.
