/* Pendulum: the wealth page. No framework, no build step, hand-rolled SVG.

   WHY THIS IS NOT ONE CHART.
   The evidence runs from 9200 BC to 2024, and a shared linear time axis makes
   that unreadable: the last two centuries, which hold almost all the data, get
   under 2% of the width, and the first attempt at it put 500 years of sparse
   dots across two thirds of the page and crushed 215 annual country series into
   a grey scribble on the right. Worse, a continuous axis invites exactly the
   comparison the data cannot support, because a dug-up house, a tax register, a
   historian's estimate and a national account measure four different things
   over four different populations.

   So: one panel per era, side by side, each with its own time scale, sharing
   one y axis. You can compare heights, which is the honest comparison, and the
   gutters say plainly that the horizontal scales differ. */

/* `scatter` is which layers show their individual observations. The tax
   registers open closed: 84 towns, 26 regional estimates and a median in one
   panel was a thicket, and the median is the thing worth reading first. The
   archaeology opens open, because 52 sites over 10,000 years is the finding
   rather than clutter, and there is no denser summary to fall back on. Both
   are toggled from the key. */
/* Two of the three scatters open on. The test is whether the layer has a
   denser summary to fall back on: the excavated sites and the tax registers are
   drawn as dots and a kernel average and nothing else, so folded away they left
   their panels holding a bare line with no visible evidence under it. The
   regional estimates do have somewhere to hide, because each one is an average
   of towns already on the chart, so they stay off and are the one thing the key
   adds rather than the two things it takes away. */
const DEFAULTS = {
  metric: "gini", country: "USA",
  scatter: { deep: true, town: true, region: false },
};
const ALL = "__all";
const state = { ...DEFAULTS, scatter: { ...DEFAULTS.scatter } };
const SCATTERS = ["deep", "town", "region"];
let DATA = null;

const $ = (sel) => document.querySelector(sel);
const clamp = (lo, v, hi) => Math.max(lo, Math.min(v, hi));
const svgEl = (name, attrs = {}) => {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
};

const METRICS = {
  gini: {
    label: "Wealth Gini", max: 1, pct: false,
    blurb: "0 if every household owns the same, 1 if one household owns everything.",
  },
  top10: {
    label: "Share held by the richest 10%", max: 100, pct: true,
    blurb: "The top decile's share of household wealth.",
  },
  top1: {
    label: "Share held by the richest 1%", max: 100, pct: true,
    blurb: "The top percentile's share of household wealth.",
  },
};

/* PANELS TILE TIME. They are periods, not sources, and they do not overlap.

   Sources overlap badly: excavated settlements run to 1970, tax registers from
   1283, national accounts from 1800. A panel per source therefore repeated
   whole centuries across neighbouring panels, which read as consecutive eras
   when it was one era measured twice. A panel per period cannot do that, and
   each simply holds whatever evidence falls inside it. Eleven of the 63 dig
   sites sit after 1283 - Cahokia, Mayapan, Tenochtitlan, the !Kung San - all
   outside Europe, where no tax register exists, so they belong in the later
   panels rather than being dropped for tidiness.

   Panel width is not proportional to length in years. The first spans 10,500
   of them and the last 224, and sizing by duration would leave the panel
   holding almost all the data a sliver. */
const PERIODS = [
  { key: "ancient", from: -1e9, to: 1283 },
  /* 1801, not 1800: Alfani's last observations are dated 1800, and with an
     exclusive upper bound they landed alone at the left edge of the national
     accounts panel. The header still reads 1800, because that is the year. */
  { key: "early", from: 1283, to: 1801, labelTo: 1800 },
  { key: "measured", from: 1801, to: 1e9 },
];

/* The key is read at a glance, so it takes the shortest name that is still
   true. The long ones belong in the panel that explains the layers. */
/* Both sources get the SAME key entry, because on the chart they are the same
   mark: every country with a reading that year, shaded from the 25th to the
   75th, median dashed through the middle. Only one of them is ever drawn, since
   the Gini comes from Alfani and Schifano and the shares from WID, so there is
   no year in which two things called "All countries" appear together.

   It reads as a pair against the entry beside it - all countries, then the one
   you picked - and that pairing is the whole point of drawing them together.
   Naming the band after its SOURCE instead put "Reconstructed estimates" next
   to "United States", which are not two of a kind. Provenance has not gone
   anywhere: it is the first thing in the hover note, the dash pattern still
   separates a reconstruction from a measurement, and the layers panel still
   lists the two sources under their own names. */
const SRC_KEY = {
  industrial: "All countries",
  modern: "All countries",
};

/* The provenance split is COUNTED in the build and carried in the payload, so
   the sentence cannot drift away from the data the way a hand-written "roughly
   a third" could. */
function srcNote(key) {
  if (key === "modern") {
    return "WID via Our World in Data, annual. Shares of household net wealth from "
         + "fiscal data and national balance sheets, interquartile range across "
         + "countries.";
  }
  const p = DATA.meta.industrial_provenance || {};
  const n = (p.named || 0) + (p.interpolated || 0) + (p.correlated || 0);
  return "Alfani and Schifano, whole-country wealth per decade, interquartile range "
       + "across countries. " + p.named + " of " + n + " country-decades are taken from "
       + "a national study, " + p.interpolated + " interpolated, " + p.correlated
       + " inferred from the top-decile share.";
}

/* ONE COLOUR for the band, on both measures, because the key now gives it one
   name. Grey is the neutral everybody-colour and it leaves the blue to mean the
   single country the reader picked, which is the comparison the panel exists to
   make. The accounts band used to be --w-now, the same #2f6fb2 as --w-pick, so
   the spread of every country and the one country chosen out of it were drawn
   in one colour and the key printed the swatch twice. Teal fixed the collision
   and introduced a hue the palette had no other use for. --w-now still names
   the modern layer in the panel that lists the four sources.

   The dash pattern, not the hue, is what separates a reconstruction from a
   measurement. */
const SOURCE_STYLE = {
  industrial: { colour: "var(--w-mid)", dashed: true },
  modern: { colour: "var(--w-mid)", dashed: false },
};

/* One country-level source per measure, not two. WID publishes no Gini, so
   that measure can only come from the decadal estimates; the shares come from
   the national accounts, which cover five times as many countries and are
   measured rather than reconstructed. Showing both on the shares put a
   reconstructed band and a measured one side by side with nothing to choose
   between them but the dash pattern. */
const METRIC_SOURCE = {
  gini: ["industrial"],
  top10: ["modern"],
  top1: ["modern"],
};

const yearLabel = (y) => (y < 0 ? `${Math.abs(y).toLocaleString()} BC` : `${y}`);

/* Round year ticks for a panel, at whatever interval gives roughly `want` of
   them. A panel spanning 10,000 years and one spanning 200 both need labels a
   reader recognises, so the step comes off a 1/2/5 ladder rather than being
   the span divided by a count, which produces marks like 1837 and 4611. */
/* The panel is divided into equal parts and a tick goes at each division, so
   the labels are evenly spread from edge to edge with no short gap at the end.

   The obvious alternative, stepping by a round number, is what was here before
   and it leaves a ragged remainder: a panel running 1283 to 1800 stepped by 200
   labelled 1283, 1483 and 1683 and then stopped 117 years short of its own
   right edge. Round numbers are worth less here than even spacing, because the
   spacing is what a reader uses to judge distance. Labels are rounded to
   something readable and sit at their true position. */
function ticksFor(x0, x1, want) {
  const span = x1 - x0;
  if (span <= 0) return [x0];
  // one interval is allowed, so a phone can ask for just the two ends
  const n = Math.max(1, Math.min(6, want));
  const step = span / n;
  const grain = step > 1000 ? 100 : step > 200 ? 50 : step > 40 ? 10 : 1;
  /* The two ends are the panel's exact bounds, never rounded. Rounding them
     gave the boundary year two different labels on the two panels that share
     it: 1283 came out as "1300" on the left of the gutter and "1280" on the
     right, which reads as an error rather than as rounding. */
  const out = [x0];
  for (let i = 1; i < n; i += 1) {
    out.push(Math.round((x0 + step * i) / grain) * grain);
  }
  out.push(x1);
  return out;
}
const fmt = (v) => (METRICS[state.metric].pct ? `${v.toFixed(1)}%` : v.toFixed(2));

/* --------------------------------------------------------------- what exists */

function pointsIn(era, metric) {
  return DATA.points.filter((p) => p.layer === era && !p.rollup && p[metric] != null);
}

function countrySeries(iso, era, metric) {
  const c = DATA.countries[iso];
  if (!c || !c[era]) return [];
  return c[era][metric] || [];
}

/* Median and quartiles across every country with a reading that year. This
   replaces a faint line per country: 215 of them was a grey scribble that hid
   the one line the reader had chosen, and told them nothing about the spread
   they were meant to be reading it against. */
function distribution(era, metric) {
  const byYear = new Map();
  for (const c of Object.values(DATA.countries)) {
    for (const [y, v] of (c[era] && c[era][metric]) || []) {
      if (!byYear.has(y)) byYear.set(y, []);
      byYear.get(y).push(v);
    }
  }
  const at = (arr, q) => {
    const i = (arr.length - 1) * q;
    const lo = Math.floor(i), hi = Math.ceil(i);
    return arr[lo] + (arr[hi] - arr[lo]) * (i - lo);
  };
  return [...byYear.entries()]
    .filter(([, vs]) => vs.length >= 4)     // a quartile over three countries is noise
    .map(([y, vs]) => {
      vs.sort((a, b) => a - b);
      return { year: y, p25: at(vs, 0.25), p50: at(vs, 0.5), p75: at(vs, 0.75), n: vs.length };
    })
    .sort((a, b) => a.year - b.year);
}

/* A locally weighted average, Gaussian kernel.

   The rolling median of nine that this replaces was jumpy for a reason worth
   writing down: it steps a fixed COUNT of observations at a time, so where the
   sites cluster it crawls and where they are sparse it leaps centuries between
   consecutive output points, and the median itself jumps whole values as one
   observation enters the window and another leaves. On irregularly dated data
   that produces a staircase, which is an artefact of the estimator rather than
   anything in the record.

   This evaluates on a regular grid instead and weights every observation by
   its distance in TIME, so nothing enters or leaves abruptly and the spacing of
   the output does not depend on the spacing of the input. Bandwidth is a share
   of the span, which is the only free parameter and is stated on the page. */
function kernelSmooth(pairs, { band = 0.12, steps = 64 } = {}) {
  const xs = pairs.filter((p) => p[1] != null).sort((a, b) => a[0] - b[0]);
  /* Twelve, not five. Below that the line is a drawing of the sample rather
     than a summary of it: eleven dig sites scattered across the 1283 to 1800
     panel produced a confident-looking curve that was really four points and a
     gap. A panel with too few observations shows its dots and no line. */
  if (xs.length < 12) return [];
  const lo = xs[0][0], hi = xs[xs.length - 1][0];
  if (hi === lo) return [];
  /* The bandwidth is a share of the SPAN, floored at a multiple of the typical
     SPACING. On the decadal estimates a span-only bandwidth came out at 9.5
     years against a 10-year step, so each output point was dominated by the
     single nearest observation and the "smoothed" line was the raw staircase.
     Floored at two and a half steps it is a smooth curve, and short holes in
     the annual series close while the twenty and thirty year ones stay open. */
  const gaps = xs.slice(1).map((p, i) => p[0] - xs[i][0]).sort((a, b) => a - b);
  const step = gaps[Math.floor(gaps.length / 2)] || 1;
  const h = Math.max((hi - lo) * band, step * 2.5);
  const out = [];
  for (let i = 0; i <= steps; i += 1) {
    const x = lo + ((hi - lo) * i) / steps;
    let num = 0, den = 0;
    for (const [xi, yi] of xs) {
      const w = Math.exp(-0.5 * ((x - xi) / h) ** 2);
      num += w * yi; den += w;
    }
    /* Where the nearest observation is more than two bandwidths away the
       weights collapse to nothing and the estimate is meaningless, so the line
       simply stops rather than interpolating across an empty stretch. */
    if (den > 0.6) out.push([Math.round(x), num / den]);
  }
  return out;
}

/* Split a series wherever it jumps a hole big enough that joining across it
   would be an assertion rather than a drawing. The threshold is five times the
   series' own typical step, floored at fifteen years, which keeps an annual
   series continuous through the odd missing year and through the ten-year steps
   of the nineteenth century, and breaks it over the twenty and thirty year ones
   that the quartile band beside it also declines to cross. */
function breakOnGaps(pairs) {
  if (pairs.length < 2) return pairs.length ? [pairs] : [];
  const gaps = pairs.slice(1).map((p, i) => p[0] - pairs[i][0]).sort((a, b) => a - b);
  const step = gaps[Math.floor(gaps.length / 2)] || 1;
  const max = Math.max(15, step * 5);
  const out = [[pairs[0]]];
  for (let i = 1; i < pairs.length; i += 1) {
    if (pairs[i][0] - pairs[i - 1][0] > max) out.push([]);
    out[out.length - 1].push(pairs[i]);
  }
  return out.filter((seg) => seg.length);
}

function inPeriod(period, year) {
  return year >= period.from && year < period.to;
}

/* The quartile band is jagged for a reason that is not in the data: the set
   of countries reporting changes from year to year, so a quartile jumps as one
   enters or leaves rather than because anybody's wealth moved. Each of the
   three lines is put through the same kernel used for the scatters, which
   leaves the level alone and takes out the sampling chatter. */
function smoothBand(dist) {
  if (dist.length < 12) return dist;
  const at = {};
  for (const k of ["p25", "p50", "p75"]) {
    for (const [y, v] of kernelSmooth(dist.map((d) => [d.year, d[k]]), { band: 0.05 })) {
      (at[y] = at[y] || {})[k] = v;
    }
  }
  const n = Object.fromEntries(dist.map((d) => [d.year, d.n]));
  return Object.entries(at)
    .filter(([, v]) => v.p25 != null && v.p50 != null && v.p75 != null)
    .map(([y, v]) => ({ year: +y, ...v, n: n[+y] ?? dist[0].n }))
    .sort((a, b) => a.year - b.year);
}

function periodContent(period, metric) {
  const pts = DATA.points.filter((p) =>
    !p.rollup && p[metric] != null && inPeriod(period, p.year))
    .map((p) => ({ ...p, toggle: p.layer === "deep" ? "deep" : "town" }));

  /* Alfani's regional figures are point estimates every fifty years, not a
     continuous series, so they are drawn as dots like everything else in the
     panel rather than as lines over the top of it. Charlie asked why the middle
     panel had both, and the answer was that it should not: one panel, one kind
     of mark, one summary line. They are hollow because they are an aggregate of
     many places rather than a single assessment, and they are the ONLY evidence
     for Holland and Flanders, so they cannot simply be dropped. */
  const regionPts = DATA.regions.flatMap((r) =>
    (r[metric] || []).filter(([y]) => inPeriod(period, y)).map(([y, v]) => ({
      place: r.label, group: "Regional estimate", layer: "preindustrial",
      year: y, [metric]: v, aggregate: true, n: null, toggle: "region",
      basis: "Alfani's estimate for the whole state, every fifty years",
    })));

  const series = (METRIC_SOURCE[metric] || []).map((key) => ({
    key,
    label: DATA.meta.layers[key].label,
    dist: smoothBand(distribution(key, metric)).filter((d) => inPeriod(period, d.year)),
    sel: state.country === ALL
      ? [] : countrySeries(state.country, key, metric).filter(([y]) => inPeriod(period, y)),
    ...SOURCE_STYLE[key],
  })).filter((x) => x.dist.length > 1 || x.sel.length > 1);

  const all = [...pts, ...regionPts];

  /* One trend line per evidence type, never across them. A median drawn
     through dig sites and tax assessments together would be a summary of two
     different measurements. */
  const trends = [];
  for (const [layer, colour] of [["deep", "var(--w-deep)"], ["preindustrial", "var(--w-early)"]]) {
    if (layer === "deep" && period.key !== "ancient") continue;
    const own = all.filter((p) => p.layer === layer).map((p) => [p.year, p[metric]]);
    const line = kernelSmooth(own);
    if (line.length > 1) trends.push({ layer, colour, line });
  }

  return { pts: all, regions: [], series, trends };
}

/* How many years a panel covers, from its own bounds where they are finite
   and from its data where they are not. */
function spanOf(era) {
  const c = era.content;
  const ys = [...c.pts.map((p) => p.year),
              ...c.series.flatMap((x) => [...x.dist.map((d) => d.year),
                                          ...x.sel.map(([y]) => y)])];
  const lo = era.from > -1e8 ? era.from : (ys.length ? Math.min(...ys) : 0);
  const hi = era.to < 1e8 ? era.to : (ys.length ? Math.max(...ys) : 1);
  return Math.max(1, hi - lo);
}

function activeEras(metric) {
  return PERIODS.map((e) => ({ ...e, content: periodContent(e, metric) }))
    .filter((e) => e.content.pts.length || e.content.regions.length || e.content.series.length);
}

/* ------------------------------------------------------------------- drawing */

function boxFor(svgId, ratio, minH, maxH) {
  const svg = $(svgId);
  const measured = Math.round(svg.parentElement.getBoundingClientRect().width);
  const w = measured > 40 ? measured
    : Math.round(clamp(280, document.documentElement.clientWidth - 76, 920));
  return { w, h: Math.round(clamp(minH, w * ratio, maxH)) };
}

/* Both an aria-label and a <title>: screen readers take the label, and a
   browser's own tooltip takes the title, so a keyboard user and a mouse user
   get the same sentence. Dropped in a rewrite, which threw at the end of two
   chart functions and stopped the ones after them ever running. */
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

/* A touch screen has no hover, so pointerenter fired on tap and pointerleave
   fired again the moment the finger lifted: the readout appeared and vanished
   inside the same gesture and a dot was effectively unreadable on a phone. On a
   coarse pointer the readout is PINNED instead - one tap opens it, and it stays
   until the next tap somewhere else. Nothing closes it in between, which is the
   point: a reader wants to look at the number, not hold a finger still. */
const COARSE = window.matchMedia("(hover: none)").matches;

const hook = (el, show) => {
  if (COARSE) {
    el.addEventListener("pointerdown", show);
    return;
  }
  el.addEventListener("pointerenter", show);
  el.addEventListener("pointermove", show);
};

/* Only a mouse leaving the chart clears it. */
const clearOnLeave = (svg, readout) => {
  svg.onpointerleave = COARSE ? null : () => { readout.hidden = true; };
};

function drawEras() {
  const metric = state.metric, M = METRICS[metric];
  const eras = activeEras(metric);
  const svg = $("#eras");
  const readout = $("#eras-readout");
  svg.innerHTML = "";
  readout.hidden = true;

  /* The panels stay side by side on a phone. Stacking them gave each its own
     y axis and its own block of white space, and three little charts down the
     page stopped reading as one timeline at all. Narrow and tall instead: the
     shared vertical scale is the whole argument, and it only works if they sit
     against each other. */
  const narrow = window.matchMedia("(max-width: 700px)").matches;
  const stacked = false;
  const box = boxFor("#eras", narrow ? 1.15 : 0.46, narrow ? 300 : 260, narrow ? 460 : 430);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);

  /* More room on the right at phone width: the last tick is centred on the
     panel's right edge, so at r=8 the "2010" ran off the side of the SVG. */
  const pad = { l: narrow ? 30 : 44, r: narrow ? 20 : 8, t: 10, b: 40 };
  const gut = narrow ? 7 : 16;
  const iw = box.w - pad.l - pad.r;

  /* On a phone the panels stack, each getting the full width and its own y
     axis. Side by side at 375px they would be 70px wide apiece. */
  const lanes = eras.map((e, i) => {
    if (stacked) {
      const laneH = (box.h - pad.t - pad.b) / eras.length;
      return { x: pad.l, w: iw, y: pad.t + i * laneH, h: laneH - 34 };
    }
    /* Width by the LOG of the span. Equal widths made 10,000 years and 200
       years the same size, which is what an inconsistent timescale looks like.
       Strictly proportional leaves the modern panel four pixels wide, and the
       square root was still harsh enough to squash the panel holding most of
       the data into an unreadable scribble. Log is the gentle version: the
       first panel is visibly the longest and the last is still legible. */
    const room = iw - gut * (eras.length - 1);
    const wts = eras.map((e) => Math.log10(Math.max(10, spanOf(e))));
    const total = wts.reduce((a, v) => a + v, 0);
    const x = pad.l + wts.slice(0, i).reduce((a, v) => a + (v / total) * room, 0) + i * gut;
    return { x, w: (wts[i] / total) * room, y: pad.t, h: box.h - pad.t - pad.b };
  });

  const ticks = M.max === 1 ? [0, 0.25, 0.5, 0.75, 1] : [0, 25, 50, 75, 100];
  const yOf = (lane, v) => lane.y + (1 - v / M.max) * lane.h;

  eras.forEach((era, i) => {
    const lane = lanes[i];
    const { pts, regions, series, trends } = era.content;
    const years = [
      ...pts.map((p) => p.year),

      ...series.flatMap((x) => [...x.dist.map((d) => d.year), ...x.sel.map(([y]) => y)]),
    ];
    /* The axis runs to the PERIOD boundary, not to the last observation in
       it. Left on the data, the first panel ended at 1243 and the second began
       at 1283, which put a forty-year hole between two panels that are meant to
       tile. Only the open outer ends take their bound from the data. */
    let x0 = era.from > -1e8 ? era.from : Math.min(...years);
    let x1 = era.to < 1e8 ? era.to : Math.max(...years);
    if (x0 === x1) { x0 -= 1; x1 += 1; }
    const padY = (x1 - x0) * 0.03;
    const xOf = (y) => lane.x + ((y - (x0 - padY)) / ((x1 + padY) - (x0 - padY))) * lane.w;

    // gridlines, and the y labels only where they will be read
    for (const t of ticks) {
      const y = yOf(lane, t);
      svg.appendChild(svgEl("line", {
        x1: lane.x, x2: lane.x + lane.w, y1: y.toFixed(1), y2: y.toFixed(1),
        stroke: "var(--rule)", "stroke-width": 1,
      }));
      if (i === 0 || stacked) {
        const lab = svgEl("text", {
          x: lane.x - 8, y: (y + 4).toFixed(1), "text-anchor": "end",
          "font-size": 11, fill: "var(--ink-faint)",
        });
        lab.textContent = M.pct ? `${t}%` : t.toFixed(2);
        svg.appendChild(lab);
      }
    }

    /* No panel headers at all. They read "9,200 BC to 1283" over an axis
       whose first and last ticks are 9,200 BC and 1283, which is the same two
       years printed twice, eight pixels apart. They came off the phone layout
       first, for collisions; the redundancy is the better reason and it holds
       at every width. */

    /* The panels share their boundary years, so without this the same year is
       printed twice, once either side of the gutter. The left panel keeps it. */
    // ends only on a phone: a 100px lane cannot hold three dates
    const xticks = ticksFor(x0, x1, narrow ? 1 : Math.max(2, Math.round(lane.w / 78)));
    for (const [ti, t] of xticks.entries()) {
      if (i > 0 && ti === 0) continue;
      const tx = xOf(t);
      if (tx < lane.x - 1 || tx > lane.x + lane.w + 1) continue;
      svg.appendChild(svgEl("line", {
        x1: tx.toFixed(1), x2: tx.toFixed(1),
        y1: (lane.y + lane.h).toFixed(1), y2: (lane.y + lane.h + 4).toFixed(1),
        stroke: "var(--rule)", "stroke-width": 1,
      }));
      const lab = svgEl("text", {
        // 20, not 17: at 17 the first x label's box clipped the bottom y label's
        x: tx.toFixed(1), y: (lane.y + lane.h + 20).toFixed(1),
        "text-anchor": "middle", "font-size": 10.5, fill: "var(--ink-faint)",
      });
      // the last tick names the period's end, which is the header's year
      lab.textContent = yearLabel(ti === xticks.length - 1 ? (era.labelTo ?? t) : t);
      svg.appendChild(lab);
    }

    if (i < eras.length - 1 && !stacked) {
      svg.appendChild(svgEl("line", {
        x1: (lane.x + lane.w + gut / 2).toFixed(1), x2: (lane.x + lane.w + gut / 2).toFixed(1),
        y1: lane.y, y2: lane.y + lane.h,
        stroke: "var(--rule)", "stroke-width": 1, "stroke-dasharray": "2 4",
      }));
    }

    // ---- one quartile band and one country line per source on this panel
    for (const src of series) {
      if (src.dist.length > 1) {
        const top = src.dist.map((d) => `${xOf(d.year).toFixed(1)},${yOf(lane, d.p75).toFixed(1)}`);
        const bot = src.dist.slice().reverse()
          .map((d) => `${xOf(d.year).toFixed(1)},${yOf(lane, d.p25).toFixed(1)}`);
        svg.appendChild(svgEl("polygon", {
          points: [...top, ...bot].join(" "),
          fill: src.colour, "fill-opacity": src.dashed ? 0.1 : 0.15,
        }));
        svg.appendChild(svgEl("polyline", {
          points: src.dist.map((d) => `${xOf(d.year).toFixed(1)},${yOf(lane, d.p50).toFixed(1)}`).join(" "),
          fill: "none", stroke: src.colour, "stroke-width": 1.5,
          "stroke-opacity": 0.5, "stroke-dasharray": "4 3",
        }));
      }
      /* NOT smoothed, unlike the band above it, and the difference is the
         point. The band wobbles because the SET of reporting countries changes
         from year to year, which is an artefact of the sample. One country's
         line wobbles because that country's wealth moved, which is the thing
         you picked the country to see. Britain's top decile shifts 2.9 points
         inside a single year at the 90th percentile of its own steps, and a
         kernel wide enough to calm that would also flatten 1929 to 1932.

         What the country line DID borrow from the band is where to stop. The
         modern series is annual from about 1910 and decadal or worse before
         it, so a plain polyline drew a confident straight segment across the
         thirty-year hole either side of 1850, while the band beside it, which
         stops once the nearest reading is more than about sixteen years away,
         correctly showed nothing there. Two lines disagreeing about whether
         data exists reads as a bug. */
      for (const seg of breakOnGaps(src.sel)) {
        /* A reading with no neighbour close enough to join to is drawn as a
           dot rather than dropped. Britain and America both have single
           readings at 1820, 1850 and 1880 with thirty years either side, and
           silently discarding them would have replaced one wrong impression,
           that the series is continuous, with another, that nothing was
           measured before 1900. */
        if (seg.length === 1) {
          svg.appendChild(svgEl("circle", {
            cx: xOf(seg[0][0]).toFixed(1), cy: yOf(lane, seg[0][1]).toFixed(1),
            r: 2.8, fill: "var(--w-pick)",
          }));
          continue;
        }
        const line = svgEl("polyline", {
          points: seg.map(([y, v]) => `${xOf(y).toFixed(1)},${yOf(lane, v).toFixed(1)}`).join(" "),
          fill: "none", stroke: "var(--w-pick)", "stroke-width": src.dashed ? 2 : 2.6,
          "stroke-linejoin": "round", "stroke-linecap": "round",
        });
        if (src.dashed) line.setAttribute("stroke-dasharray", "6 4");
        svg.appendChild(line);
      }
    }

    // ---- a rolling median through each scatter
    for (const tr of trends) {
      svg.appendChild(svgEl("polyline", {
        points: tr.line.map(([y, v]) => `${xOf(y).toFixed(1)},${yOf(lane, v).toFixed(1)}`).join(" "),
        fill: "none", stroke: tr.colour, "stroke-width": 2.4,
        "stroke-linejoin": "round", "stroke-linecap": "round", "stroke-opacity": 0.95,
      }));
    }

    /* House sizes are the weakest evidence on the page and they only earn a
       place where nothing better survives. Eleven dig sites fall after 1283,
       inside panels that have tax registers or national accounts, and drawing
       them there put a scatter of orange next to far better measurements of the
       same centuries. They stay in the settlement-size chart, which is what
       they are actually good for. */
    /* ---- a hover band for the line panels, because an annual point is
       smaller than a fingertip.

       It is appended BEFORE the dots, not after. SVG hit-testing gives the
       pointer to whatever was drawn last, so a full-lane transparent rect
       added at the end covered all 63 excavated sites and every tax
       assessment: their hover handlers were wired correctly and could never
       fire, and hovering a dot produced the panel's readout instead of that
       site's. */
    if (series.length || trends.length) {
      const band = svgEl("rect", {
        x: lane.x, y: lane.y, width: lane.w, height: lane.h, fill: "transparent",
      });
      hook(band, (evt) => {
        const r = svg.getBoundingClientRect();
        const px = (evt.clientX - r.left) * (box.w / r.width);
        const yr = Math.round((x0 - padY) + ((px - lane.x) / lane.w) * ((x1 + padY) - (x0 - padY)));
        const near = (arr, get) => arr.reduce((best, d) =>
          (!best || Math.abs(get(d) - yr) < Math.abs(get(best) - yr)) ? d : best, null);
        const label = state.country === ALL
          ? "All countries" : (DATA.countries[state.country]?.label || state.country);
        const bits = [`<b>${yearLabel(yr)}</b>`];
        /* The averages are the only thing drawn in two of the three panels, so
           without these the left of the chart had no readout at all. */
        for (const tr of trends) {
          const near = tr.line.reduce((best, p) =>
            (!best || Math.abs(p[0] - yr) < Math.abs(best[0] - yr)) ? p : best, null);
          if (near && Math.abs(near[0] - yr) <= Math.max(8, (x1 - x0) / 40)) {
            bits.push(`<div class="row"><span>${LAYER_DOT[tr.layer === "deep"
              ? "deep" : "town"][1]}, average</span><span>${fmt(near[1])}</span></div>`);
          }
        }
        /* Both sources at once where both reach this year. Seeing a
           reconstruction and a measurement disagree is the point of the panel,
           not a glitch to hide. */
        for (const src of series) {
          const sp = near(src.sel, (p) => p[0]);
          const dp = near(src.dist, (d) => d.year);
          if (sp && Math.abs(sp[0] - yr) <= 8) {
            bits.push(`<div class="row"><span>${label}</span>` +
                      `<span>${fmt(sp[1])}</span></div>`);
          }
          if (dp && Math.abs(dp.year - yr) <= 8) {
            bits.push(`<div class="row"><span>middle country</span>` +
                      `<span>${fmt(dp.p50)}</span></div>`,
              `<div class="row"><span>middle half</span>` +
              `<span>${fmt(dp.p25)} to ${fmt(dp.p75)}</span></div>`);
          }
        }
        if (bits.length === 1) { readout.hidden = true; return; }
        readout.innerHTML = bits.join("");
        readout.hidden = false;
        placeReadout(readout, evt);
      });
      svg.appendChild(band);
    }

    const better = i > 0;
    for (const p of pts) {
      if (!state.scatter[p.toggle]) continue;
      if (p.layer === "deep" && better) continue;
      /* A whole region is the same shape as a single town, a shade
         darker. Hollow rings read as a different KIND of thing and drew more
         attention than an aggregate deserves next to the towns it averages. */
      const hue = p.layer === "deep" ? "var(--w-deep)"
        : p.aggregate ? "var(--w-region)" : "var(--w-early)";
      const dot = svgEl("circle", {
        cx: xOf(p.year).toFixed(1), cy: yOf(lane, p[metric]).toFixed(1),
        r: p.aggregate ? 3.8 : 3.2, class: "dot",
        fill: hue, "fill-opacity": p.aggregate ? 0.85 : 0.6,
      });
      hook(dot, (evt) => {
        readout.innerHTML = `<b>${p.place}</b>` +
          `<div class="row"><span>${yearLabel(p.year)}</span><span>${fmt(p[metric])}</span></div>` +
          (p.n ? `<div class="row"><span>households sampled</span>` +
                 `<span>${Math.round(p.n).toLocaleString()}</span></div>` : "") +
          (p.group ? `<div class="row"><span>region</span><span>${p.group}</span></div>` : "") +
          `<div class="prov">${DATA.meta.layers[p.layer].label}. ${p.basis}</div>`;
        readout.hidden = false;
        placeReadout(readout, evt);
      });
      svg.appendChild(dot);
    }

  });

  clearOnLeave(svg, readout);
  svg.setAttribute("aria-label",
    `${M.label}, in ${eras.length} panels: ` +
    eras.map((e) => e.label).join(", ") +
    ". Each panel has its own time scale and they share one vertical scale.");

  $("#eras-title").textContent = M.label;
  $("#eras-blurb").textContent = M.blurb;
  /* The count changes with the measure: no national accounts publish a Gini
     and no historian's estimate reaches the
     richest 1%, so the panel count follows the measure. */
  $("#eras-caption").textContent =
    "Each panel has its own time scale. Only the heights are comparable.";
}

/* ------------------------------------------------- the archaeology, two cuts */

/* Camp, village, town, city. Kohler's own site classification, and a better
   cut than his five-step political taxonomy: the words need no glossary, the
   medians are monotonic where the political one has a flat spot, and it is the
   same claim about scale. The political coding is still in the payload. */
/* Camp is dropped: two sites is not a category, it is two sites, and a box
   plot over n=2 draws a box that means nothing. The foraging figure survives in
   the caption where it can be stated as what it is. */
const SIZES = ["village", "town", "city"];
const SIZE_LABEL = { village: "Village", town: "Town", city: "City" };

function deepSites() {
  return DATA.points.filter((p) => p.layer === "deep" && p.gini != null);
}

const median = (xs) => {
  const v = xs.slice().sort((a, b) => a - b);
  const i = (v.length - 1) / 2;
  return v.length % 2 ? v[i] : (v[i - 0.5] + v[i + 0.5]) / 2;
};

const quantile = (xs, q) => {
  const v = xs.slice().sort((a, b) => a - b);
  const i = (v.length - 1) * q;
  const lo = Math.floor(i), hi = Math.ceil(i);
  return v[lo] + (v[hi] - v[lo]) * (i - lo);
};

/* A box plot, not a bar chart of the medians. n runs 2 to 28 per row and the
   ranges overlap heavily - towns run 0.12 to 0.68 - so bars would assert a
   precision the sample cannot carry. The box is the middle half, the line in it
   is the median, the whisker is the full range, and every site is still drawn
   as a dot so the reader can count them. */
function drawScale() {
  const svg = $("#scale");
  const readout = $("#scale-readout");
  svg.innerHTML = ""; readout.hidden = true;

  const rows = SIZES
    .map((k) => ({ key: k, pts: deepSites().filter((p) => p.settlement === k) }))
    .filter((r) => r.pts.length);
  if (!rows.length) return;

  const narrow = window.matchMedia("(max-width: 700px)").matches;
  const box = boxFor("#scale", narrow ? 0.62 : 0.34, 180, 300);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: narrow ? 62 : 84, r: 16, t: 8, b: 30 };
  const iw = box.w - pad.l - pad.r;
  const rowH = (box.h - pad.t - pad.b) / rows.length;
  const xOf = (v) => pad.l + v * iw;

  for (const t of [0, 0.2, 0.4, 0.6, 0.8, 1]) {
    svg.appendChild(svgEl("line", {
      x1: xOf(t).toFixed(1), x2: xOf(t).toFixed(1), y1: pad.t,
      y2: (box.h - pad.b).toFixed(1), stroke: "var(--rule)", "stroke-width": 1,
    }));
    const lab = svgEl("text", {
      x: xOf(t).toFixed(1), y: (box.h - pad.b + 17).toFixed(1),
      "text-anchor": "middle", "font-size": 11, fill: "var(--ink-faint)",
    });
    lab.textContent = t.toFixed(1);
    svg.appendChild(lab);
  }

  rows.forEach((row, i) => {
    const cy = pad.t + i * rowH + rowH / 2;
    const vals = row.pts.map((p) => p.gini);
    const q1 = quantile(vals, 0.25), q3 = quantile(vals, 0.75), m = median(vals);
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const bh = Math.min(26, rowH * 0.5);

    const name = svgEl("text", {
      x: pad.l - 12, y: (cy + 1).toFixed(1), "text-anchor": "end",
      "font-size": 13, fill: "var(--ink)",
    });
    name.textContent = SIZE_LABEL[row.key] || row.key;
    svg.appendChild(name);
    const n = svgEl("text", {
      x: pad.l - 12, y: (cy + 15).toFixed(1), "text-anchor": "end",
      "font-size": 10.5, fill: "var(--ink-faint)",
    });
    n.textContent = `${row.pts.length} site${row.pts.length === 1 ? "" : "s"}`;
    svg.appendChild(n);

    // whisker across the full range
    svg.appendChild(svgEl("line", {
      x1: xOf(lo).toFixed(1), x2: xOf(hi).toFixed(1),
      y1: cy.toFixed(1), y2: cy.toFixed(1),
      stroke: "var(--w-deep)", "stroke-width": 1.4, "stroke-opacity": 0.55,
    }));
    // the middle half
    svg.appendChild(svgEl("rect", {
      x: xOf(q1).toFixed(1), y: (cy - bh / 2).toFixed(1),
      width: Math.max(1, xOf(q3) - xOf(q1)).toFixed(1), height: bh.toFixed(1),
      rx: 3, fill: "var(--w-deep)", "fill-opacity": 0.2,
      stroke: "var(--w-deep)", "stroke-opacity": 0.5, "stroke-width": 1,
    }));

    for (const p of row.pts) {
      // on the line, not scattered around it: the vertical axis here is the
      // category, so vertical position carried no meaning and read as one
      const dot = svgEl("circle", {
        cx: xOf(p.gini).toFixed(1), cy: cy.toFixed(1),
        r: 3, fill: "var(--w-deep)", "fill-opacity": 0.5, class: "dot",
      });
      hook(dot, (evt) => {
        const ci = (p.lo != null && p.hi != null)
          ? `<div class="row"><span>80% interval</span>`
            + `<span>${p.lo.toFixed(2)} to ${p.hi.toFixed(2)}</span></div>` : "";
        readout.innerHTML = `<b>${p.place}</b>` +
          `<div class="row"><span>${yearLabel(p.year)}</span>` +
          `<span>${p.gini.toFixed(2)}</span></div>` + ci +
          `<div class="row"><span>economy</span><span>${p.feeding || "unknown"}</span></div>` +
          `<div class="prov">${p.group}</div>`;
        readout.hidden = false; placeReadout(readout, evt);
      });
      svg.appendChild(dot);
    }

    // the median, on top of everything
    svg.appendChild(svgEl("line", {
      x1: xOf(m).toFixed(1), x2: xOf(m).toFixed(1),
      y1: (cy - bh / 2).toFixed(1), y2: (cy + bh / 2).toFixed(1),
      stroke: "var(--w-median)", "stroke-width": 2.6, "stroke-linecap": "round",
    }));
  });

  clearOnLeave(svg, readout);
  const first = median(rows[0].pts.map((p) => p.gini));
  const last = median(rows[rows.length - 1].pts.map((p) => p.gini));
  const yrs = deepSites().map((p) => p.year);
  $("#scale-sub").textContent =
    `${deepSites().length} excavated settlements, ${yearLabel(Math.min(...yrs))} to `
    + `${yearLabel(Math.max(...yrs))}.`;
  $("#scale-caption").textContent =
    `Median Gini ${first.toFixed(2)} in villages, ${last.toFixed(2)} in cities.`;
  describe(svg, "Wealth Gini at every excavated site, grouped by whether the "
                + "site was a camp, a village, a town or a city.");
}

/* ----------------------------------------------------------------- furniture */

/* colour, label, and what it actually is. The explanation is on the key
   itself because that is where a reader is when the question occurs to them,
   and the panel that spells all four out is a long way down the page. */
/* The measure as a noun that fits mid-sentence. METRICS[].label is the control's
   wording ("Share held by the richest 10%") and does not. */
const MEASURE_NOUN = {
  gini: "Gini", top10: "Top-decile share", top1: "Top-percentile share",
};

const LAYER_DOT = {
  /* Counted, not typed. "63 excavated sites, 9200 BC to AD 1970" was three
     numbers written into a string beside a payload that already knows all
     three, which is how a caption ends up describing the file it used to be
     built from. */
  deep: ["var(--w-deep)", "Excavated sites",
         () => {
           const ys = DATA.points.filter((p) => p.layer === "deep").map((p) => p.year);
           return `Kohler and others, ${ys.length} excavated sites, `
                + `${yearLabel(Math.min(...ys))} to AD ${Math.max(...ys)}. Each Gini `
                + "is taken across house floor areas, the standard proxy for "
                + "household wealth where nothing was written down.";
         }],
  /* A FUNCTION, because this layer supplies deciles as well as Ginis and the
     note names the measure. Written as a fixed string it said "Gini of taxable
     wealth" while the chart was drawing the top-decile share. */
  town: ["var(--w-early)", "Tax records",
         () => `${MEASURE_NOUN[state.metric]} of taxable wealth from lay subsidies `
             + "and estimi, one jurisdiction per observation. Alfani. English "
             + "figures corrected for households below the assessment threshold."],
  region: ["var(--w-region)", "Whole regions",
           "Alfani's state-level estimates, fifty-year intervals. Aggregated "
           + "over many local registers."],
};

/* Which scatter layers have an average drawn through them. The line is the same
   colour as its own dots, which is why it needs no key entry of its own: see
   the note in renderLegend. */
const TRENDED = new Set(["deep", "town"]);
const TREND_NOTE = " The line through them is a locally weighted average, "
                 + "Gaussian kernel.";

function renderLegend() {
  const eras = activeEras(state.metric);
  const pts = eras.flatMap((e) => e.content.pts);
  const hasToggle = (k) => pts.some((p) => p.toggle === k);
  const trends = eras.flatMap((e) => e.content.trends);
  const sources = eras.flatMap((e) => e.content.series);

  /* Every entry is a thing on the chart, and every thing on the chart has an
     entry. Both halves of that have been broken before. The three scatter
     entries are buttons: pressing one folds its observations away.

     ORDER FOLLOWS THE CHART, left to right. The key used to lead with the two
     summary lines and finish with the observations, which put "Excavated sites"
     at the far right of the key and its dots at the far left of the panel.
     Reading order now matches: the dig sites and the tax records first, because
     that is the order their panels appear in, then the two things drawn across
     the top of the panels they belong to, then the country the reader picked. */
  const out = [];
  for (const key of SCATTERS) {
    if (!hasToggle(key)) continue;
    const [colour, label, rawNote] = LAYER_DOT[key];  // note may be a function
    const note = typeof rawNote === "function" ? rawNote() : rawNote;
    /* The average line has no entry of its own. It used to, and the entry was
       wrong twice over: it read as a duplicate of the quartile band, which is a
       different layer entirely rather than a second summary of the same one,
       and where BOTH a terracotta and a gold average were drawn the single
       entry took a neutral grey swatch matching neither line. Folded into the
       dots it runs through, the key is one entry per colour again. */
    const trended = TRENDED.has(key === "town" ? "town" : key)
      && trends.some((t) => (t.layer === "deep" ? "deep" : "town") === key);
    out.push({ colour, label, note: note + (trended ? TREND_NOTE : ""),
               toggle: key, on: state.scatter[key] });
  }
  for (const src of sources) {
    out.push({ colour: src.colour, label: SRC_KEY[src.key] || src.label,
               note: srcNote(src.key) });
  }
  /* No note. The entry is the country's own name in the same blue as its line,
     which is the whole of what it means, and an explainer that only restated
     the drawing conventions was the least useful thing in the key. Entries with
     no note also lose the dotted underline, so nothing invites a hover that
     returns nothing. */
  if (sources.length && state.country !== ALL) {
    out.push({ colour: "var(--w-pick)",
               label: DATA.countries[state.country]?.label || state.country });
  }

  const tip = (n) => (n ? ` title="${n.replace(/"/g, "&quot;")}"` : "");
  $("#legend-eras").innerHTML = out.map((e) => (e.toggle
    ? `<button type="button" class="key" data-scatter="${e.toggle}"`
      + `${tip(e.note)} aria-pressed="${e.on}">`
      + `<i style="background:${e.colour}"></i>${e.label}</button>`
    : e.note
      ? `<span class="explained"${tip(e.note)} tabindex="0">`
        + `<i style="background:${e.colour}"></i>${e.label}</span>`
      : `<span><i style="background:${e.colour}"></i>${e.label}</span>`)).join("");

  for (const btn of $("#legend-eras").querySelectorAll("[data-scatter]")) {
    btn.addEventListener("click", () => {
      const k = btn.dataset.scatter;
      state.scatter[k] = !state.scatter[k];
      render();
    });
  }
}

function renderLayers() {
  const L = DATA.meta.layers;
  const present = new Set(
    activeEras("gini").concat(activeEras("top10"))
      .flatMap((e) => [...e.content.pts.map((p) => p.layer),
                       ...e.content.series.map((x) => x.key)]));
  const swatch = { deep: "--w-deep", preindustrial: "--w-early",
                   industrial: "--w-mid", modern: "--w-now" };
  $("#layers").innerHTML = Object.entries(L).map(([key, v]) =>
    `<dt><i style="background:var(${swatch[key]})"></i>${v.label}` +
    (present.has(key) ? "" : ` <span class="pending">not loaded</span>`) +
    `</dt><dd>${v.note}</dd>`).join("");
  $("#sources").innerHTML = DATA.meta.sources.map((s) =>
    `<li><a href="${s.url}" rel="noopener">${s.name}</a>, ${s.publisher}. ${s.role}</li>`).join("");
}

function buildPickers() {
  const sel = $("#country-sel");
  /* Filtered on the CURRENT measure, not on having any data at all. Half the
     list had no Gini, so picking one of those drew the band and no line and
     looked broken. Rebuilt whenever the measure changes; the selection is kept
     if it survives, and falls back to all countries if it does not. */
  /* TWO points, not one. Fifteen countries carry a single decade of
     estimates and nothing else - Slovakia, Malta, Cyprus, Austria and eleven
     others - so on the Gini they passed a `.length` test, appeared in the
     picker, and then drew nothing at all, because a line needs two ends.
     They still sit inside the quartile band, which is where a single
     observation belongs. */
  const usable = (c) => Math.max((c.industrial[state.metric] || []).length,
                                 (c.modern[state.metric] || []).length) > 1;
  const rows = Object.values(DATA.countries).filter(usable)
    .sort((a, b) => a.label.localeCompare(b.label));
  /* "All countries" is not a country: it drops the highlighted line and leaves
     the quartile band, which is every country at once. */
  sel.innerHTML = `<option value="${ALL}">All countries</option>`
    + rows.map((c) => `<option value="${c.iso}">${c.label}</option>`).join("");
  if (state.country !== ALL && !rows.some((c) => c.iso === state.country)) {
    state.country = ALL;
  }
  sel.value = state.country;
  $("#metric-sel").value = state.metric;
}

function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  if (METRICS[p.get("metric")]) state.metric = p.get("metric");
  const c = p.get("country");
  if (c === ALL || (c && DATA.countries[c])) state.country = c;
  for (const k of SCATTERS) {
    if (p.get(k) === "1" || p.get(k) === "0") state.scatter[k] = p.get(k) === "1";
  }
}

function writeHash() {
  const p = new URLSearchParams();
  for (const k of ["metric", "country"]) if (state[k] !== DEFAULTS[k]) p.set(k, state[k]);
  for (const k of SCATTERS) {
    if (state.scatter[k] !== DEFAULTS.scatter[k]) p.set(k, state.scatter[k] ? "1" : "0");
  }
  const h = p.toString();
  try {
    history.replaceState(null, "", h ? `#${h}` : location.pathname + location.search);
  } catch { /* sandboxed iframes refuse this, and it must not take the page down */ }
}

function render() {
  renderLegend();
  drawEras();
  drawScale();
  /* The picker's hint, which until now was always blank. WID imputes the
     wealth distribution of a country with no survey from a regional group, so
     picking Anguilla drew a line that is really the Caribbean, to within a
     hundredth of a point of Antigua, Grenada and thirteen others. The chart
     cannot show that and the reader has no way to know it. */
  const twin = DATA.countries[state.country]?.twin_of;
  $("#country-hint").textContent = twin
    ? `No wealth survey. WID imputes this from a regional group of `
      + `${twin.length + 1}, so the line is all but identical to ${twin[0]}.`
    : "";
  writeHash();
}

function wire() {
  $("#metric-sel").addEventListener("change", (e) => {
    state.metric = e.target.value; buildPickers(); render();
  });
  $("#country-sel").addEventListener("change", (e) => { state.country = e.target.value; render(); });
  let t = null;
  window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(render, 140); });
}

fetch("data.json")
  .then((r) => { if (!r.ok) throw new Error(`data.json ${r.status}`); return r.json(); })
  .then((d) => {
    DATA = d;
    readHash(); buildPickers(); renderLayers(); wire(); render();
    document.body.classList.remove("loading");
  })
  .catch((err) => {
    /* Name which half failed. "Could not load the data" reported for a render
       bug sent an earlier session looking in entirely the wrong place. */
    const stage = DATA ? "draw the charts" : "load the data";
    document.body.classList.remove("loading");
    $("main").insertAdjacentHTML("afterbegin",
      `<section class="panel"><h2>Could not ${stage}</h2><p class="sub">${err.message}</p></section>`);
    throw err;
  });
