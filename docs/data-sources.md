# Data sources register

Researched 2026-08-18. Every row was checked live, not recalled. Coverage
end-dates matter more than anything else here: the academic data is
excellent up to about 2019-2022 and then goes quiet, which is exactly the
window a 2026 site most wants to show.

## Tier 1, wire these first (no key, no friction)

### Our World in Data grapher API
- **What**: regime classifications, democracy indices, and, crucially -
  population living under each regime type, already computed.
- **Access**: `https://ourworldindata.org/grapher/<slug>.csv?v=1&csvType=full&useColumnShortNames=true`
  Metadata at `.metadata.json` with the same query string.
- **Verified working** 2026-08-18: `political-regime` returned 31,491 rows
  (1789-2025, every country); `people-living-in-democracies-autocracies`
  returned 1,658 rows including World and continent aggregates to 2025.
- **Key/registration**: none. Send a User-Agent header or Cloudflare 1010s you.
- **Licence**: CC-BY for OWID's own work. Third-party source terms still apply
  to the underlying data, so attribute V-Dem too.
- **Underlying**: V-Dem v16 (March 2026), so genuinely current to 2025.

### V-Dem Country-Year (direct)
- **Version**: v16, March 2026. 531 indicators + 251 indices.
- **Use if**: OWID's curated slugs don't expose an indicator we want.
- Slower and heavier than going through OWID. Prefer OWID unless blocked.

## Tier 2, the left/right spine (one-off downloads)

### Database of Political Institutions (DPI), IDB
- **What**: `execrlc` codes the chief executive's party as Right / Left /
  Centre / No information. This is the machine-readable version of the seed
  spreadsheet, for ~180 countries instead of 15.
- **Coverage**: 1975 onwards. DPI2020 covered 1975-2020; a 2023 edition is
  published on the IDB data portal.
- **Access**: https://www.iadb.org/en/knowledge-resources/research-idb/research-datasets/database-political-institutions
- **Gap**: ends ~2022. The seed sheet covers 2023-2025 for 15 countries.

## Tier 3, the nuanced spectrum (answers "more than +1/-1")

### V-Party (V-Dem Institute)
- **What**: expert-coded party positions on multiple dimensions, economic
  left-right, populism, anti-pluralism, illiberalism, not one axis.
- **Coverage**: 178 countries, 3,489 parties, 2,805 elections, ~11,914
  party-election-year units.
- **Version**: v2, February 2022. **This is the problem**, V-Party has not
  been updated alongside V-Dem's main dataset, so it effectively stops around
  the 2019 election round. Six years stale as of now.
- **Formats**: SPSS, Stata, CSV, R.

### Manifesto Project (MARPOR/CMP)
- **What**: RILE, a *continuous* left-right score derived by content-coding
  party manifestos. The canonical continuous spectrum measure.
- **Coverage**: 1,300+ parties, 67 countries, 1945-present, updated annually.
- **Access**: REST API plus the `manifestoR` R package. Free registration for
  an API key.
- **Gap**: 67 countries skews OECD/Europe/Latin America. Not global.

### Chapel Hill Expert Survey (CHES)
- **What**: expert survey placing parties on left-right, EU position, and the
  GAL-TAN (liberal/authoritarian) axis.
- **Coverage**: Europe only, 1999-2024.
- **Use as**: the second axis for a 2-D spectrum view of Europe.

## Tier 4, supporting

- **UN World Population Prospects** via OWID for population weights.
- **Country groups** (G7, G20, OECD, EU, BRICS, ASEAN, Commonwealth) -
  hand-maintained in `config/country_groups.yaml`. Small and stable.

## Prior art, checked, and what it leaves open

- **OWID "People living in democracies and autocracies"** already does
  population-weighted regime type as a time series, and does it well. Do not
  rebuild it; link to it and use their data.
- **Arden Strategies "Global Parliament Index"** does population-weighted
  ideology across ten categories with a rotatable globe, but it is a **2025
  snapshot only**, with a proprietary classification and no downloadable data.
  https://ardenstrategies.com/services/global-campaign-advisory/global-parliament/
- **Political Compass**, **Polity5**, **Freedom House**, different questions,
  and the names are taken. Avoid collision.

**The open ground**: population-weighted *ideological* orientation as a
**long time series** built on **open data**. OWID has the time series but for
regime type, not ideology. Arden has the ideology and the population weighting
but only for one year and won't share the data. Nobody has the intersection.
That intersection is the project.

## Wikidata layer, how it is queried, and what it gets wrong

Added 2026-08-18 to extend past DPI's 2023 end. Three bugs were found and fixed
while building it, all of which produced plausible-looking wrong answers:

1. **Pooled party memberships.** The naive query joins a head of government to
   *every* party they have ever belonged to. Macron returned Renaissance, the
   Socialist Party and En Marche at once, so France averaged to a nonsense
   position and was labelled "Union for a Popular Movement", Chirac's party -
   in 2025. Fixed by requiring the P102 membership statement's own date
   qualifiers to overlap the term.
2. **Wrong year assignment.** Terms were being credited to their start year,
   which contradicts the 1 January convention used everywhere else. A
   government formed in September 2024 was claiming 2024. Fixed by assigning a
   term to year Y only if it was already in office on 1 January of Y. This is
   what makes UK 2024 read Conservative and UK 2025 read Labour, correctly.
3. **Stale party labels on extended years.** `extend_years` carries DPI's last
   known party name into 2024-2026 so later layers have somewhere to land. When
   Wikidata then resolved the year, the label was not being overwritten, so the
   UK's 2024 Labour win rendered as "left, Conservative". Fixed, and unresolved
   years now drop the carried name rather than showing someone else's.

### Known seam: DPI and Wikidata disagree

Wikidata tags the US Democratic Party as `centrism`; DPI codes it `Left`. Since
DPI wins up to 2023 and Wikidata takes over from 2024, the United States can
appear to move left-to-centre with no election in between. That is a source
disagreement, not a political event.

It is visible rather than hidden, the country strip shows a source bar under
every run, and the headline chart's hover names the source mix. But it is a real
limitation, and the honest fix is a reconciliation pass that carries DPI's
coding forward whenever the governing party has not actually changed. Logged as
TODO D9.
