# TODO

Ordered. `D` = data, `B` = build, `V` = viz, `S` = ship.

## Blocking

- [x] **Name the project.** Pendulum.
- [ ] **Decide the deployment target.** Cloudflare Pages on a subdomain (the
      Chronoscape pattern) or a subdirectory of `charlie-tren.github.io` (the
      Photocopy pattern). Chronoscape's split-project problem is an argument
      for keeping this simple.

## D — data

- [x] D1. OWID fetch working, no key. `scripts/fetch_owid.py`.
- [ ] D2. **Pull DPI 2023 and rebuild left/right for ~180 countries, 1975-2022.**
      This is the spine. Then diff DPI against the seed 15 and investigate
      every disagreement — that diff is itself interesting.
- [ ] D3. Extend 2023-2026 by hand, using the 30-June convention, for whatever
      country set the site covers. DPI stops before here and this is the window
      people actually care about.
- [ ] D4. V-Party v2 for the nuanced spectrum. Note it stops ~2019 — decide
      whether to show a truncated nuanced view or interpolate forward from the
      seed. **Do not silently interpolate.**
- [ ] D5. Manifesto Project API key + RILE for a continuous axis on the 67
      countries it covers.
- [ ] D6. CHES for the second (GAL-TAN) axis, Europe only.
- [ ] D7. Population weights from OWID `population`. Watch the entity-name
      joins — OWID uses its own names and OWID_* codes for aggregates.
- [ ] D8. One provenance record per series: source, version, retrieved date,
      licence, coverage end. Rendered on the site, not buried.

## B — build

- [ ] B1. Pipeline: `raw/ -> normalise -> data/out/*.json`. Static, committed,
      no runtime API calls from the browser.
- [ ] B2. Country-group filter applied at build time so the JSON stays small.
- [ ] B3. Country-count vs population-weighted computed as two series, toggled
      client-side.
- [ ] B4. Tests on the aggregation maths. Weighted mean with missing countries
      is where this will silently go wrong.

## V — viz

- [ ] V1. Stacked area, share of world population by government orientation,
      over time. **This is the headline chart and the thing nobody else has.**
- [ ] V2. The index line (mean orientation) with a trailing 3-year MA.
- [ ] V3. Group toggle: World / G7 / G20 / OECD / EU / BRICS+ / ASEAN / Original 15.
- [ ] V4. Weighting toggle: one country one vote vs one person one vote.
- [ ] V5. Spectrum toggle: 3-bucket (left/centre/right) vs the V-Party
      multi-dimensional view.
- [ ] V6. Map or cartogram, one year at a time, with a year scrubber.
- [ ] V7. Country detail on click: that country's own history as a strip.
- [ ] V8. Deep links — every toggle state in the URL so a view is shareable.
      **Never write the default state to the URL.**

## S — ship

- [ ] S1. Open on the headline chart with a default already selected. No
      "choose a country" landing screen, no empty first paint.
- [ ] S2. Attribution page: V-Dem, OWID, DPI, Manifesto, CHES, with licences.
      CC-BY means naming them is an obligation, not a courtesy.
- [ ] S3. Methodology page — the 30-June rule, what 0 means, why the MA is
      trailing, what the seed data is and where it is judgement rather than source.
- [ ] S4. Mobile. A 32-year x-axis on a phone is the hard case.
- [ ] S5. Link out to OWID's democracy page rather than reimplementing it.

## Parked

- Regime type (democracy/autocracy) as a *second* axis crossed with ideology —
  "how many people live under right-wing autocracies" is a better question than
  either axis alone. Parked only because it doubles the build.
