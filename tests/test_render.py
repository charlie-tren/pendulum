"""The three pages as a browser actually renders them.

THIS IS THE TEST THAT WAS MISSING. On 23/09/2026 Pendulum served every file
with a 200, passed a suite of 62 tests, and showed a reader nothing but the
words "Loading the data" for eight hours, because one JavaScript error fired
above the line that unhides the panels. Nothing that reads a file can see that.
Something has to open the page.

Everything here is a question you can only answer by rendering:

  * did the page draw at all, and did anything throw on the way,
  * is each chart's geometry computed for the width it is displayed at,
  * does the page stay inside a phone screen,
  * do the controls only offer things that draw, and do the images load.

It is one browser and one server for the whole module, which keeps it to a few
seconds. If Playwright is not installed the module skips rather than fails: it
is a dev dependency here, not a runtime one.

    python -m pytest tests/test_render.py -q
"""
from __future__ import annotations

import contextlib
import functools
import http.server
import socket
import threading
from pathlib import Path

import pytest

pw_api = pytest.importorskip(
    "playwright.sync_api", reason="Playwright is a dev dependency")

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

PAGES = {"pendulum": "/", "inequality": "/inequality/", "polarisation": "/polarisation/"}

# the widths the charts are checked at: two desktops, a tablet, three phones
# and one narrower than any phone sold, because the failure is silent at all of
# them and costs nothing to rule out
WIDTHS = (1400, 1100, 900, 780, 500, 390, 330)


@pytest.fixture(scope="module")
def server():
    """A throwaway static server on a free port. The pages fetch their data, so
    file:// cannot run them: a rendering test needs a real origin."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(SITE))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    httpd.log_message = lambda *a, **k: None
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture(scope="module")
def browser():
    with pw_api.sync_playwright() as pw:
        b = pw.chromium.launch()
        try:
            yield b
        finally:
            b.close()


@contextlib.contextmanager
def opened(browser, server, path, width=1180):
    """A page, loaded, with everything it complained about on the way."""
    page = browser.new_page(viewport={"width": width, "height": 900})
    problems: list[str] = []
    page.on("pageerror", lambda e: problems.append(f"uncaught: {e}"))
    page.on("console",
            lambda m: problems.append(f"console: {m.text}") if m.type == "error" else None)
    page.on("requestfailed",
            lambda r: problems.append(f"failed request: {r.url}"))
    try:
        page.goto(f"{server}{path}", wait_until="networkidle")
        page.wait_for_timeout(900)
        yield page, problems
    finally:
        page.close()


@pytest.mark.parametrize("name,path", PAGES.items(), ids=list(PAGES))
def test_the_page_draws_and_nothing_throws(browser, server, name, path):
    """The whole outage in one assertion. `body.loading` puts display:none on
    every panel, so the page is the word "Loading" until a script takes the
    class off - and anything that throws before that line leaves it on."""
    with opened(browser, server, path) as (page, problems):
        assert not problems, f"{name}: {problems}"
        assert not page.evaluate("document.body.classList.contains('loading')"), (
            f"{name} never unhid its panels")
        drawn = page.evaluate("""() => [...document.querySelectorAll('svg[viewBox]')]
            .filter(s => s.id).map(s => [s.id, s.children.length])""")
        assert drawn, f"{name} drew no charts at all"
        empty = [i for i, n in drawn if n == 0]
        assert not empty, f"{name}: these charts are empty: {empty}"


@pytest.mark.parametrize("name,path", PAGES.items(), ids=list(PAGES))
def test_every_chart_with_words_on_it_is_drawn_at_its_own_width(browser, server, name, path):
    """A chart here measures its container and sets a viewBox of one unit per
    CSS pixel. When the measurement is wrong the drawing is simply scaled, so
    every label shrinks with it and nothing looks broken - which is how all
    three pages shipped a 920-unit viewBox inside an 874px box.

    ONLY THE CHARTS THAT CARRY TEXT. The world map is projected at build time
    into a fixed 1000-unit space and scaled to fit, which is correct for a map
    and is the whole reason its geometry can live in a JSON file: it has no
    labels to shrink, because a country is named by tapping it."""
    with opened(browser, server, path) as (page, _):
        for w in WIDTHS:
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(320)
            off = page.evaluate("""() => [...document.querySelectorAll('svg[viewBox]')]
                .filter(s => s.id && s.querySelector('text'))
                .map(s => ({ id: s.id, vb: +s.getAttribute('viewBox').split(' ')[2],
                             box: Math.round(s.parentElement.getBoundingClientRect().width) }))
                .filter(r => r.box > 40 && Math.abs(r.vb - r.box) > 4)""")
            assert not off, f"{name} at {w}px: {off}"


@pytest.mark.parametrize("name,path", PAGES.items(), ids=list(PAGES))
def test_no_label_on_a_chart_renders_too_small_to_read(browser, server, name, path):
    """The measurement that catches the scaling bug wherever it comes from, and
    the only one that cannot be fooled: inside a scaled viewBox `font-size`
    reports the USER-UNIT size and looks perfectly healthy while the eye gets a
    quarter of it. The rendered box is the truth.

    Measured across all three pages at seven widths, the smallest label on the
    estate is 14px. The floor here is 11, which leaves room to retune type and
    still fails loudly on the 4px disaster this is here to prevent."""
    FLOOR = 11
    with opened(browser, server, path) as (page, _):
        for w in WIDTHS:
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(320)
            small = page.evaluate("""(floor) => [...document.querySelectorAll('svg text')]
                .map(t => ({ text: t.textContent.slice(0, 20),
                             h: +t.getBoundingClientRect().height.toFixed(1) }))
                .filter(r => r.h > 0 && r.h < floor)""", FLOOR)
            assert not small, f"{name} at {w}px, under {FLOOR}px: {small}"


@pytest.mark.parametrize("name,path", PAGES.items(), ids=list(PAGES))
def test_the_page_stays_inside_a_phone(browser, server, name, path):
    """A screenshot is taken at the viewport width, so sideways overflow is the
    one fault it can never show: it is off the right edge of the picture."""
    with opened(browser, server, path, width=390) as (page, _):
        sw = page.evaluate("document.documentElement.scrollWidth")
        cw = page.evaluate("document.documentElement.clientWidth")
        assert sw <= cw + 1, f"{name} scrolls sideways at 390px: {sw} into {cw}"


def test_a_menu_only_offers_a_country_that_draws(browser, server):
    """A control must not offer what it cannot render. The society menu lists
    the countries V-Dem rates over a long enough span; the party menu lists the
    ones V-Party codes at two elections or more, which is a different set and
    not a subset."""
    with opened(browser, server, PAGES["polarisation"]) as (page, _):
        bad = page.evaluate("""() => {
          const opts = (id) => [...document.querySelector(id).options]
            .map(o => o.value).filter(v => v !== '__all');
          return {
            society: opts('#country-sel')
              .filter(v => ((DATA.society[v] || {}).camps || []).length < 2),
            party: opts('#country-sel-2')
              .filter(v => !Object.values(DATA.party[v] || {}).some(r => r.length > 1)),
          };
        }""")
        assert not bad["society"], f"society menu offers: {bad['society']}"
        assert not bad["party"], f"party menu offers: {bad['party']}"


def test_the_two_country_menus_are_independent(browser, server):
    """One per panel, because the panels answer different questions off
    different datasets. They shared a country for a day and picking one for the
    chart above routinely emptied the one below."""
    with opened(browser, server, PAGES["polarisation"]) as (page, _):
        page.select_option("#country-sel", "Brazil")
        page.wait_for_timeout(350)
        assert page.eval_on_selector("#country-sel-2", "e => e.value") == "__all"
        page.select_option("#country-sel-2", "Poland")
        page.wait_for_timeout(350)
        assert page.eval_on_selector("#country-sel", "e => e.value") == "Brazil"


def test_picking_a_country_shows_that_country_s_top_four(browser, server):
    """The default set is computed per country, off the same ranking the key is
    sorted by, so it has to BE the top of the key rather than a second opinion
    about it."""
    with opened(browser, server, PAGES["polarisation"]) as (page, _):
        for country in ("Australia", "United States of America", "Sweden"):
            page.select_option("#country-sel-2", country)
            page.wait_for_timeout(400)
            keys = page.evaluate("""() => [...document.querySelectorAll('#legend-axes [data-axis]')]
                .map(e => [e.dataset.axis, e.getAttribute('aria-pressed') === 'true'])""")
            on = [k for k, pressed in keys if pressed]
            assert on == [k for k, _ in keys[:4]], (
                f"{country}: switched on {on}, top of the key is "
                f"{[k for k, _ in keys[:4]]}")


def test_every_flag_in_a_ranked_list_loads(browser, server):
    """Three of the units V-Dem rates have no ISO code, so a flag service keyed
    on alpha-2 has nothing for them and they are served from this repo. A
    broken image is invisible in the markup and obvious on the page."""
    with opened(browser, server, PAGES["polarisation"]) as (page, _):
        broken = page.evaluate("""() => [...document.querySelectorAll('.flag')]
            .filter(e => e.tagName === 'IMG' && e.complete && e.naturalWidth === 0)
            .map(e => e.getAttribute('src'))""")
        assert not broken, f"broken flags: {broken}"
        rows = page.evaluate("document.querySelectorAll('#camps-ranks .rank').length")
        assert rows == 4, f"expected four ranked lists, found {rows}"


COUNT_URL_WRITES = """() => {
    window.__writes = 0;
    const real = history.replaceState.bind(history);
    history.replaceState = (...a) => { window.__writes++; return real(...a); };
}"""


def test_a_running_timeline_does_not_rewrite_the_url(browser, server):
    """Cloudflare's beacon counts every history.replaceState as a pageview. The
    timeline used to write the URL on each Play tick, every 320ms, so one
    visitor watching for two and a half minutes read as 480 pageviews. While it
    plays nothing is written; when it stops, exactly one write."""
    with opened(browser, server, PAGES["pendulum"]) as (page, _):
        page.evaluate(COUNT_URL_WRITES)
        page.click('.play[data-play="year"]')
        page.wait_for_timeout(2500)
        assert page.evaluate("window.__writes") == 0, "the URL was written while playing"
        page.click('.play[data-play="year"]')
        page.wait_for_timeout(1500)
        assert page.evaluate("window.__writes") == 1
        assert "year=" in page.evaluate("location.hash")


def test_dragging_a_slider_writes_the_url_once(browser, server):
    with opened(browser, server, PAGES["pendulum"]) as (page, _):
        page.evaluate(COUNT_URL_WRITES)
        page.evaluate("""() => {
            const el = document.querySelector('#year');
            for (let v = +el.min; v < +el.min + 30; v++) {
                el.value = v; el.dispatchEvent(new Event('input'));
            }
        }""")
        page.wait_for_timeout(1500)
        assert page.evaluate("window.__writes") == 1


def test_resizing_inequality_does_not_rewrite_the_url(browser, server):
    """render() runs on every resize and called writeHash with an unchanged
    state, so resizing a window counted as reading."""
    with opened(browser, server, PAGES["inequality"]) as (page, _):
        page.evaluate(COUNT_URL_WRITES)
        for w in (900, 1000, 1100, 1180):
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(250)
        page.wait_for_timeout(1500)
        assert page.evaluate("window.__writes") == 0
