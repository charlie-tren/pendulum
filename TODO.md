# TODO

## Needs Charlie

Six open. D5, D6, D10 and S6 are parked on a decision or a free account, not on
work. D7 is real unbuilt scope. V6 is live copy he has already rejected, so it
is the one worth doing first.

- [ ] **D5. Manifesto Project.** Needs a free account for the API key, which is
      not mine to create. Register at https://manifesto-project.wzb.eu and I
      will wire it in. It would give a continuous left-right axis back to 1945
      for the 67 countries it covers, which is a better spine for the older
      decades than anything currently in use.
- [ ] **D6. CHES.** Data is downloaded and sitting in `data/raw/ches_trend.csv`
      (1999-2024, seven waves, 28 countries, with `lrgen` and `galtan`), but I
      stopped short of building it. It covers a tenth of world population and
      does not say which party governs, so it is a Europe-only second axis
      rather than a data fill. Your call whether that is worth having.
- [ ] **D7. Subnational: Australia, the United States, Germany** (asked
      2026-08-19). Add a level below the country, so the map and the charts can
      resolve states rather than only national governments. The three named are
      the right three to start with: all federal, all with a long unbroken
      record of who held each state, and between them they cover a two-party
      case, a fifty-unit case and a coalition case.
      **What each needs, and why they are not the same job:**
      - **Australia** - 6 states + 2 territories. Premiers map to Labor / Liberal
        / LNP / CLP almost mechanically, so this is close to pure hand-coding and
        is the one to build first as the proof.
      - **United States** - 50 states. Governor plus legislative control are both
        well documented year by year, but they disagree often enough that the
        first decision is *which one the colour means*. Pendulum codes the chief
        executive nationally, so the governor is the consistent choice, with
        legislative control as a possible second layer.
      - **Germany** - 16 Länder, and the hard one. Almost every Land is governed
        by a coalition, so a single left / right reading needs a rule for who
        leads it, and that rule has to be written down the way the national
        conventions already are in `CLAUDE.md`.
      **Open questions before any of it is worth building:** the population
      weighting needs subnational population per year, not just national; the map
      needs state geometry, which Natural Earth has at 1:110m for admin-1 but at
      a size worth checking before committing; and the year slider has to mean
      the same thing at both levels. Scope this properly before writing code -
      it is a second data model, not a wider version of the current one.
- [x] ~~**D8. An inequality section, wealth-first**~~ - **BUILT AND LIVE
      2026-08-22/23** at https://charlietrenorden.com/inequality/. Verified live:
      the payload spans -9200 to 2024 and carries all four layers.
      Three of the four layers shipped from open sources. The fourth, the
      archaeology, did NOT need the tDAR account after all: Kohler et al. 2017,
      Nature 551, is the published precursor and Springer serves its
      supplementary table with no login. 63 sites, 9200 BC to AD 1970. See D10
      for the upgrade path.
- [x] ~~**D9. Two more charts from data already in the payload**~~ - PART DONE,
      PART REVERSED, 2026-08-22/23.
      **Inequality by Size of Settlement** is live, cut by Kohler's camp /
      village / town / city classification rather than his five-step political
      taxonomy: the words need no glossary and the medians are monotonic where
      the political cut has a flat spot. Village 0.24, town 0.28, city 0.38.
      **Two Hemispheres** was built and then removed on Charlie's call.
      **Cities and Countryside in Piedmont** was built as a third, testing the
      settlement-size claim against the tax records, and also removed on his
      call. Worth knowing what it showed if it is ever revived: the towns run
      about 0.07 above the countryside from 1500 to 1700 and then the gap closes
      and reverses by 1800. The roll-up rows it needed are in
      `alfani_piedmont_places.csv` as "Piedmont (cities only)" and
      "(rural areas only)".

- [ ] **D10. The fuller GINI Project database.** The page currently runs on
      Kohler et al. 2017: 63 sites. The successor is 47,000 houses at 1,100+
      sites, 10500 BC to AD 1980, and `build_wealth.py` already prefers it the
      moment the file exists at `data/raw/wealth/gini_project.csv`.
      **Needs Charlie:** tDAR requires a free account, which is not mine to
      create. https://core.tdar.org/project/496853

- [ ] **S6. Decide whether `charlie-tren/pendulum` goes public.** The footer on
      both pages said "Built from open data. Code and data." and linked to this
      repo, which is PRIVATE while the site is public, so it was a 404 for every
      visitor. The link is removed rather than left broken. If the repo goes
      public the link goes straight back; if not, it stays off. Charlie's call.

- [ ] **V6. Pick a standfirst for the inequality page.** Twenty options were
      given on 23/08/2026, grouped by angle. The page currently carries "How
      unevenly wealth has been held, as far back as anything survives to measure
      it.", which he has said he does not like, so this is live copy he has
      already rejected. Recommended: "It has fallen twice in eleven thousand
      years. Once after the Black Death, once after 1940." Both halves are in
      the data: the tax-register median runs 0.78 in the 1280s to 0.61 in the
      century after the plague, and the modern top-tenth share goes 77% in 1940
      to 61% by 1980. The dates are the data; the causes are Alfani's and
      Scheidel's argument, not something this page demonstrates.

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
- [x] D2b. Reframed by measurement. The contested cases are not three countries:
      DPI and V-Party disagree on 34% of the 3,885 country-years where both have
      an opinion, worst in Luxembourg, Malta, Belgium and the Netherlands, and DPI
      reads the world further left because it barely uses its centre bucket. The
      agreement rate is now computed in the build and stated on the site. Was:
      Personality-driven party systems, decide whether to defer to DPI or mark
      them contested on the site. Leaning: mark contested, it's more honest and
      more interesting.
- [x] D3. DONE and long since past the state described here. `hand_coded.csv` now
      carries 93 rules spanning 1975 to 2026, each with a written basis and a
      verification date, checked against DPI in the test suite. Was: 18 rules
      covering 2020-2023.
- [x] D3b. DONE. 2024-2026 hand-coded for the largest unresolved countries.
- [x] D3c. Hand-coded rows now carry a written basis and date each, are checked
      against DPI by `scripts/audit_hand_coded.py` in the test suite, and the
      Sources panel says what share of country-years rests on them. Was:
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
- [x] D7. Population weights joined. All 183 DPI countries resolve to OWID
      entities via `config/country_map.yaml`; 8 historical states dropped.
- [x] D8a. Provenance emitted per group-year (`source` block: dpi / vparty /
      carry_forward / none) and rendered in the preview.
- [x] D8. `config/sources.yaml` carries publisher, licence, retrieval date,
      coverage and role for all seven sources, rendered in the Sources panel. Was:
      licence, coverage end. Rendered on the site, not buried.

## B, build

- [x] B1. Pipeline built: `scripts/build_index.py` -> `data/out/orientation.json`.
- [x] B2. Group filter applied at build time. 232KB for all 8 groups; fine as one file.
- [x] B3. Both weightings emitted per group, plus a trailing 3-year MA on each.
- [x] B4. `tests/test_aggregate.py`, 15 tests. Caught a real double-count on its
      first run: DPI carries both Swaziland and eSwatini, overlapping in 2019-20.
      Was:
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
- [x] S5. Linked from the Sources panel.

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
- [x] Largely closed. 47-50 countries remain unresolved for 2024-2026 but they
      carry only 2.6-2.9% of world population between them. Was:
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
- [x] Superseded by the line above; the fifth-of-population figure was stale. Was:
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
- [x] DONE. The Soviet, Yugoslav and Czechoslovak territories are coded from DPI's
      own reading of the unions that governed them, and Russia is seeded for
      1975-1991. The 1975 weighting went from 3.90bn to 4.05bn against an actual
      world of 4.07bn. Was:
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
