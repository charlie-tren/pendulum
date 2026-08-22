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

const DEFAULTS = { metric: "gini", country: "GBR" };
const state = { ...DEFAULTS };
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
    blurb: "0 is everyone equal, 1 is one household owning everything.",
  },
  top10: {
    label: "Share held by the richest 10%", max: 100, pct: true,
    blurb: "Out of all the household wealth there was.",
  },
  top1: {
    label: "Share held by the richest 1%", max: 100, pct: true,
    blurb: "Out of all the household wealth there was.",
  },
};

/* Panels are periods, not sources. The historians' estimates and the national
   accounts both cover 1800 onwards, so giving them a panel each put "1820 to
   2010" next to "1820 to 2024" and read as two consecutive eras when it is one
   era measured twice. They share the last panel and its time axis, and the
   legend tells them apart instead.

   Panel width is not proportional to length in years. The archaeology spans
   11,000 and the last panel 224, and sizing by duration would leave the one
   with all the data a sliver. */
const ERAS = [
  { key: "deep", layers: ["deep"], kind: "dots", label: "Dug-up houses" },
  { key: "preindustrial", layers: ["preindustrial"], kind: "dots", label: "Tax registers" },
  { key: "measured", layers: ["industrial", "modern"], kind: "band", label: "Whole countries" },
];

const yearLabel = (y) => (y < 0 ? `${Math.abs(y)} BC` : `${y}`);
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

function eraContent(era, metric) {
  if (era.kind === "dots") {
    const pts = pointsIn(era.key, metric);
    const regions = era.key === "preindustrial"
      ? DATA.regions.filter((s) => (s[metric] || []).length) : [];
    return { pts, regions, series: [] };
  }
  /* One entry per source layer, drawn on the panel's shared axis. Dashed for
     the reconstructed decadal estimates, solid for the measured annual ones. */
  return {
    pts: [], regions: [],
    series: era.layers.map((key) => ({
      key,
      label: DATA.meta.layers[key].label,
      dist: distribution(key, metric),
      sel: countrySeries(state.country, key, metric),
      dashed: key === "industrial",
      colour: key === "industrial" ? "var(--w-mid)" : "var(--w-now)",
    })).filter((s) => s.dist.length || s.sel.length),
  };
}

function activeEras(metric) {
  return ERAS.map((e) => ({ ...e, content: eraContent(e, metric) }))
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
    const { pts, regions, series } = era.content;
    const years = [
      ...pts.map((p) => p.year),
      ...regions.flatMap((s) => s[metric].map(([y]) => y)),
      ...series.flatMap((s) => [...s.dist.map((d) => d.year), ...s.sel.map(([y]) => y)]),
    ];
    let x0 = Math.min(...years), x1 = Math.max(...years);
    if (x0 === x1) { x0 -= 1; x1 += 1; }
    const padY = (x1 - x0) * 0.04;
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

    // era name above, span below: the two facts that stop the panels reading
    // as one continuous axis
    const name = svgEl("text", {
      x: lane.x, y: (lane.y - 1).toFixed(1), "font-size": 12,
      "font-weight": 600, fill: "var(--ink-soft)",
    });
    name.textContent = era.label;
    svg.appendChild(name);
    const span = svgEl("text", {
      x: (lane.x + lane.w / 2).toFixed(1), y: (lane.y + lane.h + 17).toFixed(1),
      "text-anchor": "middle", "font-size": 11, fill: "var(--ink-faint)",
    });
    span.textContent = `${yearLabel(x0)} to ${yearLabel(x1)}`;
    svg.appendChild(span);

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

    // ---- regional lines through the pre-industrial towns
    for (const s of regions) {
      const p = s[metric];
      svg.appendChild(svgEl("polyline", {
        points: p.map(([y, v]) => `${xOf(y).toFixed(1)},${yOf(lane, v).toFixed(1)}`).join(" "),
        fill: "none", stroke: "var(--w-early)", "stroke-width": 1.8, "stroke-opacity": 0.75,
      }));
    }

    // ---- one dot per site or assessment
    for (const p of pts) {
      const dot = svgEl("circle", {
        cx: xOf(p.year).toFixed(1), cy: yOf(lane, p[metric]).toFixed(1), r: 3.2,
        fill: `var(--w-${era.key === "deep" ? "deep" : "early"})`,
        "fill-opacity": 0.6, class: "dot",
      });
      hook(dot, (evt) => {
        readout.innerHTML = `<b>${p.place}</b>` +
          `<div class="row"><span>${yearLabel(p.year)}</span><span>${fmt(p[metric])}</span></div>` +
          (p.n ? `<div class="row"><span>sample</span><span>${Math.round(p.n).toLocaleString()}</span></div>` : "") +
          `<div class="prov">${p.basis}</div>`;
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
        const label = DATA.countries[state.country]?.label || state.country;
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
    `${n}, one per period, each on its own time scale. The gaps between them are ` +
    "not gaps in history. They share the vertical scale, which is the only " +
    "comparison this evidence supports.";
}

/* ----------------------------------------------------------------- furniture */

function renderLegend() {
  const eras = activeEras(state.metric);
  const has = (k) => eras.some((e) => e.key === k);
  const sources = eras.flatMap((e) => e.content.series || []);
  const out = [];
  if (has("deep")) out.push(["var(--w-deep)", "One dig site"]);
  if (has("preindustrial")) out.push(["var(--w-early)", "One tax assessment"]);
  for (const src of sources) out.push([src.colour, `${src.label}, middle half`]);
  if (sources.length) {
    out.push(["var(--w-pick)", DATA.countries[state.country]?.label || state.country]);
  }
  $("#legend-eras").innerHTML = out.map(([c, t]) =>
    `<span><i style="background:${c}"></i>${t}</span>`).join("");
}

function renderLayers() {
  const L = DATA.meta.layers;
  const present = new Set(
    activeEras("gini").concat(activeEras("top10"))
      .flatMap((e) => e.layers));
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
  sel.innerHTML = Object.values(DATA.countries)
    .filter((c) => c.modern.top10.length || c.industrial.gini.length)
    .sort((a, b) => a.label.localeCompare(b.label))
    .map((c) => `<option value="${c.iso}">${c.label}</option>`).join("");
  sel.value = state.country;
  $("#metric-sel").value = state.metric;
}

function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  if (METRICS[p.get("metric")]) state.metric = p.get("metric");
  if (p.get("country") && DATA.countries[p.get("country")]) state.country = p.get("country");
}

function writeHash() {
  const p = new URLSearchParams();
  for (const k of ["metric", "country"]) if (state[k] !== DEFAULTS[k]) p.set(k, state[k]);
  const h = p.toString();
  try {
    history.replaceState(null, "", h ? `#${h}` : location.pathname + location.search);
  } catch { /* sandboxed iframes refuse this, and it must not take the page down */ }
}

function render() {
  renderLegend();
  drawEras();
  const c = DATA.countries[state.country];
  const spans = [];
  if (c?.industrial.gini.length) spans.push(c.industrial.gini[0][0]);
  if (c?.modern.top10.length) spans.push(c.modern.top10[0][0]);
  $("#country-hint").textContent = spans.length
    ? `charted from ${Math.min(...spans)}` : "no national series";
  writeHash();
}

function wire() {
  $("#metric-sel").addEventListener("change", (e) => { state.metric = e.target.value; render(); });
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
