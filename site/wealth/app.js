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
const DEFAULTS = {
  metric: "gini", country: "GBR",
  scatter: { deep: true, preindustrial: false },
};
const ALL = "__all";
const state = { ...DEFAULTS, scatter: { ...DEFAULTS.scatter } };
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
    blurb: "Half the mean absolute difference in wealth between any two "
         + "households, over the mean. 0 is a perfectly even distribution, "
         + "1 is the limit where one household holds everything.",
  },
  top10: {
    label: "Share held by the richest 10%", max: 100, pct: true,
    blurb: "The top decile's share of total household wealth in the unit "
         + "being measured, which is a settlement, a county or a country "
         + "depending on the period.",
  },
  top1: {
    label: "Share held by the richest 1%", max: 100, pct: true,
    blurb: "The top percentile's share of total household wealth in the unit "
         + "being measured, which is a settlement, a county or a country "
         + "depending on the period.",
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

const SOURCE_STYLE = {
  industrial: { colour: "var(--w-mid)", dashed: true },
  modern: { colour: "var(--w-now)", dashed: false },
};

const yearLabel = (y) => (y < 0 ? `${Math.abs(y).toLocaleString()} BC` : `${y}`);

/* Round year ticks for a panel, at whatever interval gives roughly `want` of
   them. A panel spanning 10,000 years and one spanning 200 both need labels a
   reader recognises, so the step comes off a 1/2/5 ladder rather than being
   the span divided by a count, which produces marks like 1837 and 4611. */
function ticksFor(x0, x1, want) {
  const span = x1 - x0;
  if (span <= 0) return [x0];
  const raw = span / Math.max(1, want);
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * mag).find((v) => v >= raw) || 10 * mag;
  const out = [];
  for (let t = Math.ceil(x0 / step) * step; t <= x1; t += step) out.push(Math.round(t));
  // a panel whose round steps all fall outside it still needs its ends named
  return out.length >= 2 ? out : [x0, x1];
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

/* A rolling median through scattered observations. The archaeological dots
   are irregular in time and vary by an order of magnitude between neighbouring
   sites, so a mean would chase outliers and a fixed-year window would be empty
   for centuries at a stretch. This takes an odd-sized window of consecutive
   observations by date and plots its median at the window's median year, which
   is a defensible summary of a scatter and is described as such on the page. */
function rollingMedian(pairs, win) {
  const xs = pairs.slice().sort((a, b) => a[0] - b[0]);
  if (xs.length < win + 2) return [];
  const out = [];
  const half = (win - 1) / 2;
  for (let i = half; i < xs.length - half; i += 1) {
    const w = xs.slice(i - half, i + half + 1);
    const vs = w.map((p) => p[1]).sort((a, b) => a - b);
    out.push([xs[i][0], vs[half]]);
  }
  return out;
}

function inPeriod(period, year) {
  return year >= period.from && year < period.to;
}

function periodContent(period, metric) {
  const pts = DATA.points.filter((p) =>
    !p.rollup && p[metric] != null && inPeriod(period, p.year));

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
      year: y, [metric]: v, aggregate: true, n: null,
      basis: "Alfani's estimate for the whole state, every fifty years",
    })));

  const series = ["industrial", "modern"].map((key) => ({
    key,
    label: DATA.meta.layers[key].label,
    dist: distribution(key, metric).filter((d) => inPeriod(period, d.year)),
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
    const own = all.filter((p) => p.layer === layer).map((p) => [p.year, p[metric]]);
    const line = rollingMedian(own, 9);
    if (line.length > 1) trends.push({ layer, colour, line });
  }

  return { pts: all, regions: [], series, trends };
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

const hook = (el, show) => {
  el.addEventListener("pointerenter", show);
  el.addEventListener("pointermove", show);
};

function drawEras() {
  const metric = state.metric, M = METRICS[metric];
  const eras = activeEras(metric);
  const svg = $("#eras");
  const readout = $("#eras-readout");
  svg.innerHTML = "";
  readout.hidden = true;

  const stacked = window.matchMedia("(max-width: 700px)").matches;
  const box = boxFor("#eras", stacked ? 1.9 : 0.46, stacked ? 520 : 260, stacked ? 1000 : 430);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);

  const pad = { l: 44, r: 8, t: 10, b: 40 };
  const gut = stacked ? 0 : 16;
  const iw = box.w - pad.l - pad.r;

  /* On a phone the panels stack, each getting the full width and its own y
     axis. Side by side at 375px they would be 70px wide apiece. */
  const lanes = eras.map((e, i) => {
    if (stacked) {
      const laneH = (box.h - pad.t - pad.b) / eras.length;
      return { x: pad.l, w: iw, y: pad.t + i * laneH, h: laneH - 34 };
    }
    const each = (iw - gut * (eras.length - 1)) / eras.length;
    return { x: pad.l + i * (each + gut), w: each, y: pad.t, h: box.h - pad.t - pad.b };
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

    /* The panel is named by the period it covers, and the axis underneath
       carries real dated ticks rather than one range caption. A single "9200
       BC to 1283" told a reader nothing about where inside it a dot sat. */
    const name = svgEl("text", {
      x: lane.x, y: (lane.y - 1).toFixed(1), "font-size": 12,
      "font-weight": 600, fill: "var(--ink-soft)",
    });
    name.textContent = `${yearLabel(x0)} to ${yearLabel(era.labelTo ?? x1)}`;
    svg.appendChild(name);

    for (const t of ticksFor(x0, x1, Math.max(2, Math.round(lane.w / 78)))) {
      const tx = xOf(t);
      if (tx < lane.x - 1 || tx > lane.x + lane.w + 1) continue;
      svg.appendChild(svgEl("line", {
        x1: tx.toFixed(1), x2: tx.toFixed(1),
        y1: (lane.y + lane.h).toFixed(1), y2: (lane.y + lane.h + 4).toFixed(1),
        stroke: "var(--rule)", "stroke-width": 1,
      }));
      const lab = svgEl("text", {
        x: tx.toFixed(1), y: (lane.y + lane.h + 17).toFixed(1),
        "text-anchor": "middle", "font-size": 10.5, fill: "var(--ink-faint)",
      });
      lab.textContent = yearLabel(t);
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
      if (src.sel.length > 1) {
        const line = svgEl("polyline", {
          points: src.sel.map(([y, v]) => `${xOf(y).toFixed(1)},${yOf(lane, v).toFixed(1)}`).join(" "),
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

    // ---- one dot per site or assessment, unless its layer is folded away
    for (const p of pts) {
      if (!state.scatter[p.layer]) continue;
      const hue = `var(--w-${p.layer === "deep" ? "deep" : "early"})`;
      const dot = svgEl("circle", {
        cx: xOf(p.year).toFixed(1), cy: yOf(lane, p[metric]).toFixed(1),
        r: p.aggregate ? 4.2 : 3.2, class: "dot",
        // hollow says "this is many places averaged", solid says "one place"
        fill: p.aggregate ? "none" : hue,
        "fill-opacity": p.aggregate ? 1 : 0.6,
        stroke: p.aggregate ? "var(--w-region)" : "none",
        "stroke-width": p.aggregate ? 1.6 : 0,
      });
      hook(dot, (evt) => {
        readout.innerHTML = `<b>${p.place}</b>` +
          `<div class="row"><span>${yearLabel(p.year)}</span><span>${fmt(p[metric])}</span></div>` +
          (p.n ? `<div class="row"><span>households sampled</span>` +
                 `<span>${Math.round(p.n).toLocaleString()}</span></div>` : "") +
          (p.aggregate ? "" : "") +
          (p.group ? `<div class="row"><span>region</span><span>${p.group}</span></div>` : "") +
          `<div class="prov">${DATA.meta.layers[p.layer].label}. ${p.basis}</div>`;
        readout.hidden = false;
        placeReadout(readout, evt);
      });
      svg.appendChild(dot);
    }

    // ---- a hover band for the line eras, because annual points are smaller
    //      than a fingertip
    if (series.length) {
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
        const bits = [`<b>${label}</b>`];
        /* Both sources at once where both reach this year. Seeing a
           reconstruction and a measurement disagree is the point of the panel,
           not a glitch to hide. */
        for (const src of series) {
          const sp = near(src.sel, (p) => p[0]);
          const dp = near(src.dist, (d) => d.year);
          if (sp && Math.abs(sp[0] - yr) <= 8) {
            bits.push(`<div class="row"><span>${src.label}, ${sp[0]}</span>` +
                      `<span>${fmt(sp[1])}</span></div>`);
          } else if (dp && Math.abs(dp.year - yr) <= 8) {
            bits.push(`<div class="row"><span>${src.label}, ${dp.year}</span>` +
                      `<span>middle ${fmt(dp.p50)}</span></div>`);
          }
        }
        if (bits.length === 1) { readout.hidden = true; return; }
        readout.innerHTML = bits.join("") +
          `<div class="prov">dashed is reconstructed, solid is measured</div>`;
        readout.hidden = false;
        placeReadout(readout, evt);
      });
      svg.appendChild(band);
    }
  });

  svg.onpointerleave = () => { readout.hidden = true; };
  svg.setAttribute("aria-label",
    `${M.label}, in ${eras.length} panels: ` +
    eras.map((e) => e.label).join(", ") +
    ". Each panel has its own time scale and they share one vertical scale.");

  $("#eras-title").textContent = M.label;
  $("#eras-blurb").textContent = M.blurb;
  /* The count changes with the measure: no national accounts publish a Gini
     and no historian's estimate reaches the
     richest 1%, so the panel count follows the measure. */
  const n = ["", "One panel", "Two panels", "Three panels", "Four panels"][eras.length];
  $("#eras-caption").textContent =
    `${n}, one per period. The horizontal scale differs between them and the ` +
    "vertical scale does not, so heights are comparable across panels and " +
    "horizontal distances are not.";
}

/* ------------------------------------------------- the archaeology, two cuts */

/* Kohler's own five-step coding of political organisation, smallest first.
   Ordering matters: the whole point of the chart is that it is monotonic, and
   sorting alphabetically would hide that. */
const SCALES = ["family", "local", "big man", "regional", "state"];

const OLD_WORLD = new Set([
  "Europe & NE", "Northeast China", "Central China", "East Coast China", "Egypt",
]);

function deepSites() {
  return DATA.points.filter((p) => p.layer === "deep" && p.gini != null);
}

const median = (xs) => {
  const v = xs.slice().sort((a, b) => a - b);
  const i = (v.length - 1) / 2;
  return v.length % 2 ? v[i] : (v[i - 0.5] + v[i + 0.5]) / 2;
};

/* A strip plot, not a bar chart of the medians. n is 1 to 22 per row and the
   ranges overlap heavily - states run 0.12 to 0.68 - so a bar would assert a
   precision the sample cannot carry. Showing every site and marking the median
   lets a reader see the overlap for themselves. */
function drawScale() {
  const svg = $("#scale");
  const readout = $("#scale-readout");
  svg.innerHTML = ""; readout.hidden = true;

  const rows = SCALES
    .map((k) => ({ key: k, pts: deepSites().filter((p) => p.scale === k) }))
    .filter((r) => r.pts.length);
  if (!rows.length) return;

  const box = boxFor("#scale", 0.34, 190, 300);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 86, r: 14, t: 8, b: 26 };
  const iw = box.w - pad.l - pad.r;
  const rowH = (box.h - pad.t - pad.b) / rows.length;
  const xOf = (v) => pad.l + v * iw;

  for (const t of [0, 0.25, 0.5, 0.75, 1]) {
    svg.appendChild(svgEl("line", {
      x1: xOf(t).toFixed(1), x2: xOf(t).toFixed(1), y1: pad.t,
      y2: (box.h - pad.b).toFixed(1), stroke: "var(--rule)", "stroke-width": 1,
    }));
    const lab = svgEl("text", {
      x: xOf(t).toFixed(1), y: (box.h - pad.b + 16).toFixed(1),
      "text-anchor": "middle", "font-size": 11, fill: "var(--ink-faint)",
    });
    lab.textContent = t.toFixed(2);
    svg.appendChild(lab);
  }

  rows.forEach((row, i) => {
    const cy = pad.t + i * rowH + rowH / 2;
    const name = svgEl("text", {
      x: pad.l - 12, y: (cy + 4).toFixed(1), "text-anchor": "end",
      "font-size": 12.5, fill: "var(--ink-soft)",
    });
    name.textContent = row.key;
    svg.appendChild(name);

    const n = svgEl("text", {
      x: pad.l - 12, y: (cy + 17).toFixed(1), "text-anchor": "end",
      "font-size": 10.5, fill: "var(--ink-faint)",
    });
    n.textContent = `${row.pts.length} site${row.pts.length === 1 ? "" : "s"}`;
    svg.appendChild(n);

    for (const p of row.pts) {
      // a deterministic vertical offset so overlapping sites stay countable
      const j = ((p.year * 2654435761) % 1000) / 1000 - 0.5;
      const dot = svgEl("circle", {
        cx: xOf(p.gini).toFixed(1), cy: (cy + j * rowH * 0.52).toFixed(1),
        r: 3.4, fill: "var(--w-deep)", "fill-opacity": 0.55, class: "dot",
      });
      hook(dot, (evt) => {
        readout.innerHTML = `<b>${p.place}</b>` +
          `<div class="row"><span>${yearLabel(p.year)}</span><span>${p.gini.toFixed(2)}</span></div>` +
          `<div class="row"><span>scale</span><span>${p.scale}</span></div>` +
          `<div class="prov">${p.group}</div>`;
        readout.hidden = false; placeReadout(readout, evt);
      });
      svg.appendChild(dot);
    }

    const m = median(row.pts.map((p) => p.gini));
    svg.appendChild(svgEl("line", {
      x1: xOf(m).toFixed(1), x2: xOf(m).toFixed(1),
      y1: (cy - rowH * 0.34).toFixed(1), y2: (cy + rowH * 0.34).toFixed(1),
      stroke: "var(--w-pick)", "stroke-width": 2.6, "stroke-linecap": "round",
    }));
  });

  svg.onpointerleave = () => { readout.hidden = true; };
  const lo = median(rows[0].pts.map((p) => p.gini));
  const hi = median(rows[rows.length - 1].pts.map((p) => p.gini));
  $("#scale-caption").textContent =
    `Median Gini runs from ${lo.toFixed(2)} at ${rows[0].key} scale to ` +
    `${hi.toFixed(2)} at ${rows[rows.length - 1].key} scale, across ` +
    `${deepSites().length} sites. The ranges overlap, so this is a tendency ` +
    `across the sample rather than a rule about any one society.`;
  describe(svg, "Wealth Gini at each excavated site, grouped by the political "
                + "scale of the society that built it, smallest at the top.");
}

function drawOldNew() {
  const svg = $("#oldnew");
  const readout = $("#oldnew-readout");
  svg.innerHTML = ""; readout.hidden = true;

  const sites = deepSites();
  if (!sites.length) return;
  const box = boxFor("#oldnew", 0.34, 190, 300);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 44, r: 12, t: 10, b: 28 };
  const iw = box.w - pad.l - pad.r, ih = box.h - pad.t - pad.b;
  const years = sites.map((p) => p.year);
  const x0 = Math.min(...years), x1 = Math.max(...years);
  const xOf = (y) => pad.l + ((y - x0) / (x1 - x0)) * iw;
  const yOf = (v) => pad.t + (1 - v) * ih;

  for (const t of [0, 0.25, 0.5, 0.75, 1]) {
    svg.appendChild(svgEl("line", {
      x1: pad.l, x2: pad.l + iw, y1: yOf(t).toFixed(1), y2: yOf(t).toFixed(1),
      stroke: "var(--rule)", "stroke-width": 1,
    }));
    const lab = svgEl("text", {
      x: pad.l - 8, y: (yOf(t) + 4).toFixed(1), "text-anchor": "end",
      "font-size": 11, fill: "var(--ink-faint)",
    });
    lab.textContent = t.toFixed(2);
    svg.appendChild(lab);
  }
  for (const t of ticksFor(x0, x1, Math.max(3, Math.round(iw / 90)))) {
    const lab = svgEl("text", {
      x: xOf(t).toFixed(1), y: (pad.t + ih + 18).toFixed(1),
      "text-anchor": "middle", "font-size": 10.5, fill: "var(--ink-faint)",
    });
    lab.textContent = yearLabel(t);
    svg.appendChild(lab);
  }

  const halves = [
    { key: "Old World", colour: "var(--w-deep)", pts: sites.filter((p) => OLD_WORLD.has(p.group)) },
    { key: "New World", colour: "var(--w-now)", pts: sites.filter((p) => !OLD_WORLD.has(p.group)) },
  ];
  for (const h of halves) {
    for (const p of h.pts) {
      const dot = svgEl("circle", {
        cx: xOf(p.year).toFixed(1), cy: yOf(p.gini).toFixed(1), r: 3.4,
        fill: h.colour, "fill-opacity": 0.55, class: "dot",
      });
      hook(dot, (evt) => {
        readout.innerHTML = `<b>${p.place}</b>` +
          `<div class="row"><span>${yearLabel(p.year)}</span><span>${p.gini.toFixed(2)}</span></div>` +
          `<div class="prov">${h.key}. ${p.group}</div>`;
        readout.hidden = false; placeReadout(readout, evt);
      });
      svg.appendChild(dot);
    }
    const line = rollingMedian(h.pts.map((p) => [p.year, p.gini]), 7);
    if (line.length > 1) {
      svg.appendChild(svgEl("polyline", {
        points: line.map(([y, v]) => `${xOf(y).toFixed(1)},${yOf(v).toFixed(1)}`).join(" "),
        fill: "none", stroke: h.colour, "stroke-width": 2.4,
        "stroke-linejoin": "round", "stroke-linecap": "round",
      }));
    }
  }
  svg.onpointerleave = () => { readout.hidden = true; };

  $("#legend-old").innerHTML = halves.map((h) =>
    `<span><i style="background:${h.colour}"></i>${h.key}, ${h.pts.length} sites</span>`).join("")
    + '<span><i style="background:var(--ink-soft)"></i>Rolling median of seven</span>';

  const om = median(halves[0].pts.map((p) => p.gini));
  const nm = median(halves[1].pts.map((p) => p.gini));
  $("#oldnew-caption").textContent =
    `Median Gini ${om.toFixed(2)} across ${halves[0].pts.length} Old World sites, ` +
    `${nm.toFixed(2)} across ${halves[1].pts.length} in the New. The two samples ` +
    `are small and unevenly dated, so the gap is suggestive rather than settled.`;
  describe(svg, "Wealth Gini at every excavated site over time, split between "
                + "Old World and New World.");
}

/* ----------------------------------------------------------------- furniture */

const LAYER_DOT = {
  deep: ["var(--w-deep)", "Every excavated settlement"],
  preindustrial: ["var(--w-early)", "Every tax assessment"],
};

function renderLegend() {
  const eras = activeEras(state.metric);
  const pts = eras.flatMap((e) => e.content.pts);
  const has = (k) => pts.some((p) => p.layer === k);
  const trends = eras.flatMap((e) => e.content.trends);
  const sources = eras.flatMap((e) => e.content.series);

  /* Every entry is a thing on the chart, and every thing on the chart has an
     entry. Both halves of that have been broken before. The two scatter
     entries are buttons: pressing one folds its observations away and leaves
     the median. */
  const out = [];
  for (const key of ["deep", "preindustrial"]) {
    if (!has(key)) continue;
    const [colour, label] = LAYER_DOT[key];
    out.push({ colour, label, toggle: key, on: state.scatter[key] });
  }
  if (trends.length) {
    out.push({ colour: trends.length === 1 ? trends[0].colour : "var(--ink-soft)",
               label: "Rolling median of nine" });
  }
  if (pts.some((p) => p.aggregate && state.scatter[p.layer])) {
    out.push({ colour: "var(--w-region)", label: "A whole region, hollow" });
  }
  for (const src of sources) {
    out.push({ colour: src.colour, label: `${src.label}, middle half` });
  }
  if (sources.length && state.country !== ALL) {
    out.push({ colour: "var(--w-pick)",
               label: DATA.countries[state.country]?.label || state.country });
  }

  $("#legend-eras").innerHTML = out.map((e) => (e.toggle
    ? `<button type="button" class="key" data-scatter="${e.toggle}" `
      + `aria-pressed="${e.on}"><i style="background:${e.colour}"></i>${e.label}</button>`
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
  const rows = Object.values(DATA.countries)
    .filter((c) => (c.industrial[state.metric] || []).length
                || (c.modern[state.metric] || []).length)
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
  for (const k of ["deep", "preindustrial"]) {
    if (p.get(k) === "1" || p.get(k) === "0") state.scatter[k] = p.get(k) === "1";
  }
}

function writeHash() {
  const p = new URLSearchParams();
  for (const k of ["metric", "country"]) if (state[k] !== DEFAULTS[k]) p.set(k, state[k]);
  for (const k of ["deep", "preindustrial"]) {
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
  drawOldNew();
  if (state.country === ALL) {
    /* Count what the band is actually drawn from on THIS measure, not every
       country in the file. The two differ by a factor of five on the Gini. */
    const n = Object.values(DATA.countries).filter((x) =>
      (x.industrial[state.metric] || []).length || (x.modern[state.metric] || []).length).length;
    $("#country-hint").textContent = `${n} countries on this measure`;
  } else {
    const c = DATA.countries[state.country];
    const spans = [];
    if (c?.industrial.gini.length) spans.push(c.industrial.gini[0][0]);
    if (c?.modern.top10.length) spans.push(c.modern.top10[0][0]);
    $("#country-hint").textContent = spans.length
      ? `charted from ${Math.min(...spans)}` : "no national series";
  }
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
