# country-iso-search changelog

For more context information, please read through the
[release notes](https://github.com/plotly/country-iso-search/releases).

To see all merged commits on the main branch that will be part of the next country-iso-search release, go to:

<https://github.com/plotly/country-iso-search/compare/vX.Y.Z...main>

where X.Y.Z is the semver of the most recent country-iso-search release.


## [Unreleased]

## [0.1.2] -- 2026-08-27

### Changed
- Updated name from "Nauru" to "Naoero" per update from country and ISO-3166 [[#7](https://github.com/plotly/country-iso-search/pull/7)]

### Fixed
- Use escaped Unicode characters for regex patterns to avoid error on a page that omits a UTF-8 charset [[#6](https://github.com/plotly/country-iso-search/pull/6)]

## [0.1.1] -- 2026-06-22

### Changed
- `sanitize` now drops `the` immediately after `,` or `(`, so ISO 3166-1 article forms like `"Korea, the Republic of"`, `"Korea (the Republic of)"` resolve correctly
- `sanitize` now strips `[` and `]` so the ISO annotation form `"Falkland Islands (the) [Malvinas]"` resolves
- Resolution now covers all 249 ISO 3166-1 short uppercase names
- Constituent components of multi-part country names now resolve as aliases: `"Antigua"` / `"Barbuda"` → ATG
- Comma-inverted aliases added for countries whose canonical name doesn't already cover the form: `"Korea, Republic of"` → KOR

## [0.1.0] -- 2026-06-22

Initial release.

### Added
- `lookupAlpha3(input)` resolves a country reference to its ISO 3166-1 alpha-3 code. Accepts alpha-3 (`"FRA"`, case-insensitive), alpha-2 (`"FR"`, case-insensitive), UN M49 numeric as a number or any numeric string (`250`, `"250"`, `4`, `"04"`, `"0250"` — leading zeros are stripped before zero-padding to 3 digits), or a country name / alias (case-insensitive; sanitized before matching — see below)
- `lookup(input)` — same input shape as `lookupAlpha3` but returns the full `CountryRecord` (or `undefined`) so callers get `iso2`, `m49`, the canonical `name`, and `aliases` in one call
- `createLookup(records)` — builds a scoped lookup over a custom record list
- `sanitize(input)` exported for advanced use; produces the same normalized key the internal name/alias index is built with
- 249 ISO 3166-1 records in `COUNTRIES`
- ~1,700 aliases in total, covering English long forms (`Republic of X`, `Kingdom of X`, etc.), historical official names (Burma, Persia, Ceylon, Formosa, Zaire, Rhodesia, etc.), native-language names in each country's official languages, and flag emojis (e.g. `🇫🇷` → `FRA`)
- `COUNTRIES` exported as `ReadonlyArray<CountryRecord>`
- `byAlpha3`, `byAlpha2`, `byM49` exported as `ReadonlyMap<string, CountryRecord>` lookups over `COUNTRIES`
- `CountryRecord`, `CountryLookup` TypeScript types exported
- Dual-format package: ships ESM and CJS bundles plus TypeScript declarations in `dist/`
- MIT licensed
