# Seed data: coding convention and corrections

The seed series is the hand-coded 15-country sheet (`Elections.xlsx`,
1994-2025). It is retained, not discarded, because it covers 2023-2025 —
a window where DPI and V-Party have no data.

## Convention (was undefined; now fixed)

**A country's orientation for year Y is the orientation of the party of the
head of government on 30 June of year Y.**

Head of government, not head of state. Chosen because it is unambiguous,
reproducible by anyone, and resolves every transition-year edge case with one
rule. Codes: `+1` right-of-centre, `-1` left-of-centre, `0` centrist,
grand-coalition, technocratic, or national-unity.

Open question: semi-presidential systems (France, and to a degree Korea and
Colombia) where the president and PM can be from different camps. Currently
the rule says PM. Flag for review.

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
