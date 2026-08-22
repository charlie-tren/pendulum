"""Ground-truth audit: check the built data against governments we know.

The aggregate tests prove the maths is self-consistent. They cannot tell you the
answer is TRUE - every one of them passed while the US sat at centre through
Biden's second term, and while V-Party had Japan governed by the LDP a year
before it won. This asks a different question: for country-years where the
answer is not in doubt, does the site say the right thing?

    python scripts/audit_ground_truth.py            # run the checks
    python scripts/audit_ground_truth.py JPN CHL    # and print those timelines

Known accepted mismatch: Japan 2010-2011 reads centre, not left. That is
V-Party's rating of the DPJ, which is commonly described as centrist, so the
expectation below is the arguable one rather than the data.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
D = json.load(open(ROOT/"data/out/orientation.json", encoding="utf-8"))
M = D["map"]; Y0 = M["year0"]
LET = {"l":"left","c":"centre","r":"right","n":"no_reading","u":"unresolved"}

def at(iso, y):
    row = M["codes"].get(iso)
    if not row: return "MISSING-COUNTRY"
    i = y - Y0
    return LET.get(row[i], "?") if 0 <= i < len(row) else "OUT-OF-RANGE"

def timeline(iso, a, b):
    return " ".join(f"{y}:{at(iso,y)[0]}" for y in range(a, b+1))

# (iso, year, expected, what actually happened)
CHECKS = [
 # --- Anglosphere, where the party's own label is unambiguous ---
 ("GBR",1980,"right","Thatcher, Conservative"),
 ("GBR",1998,"left","Blair, Labour"),
 ("GBR",2012,"right","Cameron, Conservative"),
 ("GBR",2025,"left","Starmer, Labour, won July 2024"),
 ("USA",1985,"right","Reagan, Republican"),
 ("USA",1995,"left","Clinton, Democrat"),
 ("USA",2005,"right","Bush, Republican"),
 ("USA",2015,"left","Obama, Democrat"),
 ("USA",2019,"right","Trump, Republican"),
 ("USA",2022,"left","Biden, Democrat"),
 ("USA",2026,"right","Trump, inaugurated Jan 2025"),
 ("AUS",1990,"left","Hawke, Labor"),
 ("AUS",2000,"right","Howard, Liberal"),
 ("AUS",2010,"left","Rudd/Gillard, Labor"),
 ("AUS",2018,"right","Turnbull/Morrison, Liberal"),
 ("AUS",2023,"left","Albanese, Labor, won May 2022"),
 ("CAN",2010,"right","Harper, Conservative"),
 ("CAN",2020,"left","Trudeau, Liberal"),
 ("NZL",2005,"left","Clark, Labour"),
 ("NZL",2015,"right","Key, National"),
 # --- Europe ---
 ("FRA",1990,"left","Mitterrand, PS"),
 ("FRA",2005,"right","Chirac, UMP"),
 ("FRA",2013,"left","Hollande, PS"),
 ("DEU",1985,"right","Kohl, CDU"),
 ("DEU",2000,"left","Schroeder, SPD"),
 ("DEU",2010,"right","Merkel, CDU"),
 ("DEU",2022,"left","Scholz, SPD, took office Dec 2021"),
 ("ESP",1990,"left","Gonzalez, PSOE"),
 ("ESP",2000,"right","Aznar, PP"),
 ("ESP",2010,"left","Zapatero, PSOE"),
 ("ITA",2003,"right","Berlusconi"),
 ("SWE",1990,"left","Carlsson, Social Democrats"),
 ("POL",2010,"right","Tusk/Kaczynski era, PO"),
 # --- Latin America ---
 ("VEN",2005,"left","Chavez"),
 ("BRA",2005,"left","Lula, PT"),
 ("BRA",2020,"right","Bolsonaro"),
 ("BRA",2024,"left","Lula, took office Jan 2023"),
 ("ARG",2010,"left","Cristina Kirchner"),
 ("ARG",2018,"right","Macri"),
 ("CHL",1995,"left","Frei, Concertacion"),
 ("CUB",1990,"left","Castro, Communist Party"),
 # --- Asia ---
 ("CHN",1990,"left","Communist Party"),
 ("CHN",2020,"left","Communist Party"),
 ("IND",1990,"left","Congress"),
 ("IND",2020,"right","Modi, BJP"),
 ("JPN",2000,"right","LDP"),
 ("JPN",2011,"left","DPJ, in office 2009-2012"),
 ("KOR",2020,"left","Moon Jae-in"),
 ("VNM",2000,"left","Communist Party"),
 # --- former USSR / Eastern bloc ---
 ("RUS",1985,"left","Soviet Union, CPSU"),
 ("POL",1985,"left","Polish United Workers' Party"),
 # --- Africa ---
 ("ZAF",2000,"left","ANC, Mbeki"),
 ("ZAF",2020,"left","ANC, Ramaphosa"),
 # --- absolute monarchies: the axis should not apply ---
 ("SAU",2000,"no_reading","absolute monarchy, no parties"),
 ("SAU",2020,"no_reading","absolute monarchy, no parties"),
 ("OMN",2010,"no_reading","absolute monarchy"),
 ("QAT",2010,"no_reading","absolute monarchy"),
 ("ARE",2010,"no_reading","federation of monarchies"),
]

bad = []
for iso, y, exp, why in CHECKS:
    got = at(iso, y)
    if got != exp:
        bad.append((iso, y, exp, got, why))
print(f"{len(CHECKS)} ground-truth checks, {len(bad)} mismatches\n")
for iso, y, exp, got, why in bad:
    print(f"  {iso} {y}: expected {exp:11s} got {got:11s}   ({why})")
if len(sys.argv) > 1:
    for iso in sys.argv[1:]:
        print(f"\n{iso}: {timeline(iso, 1975, 2026)}")
