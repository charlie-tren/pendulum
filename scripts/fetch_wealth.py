"""Fetch the wealth-inequality sources into data/raw/wealth/.

Four layers, because no single source covers the range. Each is a different
measurement and they are kept apart all the way through, exactly as
`no_reading` is kept apart from `unresolved` on the political side.

  1. deep          Wealth Gini from house floor areas. Fetched here from Kohler
                   et al. 2017, whose 63 sites run 9200 BC to AD 1970 and are
                   openly downloadable from Springer. The far bigger GINI
                   Project database that superseded it (47,000 houses) is NOT
                   fetchable: tDAR requires a free account, see TODO D8. Drop
                   that export at data/raw/wealth/gini_project.csv and
                   build_wealth.py prefers it over this one automatically.
  2. preindustrial Alfani / EINITE, taxable wealth from tax records, Europe
  3. industrial    Alfani and Schifano, 39 countries, every decade 1820-2010
  4. modern        WID via Our World in Data, annual, 226 entities

The Alfani files are xlsx, so this converts them to CSV on the way in and the
build stays stdlib-only. openpyxl is a fetch-time dependency the way pyreadr
already is for V-Party.

    python scripts/fetch_wealth.py
"""
from __future__ import annotations

import csv
import sys
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "wealth"

# OWID's Cloudflare 1010s a missing User-Agent. Alfani's WordPress host is
# happier with a browser-shaped one.
UA = "Mozilla/5.0 (compatible; pendulum/0.1; +https://charlietrenorden.com)"

OWID = "https://ourworldindata.org/grapher/{slug}.csv?v=1&csvType=full&useColumnShortNames=true"
OWID_SLUGS = [
    "wealth-share-richest-1-percent",    # WID, 1800-2024, 226 entities
    "wealth-share-richest-10-percent",   # WID, 1800-2024, 226 entities
]

ALFANI = "https://guidoalfani.eu/wp-content/uploads/{path}"
# name -> (path, sheet, the row that holds the column headings, 0-based)
ALFANI_FILES = {
    # Wealth Gini and quartile shares by English county, from the lay subsidies
    "england_counties":  ("2023/07/WealthInequality_England.xlsx", "Inequality_Counties", 2),
    # Wealth Gini and quartile shares by place, Piedmont
    "piedmont_places":   ("2023/07/Database_Alfani_Piedmont.xlsx", "Foglio1", 2),
    # Regional wealth Gini every fifty years, Italy and the Low Countries
    "regions_1500_1800": ("2023/07/Inequality_and_Inequality_Extraction_1500-1800.xlsx", "Figure3a", 0),
    # Wealth Gini and top-10% share by country, every decade
    # this one has no preamble, so its table starts on the first row
    "countries_1820_2010": ("2023/07/Wealth_Inequality_Alfani_Schifano.xlsx", "Data", 0),
}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


# Kohler et al. 2017, "Greater post-Neolithic wealth disparities in Eurasia than
# in North America and Mesoamerica", Nature 551. Supplementary Table 2 is the
# site-level Gini file, and Springer serves it without a login.
KOHLER = ("https://media.springernature.com/original/springer-static/esm/"
          "art%3A10.1038%2Fnature24646/MediaObjects/"
          "41586_2017_BFnature24646_MOESM3_ESM.xls")


def xls_to_csv(xls: Path, sheet: str, out: Path) -> int:
    """Legacy .xls, so xlrd rather than openpyxl. Fetch-time only."""
    import xlrd

    wb = xlrd.open_workbook(str(xls))
    ws = wb.sheet_by_name(sheet)
    head = [str(ws.cell_value(0, c)).strip() for c in range(ws.ncols)]
    body = []
    for r in range(1, ws.nrows):
        cells = []
        for c in range(ws.ncols):
            v = ws.cell_value(r, c)
            # xlrd hands back every number as a float, so a year comes out
            # "-9200.0" and a household count "106.0"
            if isinstance(v, float) and v == int(v):
                v = int(v)
            cells.append(str(v).strip())
        if any(cells):
            body.append(cells)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(body)
    return len(body)


def sheet_to_csv(xlsx: Path, sheet: str, header_row: int, out: Path) -> int:
    """Write one sheet out as CSV, starting at the real header row.

    Every one of these files opens with a couple of free-text lines describing
    the database before the table starts, so the header row is given per file
    rather than assumed to be the first.
    """
    import openpyxl

    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb[sheet]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()

    head = [str(c).strip() if c is not None else "" for c in rows[header_row]]
    # trailing unnamed columns are Excel's padding, not data
    while head and not head[-1]:
        head.pop()
    width = len(head)

    body = []
    for r in rows[header_row + 1:]:
        cells = ["" if c is None else str(c).strip() for c in r[:width]]
        if any(cells):
            body.append(cells)

    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(body)
    return len(body)


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    failed = []

    for slug in OWID_SLUGS:
        try:
            out = RAW / f"{slug}.csv"
            out.write_bytes(get(OWID.format(slug=slug)))
            n = sum(1 for _ in open(out, encoding="utf-8")) - 1
            print(f"  {out.name:44s} {n:>7,} rows")
        except Exception as err:                       # noqa: BLE001
            failed.append(f"{slug}: {err}")

    tmp = RAW / "_tmp.xlsx"
    for name, (path, sheet, header_row) in ALFANI_FILES.items():
        try:
            tmp.write_bytes(get(ALFANI.format(path=path)))
            out = RAW / f"alfani_{name}.csv"
            n = sheet_to_csv(tmp, sheet, header_row, out)
            print(f"  {out.name:44s} {n:>7,} rows")
        except Exception as err:                       # noqa: BLE001
            failed.append(f"{name}: {err}")
    try:
        tmp.write_bytes(get(KOHLER))
        out = RAW / "kohler2017_sites.csv"
        n = xls_to_csv(tmp, "Table 2 Data", out)
        print(f"  {out.name:44s} {n:>7,} rows")
    except Exception as err:                           # noqa: BLE001
        failed.append(f"kohler2017: {err}")
    tmp.unlink(missing_ok=True)

    bigger = RAW / "gini_project.csv"
    print(f"\n  the fuller GINI Project database: "
          f"{'present' if bigger.exists() else 'not present, see TODO D8'}")

    for line in failed:
        print(f"  FAILED {line}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
