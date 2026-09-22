/* html/assets/app.js
 *
 * Charts, navigation, and the table view for the monitoring plan page.
 * All numbers come from data/figures.js (window.FH_DATA), which is generated
 * by scripts/build_html_data.py. Nothing is hardcoded here.
 *
 * Chart colour rule: one series colour, one accent. EIP green never encodes a
 * data category against EIP orange, because the pair fails colour vision
 * separation. Every bar carries a direct value label, so colour is never the
 * only channel, and every figure has a table view underneath it.
 */
(function () {
  "use strict";

  var D = window.FH_DATA;
  if (!D) { console.error("figures.js did not load"); return; }

  // ---------------------------------------------------------------- theme

  function tokens() {
    var cs = getComputedStyle(document.documentElement);
    return {
      ink: cs.getPropertyValue("--ink").trim(),
      dim: cs.getPropertyValue("--ink-dim").trim(),
      series: cs.getPropertyValue("--series").trim(),
      soft: cs.getPropertyValue("--series-soft").trim(),
      accent: cs.getPropertyValue("--accent").trim(),
      grid: cs.getPropertyValue("--chart-grid").trim()
    };
  }

  function baseLayout(t, title) {
    return {
      font: { family: "Open Sans, system-ui, sans-serif", color: t.ink, size: 13 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      margin: { l: 52, r: 18, t: 46, b: 70 },
      showlegend: false,
      bargap: 0.34,
      title: { text: title, font: { size: 14, color: t.ink }, x: 0.02, xanchor: "left" },
      xaxis: { tickfont: { color: t.ink }, showgrid: false, zeroline: false, fixedrange: true },
      yaxis: { tickfont: { color: t.dim }, gridcolor: t.grid, zeroline: false, fixedrange: true }
    };
  }

  var CFG = { displayModeBar: false, responsive: true };

  // ---------------------------------------------------------------- table view

  function tableView(id, head, rows, label) {
    var host = document.getElementById(id);
    if (!host) { return; }
    var html = "<summary>" + (label || "Show the numbers") + "</summary><table><thead><tr>";
    head.forEach(function (h, i) {
      html += '<th' + (i ? ' class="num"' : "") + ">" + h + "</th>";
    });
    html += "</tr></thead><tbody>";
    rows.forEach(function (r) {
      html += "<tr>";
      r.forEach(function (c, i) {
        html += "<td" + (i ? ' class="num"' : "") + ">" + c + "</td>";
      });
      html += "</tr>";
    });
    host.innerHTML = html + "</tbody></table>";
  }

  // ---------------------------------------------------------------- charts

  function drawAll() {
    var t = tokens();
    var a = D.attainment;

    // 1. VP10 attainment. One measure across three types, so one colour; the
    //    standard is the only thing that earns the accent.
    Plotly.react("chartAttainment", [{
      type: "bar",
      x: a.types,
      y: a.pct,
      marker: { color: t.series, line: { width: 0 } },
      text: a.pct.map(function (v) { return v + "%"; }),
      textposition: "outside",
      textfont: { color: t.ink, size: 13 },
      hovertemplate: "%{x}<br>%{y}% of forest meets target<extra></extra>"
    }], Object.assign(baseLayout(t, "VP10 stand density: percent of forest meeting its target"), {
      yaxis: { tickfont: { color: t.dim }, gridcolor: t.grid, zeroline: false, fixedrange: true, range: [0, 72], ticksuffix: "%" },
      shapes: [{ type: "line", x0: -0.5, x1: 2.5, y0: a.standard_pct, y1: a.standard_pct, line: { color: t.accent, width: 1.5, dash: "dot" } }],
      annotations: [{ x: -0.45, y: a.standard_pct, xanchor: "left", yanchor: "bottom", text: a.standard_pct + " percent standard", showarrow: false, font: { size: 11, color: t.accent } }]
    }), CFG);

    // 2. Cells on the forested frame by cell size. Accent marks the two
    //    candidates that matter; the target line is the reporting requirement.
    var c = D.cells;
    Plotly.react("chartCells", [{
      type: "bar",
      x: c.label,
      y: c.n_cells,
      marker: {
        color: c.cell_ha.map(function (h) {
          return c.highlight_ha.indexOf(h) >= 0 ? t.accent : t.series;
        }),
        line: { width: 0 }
      },
      text: c.n_cells.map(String),
      textposition: "outside",
      textfont: { color: t.ink, size: 13 },
      hovertemplate: "%{x} ha cells<br>%{y} cells on the frame<extra></extra>"
    }], Object.assign(baseLayout(t, "Cells on the 115,396 acre forested frame, by cell size"), {
      xaxis: {
        type: "category", tickmode: "array",
        tickvals: c.label,
        ticktext: c.label.map(function (l, i) {
          if (c.cell_ha[i] === c.highlight_ha[1]) { return l + "<br>owl cell"; }
          if (c.cell_ha[i] === c.highlight_ha[0]) { return l + "<br>nested third"; }
          return l;
        }),
        tickfont: { color: t.ink }, showgrid: false, zeroline: false, fixedrange: true,
        title: { text: "cell size, hectares", font: { size: 11, color: t.dim } }
      },
      yaxis: { tickfont: { color: t.dim }, gridcolor: t.grid, zeroline: false, fixedrange: true, range: [0, 540] },
      shapes: [{ type: "line", x0: -0.5, x1: c.label.length - 0.5, y0: c.target, y1: c.target, line: { color: t.accent, width: 1.5, dash: "dot" } }],
      annotations: [
        { x: -0.45, y: c.target, xanchor: "left", yanchor: "bottom", text: c.target + " plots needed", showarrow: false, font: { size: 11, color: t.accent } }
      ]
    }), CFG);

    // 3. Pat's increments, in sites.
    var inc = D.increments;
    Plotly.react("chartIncrements", [{
      type: "bar",
      orientation: "h",
      x: inc.sites,
      y: inc.label,
      marker: {
        color: inc.label.map(function (_, i) { return i === inc.current ? t.accent : t.series; }),
        line: { width: 0 }
      },
      text: inc.sites.map(String),
      textposition: "outside",
      textfont: { color: t.ink, size: 13 },
      hovertemplate: "%{y}<br>%{x} sites<extra></extra>"
    }], Object.assign(baseLayout(t, "Sites in each TEON sampling increment, counted on the Basin grid"), {
      margin: { l: 205, r: 46, t: 46, b: 44 },
      xaxis: { tickfont: { color: t.dim }, gridcolor: t.grid, zeroline: false, fixedrange: true, range: [0, 320] },
      yaxis: { tickfont: { color: t.ink }, showgrid: false, zeroline: false, fixedrange: true, autorange: "reversed" }
    }), CFG);

    // 4. Plot size and LiDAR uncertainty.
    var p = D.plotsize;
    Plotly.react("chartSize", [{
      type: "bar",
      x: p.label,
      y: p.mg_ha,
      marker: {
        color: p.label.map(function (_, i) { return i === p.highlight ? t.accent : t.series; }),
        line: { width: 0 }
      },
      text: p.mg_ha.map(function (v) { return v.toFixed(1); }),
      textposition: "outside",
      textfont: { color: t.ink, size: 13 },
      hovertemplate: "%{x}<br>%{y} Mg per hectare<extra></extra>"
    }], Object.assign(baseLayout(t, "Uncertainty in LiDAR biomass estimates by plot size, Mg per hectare"), {
      yaxis: { tickfont: { color: t.dim }, gridcolor: t.grid, zeroline: false, fixedrange: true, range: [0, 22] },
      annotations: [{ x: p.label[p.highlight], y: p.mg_ha[p.highlight], yanchor: "bottom", yshift: 22, text: "our plot", showarrow: false, font: { size: 11, color: t.accent } }]
    }), CFG);

    // 5. Plots purchased by unit rate.
    var m = D.money;
    Plotly.react("chartMoney", [{
      type: "bar",
      x: m.label,
      y: m.plots,
      marker: {
        color: m.label.map(function (_, i) { return i === m.highlight ? t.accent : t.series; }),
        line: { width: 0 }
      },
      text: m.plots.map(String),
      textposition: "outside",
      textfont: { color: t.ink, size: 13 },
      hovertemplate: "%{x} per plot<br>%{y} new plots<extra></extra>"
    }], Object.assign(baseLayout(t, "New plots purchased, by per plot unit rate"), {
      yaxis: { tickfont: { color: t.dim }, gridcolor: t.grid, zeroline: false, fixedrange: true, range: [0, 190] }
    }), CFG);
  }

  // ---------------------------------------------------------------- fill text

  function fillSpans() {
    document.querySelectorAll("[data-fig]").forEach(function (el) {
      var path = el.getAttribute("data-fig").split(".");
      var v = D;
      path.forEach(function (k) { v = v == null ? v : v[k]; });
      if (v == null) { return; }
      if (typeof v === "number") {
        v = Number.isInteger(v) ? v.toLocaleString("en-US") : v.toLocaleString("en-US", { maximumFractionDigits: 2 });
      }
      el.textContent = v;
    });
  }

  function buildTables() {
    var a = D.attainment;
    tableView("dataAttainment", ["Forest type", "Percent meeting target"],
      a.types.map(function (x, i) { return [x, a.pct[i] + "%"]; }));

    var c = D.cells;
    tableView("dataCells", ["Cell size, ha", "Cells on the frame"],
      c.cell_ha.map(function (h, i) { return [h, c.n_cells[i]]; }));

    var inc = D.increments;
    tableView("dataIncrements", ["Increment", "Sites", "Cells occupied"],
      inc.label.map(function (x, i) { return [x, inc.sites[i], inc.cells[i]]; }));

    var p = D.plotsize;
    tableView("dataSize", ["Plot size", "Mg per hectare"],
      p.label.map(function (x, i) { return [x, p.mg_ha[i]]; }));

    var m = D.money;
    tableView("dataMoney", ["Unit rate", "New plots"],
      m.label.map(function (x, i) { return [x, m.plots[i]]; }));

    var b = D.binsize;   // absent once the display sweep is no longer produced by the repo
    if (b && b.cell_ha) {
      tableView("dataBinsize", ["Cell size, ha", "Display score"],
        b.cell_ha.map(function (h, i) { return [h, b.score[i].toFixed(3)]; }),
        "Show the display score sweep, and why it is uninformative here");
    }
  }

  // ---------------------------------------------------------------- nav

  function nav() {
    var slides = Array.prototype.slice.call(document.querySelectorAll(".slide"));
    var dots = document.getElementById("dots");
    slides.forEach(function (s, i) {
      var a = document.createElement("a");
      a.href = "#" + s.id;
      a.setAttribute("aria-label", "Section " + (i + 1) + ": " + (s.dataset.title || s.id));
      dots.appendChild(a);
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          var i = slides.indexOf(e.target);
          Array.prototype.forEach.call(dots.children, function (d, j) { d.classList.toggle("on", j === i); });
        }
      });
    }, { threshold: 0.55 });
    slides.forEach(function (s) { io.observe(s); });

    document.addEventListener("keydown", function (e) {
      if (e.target.closest("details, button, a")) { return; }
      var cur = slides.findIndex(function (s) {
        return s.getBoundingClientRect().top > -window.innerHeight * 0.5;
      });
      var n = cur;
      if (["ArrowDown", "ArrowRight", "PageDown", " "].indexOf(e.key) >= 0) { n = Math.min(slides.length - 1, cur + 1); }
      else if (["ArrowUp", "ArrowLeft", "PageUp"].indexOf(e.key) >= 0) { n = Math.max(0, cur - 1); }
      else { return; }
      e.preventDefault();
      slides[n].scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function themeToggle() {
    var btn = document.getElementById("themeToggle");
    function current() {
      return document.documentElement.dataset.theme ||
        (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    }
    function paint() { btn.textContent = current() === "dark" ? "Light" : "Dark"; }
    btn.addEventListener("click", function () {
      document.documentElement.dataset.theme = current() === "dark" ? "light" : "dark";
      paint();
      drawAll();
    });
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
      if (!document.documentElement.dataset.theme) { paint(); drawAll(); }
    });
    paint();
  }

  document.addEventListener("DOMContentLoaded", function () {
    fillSpans();
    buildTables();
    drawAll();
    nav();
    themeToggle();
  });
})();
