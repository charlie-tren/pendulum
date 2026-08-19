# Pendulum

How the world's governments have moved along the political spectrum since the
1970s, and how many people live under each kind of government.

Most charts of global politics count countries. Counting countries makes
Tuvalu equal to India. This one lets you switch between **one country, one
vote** and **one person, one vote**, and the two tell noticeably different
stories.

## Status

Early. Data pipeline works end to end against Our World in Data; the
left-right spine and the frontend are not built yet. See `TODO.md`.

## Data

Built on open data, V-Dem, Our World in Data, the IDB's Database of Political
Institutions, the Manifesto Project, and the Chapel Hill Expert Survey.
Coverage, versions and licences are catalogued in `docs/data-sources.md`.

The 15-country series in `data/seed/` is hand-coded and is clearly marked as
such wherever it appears. Its coding convention and known corrections are in
`docs/seed-corrections.md`.

## Running it

```bash
python scripts/fetch_owid.py
```

No API key required.
