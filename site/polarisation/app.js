/* Pendulum: the polarisation page. No framework, no build step, hand-rolled SVG.

   THE PAGE LEADS ON THE SOCIETY CHART, and that is a decision about what is
   worth saying rather than about what is easiest to draw. Everyone already
   believes the world is more divided than it has ever been. The expert record
   does not say that: the median country sits at 2.43 in the 1970s, 1.95 in the
   1990s and 2.55 in the 2020s, so the present is a return to where the Cold War
   left things rather than a peak. The interesting fact is not the global line,
   which is a U, it is that a handful of countries broke away from it, and that
   one of them is the United States.

   THE THREE LAYERS DO NOT VALIDATE ONE ANOTHER, and for once that is measured
   rather than asserted. Building an Esteban-Ray index out of vote shares - the
   right family, because a standard deviation cannot tell two big opposed blocs
   from six small scattered ones - and correlating it against the expert camps
   rating gives +0.16 within a country and nothing at all on changes, against a
   control autocorrelation of +0.93. How people vote and how divided they are
   turn out to be close to unrelated. So nothing on this page averages a party
   spread with a society rating, and the page says so in words. */

const ALL = "__all";
/* Opens on Australia. A page about how divided countries are should open on
   the reader's own, and Australia is also a useful default on the merits: it
   sits close to the median for most of the century, so the first thing anyone
   sees is a country tracking the world rather than an outlier arguing with it. */
/* TWO COUNTRIES, ONE PER PANEL. They were one for a day and that was wrong:
   the panels answer different questions off different datasets, and V-Dem
   rates 180 countries where V-Party codes 145, so a country picked for the
   chart above would routinely empty the one below. The party panel opens on
   every country at once, which is where its finding is - the cultural axes
   pull apart almost everywhere - and a reader who wants one country picks it
   there. */
const DEFAULTS = { country: "Australia", party: ALL };
const state = { ...DEFAULTS };
let DATA = null;

const $ = (sel) => document.querySelector(sel);
const clamp = (lo, v, hi) => Math.max(lo, Math.min(v, hi));
const svgEl = (name, attrs = {}) => {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
};

/* One hue per axis, and the hues carry the argument. The two axes that did not
   move are cool; every axis that roughly doubled is warm. A reader who takes
   nothing else from the chart should still see that the cool lines are flat. */
const AXIS_STYLE = {
  economy: { colour: "var(--p-econ)", flat: true },
  religion: { colour: "var(--p-relig)", flat: true },
  immigration: { colour: "var(--p-immig)" },
  lgbt: { colour: "var(--p-lgbt)" },
  minorities: { colour: "var(--p-minor)" },
  violence: { colour: "var(--p-viol)" },
  pluralism: { colour: "var(--p-plur)" },
  populism: { colour: "var(--p-pop)" },
  antiplural: { colour: "var(--p-anti)" },
};

/* THE WORLD VIEW'S DEFAULT IS CHOSEN; A COUNTRY'S IS COMPUTED.

   Across all countries: economics is the one that did not move and has to be
   there or the chart has no baseline, and the other three are the ones that
   did. Religious principles comes off: it is flat like economics and two flat
   lines make the same point once. The rest stay in the key for anyone checking
   that these were not picked to flatter the argument.

   For ONE country that set is the wrong question. Which issues a country's
   parties actually pulled apart on is the thing a reader came to find out, and
   it differs: Australia's top four are immigration and LGBT rights, Poland's
   are not. So picking a country shows its own top four, taken off the same
   ranking the key is already sorted by, and the reader's toggles hold until
   they pick a different country. */
const WORLD_AXES = ["economy", "immigration", "lgbt", "minorities"];
const SHOW_PER_COUNTRY = 4;
let AXES_ON = new Set(WORLD_AXES);

const fmt2 = (v) => v.toFixed(2);
const pct = (v) => `${v > 0 ? "+" : ""}${Math.round(v * 100)}%`;

/* ------------------------------------------------------------------ helpers */

function boxFor(svgId, ratio, minH, maxH) {
  const svg = $(svgId);
  const measured = Math.round(svg.parentElement.getBoundingClientRect().width);
  const w = measured > 40 ? measured
    : Math.round(clamp(280, document.documentElement.clientWidth - 76, 920));
  return { w, h: Math.round(clamp(minH, w * ratio, maxH)) };
}

function describe(svg, text) {
  svg.setAttribute("aria-label", text);
  let t = svg.querySelector("title");
  if (!t) { t = svgEl("title"); svg.prepend(t); }
  t.textContent = text;
}

function placeReadout(el, evt) {
  if (getComputedStyle(el).position === "static") return;
  const fig = el.parentElement.getBoundingClientRect();
  const x = evt.clientX - fig.left, y = evt.clientY - fig.top;
  el.style.left = "0px"; el.style.top = "0px";
  const w = el.offsetWidth, h = el.offsetHeight;
  el.style.left = `${clamp(4, x + (x + w + 18 > fig.width ? -w - 14 : 14), Math.max(4, fig.width - w - 4))}px`;
  el.style.top = `${clamp(4, y - h / 2, Math.max(4, fig.height - h - 4))}px`;
}

/* Same contract as the inequality page: a touch screen has no hover, so one tap
   pins the readout and nothing closes it until the next tap. */
const COARSE = window.matchMedia("(hover: none)").matches;
const hook = (el, show) => {
  if (COARSE) { el.addEventListener("pointerdown", show); return; }
  el.addEventListener("pointerenter", show);
  el.addEventListener("pointermove", show);
};
const clearOnLeave = (svg, readout) => {
  svg.onpointerleave = COARSE ? null : () => { readout.hidden = true; };
};

/* A locally weighted average, Gaussian kernel, the same estimator the wealth
   page uses and for the same reason: expert ratings move in steps as coders
   revise, and a raw annual line of 180 medians is a tremble rather than a
   trend. Bandwidth is a share of the span floored at a multiple of the typical
   spacing, so an annual series is smoothed and a sparse one is not invented. */
function smooth(pairs, band = 0.035) {
  const xs = pairs.filter((p) => p[1] != null).sort((a, b) => a[0] - b[0]);
  if (xs.length < 12) return xs;
  const lo = xs[0][0], hi = xs[xs.length - 1][0];
  if (hi === lo) return xs;
  const gaps = xs.slice(1).map((p, i) => p[0] - xs[i][0]).sort((a, b) => a - b);
  const step = gaps[Math.floor(gaps.length / 2)] || 1;
  const h = Math.max((hi - lo) * band, step * 2.5);
  const out = [];
  for (let i = 0; i <= 96; i += 1) {
    const x = lo + ((hi - lo) * i) / 96;
    let num = 0, den = 0;
    for (const [xi, yi] of xs) {
      const w = Math.exp(-0.5 * ((x - xi) / h) ** 2);
      num += w * yi; den += w;
    }
    /* x is NOT rounded. At 96 steps over a fifty-year span two consecutive
       output points round to the same year, and a polyline through duplicated
       x values draws a vertical riser: the fan chart came out as a staircase
       that looked like real steps in the data. The readout rounds when it
       needs a year to show; the geometry keeps the float. */
    if (den > 0.6) out.push([x, num / den]);
  }
  return out;
}

/* `ytitle` and `xtitle` are not optional decoration. Both charts here carry a
   quantity a reader cannot guess: one is an expert rating on a 0 to 4 scale
   that exists nowhere else, the other is an index against the 1970s where 1.0
   means unchanged. Unlabelled, the first looks like a percentage and the second
   looks like a raw score. */
function axisFrame(svg, box, pad, x0, x1, y0, y1, yticks, xstep,
                   ytitle = "", xtitle = "", ysize = 16, logY = false) {
  const xOf = (x) => pad.l + ((x - x0) / (x1 - x0)) * (box.w - pad.l - pad.r);
  const ly = (v) => (logY ? Math.log10(Math.max(v, 1e-6)) : v);
  const yOf = (y) => pad.t
    + (1 - (ly(y) - ly(y0)) / (ly(y1) - ly(y0))) * (box.h - pad.t - pad.b);
  for (const t of yticks) {
    const y = yOf(t);
    svg.appendChild(svgEl("line", {
      x1: pad.l, x2: box.w - pad.r, y1: y.toFixed(1), y2: y.toFixed(1),
      stroke: "var(--rule)", "stroke-width": 1,
    }));
    const lab = svgEl("text", {
      x: pad.l - 9, y: (y + 5).toFixed(1), "text-anchor": "end",
      "font-size": ysize, fill: "var(--ink-soft)",
    });
    /* two decimals only where one would collide: 1.05 and 1.1 both matter on
       the fan chart, and "1.1" against "1.1" twice is worse than a long label */
    lab.textContent = !(t % 1) ? `${t}`
      : Math.abs(t * 10 - Math.round(t * 10)) < 1e-9 ? t.toFixed(1) : t.toFixed(2);
    svg.appendChild(lab);
  }
  for (let t = Math.ceil(x0 / xstep) * xstep; t <= x1; t += xstep) {
    const x = xOf(t);
    const lab = svgEl("text", {
      x: x.toFixed(1), y: (box.h - pad.b + 20).toFixed(1),
      "text-anchor": "middle", "font-size": 12.5, fill: "var(--ink-faint)",
    });
    lab.textContent = `${t}`;
    svg.appendChild(lab);
  }
  if (ytitle) {
    const t = svgEl("text", {
      x: 0, y: 0, "font-size": 12.5, "font-weight": 600,
      fill: "var(--ink-soft)", "text-anchor": "middle",
      transform: `translate(13 ${(pad.t + (box.h - pad.b)) / 2}) rotate(-90)`,
    });
    t.textContent = ytitle;
    svg.appendChild(t);
  }
  if (xtitle) {
    const t = svgEl("text", {
      x: (pad.l + box.w - pad.r) / 2, y: box.h - 2,
      "font-size": 12.5, "font-weight": 600,
      fill: "var(--ink-soft)", "text-anchor": "middle",
    });
    t.textContent = xtitle;
    svg.appendChild(t);
  }
  return { xOf, yOf };
}

const line = (pts, colour, width, extra = {}) => svgEl("polyline", {
  points: pts, fill: "none", stroke: colour, "stroke-width": width,
  "stroke-linejoin": "round", "stroke-linecap": "round", ...extra,
});

/* ---------------------------------------------------- 1. society, the lead */

function drawCamps() {
  const svg = $("#camps"), readout = $("#camps-readout");
  svg.innerHTML = ""; readout.hidden = true;

  const band = DATA.bands.society.camps.filter((r) => r[0] >= 1900);
  const narrow = window.matchMedia("(max-width: 700px)").matches;
  /* Taller than the fan below it. This axis is a 0 to 4 rating where a tenth
     of a point is a real difference between countries, and at 0.42 the whole
     scale was 170 pixels: the gap between 2 and 3, which is the gap between a
     country that mostly gets along and one that mostly does not, was 42px. */
  const box = boxFor("#camps", narrow ? 0.95 : 0.58, 320, 540);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 62, r: narrow ? 12 : 16, t: 12, b: 56 };

  const x0 = band[0][0], x1 = band[band.length - 1][0];
  const { xOf, yOf } = axisFrame(svg, box, pad, x0, x1, 0, 4,
    [0, 1, 2, 3, 4], narrow ? 40 : 20,
    "Hostility Rating", "Year");

  /* THREE NESTED BANDS, widest first, so the whole population is on the chart
     and not just its middle. The outer pair is the full range, and in every
     single year it runs from about 0.2 to about 4.0: countries are far less
     alike than the middle half suggests, and a reader is entitled to see that
     before reading anything off the median.

     Drawing all 179 countries as lines was tried first and is worse. At any
     opacity that makes one line visible they fill the plot and bury both the
     band and the median, which is the same grey-scribble failure that took
     per-country lines off the wealth page. */
  const col = (i) => smooth(band.map((r) => [r[0], r[i]]));
  const envelope = (lo, hi, opacity) => {
    const top = hi.map(([x, y]) => `${xOf(x).toFixed(1)},${yOf(y).toFixed(1)}`);
    const bot = lo.slice().reverse()
      .map(([x, y]) => `${xOf(x).toFixed(1)},${yOf(y).toFixed(1)}`);
    svg.appendChild(svgEl("polygon", {
      points: [...top, ...bot].join(" "),
      fill: "var(--p-band)", "fill-opacity": opacity,
    }));
  };
  /* TWO envelopes, not three. Three nested fills of one colour is three
     greys, and the eye reads three greys as a legend it has to decode rather
     than as a range: the middle eighty was doing almost no work between the
     other two, and dropping it leaves the two boundaries anyone actually
     wants, the whole population and its middle. */
  /* ONE envelope. The full range was drawn to show that countries differ far
     more than the middle half suggests, and it did, but as an anonymous edge:
     a reader could see something sits at 3.99 and not which country, which is
     the only interesting part. The named lists under the chart do that job
     properly, so the outer band comes off and the shape stays readable. */
  envelope(col(3), col(5), 0.6);     // the middle half
  const p50 = col(4);
  svg.appendChild(line(
    p50.map(([x, y]) => `${xOf(x).toFixed(1)},${yOf(y).toFixed(1)}`).join(" "),
    "var(--p-med)", 2.4, { "stroke-dasharray": "5 4" }));

  const own = state.country === ALL
    ? [] : ((DATA.society[state.country] || {}).camps || []);
  const sel = smooth(own.filter((r) => r[0] >= 1900));
  if (sel.length > 1) {
    svg.appendChild(line(
      sel.map(([x, y]) => `${xOf(x).toFixed(1)},${yOf(y).toFixed(1)}`).join(" "),
      "var(--p-pick)", 2.6));
  }

  const grab = svgEl("rect", {
    x: pad.l, y: pad.t, width: box.w - pad.l - pad.r,
    height: box.h - pad.t - pad.b, fill: "transparent",
  });
  hook(grab, (evt) => {
    const r = svg.getBoundingClientRect();
    const px = (evt.clientX - r.left) * (box.w / r.width);
    const yr = Math.round(x0 + ((px - pad.l) / (box.w - pad.l - pad.r)) * (x1 - x0));
    const near = (arr) => arr.reduce((b, p) =>
      (!b || Math.abs(p[0] - yr) < Math.abs(b[0] - yr)) ? p : b, null);
    const m = near(p50), s = sel.length ? near(sel) : null;
    if (!m) { readout.hidden = true; return; }
    const row = band.reduce((b2, r) =>
      (!b2 || Math.abs(r[0] - yr) < Math.abs(b2[0] - yr)) ? r : b2, null);
    readout.innerHTML = `<b>${yr}</b>`
      + `<div class="row"><span><i style="background:var(--p-med)"></i>`
      + `median</span><span>${fmt2(m[1])}</span></div>`
      + `<div class="row"><span><i style="background:var(--p-band)"></i>`
      + `middle half</span><span>${fmt2(row[3])} to ${fmt2(row[5])}</span></div>`
      + `<div class="row"><span><i class="faint" style="background:var(--p-band)"></i>`
      + `all ${row[8]}</span><span>${fmt2(row[1])} to ${fmt2(row[7])}</span></div>`
      + (s ? `<div class="row"><span><i style="background:var(--p-pick)"></i>`
           + `${state.country}</span><span>${fmt2(s[1])}</span></div>` : "")
      + `<div class="prov">0 is no camps, 4 is a society split in two</div>`;
    readout.hidden = false;
    placeReadout(readout, evt);
  });
  svg.appendChild(grab);
  clearOnLeave(svg, readout);

  const last = band[band.length - 1];
  /* The country count is read off the payload, not typed. It moves whenever
     V-Dem extends coverage, and a sentence that quotes a number the build
     already knows is a copy waiting to go stale. */
  $("#camps-sub").textContent =
    `V-Dem asks country experts whether people who back opposing parties still `
    + `interact in a friendly way outside politics: at family functions, in `
    + `civic associations, at work. 0 is friendly, 4 is hostile. The band `
    + `covers the middle half of ${last[8]} countries.`;
  describe(svg, "Societal polarisation, 1900 to 2025: the full range of "
              + "countries, the middle half inside it, and one selected "
              + "country.");

  $("#legend-camps").innerHTML =
    `<span><i style="background:var(--p-band)"></i>Middle half</span>`
    + `<span><i class="dash"></i>Median</span>`
    + (state.country === ALL ? ""
        : `<span><i style="background:var(--p-pick)"></i>${state.country}</span>`);
}

/* ------------------------------------------------ 2. the axes, the contrast */

/* The median of an indexed series over a window, MINUS ONE, so it reads as a
   swing. The captions used to quote the last year in the series instead, which
   is a different statistic from the one the tests pin and disagreed with it by
   thirteen points on the economic axis: 2019 alone is +9%, the 2010s as a whole
   are -4%. One noisy year is not the decade. */
function median(rows, from, to) {
  const v = rows.filter((r) => r[0] >= from && r[0] <= to)
    .map((r) => r[1]).sort((a, b) => a - b);
  return v.length ? v[Math.floor(v.length / 2)] - 1 : null;
}

/* TWO SOURCES FOR ONE CHART, never mixed. With no country picked the line is
   the median across every country V-Party codes, which is what this panel
   showed from the start; with one picked it is that country's own elections.
   They are different populations, and the standfirst says which is drawn. */
function axisRows(layer, axis, country) {
  if (country === ALL) {
    return ((DATA.bands[layer] || {})[axis] || []).map((r) => [r[0], r[4]]);
  }
  return ((((DATA[layer] || {})[country]) || {})[axis] || [])
    .map((r) => [r[0], r[1]]);
}

/* THE BASELINE IS THE COUNTRY'S OWN FIRST DECADE, not a fixed 1970s. Only 74
   of the 145 countries V-Party covers held an election it codes in the 1970s:
   the other 71 are mostly post-communist and post-authoritarian states whose
   first coded election falls in the 1990s or later. Indexing those against a
   decade they have no data for draws an empty chart, and taking the nearest
   decade with data for each AXIS separately would let one country's nine lines
   each start from a different year, so the dotted line would mean nine things
   at once. One decade per country, named on the axis and in the standfirst.

   Every country here codes all nine axes at every election it codes at all,
   checked against the payload, so no axis is dropped for missing its own
   baseline. */
function baseDecade(layer, country) {
  if (country === ALL) return 1970;
  const axes = (DATA[layer] || {})[country];
  if (!axes) return null;
  const yrs = Object.values(axes).flat().map((r) => r[0]);
  return yrs.length ? Math.floor(Math.min(...yrs) / 10) * 10 : null;
}

/* ONE SERIES, AND TWO NUMBERS FOR IT. `pts` is what gets drawn, indexed so
   nine issues on nine scales can share a chart. `move` is how much further
   apart the parties actually got, in the spread's own units, and it is what
   the key is ordered on and what the per-country default is chosen by.

   THE RATIO CANNOT DO THAT JOB. A country whose parties agreed almost exactly
   on something in its baseline decade has a divisor near zero, so any later
   disagreement at all is an enormous ratio: Sweden's anti-pluralism runs 62x
   off a base of 0.008 and Germany's political pluralism 45x off 0.011. Ranked
   on the ratio, 48 of the 145 countries lead with an axis that has barely
   moved, and the four lines a reader is shown first would be the four
   measured least reliably. Ranked on the move, the US leads with political
   violence and Sweden with immigration, which is what each of them is
   actually about.

   The cost, stated because it is visible: within the four lines drawn, the
   key's order is not always their order on the chart, since the chart shows
   ratios and the key ranks moves. */
/* The bandwidth is 0.05, not 0.16. At a sixth of the span the kernel reached
   eight years either side and turned four decades of elections into four
   smooth arcs: a reader could see that the cultural lines rise and nothing
   else. At a twentieth it is about two and a half years, which keeps the
   decade shape and puts the texture back - the stall in the 1980s, the step
   around German reunification, the flattening after 2015. The floor inside
   `smooth`, at two and a half times the median spacing, still stops it drawing
   noise between sparse observations. */
function axisSeries(layer, axis, country, dec, band = 0.05) {
  const rows = axisRows(layer, axis, country);
  const base = rows.filter((r) => r[0] >= dec && r[0] <= dec + 9)
    .map((r) => r[1]).sort((a, b) => a - b);
  if (!base.length) return null;
  const b = base[Math.floor(base.length / 2)];
  // a spread of zero is a country whose coded parties all sat on one point:
  // there is no ratio to take, and dividing gives a column of Infinity
  if (!(b > 0)) return null;
  const pts = smooth(rows.map((r) => [r[0], r[1] / b]), band);
  if (pts.length < 2) return null;
  return { pts, move: b * (pts[pts.length - 1][1] - 1) };
}

/* Ticks for a ratio axis: round multiples of a power of ten. The ladder is
   chosen by trying the densest first and taking the first that does not put
   more than eight labels down the gutter, so a chart running 1 to 2 gets
   1, 1.1, 1.2 ... and one running 1 to 1,200 gets 1, 10, 100, 1,000. */
const LOG_LADDERS = [
  [1, 1.1, 1.2, 1.3, 1.5, 1.7, 2, 2.5, 3, 4, 5, 7],
  [1, 1.5, 2, 3, 5, 7],
  [1, 2, 5],
  [1, 3],
  [1],
];

function logTicks(lo, hi) {
  const e0 = Math.floor(Math.log10(lo)), e1 = Math.ceil(Math.log10(hi));
  let best = [];
  for (const ladder of LOG_LADDERS) {
    const out = [];
    for (let e = e0; e <= e1; e += 1) {
      for (const m of ladder) {
        const v = m * Math.pow(10, e);
        if (v >= lo - 1e-9 && v <= hi + 1e-9) {
          out.push(Math.round(v * 1000) / 1000);
        }
      }
    }
    best = out;
    if (out.length <= 8) break;
  }
  return best.length >= 2 ? best : [lo, hi].map((v) => Math.round(v * 100) / 100);
}

function drawFan(svgId, readoutId, legendId, layer, styles, country, dec,
                 labels, on) {
  const svg = $(svgId), readout = $(readoutId);
  svg.innerHTML = ""; readout.hidden = true;

  const series = Object.keys(styles).map((k) => {
    const s = axisSeries(layer, k, country, dec, 0.05);
    return s && {
      key: k, label: labels[k],
      colour: styles[k].colour || styles[k],
      flat: !!styles[k].flat,
      pts: s.pts, move: s.move,
    };
  }).filter(Boolean);
  if (!series.length) return;
  /* ORDERED BY HOW FAR THE PARTIES ACTUALLY MOVED APART, most first. See
     axisSeries for why that is the move rather than the ratio the chart draws.

     ONE ORDER, whatever is switched on. Grouping the shown entries first was
     tried and is worse: every toggle reshuffled the column, so the act of
     turning a line off moved four other labels and the reader lost their
     place. A key that rearranges itself when you use it is not a key. */
  series.sort((a, b) => b.move - a.move);

  /* THE KEY IS BUILT BEFORE THE CHART IS MEASURED, and the order matters now
     that the key sits beside the chart rather than above it. boxFor reads the
     figure's width, the figure is a flex child, and an empty key takes no
     width: on first paint the figure was the full 920 and the SVG took a 920
     viewBox, then the key filled, the figure shrank to 682, and the whole
     drawing was displayed at three quarters of the size its geometry was
     computed for. Fill the column first and the measurement is the real one. */
  $(legendId).innerHTML = series.map((s) =>
    `<button type="button" class="key rule" data-axis="${s.key}" `
    + `aria-pressed="${on.has(s.key)}">`
    + `<i style="background:${s.colour}"></i>${s.label}</button>`).join("");
  for (const btn of $(legendId).querySelectorAll("[data-axis]")) {
    btn.addEventListener("click", () => {
      const k = btn.dataset.axis;
      if (on.has(k)) { if (on.size > 1) on.delete(k); } else on.add(k);
      render();
    });
  }

  const shown = series.filter((s) => on.has(s.key));
  const narrow = window.matchMedia("(max-width: 700px)").matches;
  const box = boxFor(svgId, narrow ? 0.72 : 0.4, 250, 400);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 62, r: narrow ? 12 : 16, t: 12, b: 56 };

  const xs = shown.flatMap((s) => s.pts.map((p) => p[0]));
  const ys = shown.flatMap((s) => s.pts.map((p) => p[1]));
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  /* A RATIO AXIS IS A LOG AXIS, and on this chart it has to be. Everything is
     drawn against its own 1970s level, and 21% of the country-axis baselines
     in V-Party sit under 0.10 - a country whose parties agreed almost exactly
     on something fifty years ago - so any disagreement since is an enormous
     multiple. On a linear axis, 30 of the 145 countries had one line more than
     three times the height of the next and the rest lay flat along the floor;
     Mauritania reached 1,238. Those numbers are true, and a linear axis makes
     them the only thing on the chart.

     On a log axis twice as far apart and half as far apart are the same
     distance either side of the dotted 1, which is what a ratio means, and
     nothing is crushed. It barely touches the all-countries view, whose lines
     live between 0.88 and 2.05: over that range the two scales are almost the
     same picture.

     THE RANGE STILL FITS THE LINES SHOWN, padded by 6% either way so nothing
     touches an edge. A fixed range spent most of its height on emptiness. */
  const lo0 = Math.max(Math.min(...ys), 1e-3), hi0 = Math.max(...ys);
  const lo = lo0 / 1.06, hi = hi0 * 1.06;
  const ticks = logTicks(lo, hi);
  const { xOf, yOf } = axisFrame(svg, box, pad, x0, x1, lo, hi,
    ticks, narrow ? 20 : 10,
    /* 13, against the society chart's 16. That one carries five whole numbers
       on a 0 to 4 scale and they are the thing being read; this one carries
       1.25 and 1.75 as well, so the same size crowds the gutter and competes
       with the lines. */
    `Distance Between Parties, ${dec}s = 1`, "Year", 13, true);

  // the baseline: 1.0 is "exactly where it was", and it is the whole reference
  svg.appendChild(svgEl("line", {
    x1: pad.l, x2: box.w - pad.r, y1: yOf(1).toFixed(1), y2: yOf(1).toFixed(1),
    stroke: "var(--ink-faint)", "stroke-width": 1.4, "stroke-dasharray": "3 3",
  }));

  for (const s of shown) {
    svg.appendChild(line(
      s.pts.map(([x, y]) => `${xOf(x).toFixed(1)},${yOf(y).toFixed(1)}`).join(" "),
      s.colour, s.flat ? 3 : 2.4, s.flat ? {} : { "stroke-opacity": 0.95 }));
  }

  const grab = svgEl("rect", {
    x: pad.l, y: pad.t, width: box.w - pad.l - pad.r,
    height: box.h - pad.t - pad.b, fill: "transparent",
  });
  hook(grab, (evt) => {
    const r = svg.getBoundingClientRect();
    const px = (evt.clientX - r.left) * (box.w / r.width);
    const yr = Math.round(x0 + ((px - pad.l) / (box.w - pad.l - pad.r)) * (x1 - x0));
    const bits = [`<b>${yr}</b>`];
    for (const s of shown) {
      const n = s.pts.reduce((b, p) =>
        (!b || Math.abs(p[0] - yr) < Math.abs(b[0] - yr)) ? p : b, null);
      if (n && Math.abs(n[0] - yr) <= 6) {
        bits.push(`<div class="row"><span><i style="background:${s.colour}"></i>`
          + `${s.label}</span><span>${pct(n[1] - 1)}</span></div>`);
      }
    }
    if (bits.length === 1) { readout.hidden = true; return; }
    readout.innerHTML = bits.join("")
      + `<div class="prov">against the same measure in the ${dec}s</div>`;
    readout.hidden = false;
    placeReadout(readout, evt);
  });
  svg.appendChild(grab);
  clearOnLeave(svg, readout);

  /* A RULE, not a block. These entries stand for lines on the chart and the
     block swatch made them read as a row of checkboxes with an off state that
     looked broken rather than unselected. A short rule in the line's own colour
     says what it is, and an entry that is switched off simply fades. */
  return series;
}

/* "the parties in United States of America" is a machine filling a slot, and
   the United States is the country this page is most often read about. A name
   takes "the" when it is a plural or a common noun rather than a proper one:
   a union of states, a group of islands, a republic. Written as a rule rather
   than a list so a country V-Dem adds later is covered too. Only prose uses
   it; the key, the menu and the ranked lists are labels and keep the name. */
const THE = /\b(United|Republic|Islands|Isles|Kingdom|Emirates|Netherlands|Philippines|Bahamas|Gambia|Maldives|Comoros|Seychelles|Congo)\b/;
const named = (c) => (THE.test(c) ? `the ${c}` : c);

function drawAxes() {
  const c = state.party, dec = baseDecade("party", c);
  const note = $("#axes-note"), row = $("#axes-row"), sub = $("#axes-sub");
  const nothing = (msg) => {
    note.textContent = msg; note.hidden = false; row.hidden = true;
    sub.textContent = ""; $("#axes").innerHTML = "";
    $("#legend-axes").innerHTML = "";
  };

  /* NOTHING, rather than the world line under a country's name. The picker
     offers the 180 countries V-Dem rates because it drives the chart above,
     and V-Party covers 145, so some of them have no party record at all and a
     few more have a single election. Falling back to the aggregate would
     answer a question nobody asked in a way nobody could see. */
  if (dec === null) {
    nothing(`V-Party records no elections for ${named(c)}. It covers `
          + `${Object.keys(DATA.party).length} countries between 1970 and `
          + `2019, and this one is not among them.`);
    return;
  }

  /* UNHIDDEN BEFORE THE DRAW, because drawFan measures the row it sits in and
     a hidden row measures zero. Same trap as body.loading, one level down. */
  note.hidden = true; row.hidden = false;

  const labels = Object.fromEntries(
    DATA.meta.layers.party.axes.map((a) => [a.key, a.label]));
  const series = drawFan("#axes", "#axes-readout", "#legend-axes", "party",
    AXIS_STYLE, c, dec, labels, AXES_ON);
  if (!series) {
    nothing(`V-Party records a single election for ${named(c)}, so there `
          + `is nothing to draw a line between.`);
    return;
  }

  sub.textContent = (c === ALL
    ? `Each line is one thing parties argue about, across all `
      + `${Object.keys(DATA.party).length} countries V-Party codes. It shows `
      + `how far apart experts placed those parties at each election, `
    : `Each line is one thing the parties in ${named(c)} argue about. It `
      + `shows how far apart experts placed them at each election, `)
    + `against how far apart they were in the ${dec}s (dotted line).`;
  describe($("#axes"), `Nine measures of how far apart parties stand`
    + `${c === ALL ? "" : ` in ${named(c)}`}, each against its own level in `
    + `the ${dec}s.`);
}


/* ----------------------------------------------------------------- furniture */

/* WHERE COUNTRIES STAND, AND HOW FAR THEY HAVE COME. The level pair on its
   own is saturated at the hostile end: the five most divided in 2025 sit
   between 3.97 and 3.99, so their order is noise on a 0 to 4 scale. The move
   pair spreads from -1.56 to +2.64 and is the page's argument, but on its own
   it cannot say whether a country that moved a long way ended up calm or
   hostile. Both, in two pairs.

   They replaced the outer band, which showed that something sat at
   3.99 without ever saying what: the edge of a grey shape is not a finding, a
   country's name is. Clicking one picks it out on the chart above, so the list
   is also the fastest way into the control. */
function renderRanks() {
  const el = $("#camps-ranks");
  if (!el) return;
  const rows = DATA.bands.society.camps;
  const to = rows[rows.length - 1][0], from = to - 20;
  const level = [], move = [];
  for (const [name, axes] of Object.entries(DATA.society)) {
    const d = new Map(axes.camps || []);
    if (d.has(to)) level.push([name, d.get(to)]);
    // both ends, or the country is not comparable with itself
    if (d.has(from) && d.has(to)) move.push([name, d.get(to) - d.get(from)]);
  }
  level.sort((p, q) => p[1] - q[1]);
  move.sort((p, q) => p[1] - q[1]);
  /* The flag is decoration with a job: at a glance it says which part of the
     world a list is, which is the first thing anyone wants from a ranking of
     countries they may not recognise. flagcdn serves by ISO alpha-2, and the
     three entries with no code - East Germany, Somaliland, Zanzibar - simply
     get no image rather than a broken one. width and height are set so the row
     does not jump when the image lands, and loading is lazy because ten flags
     are not worth blocking on. */
  const iso = DATA.meta.iso2 || {};
  /* THREE UNITS V-DEM RATES THAT ISO DOES NOT NAME, so flagcdn has nothing to
     serve for them and they used to render as an empty box. Zanzibar reaches
     one of these lists today. The flags are committed here rather than
     hotlinked, all three public domain on Wikimedia Commons, and the file is
     the whole flag so it needs no attribution line on the page. */
  const OWN = {
    "Zanzibar": "zanzibar",
    "Somaliland": "somaliland",
    "German Democratic Republic": "east-germany",
  };
  const flag = (n) => {
    const src = OWN[n] ? `flags/${OWN[n]}.svg`
      : iso[n] ? `https://flagcdn.com/w40/${iso[n]}.png` : null;
    if (!src) return `<span class="flag flag-none" aria-hidden="true"></span>`;
    const hi = !OWN[n] && iso[n]
      ? ` srcset="https://flagcdn.com/w80/${iso[n]}.png 2x"` : "";
    return `<img class="flag" src="${src}"${hi} width="20" height="15" `
      + `alt="" loading="lazy" decoding="async">`;
  };
  /* No sub-line. The heading already says which direction and over what
     window, and a sub restating the scale a second time in the same eyeful was
     the only other thing it carried. The figure is SIGNED, because a list of
     movements where every number reads as a level is unreadable: a plus is
     printed as well as a minus even though it is redundant arithmetic, since
     the two lists sit side by side and the sign is what tells them apart. */
  const moved = (v) => `${v > 0 ? "+" : "\u2212"}${fmt2(Math.abs(v))}`;
  const list = (title, items, fmt) =>
    `<div class="rank"><h3>${title}</h3><ol>`
    + items.map(([n, v]) =>
        `<li><button type="button" data-country="${n.replace(/"/g, "&quot;")}">`
        + `${flag(n)}<span class="nm">${n}</span><b>${fmt(v)}</b></button></li>`).join("")
    + "</ol></div>";
  /* FOUR LISTS, IN TWO PAIRS: where countries stand, then how far they have
     come. The level pair alone was saturated at the hostile end - the five
     most divided sit inside 0.02 of each other, so their order is noise - and
     the move pair alone loses the fact that a country can move a long way and
     still be calm. Read together they are the page's argument: the middle
     barely shifts while the edges travel. */
  el.innerHTML =
    list(`Least Divided, ${to}`, level.slice(0, 5), fmt2)
    + list(`Most Divided, ${to}`, level.slice(-5).reverse(), fmt2)
    + list(`Less Divided Than in ${from}`, move.slice(0, 5), moved)
    + list(`More Divided Than in ${from}`, move.slice(-5).reverse(), moved);
  for (const btn of el.querySelectorAll("[data-country]")) {
    btn.addEventListener("click", () => {
      setCountry(btn.dataset.country);
      $("#country-sel").value = state.country;
      $("#camps").scrollIntoView({ block: "center", behavior: "smooth" });
    });
  }
}

/* The layers panel came off this page and the code that filled it stayed,
   guarded by a null check, which is how a script ends up writing to elements
   nobody can name. A guard is not documentation: the test that every id these
   scripts query exists in their page cannot tell a deliberate absence from the
   one that took Pendulum down, so there are no deliberate absences. */
function renderSources() {
  /* Name, publisher, link, then the release and the slice taken. Two earlier
     versions of the second line came off the page - the publishers' own blurbs
     and our notes on what each is used for - because both were sentences ABOUT
     a source rather than facts a reader could check it against. What is there
     now is a version, a publication date and a count, which is what somebody
     matching this page against the data would need. */
  $("#sources").innerHTML = DATA.meta.sources.map((s) =>
    `<li><a href="${s.url}" rel="noopener">${s.name}</a>, ${s.publisher}.`
    + `<span class="detail">${s.detail}</span></li>`).join("");
}

/* A MENU PER PANEL, EACH LISTING ONLY WHAT IT CAN DRAW. The society menu is
   the countries V-Dem rates across a long enough span to make a line; the
   party menu is the countries V-Party codes at two elections or more, which is
   134 of its 145 and includes two - Czech Republic and Turkey - that V-Dem
   names differently and so are not in the other list at all. Offering either
   menu the other's countries would put entries in it that draw nothing. */
function menuHtml(names, first) {
  return `<option value="${ALL}">${first}</option>`
    + names.map((c) => `<option value="${c}">${c}</option>`).join("");
}

function setCountry(c) { state.country = c; render(); }

/* The lines shown are re-chosen on every change of country, not on every
   render, so a reader who switches one off keeps it off while they look at
   that country and gets a fresh four when they move on. */
function setParty(c) {
  state.party = c;
  AXES_ON = c === ALL ? new Set(WORLD_AXES) : topAxes(c, SHOW_PER_COUNTRY);
  render();
}

/* The n issues this country's parties moved furthest apart on, by the same
   measure the key is ordered on, so the default set IS the top of the key
   rather than a second opinion about it. */
function topAxes(country, n) {
  const dec = baseDecade("party", country);
  if (dec === null) return new Set(WORLD_AXES);
  const ranked = Object.keys(AXIS_STYLE)
    .map((k) => [k, axisSeries("party", k, country, dec)])
    .filter(([, s]) => s)
    .sort((a, b) => b[1].move - a[1].move);
  return ranked.length ? new Set(ranked.slice(0, n).map(([k]) => k))
                       : new Set(WORLD_AXES);
}

function buildPickers() {
  const names = Object.keys(DATA.society)
    .filter((c) => (DATA.society[c].camps || []).length > 20)
    .sort((a, b) => a.localeCompare(b));
  /* "All countries" is not a country: it drops the highlighted line and leaves
     the spread and the median, which is every country at once. */
  /* "None", not "All countries". Every country is on the chart whatever this
     is set to - the bands are the whole population and nothing removes them -
     so an option called "All countries" described the chart rather than the
     choice, and reading it as "show me all of them" left a reader wondering
     what every other option did. The control draws ONE line on top of what
     is already there, and its empty state is no line. */
  if (state.country !== ALL && !names.includes(state.country)) state.country = ALL;
  const sel = $("#country-sel");
  sel.innerHTML = menuHtml(names, "None");
  sel.value = state.country;

  /* Two elections or more. One is a point, and a point is not a line: a
     country with a single coded election drew an empty chart under a heading
     saying what it was about. */
  const party = Object.keys(DATA.party)
    .filter((c) => Object.values(DATA.party[c]).some((rows) => rows.length > 1))
    .sort((a, b) => a.localeCompare(b));
  if (state.party !== ALL && !party.includes(state.party)) state.party = ALL;
  const sel2 = $("#country-sel-2");
  if (sel2) {
    sel2.innerHTML = menuHtml(party, "All countries");
    sel2.value = state.party;
  }
}

/* One re-render if the drawing disagrees with the box it ended up in.

   Every chart here measures its container and then fills it, which is fine
   until the act of filling it changes the layout. It does on the party chart:
   its key is a flex sibling, so the figure's width depends on content that does
   not exist until the draw runs. The CSS fixes the specific case; this catches
   the general one, and it runs AT MOST ONCE per render so it cannot oscillate
   between two widths that each imply the other. */
let settling = false;

function render() {
  drawCamps();
  drawAxes();
  renderRanks();
  if (settling) { settling = false; return; }
  const off = ["#camps", "#axes"].some((id) => {
    const svg = $(id);
    const vb = +(svg.getAttribute("viewBox") || "0 0 0 0").split(" ")[2];
    const w = svg.parentElement.getBoundingClientRect().width;
    return vb > 0 && w > 40 && Math.abs(vb - w) > 4;
  });
  if (off) { settling = true; render(); }
}

/* No "how is this measured" toggle. It was a third piece of chrome in a
   heading, and the two things it said that a reader needs - that the positions
   are an expert judgement, and what the line is measured against - are one
   clause in the standfirst that was already there. The coverage floor it also
   explained is enforced in the build and pinned by a test, which is where a
   rule belongs. */
function wire() {
  $("#country-sel").addEventListener("change", (e) => setCountry(e.target.value));
  const sel2 = $("#country-sel-2");
  if (sel2) sel2.addEventListener("change", (e) => setParty(e.target.value));
  let t = null;
  window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(render, 140); });
}

fetch("data.json")
  .then((r) => { if (!r.ok) throw new Error(`data.json ${r.status}`); return r.json(); })
  .then((d) => {
    DATA = d;
    /* THE PANELS ARE UNHIDDEN BEFORE ANYTHING IS DRAWN. `body.loading` sets
       `display: none` on every panel, so a chart that measures its container
       while the class is still on measures ZERO and silently falls back to a
       clamp on the viewport width. Every chart on this page was being drawn at
       a guessed width rather than its real one, which at 1400px meant a 920
       viewBox inside an 874 box: the whole drawing scaled down by five per cent
       and every label with it. */
    document.body.classList.remove("loading");
    buildPickers(); renderSources(); wire(); render();
  })
  .catch((err) => {
    const stage = DATA ? "draw the charts" : "load the data";
    document.body.classList.remove("loading");
    $("main").insertAdjacentHTML("afterbegin",
      `<section class="panel"><h2>Could not ${stage}</h2><p class="sub">${err.message}</p></section>`);
    throw err;
  });
