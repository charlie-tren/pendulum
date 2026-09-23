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
const DEFAULTS = { country: "Australia" };
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

/* Five on, four off. Economics is the one that did not move and has to be
   there or the chart has no baseline; the other four are the ones that did.
   Religious principles comes off the default set: it is flat like economics and
   two flat lines make the same point once. The rest stay in the key for anyone
   checking that these five were not chosen to flatter the argument. */
const AXES_ON = new Set(["economy", "immigration", "lgbt",
                         "minorities", "pluralism"]);

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
                   ytitle = "", xtitle = "") {
  const xOf = (x) => pad.l + ((x - x0) / (x1 - x0)) * (box.w - pad.l - pad.r);
  const yOf = (y) => pad.t + (1 - (y - y0) / (y1 - y0)) * (box.h - pad.t - pad.b);
  for (const t of yticks) {
    const y = yOf(t);
    svg.appendChild(svgEl("line", {
      x1: pad.l, x2: box.w - pad.r, y1: y.toFixed(1), y2: y.toFixed(1),
      stroke: "var(--rule)", "stroke-width": 1,
    }));
    const lab = svgEl("text", {
      x: pad.l - 9, y: (y + 5).toFixed(1), "text-anchor": "end",
      "font-size": 16, fill: "var(--ink-soft)",
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
    "How split, 0 to 4", "Year");

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
    `V-Dem asks country experts whether supporters of opposing camps still `
    + `interact in a friendly way outside politics: at family functions, in `
    + `civic associations, at work. 0 is friendly, 4 is hostile. The band `
    + `covers the middle half of ${last[8]} countries.`;
  describe(svg, "Societal polarisation, 1900 to 2025: the full range of "
              + "countries, the middle half inside it, and one selected "
              + "country.");

  $("#legend-camps").innerHTML =
    `<span class="explained" tabindex="0" title="The middle half of countries: a quarter sit above this band and a quarter below."><i style="background:var(--p-band)"></i>Middle half</span>`
    + `<span class="explained" tabindex="0" title="Half the countries sit above this line and half below it."><i class="dash"></i>Median</span>`
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

function axisIndex(layer, axis, baseFrom, baseTo) {
  const rows = (DATA.bands[layer] || {})[axis] || [];
  const base = rows.filter((r) => r[0] >= baseFrom && r[0] <= baseTo)
    .map((r) => r[4]).sort((a, b) => a - b);
  if (!base.length) return [];
  const b = base[Math.floor(base.length / 2)];
  return rows.map((r) => [r[0], r[4] / b]);
}

function drawFan(svgId, readoutId, legendId, layer, styles, baseFrom, baseTo,
                 labels, on) {
  const svg = $(svgId), readout = $(readoutId);
  svg.innerHTML = ""; readout.hidden = true;

  const series = Object.keys(styles).map((k) => ({
    key: k, label: labels[k],
    colour: styles[k].colour || styles[k],
    flat: !!styles[k].flat,
    /* 0.05, not 0.16. At a sixth of the span the kernel reached eight years
       either side and turned four decades of elections into four smooth arcs:
       a reader could see that the cultural lines rise and nothing else. At a
       twentieth it is about two and a half years, which keeps the decade shape
       and puts the texture back - the stall in the 1980s, the step around
       German reunification, the flattening after 2015. The floor at two and a
       half times the median spacing still stops it drawing noise between
       sparse observations. */
    pts: smooth(axisIndex(layer, k, baseFrom, baseTo), 0.05),
  })).filter((s) => s.pts.length > 1);
  if (!series.length) return;

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
  /* THE Y RANGE FITS THE LINES SHOWN, rather than sitting at a fixed 0.5 to
     2.2. Everything on this chart starts at 1.0 by construction and the flat
     axes never leave 0.9 to 1.1, so a fixed range spent two thirds of its
     height on empty space and squashed the whole argument into the middle
     third: the flat lines and the doubling ones looked much more alike than
     they are. Padded by a tenth of the span so nothing touches an edge, and
     the ticks follow the range rather than a fixed list. */
  const lo0 = Math.min(...ys), hi0 = Math.max(...ys);
  const padY = Math.max(0.04, (hi0 - lo0) * 0.1);
  const lo = Math.max(0, lo0 - padY), hi = hi0 + padY;
  const step = (hi - lo) > 1.2 ? 0.25 : (hi - lo) > 0.5 ? 0.1 : 0.05;
  const ticks = [];
  for (let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) {
    ticks.push(Math.round(t * 100) / 100);
  }
  const { xOf, yOf } = axisFrame(svg, box, pad, x0, x1, lo, hi,
    ticks, narrow ? 20 : 10,
    "Distance between parties, 1970s = 1", "Election year");

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
      + `<div class="prov">against the same measure in the ${baseFrom}s</div>`;
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

function drawAxes() {
  const labels = Object.fromEntries(
    DATA.meta.layers.party.axes.map((a) => [a.key, a.label]));
  const series = drawFan("#axes", "#axes-readout", "#legend-axes", "party",
    AXIS_STYLE, 1970, 1979, labels, AXES_ON);
  if (!series) return;
  describe($("#axes"), "Nine measures of how far apart parties stand, each "
                     + "against its own level in the 1970s.");
}


/* ----------------------------------------------------------------- furniture */

/* The five friendliest and the five most hostile, most recent year with a full
   set of ratings. This replaces the outer band, which showed that something sat
   at 3.99 without ever saying what: the edge of a grey shape is not a finding,
   a country's name is. Clicking one picks it out on the chart above, so the
   list is also the fastest way into the control. */
function renderRanks() {
  const el = $("#camps-ranks");
  if (!el) return;
  const rows = DATA.bands.society.camps;
  const year = rows[rows.length - 1][0];
  const vals = [];
  for (const [name, axes] of Object.entries(DATA.society)) {
    const hit = (axes.camps || []).find((r) => r[0] === year);
    if (hit) vals.push([name, hit[1]]);
  }
  vals.sort((p, q) => p[1] - q[1]);
  /* The flag is decoration with a job: at a glance it says which part of the
     world a list is, which is the first thing anyone wants from a ranking of
     countries they may not recognise. flagcdn serves by ISO alpha-2, and the
     three entries with no code - East Germany, Somaliland, Zanzibar - simply
     get no image rather than a broken one. width and height are set so the row
     does not jump when the image lands, and loading is lazy because ten flags
     are not worth blocking on. */
  const iso = DATA.meta.iso2 || {};
  const flag = (n) => (iso[n]
    ? `<img class="flag" src="https://flagcdn.com/w40/${iso[n]}.png" `
      + `srcset="https://flagcdn.com/w80/${iso[n]}.png 2x" `
      + `width="20" height="15" alt="" loading="lazy" decoding="async">`
    : `<span class="flag flag-none" aria-hidden="true"></span>`);
  const list = (title, note, items) =>
    `<div class="rank"><h3>${title}</h3><p class="rank-note">${note}</p><ol>`
    + items.map(([n, v]) =>
        `<li><button type="button" data-country="${n.replace(/"/g, "&quot;")}">`
        + `${flag(n)}<span>${n}</span><b>${fmt2(v)}</b></button></li>`).join("")
    + "</ol></div>";
  el.innerHTML =
    list("Least divided", `Opposing supporters still get on, ${year}`,
         vals.slice(0, 5))
    + list("Most divided", `They mostly do not, ${year}`,
           vals.slice(-5).reverse());
  for (const btn of el.querySelectorAll("[data-country]")) {
    btn.addEventListener("click", () => {
      state.country = btn.dataset.country;
      $("#country-sel").value = state.country;
      render();
      $("#camps").scrollIntoView({ block: "center", behavior: "smooth" });
    });
  }
}

function renderLayers() {
  const L = DATA.meta.layers;
  // the layers panel was removed from the page; the sources list stays
  if ($("#layers")) $("#layers").innerHTML = Object.entries(L).map(([key, v]) =>
    `<dt><i style="background:var(--p-${key})"></i>${v.label}</dt>`
    + `<dd>${v.note}</dd>`).join("")
    + `<dt><i style="background:var(--ink-faint)"></i>They do not check each other</dt>`
    + `<dd>Building a polarisation index out of vote shares and testing it `
    + `against the experts' camps rating gives a correlation of 0.16 within a `
    + `country, and nothing at all on changes between elections, against a `
    + `control of 0.93. How people vote and how divided they are turn out to be `
    + `close to unrelated, so nothing here averages one with the other.</dd>`;
  $("#sources").innerHTML = DATA.meta.sources.map((s) =>
    `<li><a href="${s.url}" rel="noopener">${s.name}</a>, ${s.publisher}. ${s.role}</li>`)
    .join("");
}

function buildPickers() {
  const sel = $("#country-sel");
  const names = Object.keys(DATA.society)
    .filter((c) => (DATA.society[c].camps || []).length > 20)
    .sort((a, b) => a.localeCompare(b));
  /* "All countries" is not a country: it drops the highlighted line and leaves
     the spread and the median, which is every country at once. */
  /* "None", not "All countries". Every country is on the chart whatever this
     is set to - the bands are the whole population and nothing removes them -
     so an option called "All countries" described the chart rather than the
     choice, and reading it as "show me all of them" left a reader wondering
     what the other 175 options did. The control draws ONE line on top of what
     is already there, and its empty state is no line. */
  sel.innerHTML = `<option value="${ALL}">None</option>`
    + names.map((c) => `<option value="${c}">${c}</option>`).join("");
  if (state.country !== ALL && !names.includes(state.country)) state.country = ALL;
  sel.value = state.country;
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

/* "How is this measured?" as a control rather than a wall of text nobody asked
   for. The method matters and almost no reader wants it first: behind a toggle
   it is available to anyone who doubts the chart and invisible to everyone
   else, which is the same bargain the key's hover notes make. */
function wireInfo() {
  const btn = $("#axes-info"), box = $("#axes-method");
  if (!btn || !box) return;
  btn.addEventListener("click", () => {
    const open = btn.getAttribute("aria-expanded") === "true";
    btn.setAttribute("aria-expanded", String(!open));
    box.hidden = open;
    // the label carries the state now that there is no icon to do it
    btn.textContent = open ? "How is this measured?" : "Hide";
  });
}

function wire() {
  wireInfo();
  $("#country-sel").addEventListener("change", (e) => {
    state.country = e.target.value; render();
  });
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
    buildPickers(); renderLayers(); wire(); render();
  })
  .catch((err) => {
    const stage = DATA ? "draw the charts" : "load the data";
    document.body.classList.remove("loading");
    $("main").insertAdjacentHTML("afterbegin",
      `<section class="panel"><h2>Could not ${stage}</h2><p class="sub">${err.message}</p></section>`);
    throw err;
  });
