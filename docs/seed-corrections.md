# Seed data: coding convention and corrections

The seed series is the hand-coded 15-country sheet (`Elections.xlsx`,
1994-2025). It is retained, not discarded, because it covers **2024-2025** —
past the end of DPI (2023) and five years past V-Party (~2019).

## Convention (was undefined; now aligned to the source)

**A country's orientation for year Y is that of the chief executive's party on
1 January of year Y.**

This was originally set to 30 June, which was my own invention. It has been
changed to 1 January to match DPI, whose codebook states verbatim: *"Data refer
to January 1 of each year."* Never fight the spine dataset over a convention it
already documents.

Semi-presidential systems: DPI codes the **head of state**, not the prime
minister. Evidenced by France 1997, where DPI records RPR (Chirac, President)
while the seed recorded Jospin (PS, PM). The open question from the previous
version is therefore closed — follow DPI and code the president.

Codes: `+1` right-of-centre, `-1` left-of-centre, `0` centrist. Note this is
**not** the same as DPI's `0`, which the codebook defines as *"No information"*.
Those become `uncoded` in the pipeline and are never folded into centre.

DPI's own criteria, quoted: Right for *"parties that are defined as
conservative, Christian democratic, or right-wing"*; Left for *"communist,
socialist, social democratic, or left-wing"*.

## Corrections applied — verified this session

| Country | Year | Was | Now | Evidence |
|---|---|---|---|---|
| Japan | 2024 | -1 | +1 | LDP governed throughout (Kishida, then Ishiba from Oct). |
| Japan | 2025 | -1 | +1 | LDP throughout; Ishiba to 21 Oct, then Takaichi, a hardline conservative. |
| France | 2025 | -1 | 0 | Bayrou (MoDem, centrist) at 30 June; hung parliament, Lecornu from Sept. Nothing left-wing governed France in 2025. |
| Spain | 2015 | 0 | +1 | Rajoy (PP) governed all of 2015. The inconclusive Dec 2015 election did not change the mid-year position. |

Effect on the aggregate: 2024 moves from -0.13 to **0.00**, 2025 from -0.13 to
**+0.07**. The apparent leftward swing at the end of the original series was
substantially a coding error, not a finding.

## Flagged, NOT yet corrected — needs systematic revalidation

These look wrong under the 30-June convention but were not verified against a
source this session, so they stand until checked:

- **USA 2001** coded `-1`. Bush was inaugurated in January 2001. Note the sheet
  codes Trump's 2017 inauguration as `+1` immediately, so it is internally
  inconsistent whichever convention is intended.
- **France 2001** coded `+1`. Jospin (PS) was PM until May 2002.
- The whole **France** column, pending the semi-presidential rule above.

The real fix is not hand-patching. It is to rebuild 1975-2022 from DPI, diff it
against this sheet, and investigate every disagreement. That is TODO D2.

## Moving average

The original `R` column was a **centred** 3-year mean
(`R3 = AVERAGE(Q2:Q4)`, i.e. using year t+1). Rebuilt as **trailing**
(`t-2, t-1, t`) in `data/seed/charlie_index_wide.csv`. 1994 and 1995 are now
blank rather than fabricated.

## Diff against DPI — run 2026-08-18

Over the 350 country-years where both the seed and DPI carry a code:
**73% agree, 27% disagree.** A further 100 country-years have a seed code but
no DPI code at all.

Disagreements by country: Philippines 24, Germany 14, South Korea 13,
France 11, Italy 10, Colombia 6, then single figures elsewhere. They are not
random noise — they cluster on structural differences:

- **France** — head of state vs head of government (now resolved in DPI's favour).
- **Germany** — the seed codes grand coalitions `0`; DPI codes the Chancellor's
  own party. Both defensible; they answer different questions.
- **Philippines, Colombia, South Korea** — party systems built around
  personalities rather than stable ideological blocs. Genuinely contested.
- **Transition years** generally, from the 30 June vs 1 January gap.

DPI has no code for Indonesia (30 country-years), Thailand (23), Colombia (16),
Japan (11) or Italy (11) within the seed window.
