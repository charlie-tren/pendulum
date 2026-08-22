/* Pendulum: the wealth page. Same rules as the rest of the site - no framework,
   no build step, hand-rolled SVG, charts measured in the container's own pixels
   so a label that says 11px is 11px on a phone.

   The one idea this page is built around: four kinds of evidence, kept apart.
   A dug-up house, a tax register, a decadal estimate and a national account are
   not the same measurement, so they are never joined into one line. */

const DEFAULTS = { metric: "top10", country: "GBR", early: "show" };
const state = { ...DEFAULTS };
let DATA = null;

const $ = (sel) => document.querySelector(sel);
const clamp = (lo, v, hi) => Math.max(lo, Math.min(v, hi));

const svgEl = (name, attrs = {}) => {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
};

/* Metric definitions. `layers` is not decoration: it drives the hint under the
   picker, because which layers carry a measure is the single most useful thing
   to know before reading the chart. The Gini has no modern national series
   here and the top hundredth has no decadal one, and saying so beats a reader
   wondering why a line stopped. */
const METRICS = {
  top10: {
    label: "Share held by the richest tenth", axis: "%", max: 100,
    layers: ["preindustrial", "industrial", "modern"],
    hint: "tax records, decadal estimates and national accounts",
  },
  top1: {
    label: "Share held by the richest hundredth", axis: "%", max: 100,
    layers: ["preindustrial", "modern"],
    hint: "tax records and national accounts, no decadal series",
  },
  gini: {
    label: "Wealth Gini", axis: "", max: 1,
    layers: ["preindustrial", "industrial"],
    hint: "tax records and decadal estimates, plus the archaeology when it lands",
  },
};

const COLOUR = {
  preindustrial: "var(--w-early)",
  industrial: "var(--w-mid)",
  modern: "var(--w-now)",
  deep: "var(--w-deep)",
};

const fmt = (v, m) => (METRICS[m].axis === "%" ? `${v.toFixed(1)}%` : v.toFixed(3));

/* ------------------------------------------------------------------ plumbing */

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

function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  if (METRICS[p.get("metric")]) state.metric = p.get("metric");
  if (p.get("country") && DATA.countries[p.get("country")]) state.country = p.get("country");
  if (p.get("early") === "hide") state.early = "hide";
}

function writeHash() {
  const p = new URLSearchParams();
  for (const k of ["metric", "country", "early"]) {
    if (state[k] !== DEFAULTS[k]) p.set(k, state[k]);
  }
  const h = p.toString();
  try {
    history.replaceState(null, "", h ? `#${h}` : location.pathname + location.search);
  } catch {
    /* a sandboxed iframe refuses replaceState. Shareable URLs are a nicety and
       the charts are not, so this must never take the page down with it. */
  }
}

/* The readout follows the pointer rather than parking in a corner, and flips
   side rather than running off the panel. Static on a phone, where it sits
   under the chart. */
function placeReadout(el, evt) {
  if (getComputedStyle(el).position === "static") return;
  const fig = el.parentElement.getBoundingClientRect();
  const x = evt.clientX - fig.left, y = evt.clientY - fig.top;
  el.style.left = "0px"; el.style.top = "0px";
  const w = el.offsetWidth, h = el.offsetHeight;
  el.style.left = `${clamp(4, x + (x + w + 18 > fig.width ? -w - 14 : 14), Math.max(4, fig.width - w - 4))}px`;
  el.style.top = `${clamp(4, y - h / 2, Math.max(4, fig.height - h - 4))}px`;
}

/* --------------------------------------------------------------------- scales */

function frame(svgId, ratio, minH, maxH, x0, x1, max) {
  const box = boxFor(svgId, ratio, minH, maxH);
  const svg = $(svgId);
  svg.innerHTML = "";
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 44, r: 12, t: 12, b: 28 };
  const iw = box.w - pad.l - pad.r, ih = box.h - pad.t - pad.b;
  return {
    svg, box, pad, iw, ih, x0, x1, max,
    x: (y) => pad.l + ((y - x0) / (x1 - x0)) * iw,
    y: (v) => pad.t + (1 - v / max) * ih,
  };
}

function axes(f, metric) {
  const m = METRICS[metric];
  const ticks = m.max === 1 ? [0, 0.25, 0.5, 0.75, 1] : [0, 25, 50, 75, 100];
  for (const t of ticks) {
    const y = f.y(t);
    f.svg.appendChild(svgEl("line", {
      x1: f.pad.l, x2: f.pad.l + f.iw, y1: y.toFixed(1), y2: y.toFixed(1),
      stroke: "var(--rule)", "stroke-width": 1,
    }));
    const label = svgEl("text", {
      x: f.pad.l - 8, y: (y + 4).toFixed(1), "text-anchor": "end",
      "font-size": 11, fill: "var(--ink-faint)",
    });
    label.textContent = m.axis === "%" ? `${t}%` : t.toFixed(2);
    f.svg.appendChild(label);
  }
  /* Century marks, or half-centuries when the window is short enough to take
     them. A tick every decade across seven hundred years is a grey smear. */
  const span = f.x1 - f.x0;
  const step = span > 400 ? 100 : 50;
  for (let yr = Math.ceil(f.x0 / step) * step; yr <= f.x1; yr += step) {
    const t = svgEl("text", {
      x: f.x(yr).toFixed(1), y: (f.pad.t + f.ih + 18).toFixed(1),
      "text-anchor": "middle", "font-size": 11, fill: "var(--ink-faint)",
    });
    t.textContent = yr;
    f.svg.appendChild(t);
  }
}

function polyline(f, pts, { stroke, width = 2, opacity = 1, dash = null, cls = "" }) {
  if (pts.length < 2) return null;
  const d = pts.map(([yr, v]) => `${f.x(yr).toFixed(1)},${f.y(v).toFixed(1)}`).join(" ");
  const el = svgEl("polyline", {
    points: d, fill: "none", stroke, "stroke-width": width,
    "stroke-opacity": opacity, "stroke-linejoin": "round", "stroke-linecap": "round",
  });
  if (dash) el.setAttribute("stroke-dasharray", dash);
  if (cls) el.setAttribute("class", cls);
  f.svg.appendChild(el);
  return el;
}

/* ----------------------------------------------------------------- the charts */

function seriesFor(iso, metric) {
  const c = DATA.countries[iso];
  if (!c) return { industrial: [], modern: [] };
  const ind = metric === "top1" ? [] : (c.industrial[metric] || []);
  const mod = metric === "gini" ? [] : (c.modern[metric] || []);
  return { industrial: ind, modern: mod };
}

function pointsFor(metric) {
  return DATA.points.filter((p) => !p.rollup && p[metric] != null);
}

function hook(el, show) {
  el.addEventListener("pointerenter", show);
  el.addEventListener("pointermove", show);
}

function drawLong() {
  const metric = state.metric;
  const m = METRICS[metric];
  const early = state.early === "show";
  const x0 = early ? DATA.meta.year0 : 1800;
  const f = frame("#long", 0.42, 240, 400, x0, DATA.meta.year1, m.max);
  const readout = $("#long-readout");
  readout.hidden = true;
  axes(f, metric);

  /* Every other country, very faint. The point of the backdrop is that the
     selected line is read against a spread rather than in a vacuum: a country
     at 60% means nothing until you can see the others sitting at 45 and 75. */
  for (const [iso, c] of Object.entries(DATA.countries)) {
    if (iso === state.country) continue;
    const s = metric === "gini" ? c.industrial.gini : (c.modern[metric] || []);
    polyline(f, s.filter(([y]) => y >= x0), {
      stroke: "var(--ink-faint)", width: 1, opacity: 0.16,
    });
  }

  if (early) {
    for (const p of pointsFor(metric)) {
      if (p.year < x0) continue;
      const dot = svgEl("circle", {
        cx: f.x(p.year).toFixed(1), cy: f.y(p[metric]).toFixed(1), r: 3.1,
        fill: COLOUR[p.layer], "fill-opacity": 0.62, class: "dot",
      });
      hook(dot, (evt) => {
        readout.innerHTML = `<b>${p.place}</b><div class="row">${p.year}` +
          ` &middot; ${fmt(p[metric], metric)}</div>` +
          `<div class="prov">${p.basis}</div>`;
        readout.hidden = false;
        placeReadout(readout, evt);
      });
      f.svg.appendChild(dot);
    }
  }

  const { industrial, modern } = seriesFor(state.country, metric);
  polyline(f, industrial.filter(([y]) => y >= x0),
    { stroke: COLOUR.industrial, width: 2.4, dash: "5 4" });
  polyline(f, modern.filter(([y]) => y >= x0),
    { stroke: COLOUR.modern, width: 2.6 });

  /* One shared hover band rather than a handler per point: the modern series
     is annual, so per-point targets on a phone are smaller than a fingertip. */
  const label = DATA.countries[state.country]?.label || state.country;
  const band = svgEl("rect", {
    x: f.pad.l, y: f.pad.t, width: f.iw, height: f.ih, fill: "transparent",
  });
  hook(band, (evt) => {
    const rect = f.svg.getBoundingClientRect();
    const px = (evt.clientX - rect.left) * (f.box.w / rect.width);
    const yr = Math.round(f.x0 + ((px - f.pad.l) / f.iw) * (f.x1 - f.x0));
    const near = (arr) => arr.reduce((best, r) =>
      (!best || Math.abs(r[0] - yr) < Math.abs(best[0] - yr)) ? r : best, null);
    const a = near(modern), b = near(industrial);
    const pick = [a, b].filter(Boolean)
      .reduce((best, r) => (!best || Math.abs(r[0] - yr) < Math.abs(best[0] - yr)) ? r : best, null);
    if (!pick || Math.abs(pick[0] - yr) > 25) { readout.hidden = true; return; }
    const layer = pick === a ? "modern" : "industrial";
    readout.innerHTML = `<b>${label}</b><div class="row">${pick[0]}` +
      ` &middot; ${fmt(pick[1], metric)}</div>` +
      `<div class="prov">${DATA.meta.layers[layer].label}</div>`;
    readout.hidden = false;
    placeReadout(readout, evt);
  });
  f.svg.appendChild(band);
  f.svg.onpointerleave = () => { readout.hidden = true; };

  $("#long-title").textContent = early
    ? `${m.label}, ${DATA.meta.year0} to ${DATA.meta.year1}`
    : `${m.label} since 1800`;
  describe(f.svg, `${m.label} for ${label}, ${x0} to ${DATA.meta.year1}, ` +
                  `against every other country and, before 1800, individual tax assessments.`);

  /* Country label first, rather than "the richest tenth of United Kingdom":
     the labels come from OWID and carry no article, so any sentence that puts
     one in front of them is wrong for about half the list. */
  const last = modern.length ? modern[modern.length - 1] : null;
  $("#long-caption").textContent = last
    ? `${label}, ${last[0]}: the richest ${metric === "top1" ? "hundredth" : "tenth"} ` +
      `held ${fmt(last[1], metric)} of all household wealth.`
    : `${label} has no annual series on this measure.`;
}

function drawEarly() {
  const metric = state.metric;
  const m = METRICS[metric];
  const f = frame("#early", 0.34, 200, 320, 1275, 1810, m.max);
  const readout = $("#early-readout");
  readout.hidden = true;
  axes(f, metric);

  for (const s of DATA.regions) {
    const pts = (s[metric] || []).filter(([y]) => y >= f.x0 && y <= f.x1);
    const line = polyline(f, pts, { stroke: COLOUR.preindustrial, width: 2.2, opacity: 0.9 });
    if (!line || !pts.length) continue;
    const t = svgEl("text", {
      x: (f.x(pts[pts.length - 1][0]) - 4).toFixed(1),
      y: (f.y(pts[pts.length - 1][1]) - 8).toFixed(1),
      "text-anchor": "end", "font-size": 11.5, fill: "var(--ink-soft)",
    });
    t.textContent = s.label;
    f.svg.appendChild(t);
  }

  const groups = { England: "var(--w-england)", Piedmont: "var(--w-piedmont)" };
  for (const p of pointsFor(metric)) {
    if (p.year > f.x1) continue;
    const dot = svgEl("circle", {
      cx: f.x(p.year).toFixed(1), cy: f.y(p[metric]).toFixed(1), r: 3.6,
      fill: groups[p.group] || COLOUR.preindustrial, "fill-opacity": 0.7, class: "dot",
    });
    hook(dot, (evt) => {
      readout.innerHTML = `<b>${p.place}</b><div class="row">${p.year}` +
        ` &middot; ${fmt(p[metric], metric)}</div>` +
        (p.n ? `<div class="row">${Math.round(p.n).toLocaleString()} households</div>` : "") +
        `<div class="prov">${p.basis}</div>`;
      readout.hidden = false;
      placeReadout(readout, evt);
    });
    f.svg.appendChild(dot);
  }
  f.svg.onpointerleave = () => { readout.hidden = true; };

  const n = pointsFor(metric).filter((p) => p.year <= f.x1).length;
  describe(f.svg, `${m.label} before 1800: ${n} individual tax assessments, ` +
                  `with regional estimates where they exist.`);
  $("#early-caption").textContent = metric === "gini"
    ? "The lines are regional; the dots are the towns and counties underneath them."
    : "No regional series exists for this measure, so the dots stand alone.";
}

/* ---------------------------------------------------------------- furniture */

function legend(id, entries) {
  $(id).innerHTML = entries.map(([colour, text, note]) =>
    `<span class="explained"${note ? ` title="${note}" tabindex="0"` : ""}>` +
    `<i style="background:${colour}"></i>${text}</span>`).join("");
}

function buildPickers() {
  const sel = $("#country-sel");
  const order = Object.values(DATA.countries)
    .filter((c) => c.modern.top10.length || c.industrial.gini.length)
    .sort((a, b) => a.label.localeCompare(b.label));
  sel.innerHTML = order.map((c) =>
    `<option value="${c.iso}">${c.label}</option>`).join("");
  sel.value = state.country;
  $("#metric-sel").value = state.metric;
}

function renderLayers() {
  const L = DATA.meta.layers;
  const present = { deep: DATA.meta.deep_present, preindustrial: true, industrial: true, modern: true };
  $("#layers").innerHTML = Object.entries(L).map(([key, v]) =>
    `<dt><i style="background:${COLOUR[key]}"></i>${v.label}` +
    (present[key] ? "" : ` <span class="pending">not yet loaded</span>`) +
    `</dt><dd>${v.note}</dd>`).join("");

  $("#sources").innerHTML = DATA.meta.sources.map((s) =>
    `<li><a href="${s.url}" rel="noopener">${s.name}</a>, ${s.publisher}. ` +
    `${s.role} <span class="fine">${s.licence}.</span></li>`).join("");
}

function render() {
  const m = METRICS[state.metric];
  $("#metric-hint").textContent = m.hint;
  const c = DATA.countries[state.country];
  const spans = [];
  if (c?.industrial.gini.length) spans.push("1820");
  if (c?.modern.top10.length) spans.push(`${c.modern.top10[0][0]}`);
  $("#country-hint").textContent = spans.length ? `from ${Math.min(...spans.map(Number))}` : "";

  /* The legend lists the layers this measure actually has. The Gini has no
     national-accounts series and the richest hundredth has no decadal one, so
     a fixed legend names a colour the reader cannot find. */
  const NAMED = {
    preindustrial: ["One tax assessment", DATA.meta.layers.preindustrial.note],
    industrial: ["Decadal estimate", DATA.meta.layers.industrial.note],
    modern: ["National accounts", DATA.meta.layers.modern.note],
  };
  legend("#legend-long", [
    ...m.layers
      .filter((k) => k !== "preindustrial" || state.early === "show")
      .map((k) => [COLOUR[k], ...NAMED[k]]),
    ["var(--ink-faint)", "Every other country"],
  ]);
  /* Only the Gini has regional series, so on the other two measures that
     swatch would name a colour that is nowhere on the chart, and a reader
     would go looking for a line that does not exist. */
  const hasRegions = DATA.regions.some((s) => (s[state.metric] || []).length);
  legend("#legend-early", [
    ["var(--w-england)", "England, by county"],
    ["var(--w-piedmont)", "Piedmont, by town"],
    ...(hasRegions ? [[COLOUR.preindustrial, "Regional estimate"]] : []),
  ]);
  $("#early-sub").textContent = hasRegions
    ? "Each dot is one tax assessment: an English county in the lay subsidies, or a "
      + "Piedmontese town in its estimo. The lines are regional estimates every fifty years."
    : "Each dot is one tax assessment: an English county in the lay subsidies, or a "
      + "Piedmontese town in its estimo.";

  drawLong();
  drawEarly();
  writeHash();
}

function wire() {
  $("#metric-sel").addEventListener("change", (e) => {
    state.metric = e.target.value; render();
  });
  $("#country-sel").addEventListener("change", (e) => {
    state.country = e.target.value; render();
  });
  for (const btn of document.querySelectorAll("[data-early]")) {
    btn.setAttribute("aria-checked", String(btn.dataset.early === state.early));
    btn.addEventListener("click", () => {
      state.early = btn.dataset.early;
      for (const b of document.querySelectorAll("[data-early]")) {
        b.setAttribute("aria-checked", String(b.dataset.early === state.early));
      }
      render();
    });
  }
  let t = null;
  window.addEventListener("resize", () => {
    clearTimeout(t); t = setTimeout(render, 140);
  });
}

fetch("wealth.json")
  .then((r) => { if (!r.ok) throw new Error(`wealth.json ${r.status}`); return r.json(); })
  .then((d) => {
    DATA = d;
    readHash();
    buildPickers();
    renderLayers();
    wire();
    render();
    document.body.classList.remove("loading");
  })
  .catch((err) => {
    /* Say which half failed. A render bug reported as "could not load the data"
       sent a previous session looking in the wrong place entirely. */
    const stage = DATA ? "draw the charts" : "load the data";
    document.body.classList.remove("loading");
    $("main").insertAdjacentHTML("afterbegin",
      `<section class="panel"><h2>Could not ${stage}</h2>` +
      `<p class="sub">${err.message}</p></section>`);
    throw err;
  });
