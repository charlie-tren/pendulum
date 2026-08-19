# TODO

Ordered. `D` = data, `B` = build, `V` = viz, `S` = ship.

## Blocking

- [x] **Name the project.** Pendulum.
- [x] **Deployment target: Cloudflare Pages on a subdomain.** Charlie's call to
      me, 2026-08-18. Set up ONCE and attach the custom domain immediately -
      Chronoscape's two-Pages-projects mess came from doing this twice.
- [x] **V-Party gap: run the nuanced view to 2025 on hand-coding**, with a
      visible "hand-coded from here" marker at the source's coverage end.
      Charlie's call to me, 2026-08-18.

## D, data

- [x] D1. OWID fetch working, no key. `scripts/fetch_owid.py`.
- [x] D2. DPI 2023 pulled (CC-BY 4.0, 1975-**2023**, 183 countries) and diffed
      against the seed: 73% agree, 27% disagree, clustering on structural
      differences not noise. See `docs/seed-corrections.md`.
- [ ] D2b. Work through the Philippines / Colombia / South Korea disagreements.
      Personality-driven party systems, decide whether to defer to DPI or mark
      them contested on the site. Leaning: mark contested, it's more honest and
      more interesting.
- [~] D3. Hand-coding started: `data/seed/hand_coded.csv`, 18 rules covering
      2020-2023, each with a written basis and a verification date. World
      coverage 85% -> 89% of population; ASEAN 60% -> 75%.
- [x] D3b. DONE. 2024-2026 hand-coded for the largest unresolved countries.
- [ ] D3c. Second pass on the hand-coded rows, they are my calls, not
      sourced. Charlie should review the `basis` column before this ships.
- [x] D4. V-Party v2 wired in as a **fill layer**, not just a nuance layer.
      Answers "can we fill the grey band": yes. Uncoded population falls from
      ~25% to ~2% for 1975-2019. Residual is absolute monarchies and non-party
      military governments, a real answer, not a hole.
- [x] D4b. Party-name carry-forward past V-Party's 2019 end, where DPI still
      records the same party in power. Recovers Indonesia, Turkey, Uganda,
      Romania and others for 2020-2023.
- [x] **D4c. Coverage cliff handled.** Years below 80% resolved are hatched,
      labelled provisional, and the caption names the last solid year.
- [x] D4d. Party aliases added (`config/party_aliases.yaml`), Bangladesh
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

## B, build

- [x] B1. Pipeline built: `scripts/build_index.py` -> `data/out/orientation.json`.
- [x] B2. Group filter applied at build time. 232KB for all 8 groups; fine as one file.
- [x] B3. Both weightings emitted per group, plus a trailing 3-year MA on each.
- [ ] B4. Tests on the aggregation maths. Weighted mean with missing countries
      is where this will silently go wrong.

## V, viz

- [x] V1. Stacked area, population-weighted, is the headline chart.
- [x] V2. Index line with trailing 3-year MA.
- [x] V3. Group toggle, 21 groups: World, six continents, G7, G20, EU, OECD,
      NATO, African Union, Arab League, BRICS+, ASEAN, Nordics, Anglosphere,
      Latin America, 20 most populous, and the original 15.
- [x] V4. Weighting toggle.
- [x] V5. DONE differently: the two live as separate panels, and the spectrum obeys
      multi-dimensional view.
- [x] V6. Map with a year scrubber. DONE.
- [x] V7. SUPERSEDED, the country strip was built and then removed on request.
- [x] V8. Deep links via hash; default state is never written. Verified.

## S, ship

- [x] S1. Opens on World, population-weighted.
- [x] S2. SUPERSEDED by the Sources panel, which links each source with a line of
      CC-BY means naming them is an obligation, not a courtesy.
- [x] S3. SUPERSEDED by the Notes on the Data panel. The 30-June rule is itself
      trailing, what the seed data is and where it is judgement rather than source.
- [x] S4. Mobile verified at 375px: no horizontal scroll, all panels render,
      no console errors.
- [ ] S5. Link out to OWID's democracy page rather than reimplementing it.

## Parked

- Regime type (democracy/autocracy) as a *second* axis crossed with ideology -
  "how many people live under right-wing autocracies" is a better question than
  either axis alone. Parked only because it doubles the build.

## Frontend, next

- [x] V6. Duplicate of the V-block entry. DONE.
- [x] V7. Country strip, every year since 1975 for one country, with a source
      bar underneath and party names in place. Defaults to the largest country
      in the selected group, so switching to the G7 lands on the United States.
- [x] V9. Ideology crossed with regime type. Mosaic with a year slider where
      block AREA is the share of people, plus small multiples over time. V-Dem
      Regimes of the World via OWID, codes confirmed against the dataset's own
      metadata rather than assumed.
- [x] V10. DONE as The Full Spectrum, on V-Party's ordinal rather than the raw score:
      carried through the pipeline as `score` but nothing renders it yet.
- [x] S6. DONE. Looked at in a real render; the greys were lifted clear of the panel.
      real dark display.

## Found while building the Wikidata layer

- [x] **D9. DONE.** `scripts/audit_hand_coded.py` flags any hand-coded row that
      Party `centrism` where DPI calls it `Left`, so the US appears to drift
      left-to-centre in 2024 with no election. Carry the DPI coding forward
      whenever the governing party has not actually changed. Documented in
      `docs/data-sources.md`.
- [x] D10. DONE. Both scrubbers cap at and open on the regime coverage end, so
      political series runs to 2026. Decide whether the mosaic should show a
      2026 column with the regime axis marked unknown, or stay capped.

## Design pass, 2026-08-19

- [x] Charts draw at container pixel scale. Axis text was rendering at an
      effective 3.5px on a phone.
- [x] Small multiples wrap to 2x2 below 560px.
- [x] aria-label and SVG title on all six charts. There were none.
- [x] Legends repeated beside the mosaic and the country strip.
- [x] Lead panel promoted, provenance panel demoted.
- [x] Loading state, favicon, contrast fix, em dashes removed.
- [x] Provisional label right-aligned; it was clipping to "provision".
- [x] Dark mode looked at, in a real render. The two greys were the brightest
      thing on the chart, putting the emphasis on the categories that matter
      least. Palette entries now take an optional `colour_dark`.
- [x] DONE. It follows the pointer. Was:
      band sits in most years. Consider following the pointer instead.
- [x] MIS-SCOPED. Charlie curates the panel set directly now. Was:
      provenance and small-multiples panels earn their place above the fold.

## Identity, 2026-08-19

- [x] Logo: a Newton's cradle with left blue, centre purple, right red. Chosen
      from eight rendered candidates, on the basis that it stays legible at
      16px, which 3, 4 and 8 did not. `scripts/logo_options.py` regenerates the
      contact sheet if it needs revisiting.
- [x] "Other projects" bar, matching the other project pages.
- [x] Card moved to the in-progress group with a one-line description.

- [x] Title typeface. Was a bold system sans, which belonged to a different
      site: charlietrenorden.com is serif-led. Now Spectral 600 on headings via
      `--font-display`, chosen from twelve rendered candidates.
      `scripts/title_options.py` regenerates the sheet.

## Round of feedback, 2026-08-19

- [x] "Other projects" moved to the top right.
- [x] Standfirst cut to one line.
- [x] Chart and section titles shortened.
- [x] Balance chart carries colour: filled blue below the zero line, red above.
- [x] Heading treatment made uniform; panel-lead and panel-quiet variants dropped.
- [x] Small multiples replaced by one full-width chart with regime tabs, sharing
      a y scale across tabs so switching compares like with like.
- [x] "One country at a time" section removed.
- [x] Notes section rewritten less chattily.
- [x] DONE. Dropped from the build; payload fell from 1.13MB to 944KB. Was:
      nothing reads them now that the country strip is gone. Worth dropping
      from the build, or bringing the section back in a better form.

## Feedback round, 2026-08-19 (second)

- [x] Controls aligned; flex-end had bottom-aligned two controls of different heights.
- [x] Centre colour made more saturated so it separates from blue.
- [x] Regimes panel has its own key.
- [x] Sources are links with a line of context each.
- [x] Both lines on the balance chart are now named in the copy.
- [x] Mosaic description removed.
- [x] Standfirst rewritten.
- [x] **2024-2026 coverage taken from 50% to 80% of world population** by
      hand-coding the largest unresolved countries. The 2026 world mean moved
      from +0.44 to +0.05: the apparent swing right was the missing countries.
- [ ] 92 countries are still unresolved for 2024-2026, but they carry only about
      a fifth of world population between them. Diminishing returns from here.
- [x] `countries` and `members` dropped from the build. Payload 1.13MB -> 944KB.
- [x] Readout follows the pointer instead of parking over the right-hand band.

## Map round, 2026-08-19

- [x] World map with a year scrubber, sharing state with the mosaic.
- [x] Geometry projected at build time; no mapping library on the site.
- [x] Non-party states reclassified from "no data" to "does not apply". Nine
      rows covering the Gulf monarchies, Brunei, Eswatini, Jordan, Belarus,
      South Sudan and pre-2008 Bhutan.
- [x] Original 15 and 20 most populous dropped from the selector.
- [x] Source key entries explain themselves on hover.
- [ ] 48 countries are still unresolved for 2026, though they hold about a fifth
      of world population. Serbia and Montenegro are absent from DPI entirely,
      so they have no row at all and can never be hand-filled without seeding
      the entity first.

## Map follow-up, 2026-08-19

- [x] Map scrolls inside its own box below 700px; it was 135px tall on a phone.
- [x] Dark-mode greys lifted clear of the panel colour; unresolved countries
      read as holes in the map before.
- [x] `scripts/audit_hand_coded.py` flags hand-coded rows that contradict DPI's
      own coding of the same continuing party. It caught Russia, where a
      hand-coded "right" for 2024 disagreed with DPI's Center through 2023 and
      put a step in the series that no election produced.
- [x] DONE via `config/seed_entities.yaml`. Both resolve 2006-2026. Was:
      `extend_years` has nothing to extend. Filling them means seeding the
      entities before the resolver runs.

## Seeding and the finer spectrum, 2026-08-19

- [x] `config/seed_entities.yaml` creates rows for sovereign states no source in
      the chain introduces. Serbia and Montenegro were the only two: both had
      V-Party and Wikidata records and still rendered as "no data" for every
      year, because the resolver can only fill a row that already exists.
      Palestine, Puerto Rico, Western Sahara, New Caledonia, Greenland and the
      Falklands also have geometry and no row, and are excluded on purpose.
- [x] Serbia and Montenegro fully resolved 2006 to 2026, mostly from V-Party and
      Wikidata, with four hand-coded rows closing the tail.
- [x] Seven-point spectrum panel from V-Party's own ordinal, read directly from
      the source rather than through the resolution chain. In the chain V-Party
      only fills what DPI leaves blank, so taking the score from there would
      describe a quarter of the world and call it the spectrum. Coverage is
      93-99% of population and it stops at 2019 where V-Party does.
- [x] DONE. It obeys the toggle at the top of the page rather than carrying its own.
      population-weighted only at the moment.

- [x] Spectrum panel obeys the weighting toggle at the top rather than carrying
      its own. Right is 32% by population and 11% by country, so the toggle
      earns its place here.
- [x] Play button on both year scrubbers, driving the shared year.
- [ ] The USSR shows as "no data" across the map for 1975 to 1991. DPI has rows
      for it but they are dropped, because no modern OWID population series
      exists for a state that no longer exists. Deciding what a world map should
      show for a dissolved country is a design question, not a data one.

## Copy and interaction round, 2026-08-19

- [x] Hatching removed entirely, along with the coverage caption. 80% coverage
      is sound data and marking it provisional read as a disclaimer.
- [x] Headline caption now states a fact rather than explaining the method.
- [x] Regime names explain themselves on hover, on the tabs and in a key under
      the mosaic.
- [x] Spectrum chart is hoverable, showing the year and the full breakdown.
- [x] Panels retitled: "The world, year by year" and "Seven points, not three".
- [x] Notes cut from four entries to three and roughly halved.
- [x] Scrollbars hidden on the sideways-scrolling map.
- [x] Boot catch no longer reports a load failure when the failure was in render.
