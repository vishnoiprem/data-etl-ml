# country-iso-search

[![npm](https://img.shields.io/npm/v/country-iso-search)](https://www.npmjs.com/package/country-iso-search)
[![Test](https://github.com/plotly/country-iso-search/actions/workflows/test.yml/badge.svg)](https://github.com/plotly/country-iso-search/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/npm/l/country-iso-search)](LICENSE)

Resolve country names and codes to their canonical ISO 3166-1 alpha-3 form.

<br/>
<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png" width="400px" alt="Maintained by Plotly">
  </a>
</div>
<br/>

---

**[Try it in the browser →](https://plotly.github.io/country-iso-search/demo/)** — enter a query and see what resolves. Source in [`demo/`](demo/).

Accepts alpha-3 (`"FRA"`), alpha-2 (`"FR"`), UN M49 numeric (`250`, `"250"`, `"04"`, or `"0250"` — leading zeros are stripped and the result is zero-padded to 3 digits), or a country name / alias. Name/alias matching is case-insensitive and input is sanitized before comparison: diacritics are stripped (`Türkiye` → `turkiye`), apostrophes and `.` `()` `[]` `,` are dropped, `&` becomes `and`, `-`/`–`/`—` become spaces, `st` expands to `saint`, `the` is dropped when it leads the input or follows `,`/`(` (so ISO short-name forms like `Korea (the Republic of)` and `Korea, the Republic of` both resolve), and internal whitespace is collapsed. Returns the canonical alpha-3, or `undefined` when no record matches.

## Install

```bash
npm install country-iso-search
```

## Usage

```ts
import { lookup, lookupAlpha3 } from 'country-iso-search';

lookupAlpha3('FRA');                 // 'FRA'
lookupAlpha3('FR');                  // 'FRA'
lookupAlpha3(250);                   // 'FRA' (M49 numeric)
lookupAlpha3('04');                  // 'AFG' (zero-padded to '004')
lookupAlpha3('0250');                // 'FRA' (leading zeros stripped)
lookupAlpha3('France');              // 'FRA'
lookupAlpha3('Burma');               // 'MMR' (historical name)
lookupAlpha3('Türkiye');             // 'TUR'
lookupAlpha3('cote d ivoire');       // 'CIV' (apostrophes / diacritics ignored)
lookupAlpha3('St. Kitts and Nevis'); // 'KNA'
lookupAlpha3('🇯🇵');                  // 'JPN' (flag emoji)
lookupAlpha3('not a country');       // undefined

// `lookup` returns the full record:
lookup('France')?.iso2;              // 'FR'
lookup('France')?.m49;               // '250'
```

## Custom records

Need codes for sub-national regions, historical countries, disputed areas, or anything else outside ISO 3166-1? Pass your own records to `createLookup` and use the returned scoped helpers. Spread `COUNTRIES` to layer custom records on top of the canonical data:

```ts
import { createLookup, COUNTRIES, type CountryRecord } from 'country-iso-search';

const CUSTOM: CountryRecord[] = [
    { iso3: 'XAC', iso2: '', m49: '', name: 'Aksai Chin', aliases: [] },
    { iso3: 'XJK', iso2: '', m49: '', name: 'Jammu and Kashmir', aliases: [] },
];

const { lookupAlpha3, lookup, byAlpha3, byAlpha2, byM49 } = createLookup([
    ...COUNTRIES,
    ...CUSTOM,
]);

lookupAlpha3('FRA');               // 'FRA' (canonical)
lookupAlpha3('XAC');               // 'XAC' (custom)
lookupAlpha3('Aksai Chin');        // 'XAC'
```

Leave `iso2` and `m49` blank on user-assigned codes — `createLookup` skips blank values when building the `byAlpha2` and `byM49` maps. Cross-country alias collisions throw at construction time so they can be fixed before any lookups happen.

## API

### `lookupAlpha3(input)`

- `input: string | number` — country identifier in any supported form.
- Returns `string | undefined`.

### `lookup(input)`

Same input shape as `lookupAlpha3`, but returns the full `CountryRecord` (or `undefined`). Use this when you need `iso2`, `m49`, the canonical `name`, or the `aliases` list instead of just the alpha-3.

### `createLookup(records)`

- `records: ReadonlyArray<CountryRecord>` — every record the returned lookup should resolve.
- Returns `{ lookup, lookupAlpha3, byAlpha3, byAlpha2, byM49 }` scoped to those records.
- Throws on cross-record name/alias collisions (after sanitization).

The top-level `lookup` / `lookupAlpha3` and `byAlpha3` / `byAlpha2` / `byM49` exports are a `createLookup(COUNTRIES)` instance.

### `sanitize(input)`

- `input: string` — text to normalize.
- Returns the same string lowercased with diacritics / apostrophes / `.` `()` `[]` `,` stripped, `&` mapped to `and`, hyphen-likes turned into spaces, `st` expanded to `saint`, and `the` dropped when it leads the input or follows `,`/`(`. Exported for advanced use — call it to produce keys consistent with the internal name/alias index.

### Exports

- `COUNTRIES: ReadonlyArray<CountryRecord>` — the bundled ISO 3166-1 / M49 records.
- `byAlpha3`, `byAlpha2`, `byM49` — `ReadonlyMap<string, CountryRecord>` lookups over `COUNTRIES` (use `.get(key)`; e.g. `byAlpha3.get('FRA')?.name`).
- `CountryRecord`, `CountryLookup` — TypeScript types.

### `CountryRecord`

```ts
interface CountryRecord {
    iso3: string;               // ISO 3166-1 alpha-3
    iso2: string;               // ISO 3166-1 alpha-2 (may be blank on custom records)
    m49: string;                // UN M49, 3-digit zero-padded (may be blank on custom records)
    name: string;               // English short name from UN M49
    aliases: readonly string[]; // additional lowercased forms — historical names,
                                //   common alternates, native-language variants,
                                //   and the country's flag emoji
}
```

## Data

`COUNTRIES` mirrors UN M49 / ISO 3166-1 for `iso3`, `iso2`, `m49`, and `name`. The ~1,700 aliases were assembled from CLDR, Wikidata (filtered to languages tagged official via P37), and GeoNames, then **curated by hand** to resolve substring collisions (e.g. Niger vs. Nigeria, Guinea vs. Guinea-Bissau vs. Equatorial Guinea vs. Papua New Guinea), normalize transliterations, and drop variants that would produce false matches. Aliases are stored in their sanitized form (diacritics / apostrophes / punctuation stripped, hyphens turned into spaces, `st` expanded to `saint`), so don't add accented or punctuated variants by hand — `lookupAlpha3` applies the same transform to user input at lookup time. To add an alias or fix an entry, edit [src/countries.ts](src/countries.ts) directly and open a pull request.

GeoNames (CC BY 4.0) and Unicode CLDR (Unicode License V3) require attribution. The full third-party notices live in [NOTICE](NOTICE) in this repository — **consult that file before redistributing this package or its data**, since it carries the attribution texts those licenses require to travel with downstream redistributions. Wikidata is CC0 and is acknowledged there as a courtesy.

## License

MIT — see [LICENSE](LICENSE). Third-party data attributions: [NOTICE](NOTICE).
