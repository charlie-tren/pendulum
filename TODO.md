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
- [~] D3. Hand-coding started: `data/seed/hand_coded.csv`, 18 rules covering
      2020-2023, each with a written basis and a verification date. World
      coverage 85% -> 89% of population; ASEAN 60% -> 75%.
- [ ] D3b. Extend to **2024-2026**, past DPI's end. Same file, same discipline.
- [ ] D3c. Second pass on the hand-coded rows — they are my calls, not
      sourced. Charlie should review the `basis` column before this ships.
- [x] D4. V-Party v2 wired in as a **fill layer**, not just a nuance layer.
      Answers "can we fill the grey band": yes. Uncoded population falls from
      ~25% to ~2% for 1975-2019. Residual is absolute monarchies and non-party
      military governments — a real answer, not a hole.
- [x] D4b. Party-name carry-forward past V-Party's 2019 end, where DPI still
      records the same party in power. Recovers Indonesia, Turkey, Uganda,
      Romania and others for 2020-2023.
- [x] **D4c. Coverage cliff handled.** Years below 80% resolved are hatched,
      labelled provisional, and the caption names the last solid year.
- [x] D4d. Party aliases added (`config/party_aliases.yaml`) — Bangladesh
      AL/BAL and Uzbekistan LDP/OLDP. Everything else inspected and rejected as
      a different party or a rename; those went to hand-coding instead.
- [x] D4e. **Split `uncoded` into `no_reading` and `unresolved`.** They are
      different claims. Saudi Arabia has no left-right reading because parties
      are banned; the Philippines' PFP because it is a self-described big tent.
      That is an answer. "We have no data" is not. Drawing them as one grey
      band conflated the two.
- [ ] D5. Manifesto Project API key + RILE for a continuous axis on the 67
      countries it covers.
- [ ] D6. CHES for the second (GAL-TAN) axis, Europe only.
- [x] D7. Population weights joined. All 183 DPI countries resolve to OWID
      entities via `config/country_map.yaml`; 8 historical states dropped.
- [x] D8a. Provenance emitted per group-year (`source` block: dpi / vparty /
      carry_forward / none) and rendered in the preview.
- [ ] D8. One provenance record per series: source, version, retrieved date,
      licence, coverage end. Rendered on the site, not buried.

## B — build

- [x] B1. Pipeline built: `scripts/build_index.py` -> `data/out/orientation.json`.
- [x] B2. Group filter applied at build time. 232KB for all 8 groups; fine as one file.
- [x] B3. Both weightings emitted per group, plus a trailing 3-year MA on each.
- [ ] B4. Tests on the aggregation maths. Weighted mean with missing countries
      is where this will silently go wrong.

## V — viz

- [x] V1. Stacked area, population-weighted, is the headline chart.
- [x] V2. Index line with trailing 3-year MA.
- [x] V3. Group toggle, 21 groups: World, six continents, G7, G20, EU, OECD,
      NATO, African Union, Arab League, BRICS+, ASEAN, Nordics, Anglosphere,
      Latin America, 20 most populous, and the original 15.
- [x] V4. Weighting toggle.
- [ ] V5. Spectrum toggle: 3-bucket (left/centre/right) vs the V-Party
      multi-dimensional view.
- [ ] V6. Map or cartogram, one year at a time, with a year scrubber.
- [ ] V7. Country detail on click: that country's own history as a strip.
- [x] V8. Deep links via hash; default state is never written. Verified.

## S — ship

- [x] S1. Opens on World, population-weighted.
- [ ] S2. Attribution page: V-Dem, OWID, DPI, Manifesto, CHES, with licences.
      CC-BY means naming them is an obligation, not a courtesy.
- [ ] S3. Methodology page — the 30-June rule, what 0 means, why the MA is
      trailing, what the seed data is and where it is judgement rather than source.
- [x] S4. Mobile verified at 375px: no horizontal scroll, all panels render,
      no console errors.
- [ ] S5. Link out to OWID's democracy page rather than reimplementing it.

## Parked

- Regime type (democracy/autocracy) as a *second* axis crossed with ideology —
  "how many people live under right-wing autocracies" is a better question than
  either axis alone. Parked only because it doubles the build.

## Frontend — next

- [ ] V6. Map or cartogram with a year scrubber.
- [x] V7. Country strip — every year since 1975 for one country, with a source
      bar underneath and party names in place. Defaults to the largest country
      in the selected group, so switching to the G7 lands on the United States.
- [x] V9. Ideology crossed with regime type. Mosaic with a year slider where
      block AREA is the share of people, plus small multiples over time. V-Dem
      Regimes of the World via OWID, codes confirmed against the dataset's own
      metadata rather than assumed.
- [ ] V10. The nuanced spectrum view. V-Party's continuous score is already
      carried through the pipeline as `score` but nothing renders it yet.
- [ ] S6. Dark mode is implemented via prefers-color-scheme but untested on a
      real dark display.

## Found while building the Wikidata layer

- [ ] **D9. Reconcile the DPI/Wikidata seam.** Wikidata calls the US Democratic
      Party `centrism` where DPI calls it `Left`, so the US appears to drift
      left-to-centre in 2024 with no election. Carry the DPI coding forward
      whenever the governing party has not actually changed. Documented in
      `docs/data-sources.md`.
- [ ] D10. The slider is capped at 2025 from `meta.regime_coverage_end`, but the
      political series runs to 2026. Decide whether the mosaic should show a
      2026 column with the regime axis marked unknown, or stay capped.
