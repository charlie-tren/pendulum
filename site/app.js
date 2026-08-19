/* Pendulum: static frontend. No framework, no build step, no dependencies.
   Charts are hand-rolled SVG so this still runs in five years. */

const DEFAULTS = { group: "world", weight: "by_population", year: 2023, country: null };
const BANDS = ["left", "centre", "right", "no_reading", "unresolved"];
const SOURCES = ["dpi", "vparty", "carry_forward", "hand", "wikidata", "no_reading", "unresolved"];
const REGIME_ORDER = ["closed_autocracy", "electoral_autocracy",
                      "electoral_democracy", "liberal_democracy", "unknown"];
/* Below this share of the group resolved, a year is drawn as provisional.
   Movement in a thinly-covered year is usually the data changing, not the world. */
const PROVISIONAL_BELOW = 0.8;

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

/* ---------- URL state. The default is never written to the URL. ---------- */

function readHash() {
  const params = new URLSearchParams(location.hash.slice(1));
  const group = params.get("group");
  const weight = params.get("weight");
  const year = parseInt(params.get("year"), 10);
  if (group && DATA.groups[group]) state.group = group;
  if (weight === "by_country" || weight === "by_population") state.weight = weight;
  if (Number.isInteger(year)) state.year = year;
  const country = params.get("country");
  if (country && DATA.countries.some((c) => c.entity === country)) state.country = country;
}

function writeHash() {
  const params = new URLSearchParams();
  for (const key of ["group", "weight", "year", "country"]) {
    if (key === "country" && state.country === defaultCountry(state.group)) continue;
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

function drawStack(svgId, series, keys, palette, box, { provisional = null, label = "" } = {}) {
  const svg = $(svgId);
  svg.innerHTML = "";
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 44, r: 10, t: 10, b: 26 };
  const s = scales(series, box, pad);
  hatchDefs(svg);
  axes(svg, s);

  let base = series.map(() => 0);
  for (const key of keys) {
    const top = series.map((r, i) => base[i] + (r[key] || 0));
    const pts = series.map((r, i) => `${s.x(r.year).toFixed(1)},${s.y(top[i]).toFixed(1)}`)
      .concat(series.map((r, i) => `${s.x(r.year).toFixed(1)},${s.y(base[i]).toFixed(1)}`).reverse());
    svg.appendChild(svgEl("polygon", { points: pts.join(" "), fill: palette[key].colour }));
    base = top;
  }

  if (provisional) {
    const from = s.x(provisional) - (s.iw / (s.y1 - s.y0)) / 2;
    svg.appendChild(svgEl("rect", {
      x: from, y: pad.t, width: s.box.w - pad.r - from, height: s.ih, fill: "url(#provisional)",
    }));
    svg.appendChild(svgEl("line", {
      x1: from, x2: from, y1: pad.t, y2: pad.t + s.ih,
      stroke: "var(--ink-faint)", "stroke-width": 1, "stroke-dasharray": "3 3",
    }));
    /* Left-aligning this ran the word off the plot and it rendered as
       "provision". Right-align it inside the hatched region, or outside to the
       left when the region is too narrow to hold it. */
    const LABEL_W = 58;
    const right = s.box.w - pad.r;
    const roomInside = right - from > LABEL_W + 10;
    const flag = svgEl("text", {
      x: (roomInside ? right - 6 : from - 6), y: pad.t + 14,
      "text-anchor": "end", "font-size": 11, fill: "var(--ink-faint)",
    });
    flag.textContent = "provisional";
    svg.appendChild(flag);
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
  describe(svg, "Line chart of mean government position, minus one for wholly left " +
                "to plus one for wholly right, with a three-year trailing average.");

  for (const [v, text] of [[0.98, "right"], [0.02, "left"]]) {
    const t = svgEl("text", {
      x: box.w - pad.r - 2, y: s.y(v) + (v > 0.5 ? 11 : -3),
      "text-anchor": "end", "font-size": 11, fill: "var(--ink-faint)",
    });
    t.textContent = text;
    svg.appendChild(t);
  }
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

  const cols = REGIME_ORDER
    .map((regime) => ({ regime, cells: row.cells[regime] || {} }))
    .map((col) => ({ ...col, total: sum(col.cells) }))
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
        fill: DATA.palette.buckets[band].colour, class: "mosaic-cell",
      });
      const n = (row.counts[col.regime] || {})[band] || 0;
      rect.addEventListener("pointerenter", () => {
        readout.innerHTML =
          `<b>${pct(v)} of people</b>` +
          `<div class="row"><span><i style="background:${DATA.palette.buckets[band].colour}"></i>` +
          `${DATA.palette.buckets[band].label}</span></div>` +
          `<div class="row"><span>${DATA.palette.regimes[col.regime].label}</span></div>` +
          `<div class="prov">${Math.round(v * row.pop / 1e6)}m people · ` +
          `${n} ${n === 1 ? "country" : "countries"} · ${row.year}</div>`;
        readout.hidden = false;
      });
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
    [DATA.palette.regimes[col.regime].short, pct(col.total)].forEach((text, i) => {
      const t = svgEl("text", {
        x: (x + w / 2).toFixed(1), y: (pad.t + ih + 19 + i * 15).toFixed(1),
        "text-anchor": "middle", "font-size": 12.5,
        fill: i ? "var(--ink-faint)" : "var(--ink-soft)", "font-weight": i ? 400 : 600,
      });
      t.textContent = text;
      svg.appendChild(t);
    });
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
    ? `The largest single group in ${row.year} is ` +
      `${DATA.palette.buckets[top.band].label.toLowerCase()}-governed ` +
      `${DATA.palette.regimes[top.regime].short.toLowerCase()}, at ${pct(top.v)} of ` +
      `this group's population.`
    : "";
}

/* ---------- small multiples, one panel per regime ---------- */

function drawMultiples(group) {
  const svg = $("#multiples");
  svg.innerHTML = "";
  const series = group.cross || [];
  if (!series.length) return;

  const panels = REGIME_ORDER.filter((r) => r !== "unknown");
  const probe = boxFor("#multiples", 0.27, 180, 260);
  // four panels side by side become 72px wide on a phone, which is unreadable;
  // below this width they wrap to a 2x2 grid instead
  const cols = probe.w < 560 ? 2 : 4;
  const rows = panels.length / cols;
  const box = { w: probe.w, h: rows === 1 ? probe.h : Math.round(probe.h * 1.55) };
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 4, r: 4, t: 24, b: 26 };
  const gap = 16;
  const rowGap = 30;
  const pw = (box.w - pad.l - pad.r - gap * (cols - 1)) / cols;
  const ih = (box.h - pad.t - pad.b - rowGap * (rows - 1)) / rows;
  const years = series.map((r) => r.year);
  const [y0, y1] = [Math.min(...years), Math.max(...years)];
  const ymax = Math.max(...series.flatMap((r) => panels.map((p) => sum(r.cells[p]))), 0.05);

  panels.forEach((regime, i) => {
    const ox = pad.l + (i % cols) * (pw + gap);
    const oy = pad.t + Math.floor(i / cols) * (ih + rowGap);
    const sx = (yr) => ox + ((yr - y0) / (y1 - y0)) * pw;
    const sy = (v) => oy + ih - (v / ymax) * ih;

    let base = series.map(() => 0);
    for (const band of BANDS) {
      const top = series.map((r, j) => base[j] + ((r.cells[regime] || {})[band] || 0));
      const pts = series.map((r, j) => `${sx(r.year).toFixed(1)},${sy(top[j]).toFixed(1)}`)
        .concat(series.map((r, j) => `${sx(r.year).toFixed(1)},${sy(base[j]).toFixed(1)}`).reverse());
      svg.appendChild(svgEl("polygon", {
        points: pts.join(" "), fill: DATA.palette.buckets[band].colour,
      }));
      base = top;
    }
    svg.appendChild(svgEl("line", {
      x1: ox, x2: ox + pw, y1: oy + ih, y2: oy + ih,
      stroke: "var(--rule)", "stroke-width": 1,
    }));
    const title = svgEl("text", {
      x: ox, y: oy - 9, "font-size": 12.5, fill: "var(--ink-soft)", "font-weight": 600,
    });
    title.textContent = DATA.palette.regimes[regime].short;
    svg.appendChild(title);
    for (const yr of [y0, y1]) {
      const t = svgEl("text", {
        x: sx(yr), y: oy + ih + 15, "font-size": 11, fill: "var(--ink-faint)",
        "text-anchor": yr === y0 ? "start" : "end",
      });
      t.textContent = yr;
      svg.appendChild(t);
    }
  });
  describe(svg, `Ideology composition within each regime type, ${y0} to ${y1}, ` +
                `as a share of the whole group.`);
}

/* ---------- one country, as a strip of years ---------- */

/* The largest country in the selected group, so switching to the G7 lands on
   the United States rather than stranding the panel on a country not in it. */
function defaultCountry(groupKey) {
  const members = new Set(DATA.members[groupKey] || []);
  const pool = DATA.countries.filter((c) => members.has(c.entity));
  const best = (pool.length ? pool : DATA.countries)
    .reduce((a, b) => (b.pop > a.pop ? b : a), { pop: -1, entity: null });
  return best.entity;
}

function populateCountries(group) {
  const members = new Set(DATA.members[state.group] || []);
  const pool = DATA.countries.filter((c) => members.has(c.entity));
  const list = (pool.length ? pool : DATA.countries).slice()
    .sort((a, b) => a.entity.localeCompare(b.entity));
  const select = $("#country");
  select.innerHTML = list.map((c) => `<option value="${c.entity}">${c.entity}</option>`).join("");
  if (!list.some((c) => c.entity === state.country)) state.country = defaultCountry(state.group);
  select.value = state.country;
}

function drawCountry() {
  const svg = $("#strip");
  const readout = $("#strip-readout");
  svg.innerHTML = "";
  readout.hidden = true;
  const rec = DATA.countries.find((c) => c.entity === state.country);
  if (!rec) return;

  const box = boxFor("#strip", 0.14, 108, 140);
  svg.setAttribute("viewBox", `0 0 ${box.w} ${box.h}`);
  const pad = { l: 4, r: 4, t: 8, b: 28 };
  const iw = box.w - pad.l - pad.r;
  const [y0, y1] = [1975, DATA.groups.world.by_country.slice(-1)[0].year];
  const cw = iw / (y1 - y0 + 1);
  const barH = 56;
  const srcH = 9;

  for (const run of rec.runs) {
    const x = pad.l + (run.y0 - y0) * cw;
    const w = (run.y1 - run.y0 + 1) * cw;
    const bucket = DATA.palette.buckets[run.b];
    const rect = svgEl("rect", {
      x: x.toFixed(1), y: pad.t, width: Math.max(w - 0.6, 0.6).toFixed(1), height: barH,
      fill: bucket.colour, class: "mosaic-cell",
    });
    rect.addEventListener("pointerenter", () => {
      const span = run.y0 === run.y1 ? `${run.y0}` : `${run.y0}–${run.y1}`;
      readout.innerHTML =
        `<b>${span}</b>` +
        `<div class="row"><span><i style="background:${bucket.colour}"></i>${bucket.label}</span></div>` +
        (run.p ? `<div class="row"><span>${run.p}</span></div>` : "") +
        `<div class="prov">${DATA.palette.regimes[run.r].label}<br>` +
        `via ${DATA.palette.sources[run.s].label}</div>`;
      readout.hidden = false;
    });
    svg.appendChild(rect);

    svg.appendChild(svgEl("rect", {
      x: x.toFixed(1), y: pad.t + barH + 5, width: Math.max(w - 0.6, 0.6).toFixed(1),
      height: srcH, fill: DATA.palette.sources[run.s].colour, opacity: 0.9,
    }));

    if (w > 46) {
      const t = svgEl("text", {
        x: (x + 5).toFixed(1), y: pad.t + 18, "font-size": 11.5, "font-weight": 600,
        fill: run.b === "no_reading" || run.b === "unresolved" ? "var(--ink-soft)" : "#fff",
      });
      t.textContent = run.p ? run.p.slice(0, Math.floor(w / 7)) : "";
      svg.appendChild(t);
    }
  }
  svg.onpointerleave = () => { readout.hidden = true; };

  for (let yr = 1980; yr <= y1; yr += 10) {
    const t = svgEl("text", {
      x: (pad.l + (yr - y0) * cw).toFixed(1), y: box.h - 8, "font-size": 11,
      fill: "var(--ink-faint)", "text-anchor": "middle",
    });
    t.textContent = yr;
    svg.appendChild(t);
  }

  describe(svg, `${state.country}, every year from 1975 to ${y1}, coloured by the ` +
                `political direction of its government.`);

  const flips = rec.runs.filter((r, i) =>
    i > 0 && ["left", "centre", "right"].includes(r.b) &&
    ["left", "centre", "right"].includes(rec.runs[i - 1].b) && r.b !== rec.runs[i - 1].b).length;
  $("#strip-caption").textContent =
    `${state.country} changed the political direction of its government ` +
    `${flips} ${flips === 1 ? "time" : "times"} between 1975 and ${y1}.`;
}

/* ---------- hover on the headline chart ---------- */

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
    const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
    const px = ((clientX - rect.left) / rect.width) * s.box.w;
    const year = Math.round(s.y0 + ((px - s.pad.l) / s.iw) * (s.y1 - s.y0));
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
      `<div class="row"><span><i style="background:${palette[k].colour}"></i>` +
      `${palette[k].label}</span><span>${pct(row[k])}</span></div>`);
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
    ? `${group.label}: share of people by how their country is governed`
    : `${group.label}: share of countries by government`;
  $("#group-hint").textContent = group.n_members ? `${group.n_members} countries` : "";

  $("#legend").innerHTML = BANDS.map((k) =>
    `<span><i style="background:${palette[k].colour}"></i>${palette[k].label}</span>`).join("");
  $("#legend-mosaic").innerHTML = $("#legend-strip").innerHTML = $("#legend").innerHTML;
  $("#legend-src").innerHTML = SOURCES.map((k) =>
    `<span><i style="background:${DATA.palette.sources[k].colour}"></i>` +
    `${DATA.palette.sources[k].label}</span>`).join("");

  const shareKey = byPop ? "coded_share_pop" : "coded_share_countries";
  const thin = group.index.filter((r) => (r[shareKey] ?? 1) < PROVISIONAL_BELOW && r.year > 2015);
  const runStart = thin.length ? Math.min(...thin.map((r) => r.year)) : null;

  const s = drawStack("#area", series, BANDS, palette,
    boxFor("#area", 0.42, 230, 380), {
      provisional: runStart,
      label: `Stacked area showing the share of ${byPop ? "people" : "countries"} in ` +
             `${group.label} governed from the left, centre and right, ` +
             `${series[0].year} to ${series[series.length - 1].year}.`,
    });
  attachHover(s, series, palette, group);
  drawLine(group.index);
  drawStack("#prov", group.by_country.map((r) => ({ year: r.year, ...r.source })),
    SOURCES, DATA.palette.sources, boxFor("#prov", 0.20, 130, 190),
    { label: "Which data source resolved each country-year, over time." });
  drawMosaic(group);
  drawMultiples(group);
  populateCountries(group);
  drawCountry();

  const latest = group.index[group.index.length - 1];
  const solid = [...group.index].reverse().find((r) => (r[shareKey] ?? 0) >= PROVISIONAL_BELOW);
  $("#caption").textContent = solid
    ? `Coverage is solid through ${solid.year}, when ${pct(solid[shareKey])} of ` +
      `${byPop ? "the people" : "the countries"} in this group could be placed on the ` +
      `left–right axis. By ${latest.year} that falls to ${pct(latest[shareKey])}, ` +
      `which is why later years are hatched.`
    : "Coverage in this group is too thin for the shares to be read confidently.";
  writeHash();
}

/* ---------- boot ---------- */

Promise.resolve(
  window.__PENDULUM__ || fetch("orientation.json").then((r) => r.json())
)
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

    state.country = state.country || defaultCountry(state.group);
    $("#country").addEventListener("change", (e) => {
      state.country = e.target.value;
      drawCountry();
      writeHash();
    });

    const slider = $("#year");
    const years = DATA.groups.world.cross.map((r) => r.year);
    slider.min = Math.min(...years);
    // regime data stops before the political series; the slider is capped from
    // the data rather than a hardcoded year
    slider.max = DATA.meta.regime_coverage_end;
    state.year = Math.min(Math.max(state.year, +slider.min), +slider.max);
    slider.value = state.year;
    $("#year-out").textContent = state.year;
    slider.addEventListener("input", () => {
      state.year = +slider.value;
      $("#year-out").textContent = state.year;
      drawMosaic(DATA.groups[state.group]);
      writeHash();
    });

    $("#sources").innerHTML = DATA.meta.sources.map((s) => `<li>${s}</li>`).join("");
    document.body.classList.remove("loading");
    render();

    /* Charts are sized from the container, so they have to be redrawn when it
       changes. Width only: mobile browsers fire resize on every address-bar
       collapse, and redrawing six charts for that is wasted work. */
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
    $("#chart-title").textContent = "Could not load the data.";
    console.error(err);
  });
