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

const DEFAULTS = { country: "United States of America" };
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

/* Four on, five off. The page's claim is a contrast, and a contrast needs the
   two flat lines and the two that moved most, not nine lines at once; the other
   five are there for anyone who wants to check that the four were not picked to
   flatter the point. */
const AXES_ON = new Set(["economy", "religion", "immigration", "lgbt"]);

const CHES_STYLE = {
  economy: "var(--p-econ)", general: "var(--p-relig)",
  culture: "var(--p-lgbt)", immigration: "var(--p-immig)", eu: "var(--p-plur)",
};

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

function axisFrame(svg, box, pad, x0, x1, y0, y1, yticks, xstep) {
  const xOf = (x) => pad.l + ((x - x0) / (x1 - x0)) * (box.w - pad.l - pad.r);
  const yOf = (y) => pad.t + (1 - (y - y0) / (y1 - y0)) * (box.h - pad.t - pad.b);
  for (const t of yticks) {
    const y = yOf(t);
    svg.appendChild(svgEl("line", {
      x1: pad.l, x2: box.w - pad.r, y1: y.toFixed(1), y2: y.toFixed(1),
      stroke: "var(--rule)", "stroke-width": 1,
    }));
    const lab = svgEl("text", {
      x: pad.l - 8, y: (y + 4).toFixed(1), "text-anchor": "end",
      "font-size": 11, fill: "var(--ink-faint)",
    });
    lab.textContent = typeof t === "number" && t % 1 ? t.toFixed(1) : `${t}`;
    svg.appendChild(lab);
  }
  for (let t = Math.ceil(x0 / xstep) * xstep; t <= x1; t += xstep) {
    const x = xOf(t);
    const lab = svgEl("text", {
      x: x.toFixed(1), y: (box.h - pad.b + 18).toFixed(1),
      "text-anchor": "middle", "font-size": 10.5, fill: "var(--ink-faint)",
    });
    lab.textContent = `${t}`;
    svg.appendChild(lab);
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
  const box = boxFor("#camps", narrow ? 0.72 : 0.42, 260, 420);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 34, r: narrow ? 12 : 16, t: 12, b: 34 };

  const x0 = band[0][0], x1 = band[band.length - 1][0];
  const { xOf, yOf } = axisFrame(svg, box, pad, x0, x1, 0, 4,
    [0, 1, 2, 3, 4], narrow ? 40 : 20);

  const p25 = smooth(band.map((r) => [r[0], r[1]]));
  const p50 = smooth(band.map((r) => [r[0], r[2]]));
  const p75 = smooth(band.map((r) => [r[0], r[3]]));
  const top = p75.map(([x, y]) => `${xOf(x).toFixed(1)},${yOf(y).toFixed(1)}`);
  const bot = p25.slice().reverse()
    .map(([x, y]) => `${xOf(x).toFixed(1)},${yOf(y).toFixed(1)}`);
  svg.appendChild(svgEl("polygon", {
    points: [...top, ...bot].join(" "), fill: "var(--p-band)", "fill-opacity": 0.5,
  }));
  svg.appendChild(line(
    p50.map(([x, y]) => `${xOf(x).toFixed(1)},${yOf(y).toFixed(1)}`).join(" "),
    "var(--ink-soft)", 2, { "stroke-dasharray": "5 4", "stroke-opacity": 0.8 }));

  const own = (DATA.society[state.country] || {}).camps || [];
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
    readout.innerHTML = `<b>${yr}</b>`
      + `<div class="row"><span><i style="background:var(--ink-soft)"></i>`
      + `middle country</span><span>${fmt2(m[1])}</span></div>`
      + (s ? `<div class="row"><span><i style="background:var(--p-pick)"></i>`
           + `${state.country}</span><span>${fmt2(s[1])}</span></div>` : "")
      + `<div class="prov">0 is no camps, 4 is a society split in two</div>`;
    readout.hidden = false;
    placeReadout(readout, evt);
  });
  svg.appendChild(grab);
  clearOnLeave(svg, readout);

  const at = (y) => {
    const r = band.reduce((b, p) =>
      (!b || Math.abs(p[0] - y) < Math.abs(b[0] - y)) ? p : b, null);
    return r ? r[2] : null;
  };
  const a = at(1978), z = at(2025);
  $("#camps-sub").textContent =
    `V-Dem asks its country experts, every year since 1900, whether supporters `
    + `of opposing camps avoid one another. The band is the middle half of `
    + `${band[band.length - 1][4]} countries.`;
  $("#camps-caption").textContent =
    `The middle country sits at ${fmt2(z)} today against ${fmt2(a)} in 1978. `
    + `The rise since 2010 is real, and it is a return to where the Cold War `
    + `left things rather than a new peak.`;
  describe(svg, "Societal polarisation, 1900 to 2025, as the middle half of "
              + "countries and one selected country.");

  $("#legend-camps").innerHTML =
    `<span class="explained" tabindex="0" title="The middle half of every country rated that year, and the median through it."><i style="background:var(--p-band)"></i>All countries</span>`
    + `<span><i style="background:var(--p-pick)"></i>${state.country}</span>`;
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
    .map((r) => r[2]).sort((a, b) => a - b);
  if (!base.length) return [];
  const b = base[Math.floor(base.length / 2)];
  return rows.map((r) => [r[0], r[2] / b]);
}

function drawFan(svgId, readoutId, legendId, layer, styles, baseFrom, baseTo,
                 labels, on) {
  const svg = $(svgId), readout = $(readoutId);
  svg.innerHTML = ""; readout.hidden = true;

  const series = Object.keys(styles).map((k) => ({
    key: k, label: labels[k],
    colour: styles[k].colour || styles[k],
    flat: !!styles[k].flat,
    pts: smooth(axisIndex(layer, k, baseFrom, baseTo), 0.16),
  })).filter((s) => s.pts.length > 1);
  if (!series.length) return;

  const shown = series.filter((s) => on.has(s.key));
  const narrow = window.matchMedia("(max-width: 700px)").matches;
  const box = boxFor(svgId, narrow ? 0.72 : 0.4, 250, 400);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 36, r: narrow ? 12 : 16, t: 12, b: 34 };

  const xs = shown.flatMap((s) => s.pts.map((p) => p[0]));
  const ys = shown.flatMap((s) => s.pts.map((p) => p[1]));
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const hi = Math.max(2.2, Math.ceil(Math.max(...ys) * 4) / 4);
  const { xOf, yOf } = axisFrame(svg, box, pad, x0, x1, 0.5, hi,
    [0.5, 1, 1.5, 2].filter((t) => t <= hi), narrow ? 20 : 10);

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

  $(legendId).innerHTML = series.map((s) =>
    `<button type="button" class="key" data-axis="${s.key}" `
    + `aria-pressed="${on.has(s.key)}"><i style="background:${s.colour}"></i>`
    + `${s.label}</button>`).join("");
  for (const btn of $(legendId).querySelectorAll("[data-axis]")) {
    btn.addEventListener("click", () => {
      const k = btn.dataset.axis;
      if (on.has(k)) { if (on.size > 1) on.delete(k); } else on.add(k);
      render();
    });
  }
  return series;
}

function drawAxes() {
  const labels = Object.fromEntries(
    DATA.meta.layers.party.axes.map((a) => [a.key, a.label]));
  const series = drawFan("#axes", "#axes-readout", "#legend-axes", "party",
    AXIS_STYLE, 1970, 1979, labels, AXES_ON);
  if (!series) return;
  const swing = (k) => median(axisIndex("party", k, 1970, 1979), 2010, 2019);
  $("#axes-caption").textContent =
    `Economic distance is where it was fifty years ago, ${pct(swing("economy"))}. `
    + `Distance on immigration is ${pct(swing("immigration"))} and on LGBT `
    + `rights ${pct(swing("lgbt"))}. The parties did not stop disagreeing, they `
    + `changed what they disagree about.`;
  describe($("#axes"), "Nine measures of how far apart parties stand, each "
                     + "against its own level in the 1970s.");
}

function drawChes() {
  const labels = Object.fromEntries(
    DATA.meta.layers.europe.axes.map((a) => [a.key, a.label]));
  const on = new Set(["economy", "culture"]);
  drawFan("#ches", "#ches-readout", "#legend-ches", "europe",
    CHES_STYLE, 1999, 2006, labels, on);
  const n = Object.keys(DATA.europe).length;
  $("#ches-sub").textContent =
    `The Chapel Hill Expert Survey asks a different panel of academics a `
    + `different set of questions on a different scale, across ${n} European `
    + `countries. It is a check on the chart above, not more of it.`;
  const sw = (k) => median(axisIndex("europe", k, 1999, 2006), 2019, 2024);
  $("#ches-caption").textContent =
    `It finds the same thing. Economic distance ${pct(sw("economy"))} over `
    + `twenty-five years, against ${pct(sw("culture"))} on liberal and `
    + `traditional values.`;
  describe($("#ches"), "The same measure from the Chapel Hill Expert Survey, "
                     + "1999 to 2024.");
}

/* ----------------------------------------------------------------- furniture */

function renderLayers() {
  const L = DATA.meta.layers;
  $("#layers").innerHTML = Object.entries(L).map(([key, v]) =>
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
  sel.innerHTML = names.map((c) => `<option value="${c}">${c}</option>`).join("");
  if (!names.includes(state.country)) state.country = names[0];
  sel.value = state.country;
}

function render() {
  drawCamps();
  drawAxes();
  drawChes();
}

function wire() {
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
    buildPickers(); renderLayers(); wire(); render();
    document.body.classList.remove("loading");
  })
  .catch((err) => {
    const stage = DATA ? "draw the charts" : "load the data";
    document.body.classList.remove("loading");
    $("main").insertAdjacentHTML("afterbegin",
      `<section class="panel"><h2>Could not ${stage}</h2><p class="sub">${err.message}</p></section>`);
    throw err;
  });
