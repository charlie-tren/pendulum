# Pendulum: Claude Code instructions

Read at the start of every session. Keep it short enough to actually be read.

## What this is

An interactive data-viz site showing how the world's governments have moved
along the political spectrum over time. The point of difference is that it
counts *people* under each kind of government, not just countries.

It is **not** an investment tool. It has no thesis. It is not connected to
Lighthouse or Parallax and must not import their framing. The job is to show
the data honestly and make it fun to poke at. If a change makes the site more
opinionated, it is the wrong change.

Live at https://charlietrenorden.com/pendulum/, served as a static
subdirectory of the charlie-tren.github.io repo. That is the convention every
other project on the site follows; an earlier plan for a Cloudflare Pages
subdomain was dropped once the repo made the actual pattern obvious.

To deploy: copy site/{index.html,style.css,app.js,logo.svg,orientation.json} into
charlie-tren.github.io/pendulum/ and push. Fetch first, other sessions push to
that repo constantly. The card thumbnail is shot automatically by that repo's
"Refresh card thumbnails" workflow, which Pendulum is registered with.

## The non-negotiables

1. **Never fabricate a data point.** If a source stops in 2019, the chart stops
   in 2019 or is visibly marked as extended by hand. No silent interpolation,
   no carrying the last value forward without saying so.
2. **Every series carries provenance**: source, version, retrieval date,
   licence and coverage end. All of it visible on the site.
3. **Judgement is labelled as judgement.** The seed 15-country series is
   Charlie's own coding. Where it is used, say so. Where sourced data exists,
   prefer it and show the disagreement rather than hiding it.
4. **Moving averages are trailing.** The original spreadsheet used a centred
   mean that peeked at t+1. Do not reintroduce it.
5. **CC-BY is a licence, not a suggestion.** V-Dem and OWID get named.
6. **Never renormalise away the uncoded band.** About a quarter of the world's
   population has no left-right code in DPI, concentrated in the Global South.
   Hiding it turns a Western-weighted sample into a claim about "the world".
   Worked example: ASEAN in 2023 is 18% coded, and the coded fraction is
   Vietnam and Laos, so a renormalised chart would report ASEAN as perfectly
   left-wing. Show the band.
7. **No empty first screen.** The site opens on the headline chart with a
   default already chosen. Never write the default state to the URL.
8. **Microcopy says what a control is for**, never narrates the mechanic.
   "One person, one vote" not "tap to switch weighting".
9. **No em dashes** anywhere, in the site copy or in these docs.
10. **Charts draw at container pixel scale**, never into a fixed viewBox scaled
   to fit. A fixed 960-wide viewBox rendered 11px axis labels at 3.5px on a
   phone. Every draw function measures its container and sets its own viewBox.
11. **Look at the page, do not only measure it.** The clipped "provisional"
   label survived a full round of DOM measurement and was obvious the moment
   the rendered image was viewed. Dark mode passed the same way before anyone
   saw that the greys were the brightest thing on the chart. Render locally
   with playwright and open the PNG; `scripts/logo_options.py` is the pattern.

## Coding convention for orientation

A country's orientation for year Y is that of the chief executive's party on
**1 January of year Y**. That is DPI's documented convention and we follow it
rather than invent our own. In semi-presidential systems DPI codes the **head of
state**, not the PM. `+1` right, `-1` left, `0` centrist.

`uncoded` is a separate category and must never be folded into `0`. DPI's
codebook defines its own `0` as "No information", which is a different claim
from "centrist". Full reasoning: `docs/seed-corrections.md`.

## Layout

```
/config/      country_groups.yaml and friends. Hand-maintained, small.
/data/seed/   Charlie's hand-coded 15-country series, 1994-2025. Committed.
/data/raw/    Fetched source data. Gitignored. Regenerate with scripts/.
/data/out/    Built JSON the site reads. Committed.
/scripts/     Fetch and build. Python, stdlib-first.
/site/        Static frontend. No JS build step.
/docs/        data-sources.md, seed-corrections.md.
```

## Type

Headings use **Spectral 600** via `--font-display` in `style.css`. It is the
serif charlietrenorden.com already loads, so this adds no new family to the
site and is usually cached before anyone arrives. The homepage is serif-led at
weight 400 with italic accents; a bold system sans here read as a different
site. Body text and all UI stay on the system sans stack, which suits a tool.

`scripts/title_options.py` renders twelve candidates against the mark and the
standfirst. Changing the title face is one line in `--font-display`.

## Stack

Python for the pipeline, plain static HTML/CSS/JS for the site. No JS
toolchain. Same call as Chronoscape, for the same reason: this has to still
build in two years without a dependency archaeology session. If a chart
library is needed, vendor one file rather than adding npm.

## Working notes

- `python scripts/fetch_owid.py` refreshes OWID data. No key needed, but the
  User-Agent header is mandatory or Cloudflare returns 1010.
- Read `TODO.md` before starting. It is ordered.
- Data licences and coverage end-dates are in `docs/data-sources.md`. Check
  the coverage end before promising a chart runs to the present.
