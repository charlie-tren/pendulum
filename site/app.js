/* Pendulum: static frontend. No framework, no build step, no dependencies.
   Charts are hand-rolled SVG so this still runs in five years. */

const DEFAULTS = { group: "world", weight: "by_population", year: null,
                   regime: null, missing: "include" };

/* The most recent year every year-driven chart can render. The regime data
   stops before the political series, so this is the regime end, not the last
   year in the file. */
const latestYear = () => DATA.meta.regime_coverage_end;
const BANDS = ["left", "centre", "right", "no_reading", "unresolved"];
const SOURCES = ["dpi", "vparty", "carry_forward", "hand", "wikidata", "no_reading", "unresolved"];
const REGIME_ORDER = ["closed_autocracy", "electoral_autocracy",
                      "electoral_democracy", "liberal_democracy", "unknown"];
const SPECTRUM = ["f0", "f1", "f2", "f3", "f4", "f5", "f6", "uncovered"];

const state = { ...DEFAULTS };
let DATA = null;

/* Charts are drawn in the container's own CSS pixels rather than a fixed
   960-wide viewBox. With a fixed viewBox everything scales with the container,
   so at 375px wide an 11px axis label rendered at 3.5px and the whole thing was
   unreadable on a phone. Measuring first costs a layout read and makes every
   font size mean what it says. */
const clamp = (lo, v, hi) => Math.max(lo, Math.min(v, hi));

function boxFor(svgId, ratio, minH, maxH) {
  const svg = document.querySelector(svgId);
  const measured = Math.round(svg.parentElement.getBoundingClientRect().width);
  const w = measured > 40 ? measured
    : Math.round(clamp(280, document.documentElement.clientWidth - 76, 920));
  return { w, h: Math.round(clamp(minH, w * ratio, maxH)) };
}

function describe(svg, text) {
  const title = svgEl("title");
  title.textContent = text;
  svg.insertBefore(title, svg.firstChild);
  svg.setAttribute("aria-label", text);
  svg.setAttribute("role", "img");
}

const $ = (sel) => document.querySelector(sel);
const svgEl = (name, attrs = {}) => {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
};
const pct = (v) => (v == null ? "n/a" : `${(v * 100).toFixed(v * 100 < 10 ? 1 : 0)}%`);
const sum = (obj) => Object.values(obj || {}).reduce((a, b) => a + b, 0);

/* Some palette entries carry a colour_dark. The pale greys in particular were
   the brightest thing on a dark chart, which put the emphasis on the two
   categories that matter least. */
const darkMedia = window.matchMedia("(prefers-color-scheme: dark)");
const shade = (entry) => (darkMedia.matches && entry.colour_dark) || entry.colour;

/* "Exclude" drops the two grey categories. Where the bands add to the whole
   group the remainder is rescaled, so the chart still reads as shares of the
   countries that have a reading. Where they do not, the bands are simply
   hidden and the scale is left alone. The default keeps them: a reader has to
   ask for this. */
const MISSING = new Set(["no_reading", "unresolved", "uncovered"]);

function dropMissing(series, keys, { rescale = true } = {}) {
  if (state.missing !== "exclude") return { series, keys };
  const kept = keys.filter((k) => !MISSING.has(k));
  if (!rescale) return { series, keys: kept };
  return {
    keys: kept,
    series: series.map((row) => {
      const total = kept.reduce((a, k) => a + (row[k] || 0), 0);
      const out = { ...row };
      for (const k of kept) out[k] = total ? (row[k] || 0) / total : 0;
      return out;
    }),
  };
}

/* Follow the pointer rather than parking in the top right, which is where the
   right-hand band sits in most years: the readout covered the thing it was
   describing. Measure after unhiding, and flip to the other side of the cursor
   rather than running off the panel. On mobile the readout is static, below the
   chart, so leave it alone. */
function placeReadout(el, evt) {
  if (getComputedStyle(el).position === "static") return;
  const box = el.parentElement.getBoundingClientRect();
  const pad = 14;
  const w = el.offsetWidth;
  const h = el.offsetHeight;
  let x = evt.clientX - box.left + pad;
  let y = evt.clientY - box.top + pad;
  if (x + w > box.width - 6) x = evt.clientX - box.left - w - pad;
  if (y + h > box.height - 6) y = evt.clientY - box.top - h - pad;
  el.style.left = `${clamp(6, x, Math.max(6, box.width - w - 6))}px`;
  el.style.top = `${clamp(6, y, Math.max(6, box.height - h - 6))}px`;
}

/* ---------- URL state. The default is never written to the URL. ---------- */

function readHash() {
  const params = new URLSearchParams(location.hash.slice(1));
  const group = params.get("group");
  const weight = params.get("weight");
  const year = parseInt(params.get("year"), 10);
  if (group && DATA.groups[group]) state.group = group;
  if (weight === "by_country" || weight === "by_population") state.weight = weight;
  if (Number.isInteger(year)) state.year = year;
  const regime = params.get("regime");
  if (regime && REGIME_ORDER.includes(regime)) state.regime = regime;
  if (params.get("missing") === "exclude") state.missing = "exclude";
}

function writeHash() {
  const params = new URLSearchParams();
  for (const key of ["group", "weight", "year", "regime", "missing"]) {
    if (key === "regime" && state.regime === defaultRegime()) continue;
    if (key === "year" && state.year === latestYear()) continue;
    if (state[key] !== DEFAULTS[key]) params.set(key, state[key]);
  }
  const hash = params.toString();
  try {
    history.replaceState(null, "", hash ? `#${hash}` : location.pathname + location.search);
  } catch (err) {
    /* Sandboxed contexts (an about:srcdoc iframe, a file:// page in some
       browsers) refuse replaceState with a SecurityError. Shareable URLs are a
       convenience, not a feature the charts depend on, so lose them quietly
       rather than taking the page down with them. */
  }
}

/* ---------- shared chart geometry ---------- */

function scales(series, box, pad) {
  const years = series.map((r) => r.year);
  const [y0, y1] = [Math.min(...years), Math.max(...years)];
  const iw = box.w - pad.l - pad.r;
  const ih = box.h - pad.t - pad.b;
  return {
    x: (yr) => pad.l + ((yr - y0) / (y1 - y0)) * iw,
    y: (v) => pad.t + (1 - v) * ih,
    y0, y1, iw, ih, pad, box,
  };
}

function axes(svg, s, { ticks = [0, 0.5, 1], fmt = pct, step = 10 } = {}) {
  for (const v of ticks) {
    // ticks may be on a data scale rather than 0..1, so normalise to plot space
    const at = v / (ticks[ticks.length - 1] || 1);
    svg.appendChild(svgEl("line", {
      x1: s.pad.l, x2: s.box.w - s.pad.r, y1: s.y(at), y2: s.y(at),
      stroke: "var(--rule)", "stroke-width": 1,
    }));
    const t = svgEl("text", {
      x: s.pad.l - 8, y: s.y(at) + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--ink-faint)",
    });
    t.textContent = fmt(v);
    svg.appendChild(t);
  }
  const first = Math.ceil(s.y0 / step) * step;
  for (let yr = first; yr <= s.y1; yr += step) {
    const t = svgEl("text", {
      x: s.x(yr), y: s.box.h - 8, "text-anchor": "middle",
      "font-size": 11, fill: "var(--ink-faint)",
    });
    t.textContent = yr;
    svg.appendChild(t);
  }
}

/* ---------- stacked area ---------- */

function drawStack(svgId, series, keys, palette, box, { label = "", max = 1 } = {}) {
  const svg = $(svgId);
  svg.innerHTML = "";
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 44, r: 10, t: 10, b: 26 };
  const s = scales(series, box, pad);
  axes(svg, s, max === 1 ? {} : { ticks: [0, max / 2, max] });

  let base = series.map(() => 0);
  for (const key of keys) {
    const top = series.map((r, i) => base[i] + (r[key] || 0));
    const pts = series.map((r, i) => `${s.x(r.year).toFixed(1)},${s.y(top[i] / max).toFixed(1)}`)
      .concat(series.map((r, i) =>
        `${s.x(r.year).toFixed(1)},${s.y(base[i] / max).toFixed(1)}`).reverse());
    svg.appendChild(svgEl("polygon", { points: pts.join(" "), fill: shade(palette[key]) }));
    base = top;
  }

  if (label) describe(svg, label);
  return s;
}

/* ---------- index line ---------- */

function drawLine(series) {
  const box = boxFor("#line", 0.26, 175, 240);
  const svg = $("#line");
  svg.innerHTML = "";
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 46, r: 10, t: 14, b: 26 };
  const rows = series.filter((r) => r.mean_by_country != null || r.mean_by_population != null);
  const s = scales(rows, box, pad);
  const key = state.weight === "by_country" ? "mean_by_country" : "mean_by_population";
  const maKey = `${key}_ma3`;

  /* Fit the axis to the data rather than the full minus one to plus one. The
     world never approaches either end, so the fixed scale squashed every real
     movement into the middle fifth of the chart. Zero is always included so the
     crossing point stays honest. */
  const vals = rows.flatMap((r) => [r[key], r[maKey]]).filter((v) => v != null);
  const lo = Math.min(0, ...vals);
  const hi = Math.max(0, ...vals);
  /* Symmetric about zero: left and right must be the same distance from the
     centre line, or the chart flatters whichever side happens to sit closer to
     the frame. Still far tighter than the full minus one to plus one, which put
     every real movement in a fifth of the height. */
  const reach = Math.max(Math.abs(lo), Math.abs(hi)) * 1.12 || 0.1;
  const y0 = -reach;
  const y1 = reach;
  const unit = (v) => (v - y0) / (y1 - y0);

  /* Faint rules every tenth so a reader can judge level and slope, without
     putting numbers back on an axis whose units mean nothing to them. */
  for (let v = Math.ceil(y0 * 10) / 10; v <= y1; v = Math.round((v + 0.1) * 10) / 10) {
    if (Math.abs(v) < 1e-9) continue;
    svg.appendChild(svgEl("line", {
      x1: pad.l, x2: box.w - pad.r, y1: s.y(unit(v)), y2: s.y(unit(v)),
      stroke: "var(--rule)", "stroke-width": 1,
    }));
  }
  svg.appendChild(svgEl("line", {
    x1: pad.l, x2: box.w - pad.r, y1: s.y(unit(0)), y2: s.y(unit(0)),
    stroke: "var(--ink-faint)", "stroke-width": 1.2,
  }));
  for (const [at, text] of [[1, "right"], [0, "left"]]) {
    const label = svgEl("text", {
      x: pad.l - 8, y: s.y(at) + (at ? 10 : -1), "text-anchor": "end",
      "font-size": 11.5, fill: "var(--ink-faint)",
    });
    label.textContent = text;
    svg.appendChild(label);
  }
  for (let yr = Math.ceil(s.y0 / 10) * 10; yr <= s.y1; yr += 10) {
    const t2 = svgEl("text", {
      x: s.x(yr), y: box.h - 8, "text-anchor": "middle",
      "font-size": 11, fill: "var(--ink-faint)",
    });
    t2.textContent = yr;
    svg.appendChild(t2);
  }

  const zeroY = s.y(unit(0));
  const defs = svgEl("defs");
  for (const [id, y, h] of [["clipRight", pad.t, zeroY - pad.t],
                            ["clipLeft", zeroY, pad.t + s.ih - zeroY]]) {
    const clip = svgEl("clipPath", { id });
    clip.appendChild(svgEl("rect", { x: 0, y, width: box.w, height: Math.max(h, 0) }));
    defs.appendChild(clip);
  }
  svg.appendChild(defs);

  const filled = rows.filter((r) => r[maKey] != null);
  if (filled.length > 1) {
    const top = filled.map((r) => `${s.x(r.year).toFixed(1)},${s.y(unit(r[maKey])).toFixed(1)}`);
    const poly = top.concat([
      `${s.x(filled[filled.length - 1].year).toFixed(1)},${zeroY.toFixed(1)}`,
      `${s.x(filled[0].year).toFixed(1)},${zeroY.toFixed(1)}`,
    ]).join(" ");
    for (const [clip, bucket] of [["clipRight", "right"], ["clipLeft", "left"]]) {
      svg.appendChild(svgEl("polygon", {
        points: poly, fill: shade(DATA.palette.buckets[bucket]),
        "fill-opacity": 0.22, "clip-path": `url(#${clip})`,
      }));
    }
  }

  const path = (field, stroke, width, opacity) => {
    const pts = rows.filter((r) => r[field] != null)
      .map((r) => `${s.x(r.year).toFixed(1)},${s.y(unit(r[field])).toFixed(1)}`);
    if (!pts.length) return;
    svg.appendChild(svgEl("polyline", {
      points: pts.join(" "), fill: "none", stroke,
      "stroke-width": width, "stroke-opacity": opacity,
      "stroke-linejoin": "round", "stroke-linecap": "round",
    }));
  };
  path(key, "var(--ink-faint)", 1.4, 0.55);
  path(maKey, "var(--ink)", 2.4, 1);
  describe(svg, "Mean government position over time, shaded red where the balance sits " +
                "right of centre and blue where it sits left.");

  /* Its own hover: this is two lines rather than stacked bands, so the reader
     wants the two values, not a share breakdown. */
  const readout = $("#line-readout");
  const marker = svgEl("line", {
    y1: pad.t, y2: pad.t + s.ih, stroke: "var(--ink)",
    "stroke-width": 1, "stroke-opacity": 0.35, visibility: "hidden",
  });
  svg.appendChild(marker);
  const lean = (v) => (v > 0.02 ? "right of centre" : v < -0.02 ? "left of centre" : "at the centre");
  const show = (evt) => {
    const rect = svg.getBoundingClientRect();
    const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
    const px = ((clientX - rect.left) / rect.width) * box.w;
    const year = Math.round(s.y0 + ((px - pad.l) / s.iw) * (s.y1 - s.y0));
    const row = rows.find((r) => r.year === year);
    if (!row || row[key] == null) return;
    marker.setAttribute("x1", s.x(year));
    marker.setAttribute("x2", s.x(year));
    marker.setAttribute("visibility", "visible");
    readout.innerHTML =
      `<b>${year}</b>` +
      `<div class="row"><span>This year</span><span>${row[key].toFixed(2)}</span></div>` +
      (row[maKey] != null
        ? `<div class="row"><span>Three-year</span><span>${row[maKey].toFixed(2)}</span></div>` : "") +
      `<div class="prov">${lean(row[key])}</div>` +
      (row.coded_share_pop != null
        ? `<div class="prov">${pct(state.weight === "by_population"
            ? row.coded_share_pop : row.coded_share_countries)} of the group has a reading</div>`
        : "");
    readout.hidden = false;
    placeReadout(readout, evt);
  };
  svg.addEventListener("pointermove", show);
  svg.addEventListener("touchmove", show, { passive: true });
  svg.addEventListener("pointerleave", () => {
    readout.hidden = true;
    marker.setAttribute("visibility", "hidden");
  });
}

/* ---------- regime x ideology mosaic ----------
   Column width is the share of people living under that regime type; row
   height within the column is the ideology split inside it. So the AREA of a
   block is its share of everyone, which is the only reading that answers
   "how many people live under a right-wing electoral autocracy". */

function drawMosaic(group) {
  const svg = $("#mosaic");
  const readout = $("#mosaic-readout");
  svg.innerHTML = "";
  readout.hidden = true;

  const row = (group.cross || []).find((r) => r.year === state.year);
  if (!row) {
    $("#mosaic-caption").textContent = "No regime classification for this year.";
    return;
  }

  const box = boxFor("#mosaic", 0.36, 270, 340);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 4, r: 4, t: 6, b: 46 };
  const iw = box.w - pad.l - pad.r;
  const ih = box.h - pad.t - pad.b;
  const gap = 7;

  let cols = REGIME_ORDER
    .filter((regime) => regime !== "unknown")
    .map((regime) => ({ regime, cells: row.cells[regime] || {} }));
  if (state.missing === "exclude") {
    /* Rescale the whole grid over the countries that have a reading, so the
       columns still describe the same population and the widths stay honest. */
    const coded = cols.reduce((a, col) => a + BANDS.filter((b) => !MISSING.has(b))
      .reduce((x, b) => x + (col.cells[b] || 0), 0), 0);
    cols = cols.map((col) => ({
      regime: col.regime,
      cells: Object.fromEntries(BANDS.filter((b) => !MISSING.has(b))
        .map((b) => [b, coded ? (col.cells[b] || 0) / coded : 0])),
    }));
  }
  cols = cols.map((col) => ({ ...col, total: sum(col.cells) }))
    .filter((col) => col.total > 0.0005);
  const usable = iw - gap * (cols.length - 1);

  let x = pad.l;
  for (const col of cols) {
    const w = col.total * usable;
    let y = pad.t;
    for (const band of BANDS) {
      const v = col.cells[band];
      if (!v) continue;
      const h = (v / col.total) * ih;
      const rect = svgEl("rect", {
        x: x.toFixed(1), y: y.toFixed(1),
        width: Math.max(w, 0.5).toFixed(1), height: Math.max(h, 0).toFixed(1),
        fill: shade(DATA.palette.buckets[band]), class: "mosaic-cell",
      });
      const n = (row.counts[col.regime] || {})[band] || 0;
      const show = (evt) => {
        readout.innerHTML =
          `<b>${pct(v)} of people</b>` +
          `<div class="row"><span><i style="background:${shade(DATA.palette.buckets[band])}"></i>` +
          `${DATA.palette.buckets[band].label}</span></div>` +
          `<div class="row"><span>${DATA.palette.regimes[col.regime].label}</span></div>` +
          `<div class="prov">${Math.round(v * row.pop / 1e6)}m people · ` +
          `${n} ${n === 1 ? "country" : "countries"} · ${row.year}</div>`;
        readout.hidden = false;
        placeReadout(readout, evt);
      };
      rect.addEventListener("pointerenter", show);
      rect.addEventListener("pointermove", show);
      svg.appendChild(rect);

      if (w > 64 && h > 22) {
        const light = band === "no_reading" || band === "unresolved";
        const t = svgEl("text", {
          x: (x + 8).toFixed(1), y: (y + 17).toFixed(1), "font-size": 12.5,
          fill: light ? "var(--ink-soft)" : "#fff", "font-weight": 600,
        });
        t.textContent = pct(v);
        svg.appendChild(t);
      }
      y += h;
    }
    /* Four names across one row overlapped as soon as a column narrowed. Take
       the longest form that fits, and hang the definition off the label itself
       so the words under the chart are what you hover. */
    const meta = DATA.palette.regimes[col.regime];
    const fits = (str) => str.length * 6.6 < w - 6;
    const name = fits(meta.short) ? meta.short : (fits(meta.tiny) ? meta.tiny : "");
    if (name) {
      const label = svgEl("text", {
        x: (x + w / 2).toFixed(1), y: (pad.t + ih + 19).toFixed(1),
        "text-anchor": "middle", "font-size": 12.5,
        fill: "var(--ink-soft)", "font-weight": 600, class: "regime-label",
      });
      label.textContent = name;
      const tip = svgEl("title");
      tip.textContent = `${meta.label}. ${meta.note}`;
      label.appendChild(tip);
      svg.appendChild(label);
    }
    const share = svgEl("text", {
      x: (x + w / 2).toFixed(1), y: (pad.t + ih + (name ? 34 : 20)).toFixed(1),
      "text-anchor": "middle", "font-size": 12.5, fill: "var(--ink-faint)",
    });
    share.textContent = pct(col.total);
    svg.appendChild(share);
    x += w + gap;
  }
  svg.onpointerleave = () => { readout.hidden = true; };
  describe(svg, `Mosaic for ${row.year}. Column width is the share of people under each ` +
                `regime type; block height is the ideology split within it.`);

  const ranked = [];
  for (const col of cols) {
    for (const band of ["left", "centre", "right"]) {
      if (col.cells[band]) ranked.push({ v: col.cells[band], band, regime: col.regime });
    }
  }
  ranked.sort((a, b) => b.v - a.v);
  const top = ranked[0];
  $("#mosaic-caption").textContent = top
    ? `The largest single group in ${row.year} was ` +
      `${DATA.palette.buckets[top.band].label.toLowerCase()}-governed ` +
      `${DATA.palette.regimes[top.regime].short.toLowerCase()}, at ${pct(top.v)} of ` +
      `this group's population.`
    : "";
}

/* ---------- the seven-point spectrum ---------- */

function drawSpectrum(group) {
  const series = (group.spectrum || {})[state.weight] || [];
  if (!series.length) return;
  const shown = dropMissing(series, SPECTRUM);
  const s = drawStack("#spectrum", shown.series, shown.keys, DATA.palette.spectrum,
    boxFor("#spectrum", 0.30, 200, 300),
    { label: `Share of the group by the governing party's position on a seven-point ` +
             `scale, ${series[0].year} to ${series[series.length - 1].year}.` });
  attachHover(s, shown.series, DATA.palette.spectrum, {
    svgId: "#spectrum", readoutId: "#spectrum-readout", keys: shown.keys,
  });

}

/* ---------- the world in one year ----------
   Geometry is projected at build time into plain SVG paths, so there is no
   mapping library here: this fills 176 shapes and stops. */

let MAP = null;
const MAP_BUCKET = { l: "left", c: "centre", r: "right",
                     n: "no_reading", u: "unresolved" };

function bucketAt(iso, year) {
  const row = DATA.map.codes[iso];
  if (!row) return "unresolved";
  const i = year - DATA.map.year0;
  return MAP_BUCKET[row[i]] || "unresolved";
}

function drawMap() {
  const svg = $("#map");
  const readout = $("#map-readout");
  if (!MAP) return;
  svg.innerHTML = "";
  readout.hidden = true;
  svg.setAttribute("viewBox", `0 0 ${MAP.width} ${MAP.height}`);

  const counts = { left: 0, centre: 0, right: 0, no_reading: 0, unresolved: 0 };
  for (const [iso, d] of Object.entries(MAP.paths)) {
    const bucket = bucketAt(iso, state.year);
    counts[bucket] += 1;
    const path = svgEl("path", {
      d, fill: shade(DATA.palette.buckets[bucket]),
      stroke: "var(--panel)", "stroke-width": 0.6, class: "mosaic-cell",
    });
    const show = (evt) => {
      const name = MAP.names[iso] || iso;
      const b = DATA.palette.buckets[bucket];
      readout.innerHTML =
        `<b>${name}</b>` +
        `<div class="row"><span><i style="background:${shade(b)}"></i>${b.label}</span></div>` +
        `<div class="prov">${state.year}</div>`;
      readout.hidden = false;
      placeReadout(readout, evt);
    };
    path.addEventListener("pointerenter", show);
    path.addEventListener("pointermove", show);
    svg.appendChild(path);
  }
  svg.onpointerleave = () => { readout.hidden = true; };

  describe(svg, `World map for ${state.year}, each country coloured by the political ` +
                `direction of its government.`);
  const named = ["left", "centre", "right"]
    .map((k) => `${counts[k]} ${DATA.palette.buckets[k].label.toLowerCase()}`).join(", ");
  $("#map-caption").textContent = `In ${state.year}: ${named}.`;
}

/* ---------- regimes over time, one at a time ---------- */

/* Four panels side by side were 72px wide on a phone and barely wider than a
   thumbnail on a desktop. One chart at full width, with tabs, is legible. */

function defaultRegime() {
  const cross = DATA.groups[state.group].cross || [];
  const solid = cross.filter((r) => r.year <= 2023).slice(-1)[0];
  if (!solid) return "electoral_autocracy";
  return REGIME_ORDER.filter((r) => r !== "unknown")
    .reduce((best, r) => (sum(solid.cells[r]) > sum(solid.cells[best]) ? r : best),
            "closed_autocracy");
}

function buildRegimeTabs() {
  const tabs = $("#regime-tabs");
  tabs.innerHTML = REGIME_ORDER.filter((r) => r !== "unknown").map((r) =>
    `<button type="button" role="radio" data-regime="${r}" ` +
    `aria-checked="${r === state.regime}" title="${DATA.palette.regimes[r].note || ""}">` +
    `${DATA.palette.regimes[r].short}</button>`).join("");
  for (const btn of tabs.querySelectorAll("button")) {
    btn.addEventListener("click", () => {
      state.regime = btn.dataset.regime;
      for (const b of tabs.querySelectorAll("button")) {
        b.setAttribute("aria-checked", String(b.dataset.regime === state.regime));
      }
      drawRegime(DATA.groups[state.group]);
      writeHash();
    });
  }
}

function drawRegime(group) {
  /* V-Dem classifies regimes only to 2025, so the final year has every country
     as unclassified and each band collapses to nothing. Stop where the source
     does rather than drawing the cliff. */
  const cross = (group.cross || []).filter((r) => r.year <= DATA.meta.regime_coverage_end);
  const series = cross.map((r) => ({ year: r.year, ...(r.cells[state.regime] || {}) }));
  if (!series.length) return;
  const label = DATA.palette.regimes[state.regime].short;
  /* All four regimes share one y scale, so switching tabs compares like with
     like instead of rescaling under the reader. */
  const max = Math.max(...cross.flatMap((r) =>
    REGIME_ORDER.filter((x) => x !== "unknown").map((x) => sum(r.cells[x]))), 0.05);

  const shownR = dropMissing(series, BANDS, { rescale: false });
  const sR = drawStack("#regime", shownR.series, shownR.keys, DATA.palette.buckets,
    boxFor("#regime", 0.34, 210, 320), {
      max,
      label: `${label} as a share of the group, split by the ideology of their ` +
             `governments, ${series[0].year} to ${series[series.length - 1].year}.`,
    });
  attachHover(sR, shownR.series, DATA.palette.buckets, {
    svgId: "#regime", readoutId: "#regime-readout", keys: shownR.keys,
  });

  /* Sum the raw cells, not the plotted series: that carries a `year` field and
     summing it produced "202344%". */
  const share = (row) => sum(row.cells[state.regime]);
  const first = cross[0];
  const last = [...cross].reverse().find((r) => r.year <= 2023) || cross[cross.length - 1];
  $("#regime-caption").textContent =
    `${label} accounted for ${pct(share(last))} of this group in ${last.year}, ` +
    `against ${pct(share(first))} in ${first.year}.`;
}

/* ---------- hover on the headline chart ---------- */

function attachHover(s, series, palette, opts = {}) {
  const { svgId = "#area", readoutId = "#readout", keys = BANDS, group = null } = opts;
  const svg = $(svgId);
  const readout = $(readoutId);
  const marker = svgEl("line", {
    y1: s.pad.t, y2: s.pad.t + s.ih, stroke: "var(--ink)",
    "stroke-width": 1, "stroke-opacity": 0.35, visibility: "hidden",
  });
  svg.appendChild(marker);
  const counts = group ? group.by_country : null;

  const show = (evt) => {
    const rect = svg.getBoundingClientRect();
    const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
    const px = ((clientX - rect.left) / rect.width) * s.box.w;
    const year = Math.round(s.y0 + ((px - s.pad.l) / s.iw) * (s.y1 - s.y0));
    const row = series.find((r) => r.year === year);
    if (!row) return;
    marker.setAttribute("x1", s.x(year));
    marker.setAttribute("x2", s.x(year));
    marker.setAttribute("visibility", "visible");

    const countRow = (counts && counts.find((r) => r.year === year)) || {};
    const src = Object.entries(countRow.source || {})
      .filter(([, v]) => v >= 0.02)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${DATA.palette.sources[k].label} ${Math.round(v * 100)}%`)
      .join(" · ");
    const rows = keys.filter((k) => (row[k] || 0) > 0.001).map((k) =>
      `<div class="row"><span><i style="background:${shade(palette[k])}"></i>` +
      `${palette[k].label}</span><span>${pct(row[k])}</span></div>`);
    readout.innerHTML = `<b>${year}</b>${rows.join("")}` +
      (state.weight === "by_population" && row.pop
        ? `<div class="prov">${(row.pop / 1e9).toFixed(2)}bn people</div>` : "") +
      (src ? `<div class="prov">${src}</div>` : "");
    readout.hidden = false;
    placeReadout(readout, evt);
  };
  const hide = () => { readout.hidden = true; marker.setAttribute("visibility", "hidden"); };
  svg.addEventListener("pointermove", show);
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("touchmove", show, { passive: true });
}

/* Two scrubbers, one year. The mosaic and the map sit far apart on the page, so
   each carries its own control, but they are the same piece of state. */
function syncYear() {
  for (const [id, out] of [["#year", "#year-out"], ["#map-year", "#map-year-out"]]) {
    const el = $(id);
    const year = clamp(+el.min, state.year, +el.max);
    el.value = year;
    $(out).textContent = year;
  }
}

/* ---------- playing the timeline ----------
   Both scrubbers drive the same year, so one player serves them. Touching a
   slider stops playback: the person has taken over. */

const PLAY_MS = 320;
let playTimer = null;

function playing() { return playTimer !== null; }

const ICON_PLAY = "M4 2.5v11l9-5.5z";
const ICON_PAUSE = "M4 2.5h3.2v11H4zM8.8 2.5H12v11H8.8z";

function setPlayButtons(on) {
  for (const btn of document.querySelectorAll(".play")) {
    btn.setAttribute("aria-pressed", String(on));
    btn.setAttribute("aria-label", on ? "Pause the timeline" : "Play the timeline");
    const path = btn.querySelector("path");
    if (path) path.setAttribute("d", on ? ICON_PAUSE : ICON_PLAY);
  }
}

function stopPlay() {
  if (playTimer !== null) {
    clearInterval(playTimer);
    playTimer = null;
    setPlayButtons(false);
  }
}

function startPlay() {
  const slider = $("#map-year");
  const lo = +slider.min;
  const hi = +slider.max;
  // The page opens near the end of the range, so playing from there would give
  // two or three years and then a jump back. Restart the run instead.
  if (state.year > hi - 5) state.year = lo;
  setPlayButtons(true);
  playTimer = setInterval(() => {
    state.year = state.year >= hi ? lo : state.year + 1;
    syncYear();
    drawMosaic(DATA.groups[state.group]);
    drawMap();
    writeHash();
  }, PLAY_MS);
}

/* ---------- render ---------- */

function render() {
  const group = DATA.groups[state.group];
  const series = group[state.weight];
  const palette = DATA.palette.buckets;
  const byPop = state.weight === "by_population";

  $("#chart-title").textContent = byPop ? "How people are governed"
                                        : "How countries are governed";
  $("#leans-title").textContent =
    `Which way ${group.article}${group.leans_as || group.label} leans`;
  $("#group-hint").textContent = group.n_members ? `${group.n_members} countries` : "";

  $("#legend").innerHTML = BANDS.map((k) =>
    `<span><i style="background:${shade(palette[k])}"></i>${palette[k].label}</span>`).join("");
  $("#legend-mosaic").innerHTML = $("#legend-regime").innerHTML =
    $("#legend-map").innerHTML = $("#legend").innerHTML;
  $("#legend-lines").innerHTML =
    '<span><svg class="swatch" viewBox="0 0 26 8"><line x1="1" y1="4" x2="25" y2="4" ' +
    'stroke="var(--ink-faint)" stroke-width="1.6" stroke-opacity=".7"/></svg>Yearly</span>' +
    '<span><svg class="swatch" viewBox="0 0 26 8"><line x1="1" y1="4" x2="25" y2="4" ' +
    'stroke="var(--ink)" stroke-width="3"/></svg>Three-year average</span>';
  $("#legend-spectrum").innerHTML = SPECTRUM.map((k) =>
    `<span><i style="background:${shade(DATA.palette.spectrum[k])}"></i>` +
    `${DATA.palette.spectrum[k].label}</span>`).join("");
  $("#legend-src").innerHTML = SOURCES.map((k) => {
    const s = DATA.palette.sources[k];
    return `<span class="explained" title="${s.note || ""}" tabindex="0">` +
           `<i style="background:${shade(s)}"></i>${s.label}</span>`;
  }).join("");

  const shown = dropMissing(series, BANDS);
  const s = drawStack("#area", shown.series, shown.keys, palette,
    boxFor("#area", 0.42, 230, 380), {
      label: `Stacked area showing the share of ${byPop ? "people" : "countries"} in ` +
             `${group.label} governed from the left, centre and right, ` +
             `${series[0].year} to ${series[series.length - 1].year}.`,
    });
  attachHover(s, shown.series, palette, { group, keys: shown.keys });
  drawLine(group.index);
  const provSeries = group.by_country.map((r) => ({ year: r.year, ...r.source }));
  const sProv = drawStack("#prov", provSeries, SOURCES, DATA.palette.sources,
    boxFor("#prov", 0.20, 130, 190),
    { label: "Which data source resolved each country-year, over time." });
  attachHover(sProv, provSeries, DATA.palette.sources, {
    svgId: "#prov", readoutId: "#prov-readout", keys: SOURCES,
  });
  drawSpectrum(group);
  drawMosaic(group);
  drawMap();
  if (!state.regime) state.regime = defaultRegime();
  buildRegimeTabs();
  drawRegime(group);

  const last = shown.series[shown.series.length - 1];
  const unit = byPop ? "of the world's people" : "of countries";
  $("#caption").textContent =
    `In ${last.year}, ${pct(last.left)} ${unit} lived under a government of the left and ` +
    `${pct(last.right)} under one of the right.`;
  writeHash();
}

/* ---------- boot ---------- */

Promise.all([
  window.__PENDULUM__ || fetch("orientation.json").then((r) => r.json()),
  window.__PENDULUM_MAP__ || fetch("map.json").then((r) => r.json()),
])
  .then(([data, mapData]) => {
    DATA = data;
    MAP = mapData;
    readHash();

    const select = $("#group");
    select.innerHTML = Object.entries(DATA.groups)
      .map(([k, g]) => `<option value="${k}">${g.label}</option>`).join("");
    select.value = state.group;
    select.addEventListener("change", () => { state.group = select.value; render(); });

    /* Scoped to [data-weight], not ".segmented button": that selector also
       matches the missing-data control and the regime tabs, so clicking either
       of those was setting state.weight to undefined. */
    for (const btn of document.querySelectorAll("[data-weight]")) {
      btn.setAttribute("aria-checked", String(btn.dataset.weight === state.weight));
      btn.addEventListener("click", () => {
        state.weight = btn.dataset.weight;
        for (const b of document.querySelectorAll("[data-weight]")) {
          b.setAttribute("aria-checked", String(b.dataset.weight === state.weight));
        }
        render();
      });
    }


    const excl = $("#exclude-missing");
    excl.checked = state.missing === "exclude";
    excl.addEventListener("change", () => {
      state.missing = excl.checked ? "exclude" : "include";
      render();
    });

    for (const btn of document.querySelectorAll(".play")) {
      btn.addEventListener("click", () => (playing() ? stopPlay() : startPlay()));
    }

    for (const [id, out] of [["#year", "#year-out"], ["#map-year", "#map-year-out"]]) {
      const el = $(id);
      el.addEventListener("input", () => {
        stopPlay();
        state.year = +el.value;
        syncYear();
        drawMosaic(DATA.groups[state.group]);
        drawMap();
        writeHash();
      });
    }

    if (state.year == null) state.year = latestYear();
    const slider = $("#year");
    const years = DATA.groups.world.cross.map((r) => r.year);
    slider.min = Math.min(...years);
    // regime data stops before the political series; the slider is capped from
    // the data rather than a hardcoded year
    slider.max = DATA.meta.regime_coverage_end;
    state.year = Math.min(Math.max(state.year, +slider.min), +slider.max);
    $("#map-year").min = DATA.map.year0;
    $("#map-year").max = DATA.map.year1;
    syncYear();

    $("#sources").innerHTML = DATA.meta.sources.map((s) =>
      `<li><a href="${s.url}" rel="noopener">${s.name}</a>. ${s.detail}</li>`).join("");
    document.body.classList.remove("loading");
    render();

    /* Charts are sized from the container, so they have to be redrawn when it
       changes. Width only: mobile browsers fire resize on every address-bar
       collapse, and redrawing six charts for that is wasted work. */
    // theme changes swap the greys, so the charts have to be redrawn
    darkMedia.addEventListener("change", render);

    let last = window.innerWidth;
    let timer = null;
    window.addEventListener("resize", () => {
      if (window.innerWidth === last) return;
      last = window.innerWidth;
      clearTimeout(timer);
      timer = setTimeout(render, 150);
    });
  })
  .catch((err) => {
    // Distinguish a failed fetch from a failed render: reporting "could not
    // load the data" when the data loaded fine sends the next person hunting
    // in the wrong place.
    $("#chart-title").textContent = DATA
      ? "The data loaded but the charts could not be drawn."
      : "Could not load the data.";
    document.body.classList.remove("loading");
    console.error(err);
  });
