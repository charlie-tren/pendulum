/* Pendulum — static frontend. No framework, no build step, no dependencies.
   Charts are hand-rolled SVG so this still runs in five years. */

const DEFAULTS = { group: "world", weight: "by_population" };
const BANDS = ["left", "centre", "right", "no_reading", "unresolved"];
const SOURCES = ["dpi", "vparty", "carry_forward", "hand", "wikidata", "no_reading", "unresolved"];
/* Below this share of the group resolved, a year is drawn as provisional.
   Movement in a thinly-covered year is usually the data changing, not the world. */
const PROVISIONAL_BELOW = 0.8;

const state = { ...DEFAULTS };
let DATA = null;

const $ = (sel) => document.querySelector(sel);
const svgEl = (name, attrs = {}) => {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
};
const pct = (v) => (v == null ? "—" : `${(v * 100).toFixed(v * 100 < 10 ? 1 : 0)}%`);

/* ---------- URL state. The default is never written to the URL. ---------- */

function readHash() {
  const params = new URLSearchParams(location.hash.slice(1));
  const group = params.get("group");
  const weight = params.get("weight");
  if (group && DATA.groups[group]) state.group = group;
  if (weight === "by_country" || weight === "by_population") state.weight = weight;
}

function writeHash() {
  const params = new URLSearchParams();
  for (const key of ["group", "weight"]) {
    if (state[key] !== DEFAULTS[key]) params.set(key, state[key]);
  }
  const hash = params.toString();
  history.replaceState(null, "", hash ? `#${hash}` : location.pathname + location.search);
}

/* ---------- chart geometry ---------- */

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

function axes(svg, s, { ticks = [0, 0.25, 0.5, 0.75, 1], fmt = pct, step = 10 } = {}) {
  for (const v of ticks) {
    svg.appendChild(svgEl("line", {
      x1: s.pad.l, x2: s.box.w - s.pad.r, y1: s.y(v), y2: s.y(v),
      stroke: "var(--rule)", "stroke-width": 1,
    }));
    const t = svgEl("text", {
      x: s.pad.l - 8, y: s.y(v) + 4, "text-anchor": "end",
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

function hatchDefs(svg) {
  const defs = svgEl("defs");
  const pattern = svgEl("pattern", {
    id: "provisional", width: 6, height: 6,
    patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)",
  });
  pattern.appendChild(svgEl("rect", { width: 6, height: 6, fill: "var(--panel)", opacity: 0.55 }));
  pattern.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: 6, stroke: "var(--panel)", "stroke-width": 3.5,
  }));
  defs.appendChild(pattern);
  svg.appendChild(defs);
}

/* ---------- stacked area ---------- */

function drawStack(svgId, series, keys, palette, box, { provisional = null } = {}) {
  const svg = $(svgId);
  svg.innerHTML = "";
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 44, r: 10, t: 10, b: 26 };
  const s = scales(series, box, pad);
  hatchDefs(svg);
  axes(svg, s, { ticks: [0, 0.5, 1] });

  let base = series.map(() => 0);
  for (const key of keys) {
    const top = series.map((r, i) => base[i] + (r[key] || 0));
    const pts = series.map((r, i) => `${s.x(r.year).toFixed(1)},${s.y(top[i]).toFixed(1)}`)
      .concat(series.map((r, i) => `${s.x(r.year).toFixed(1)},${s.y(base[i]).toFixed(1)}`).reverse());
    svg.appendChild(svgEl("polygon", { points: pts.join(" "), fill: palette[key].colour }));
    base = top;
  }

  if (provisional && provisional.length) {
    const from = s.x(provisional[0]) - (s.iw / (s.y1 - s.y0)) / 2;
    svg.appendChild(svgEl("rect", {
      x: from, y: pad.t, width: s.box.w - pad.r - from, height: s.ih,
      fill: "url(#provisional)",
    }));
    svg.appendChild(svgEl("line", {
      x1: from, x2: from, y1: pad.t, y2: pad.t + s.ih,
      stroke: "var(--ink-faint)", "stroke-width": 1, "stroke-dasharray": "3 3",
    }));
    const label = svgEl("text", {
      x: from + 6, y: pad.t + 14, "font-size": 11, fill: "var(--ink-faint)",
    });
    label.textContent = "provisional";
    svg.appendChild(label);
  }
  return s;
}

/* ---------- index line ---------- */

function drawLine(series) {
  const box = { w: 960, h: 240 };
  const svg = $("#line");
  svg.innerHTML = "";
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 44, r: 10, t: 12, b: 26 };
  const rows = series.filter((r) => r.mean_by_country != null || r.mean_by_population != null);
  const s = scales(rows, box, pad);
  const key = state.weight === "by_country" ? "mean_by_country" : "mean_by_population";
  const toUnit = (v) => (v + 1) / 2;

  axes(svg, s, {
    ticks: [0, 0.25, 0.5, 0.75, 1],
    fmt: (v) => { const n = v * 2 - 1; return n === 0 ? "0" : (n > 0 ? "+" : "") + n.toFixed(1); },
  });
  svg.appendChild(svgEl("line", {
    x1: pad.l, x2: box.w - pad.r, y1: s.y(0.5), y2: s.y(0.5),
    stroke: "var(--ink-faint)", "stroke-width": 1.2,
  }));

  const path = (field, stroke, width, opacity) => {
    const pts = rows.filter((r) => r[field] != null)
      .map((r) => `${s.x(r.year).toFixed(1)},${s.y(toUnit(r[field])).toFixed(1)}`);
    if (!pts.length) return;
    svg.appendChild(svgEl("polyline", {
      points: pts.join(" "), fill: "none", stroke,
      "stroke-width": width, "stroke-opacity": opacity,
      "stroke-linejoin": "round", "stroke-linecap": "round",
    }));
  };
  path(key, "var(--ink-faint)", 1.4, 0.55);
  path(`${key}_ma3`, "var(--ink)", 2.4, 1);

  for (const [v, text] of [[0.98, "right"], [0.02, "left"]]) {
    const t = svgEl("text", {
      x: box.w - pad.r - 2, y: s.y(v) + (v > 0.5 ? 11 : -3),
      "text-anchor": "end", "font-size": 11, fill: "var(--ink-faint)",
    });
    t.textContent = text;
    svg.appendChild(t);
  }
}

/* ---------- interaction ---------- */

function attachHover(s, series, palette, group) {
  const svg = $("#area");
  const readout = $("#readout");
  const marker = svgEl("line", {
    y1: s.pad.t, y2: s.pad.t + s.ih, stroke: "var(--ink)",
    "stroke-width": 1, "stroke-opacity": 0.35, visibility: "hidden",
  });
  svg.appendChild(marker);

  const counts = group.by_country;
  const show = (evt) => {
    const rect = svg.getBoundingClientRect();
    const px = ((evt.touches ? evt.touches[0].clientX : evt.clientX) - rect.left)
      / rect.width * s.box.w;
    const frac = (px - s.pad.l) / s.iw;
    const year = Math.round(s.y0 + frac * (s.y1 - s.y0));
    const row = series.find((r) => r.year === year);
    if (!row) return;
    marker.setAttribute("x1", s.x(year));
    marker.setAttribute("x2", s.x(year));
    marker.setAttribute("visibility", "visible");

    const countRow = counts.find((r) => r.year === year) || {};
    const src = Object.entries(countRow.source || {})
      .filter(([, v]) => v >= 0.02)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${DATA.palette.sources[k].label} ${Math.round(v * 100)}%`)
      .join(" · ");
    const rows = BANDS.filter((k) => (row[k] || 0) > 0.001).map((k) =>
      `<div class="row"><span><i style="background:${palette[k].colour}"></i>${palette[k].label}</span><span>${pct(row[k])}</span></div>`);
    readout.innerHTML = `<b>${year}</b>${rows.join("")}` +
      (state.weight === "by_population" && row.pop
        ? `<div class="prov">${(row.pop / 1e9).toFixed(2)}bn people</div>` : "") +
      (src ? `<div class="prov">${src}</div>` : "");
    readout.hidden = false;
  };
  const hide = () => { readout.hidden = true; marker.setAttribute("visibility", "hidden"); };
  svg.addEventListener("pointermove", show);
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("touchmove", show, { passive: true });
}

/* ---------- render ---------- */

function render() {
  const group = DATA.groups[state.group];
  const series = group[state.weight];
  const palette = DATA.palette.buckets;
  const byPop = state.weight === "by_population";

  $("#chart-title").textContent = byPop
    ? `${group.label} — share of people by how their country is governed`
    : `${group.label} — share of countries by government`;
  $("#group-hint").textContent = group.n_members
    ? `${group.n_members} countries` : "";

  $("#legend").innerHTML = BANDS.map((k) =>
    `<span><i style="background:${palette[k].colour}"></i>${palette[k].label}</span>`).join("");
  $("#legend-src").innerHTML = SOURCES.map((k) =>
    `<span><i style="background:${DATA.palette.sources[k].colour}"></i>${DATA.palette.sources[k].label}</span>`).join("");

  const shareKey = byPop ? "coded_share_pop" : "coded_share_countries";
  const thin = group.index.filter((r) => (r[shareKey] ?? 1) < PROVISIONAL_BELOW).map((r) => r.year);
  const runStart = thin.length ? Math.min(...thin.filter((y) => y > 2015)) : null;

  const s = drawStack("#area", series, BANDS, palette, { w: 960, h: 380 },
    { provisional: runStart ? [runStart] : null });
  attachHover(s, series, palette, group);
  drawLine(group.index);
  drawStack("#prov", group.by_country.map((r) => ({ year: r.year, ...r.source })),
    SOURCES, DATA.palette.sources, { w: 960, h: 200 });

  const latest = group.index[group.index.length - 1];
  const solid = [...group.index].reverse().find((r) => (r[shareKey] ?? 0) >= PROVISIONAL_BELOW);
  $("#caption").textContent = solid
    ? `Coverage is solid through ${solid.year}, when ${pct(solid[shareKey])} of ` +
      `${byPop ? "the people" : "the countries"} in this group could be placed on the ` +
      `left–right axis. By ${latest.year} that falls to ${pct(latest[shareKey])}, which is ` +
      `why later years are hatched.`
    : "Coverage in this group is too thin for the shares to be read confidently.";
  writeHash();
}

/* ---------- boot ---------- */

fetch("orientation.json")
  .then((r) => r.json())
  .then((data) => {
    DATA = data;
    readHash();

    const select = $("#group");
    select.innerHTML = Object.entries(DATA.groups)
      .map(([k, g]) => `<option value="${k}">${g.label}</option>`).join("");
    select.value = state.group;
    select.addEventListener("change", () => { state.group = select.value; render(); });

    for (const btn of document.querySelectorAll(".segmented button")) {
      btn.setAttribute("aria-checked", String(btn.dataset.weight === state.weight));
      btn.addEventListener("click", () => {
        state.weight = btn.dataset.weight;
        for (const b of document.querySelectorAll(".segmented button")) {
          b.setAttribute("aria-checked", String(b.dataset.weight === state.weight));
        }
        render();
      });
    }

    $("#sources").innerHTML = DATA.meta.sources.map((s) => `<li>${s}</li>`).join("");
    render();
  })
  .catch((err) => {
    $("#chart-title").textContent = "Could not load the data.";
    console.error(err);
  });
