"""The three pages against the three scripts that drive them.

WHY THIS FILE EXISTS. On 23/09/2026 a line reading "Built from open data" was
removed from all three pages. On Pendulum it lived inside a <footer> that also
held <ul id="sources">, so taking the line took the list. `app.js` then threw
on `$("#sources").innerHTML` - and that write sat ABOVE the line that removes
`body.loading`, so every chart on the page stayed hidden and the page read
"Loading the data" for eight hours. Nothing failed. The data files were served
200, the stylesheet was fine, the suite was green, and the only evidence was one
console message on a page nobody had open.

Two things are checked here, and between them they close that hole:

  * every element id a script writes to exists in the page it runs in, so a
    deleted block cannot silently orphan the code that filled it, and
  * the page is unhidden and drawn BEFORE the optional furniture, so a write
    that does fail cannot take the charts with it.

    python -m pytest tests/test_pages.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# script, page, and the call that unhides that page
PAGES = [
    ("site/app.js", "site/index.html"),
    ("site/inequality/app.js", "site/inequality/index.html"),
    ("site/polarisation/app.js", "site/polarisation/index.html"),
]

# every way these scripts reach for an element by id
QUERY = re.compile(
    r'\$\("#([\w-]+)"\)'
    r'|getElementById\("([\w-]+)"\)'
    r'|querySelector\("#([\w-]+)"\)'
)


def ids_queried(src: str) -> set[str]:
    return {m for hit in QUERY.findall(src) for m in hit if m}


def ids_declared(html: str) -> set[str]:
    return set(re.findall(r'\bid="([\w-]+)"', html))


@pytest.mark.parametrize("js,html", PAGES, ids=lambda p: Path(p).parent.name or "pendulum")
def test_every_id_a_script_reaches_for_exists_in_its_page(js, html):
    """NO EXEMPTION LIST, deliberately. A null-guarded write to an element that
    no longer exists is dead code wearing a seatbelt, and a list of allowed
    absences here cannot tell that apart from the absence that took the page
    down. If a panel goes, the code that filled it goes in the same commit."""
    missing = ids_queried((ROOT / js).read_text(encoding="utf-8")) \
        - ids_declared((ROOT / html).read_text(encoding="utf-8"))
    assert not missing, (
        f"{js} writes to elements {sorted(missing)} that {html} does not have")


def touches_dom(body: str) -> bool:
    return bool(QUERY.search(body))


def dom_functions(src: str) -> set[str]:
    """Top-level functions whose body reaches for an element by id, so calling
    one can throw on a null."""
    out = set()
    for m in re.finditer(r"^function ([\w$]+)\(", src, re.M):
        start = m.end()
        nxt = re.search(r"^function [\w$]+\(", src[start:], re.M)
        body = src[start:start + (nxt.start() if nxt else len(src))]
        if touches_dom(body):
            out.add(m.group(1))
    return out


@pytest.mark.parametrize("js,html", PAGES, ids=lambda p: Path(p).parent.name or "pendulum")
def test_the_page_is_unhidden_before_anything_can_throw(js, html):
    """`body.loading` puts `display: none` on every panel, so whatever removes
    it has to run before anything that might fail. The order is the entire
    defence: with it, a broken caption costs a caption; without it, a broken
    caption costs the page, which is what it cost.

    Measured inside the BOOT BLOCK rather than over the whole file, because a
    function that writes to the DOM is usually DEFINED above the boot and
    CALLED after it - reading the file top to bottom gets that backwards."""
    src = (ROOT / js).read_text(encoding="utf-8")
    boot = src[src.rindex("fetch("):]
    assert 'classList.remove("loading")' in boot, f"{js} never unhides the page"
    unhide = boot.index('classList.remove("loading")')
    before = boot[:unhide]

    stray = ids_queried(before)
    assert not stray, (
        f"{js} writes {sorted(stray)} before it unhides the page, so a missing "
        "one of those would hide every chart")

    called = {f for f in dom_functions(src) if re.search(rf"\b{f}\s*\(", before)}
    assert not called, (
        f"{js} calls {sorted(called)} before it unhides the page, and they "
        "reach for elements by id, so one missing element would hide every "
        "chart")


@pytest.mark.parametrize("js,html", PAGES, ids=lambda p: Path(p).parent.name or "pendulum")
def test_the_loading_class_is_actually_removed(js, html):
    """The pair that makes the rule above meaningful: the page sets the class
    in its markup and the script has to take it off."""
    assert 'class="loading"' in (ROOT / html).read_text(encoding="utf-8")
    assert 'classList.remove("loading")' in (ROOT / js).read_text(encoding="utf-8")


def test_one_stylesheet_reaches_all_three_pages():
    """style.css is one source copied into the two sub-pages. The copies are
    checked elsewhere for being identical; this checks all three pages ask for
    the file at all, since a page with no stylesheet still renders."""
    for _, html in PAGES:
        assert 'href="style.css"' in (ROOT / html).read_text(encoding="utf-8"), html
