# TODO

Ordered. `D` = data, `B` = build, `V` = viz, `S` = ship.

## Blocking

- [x] **Name the project.** Pendulum.
- [x] **Deployment target: Cloudflare Pages on a subdomain.** Charlie's call to
      me, 2026-08-18. Set up ONCE and attach the custom domain immediately —
      Chronoscape's two-Pages-projects mess came from doing this twice.
- [x] **V-Party gap: run the nuanced view to 2025 on hand-coding**, with a
      visible "hand-coded from here" marker at the source's coverage end.
      Charlie's call to me, 2026-08-18.

## D — data

- [x] D1. OWID fetch working, no key. `scripts/fetch_owid.py`.
- [x] D2. DPI 2023 pulled (CC-BY 4.0, 1975-**2023**, 183 countries) and diffed
      against the seed: 73% agree, 27% disagree, clustering on structural
      differences not noise. See `docs/seed-corrections.md`.
- [ ] D2b. Work through the Philippines / Colombia / South Korea disagreements.
      Personality-driven party systems — decide whether to defer to DPI or mark
      them contested on the site. Leaning: mark contested, it's more honest and
      more interesting.
- [ ] D3. Extend **2024-2026** by hand on the 1 January convention. DPI stops at
      2023 and this is the window people actually care about. Mark it as
      hand-coded wherever it renders.
- [ ] D4. V-Party v2 for the nuanced spectrum. Note it stops ~2019 — decide
      whether to show a truncated nuanced view or interpolate forward from the
      seed. **Do not silently interpolate.**
- [ ] D5. Manifesto Project API key + RILE for a continuous axis on the 67
      countries it covers.
- [ ] D6. CHES for the second (GAL-TAN) axis, Europe only.
- [x] D7. Population weights joined. All 183 DPI countries resolve to OWID
      entities via `config/country_map.yaml`; 8 historical states dropped.
- [ ] D8. One provenance record per series: source, version, retrieved date,
      licence, coverage end. Rendered on the site, not buried.

## B — build

- [x] B1. Pipeline built: `scripts/build_index.py` -> `data/out/orientation.json`.
- [x] B2. Group filter applied at build time. 232KB for all 8 groups; fine as one file.
- [x] B3. Both weightings emitted per group, plus a trailing 3-year MA on each.
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
