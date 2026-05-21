// ============================================================
// chart-canvas-helpers.js — Canvas utilities for animated sims.
// Counterpart to chart-helpers.js (which handles static SVG).
// Pure vanilla JS. No external dependencies. Inline-friendly.
// ============================================================

// ---------- HiDPI canvas setup ----------
// Returns { ctx, w, h } where w/h are logical CSS pixels.
// Call once on init; if the container resizes, call again.
//   const { ctx, w, h } = setupHiDPICanvas(canvas);
function setupHiDPICanvas(canvas, opts) {
  opts = opts || {};
  var dpr = window.devicePixelRatio || 1;
  var rect = canvas.getBoundingClientRect();
  var w = opts.width || rect.width || canvas.clientWidth || 600;
  var h = opts.height || rect.height || canvas.clientHeight || 300;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  var ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.imageSmoothingEnabled = true;
  return { ctx: ctx, w: w, h: h, dpr: dpr };
}

// ---------- Clear ----------
//   clearCanvasCtx(ctx, w, h);              // transparent
//   clearCanvasCtx(ctx, w, h, '#FAF9F7');   // filled
function clearCanvasCtx(ctx, w, h, bg) {
  if (bg) {
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);
  } else {
    ctx.clearRect(0, 0, w, h);
  }
}

// ---------- CSS variable resolver (reused if chart-helpers.js loaded) ----------
// Safe to call whether or not chart-helpers.js is present.
var _ccResolvedColors = {};
function resolveCSSColor(cssValue) {
  if (typeof resolveColor === 'function') return resolveColor(cssValue);
  if (!cssValue || cssValue.indexOf('var(') === -1) return cssValue;
  if (_ccResolvedColors[cssValue]) return _ccResolvedColors[cssValue];
  var m = cssValue.match(/var\(--([^,)]+)(?:,\s*([^)]+))?\)/);
  if (!m) return cssValue;
  var resolved = getComputedStyle(document.documentElement)
    .getPropertyValue('--' + m[1].trim()).trim();
  var result = resolved || (m[2] ? m[2].trim() : '#2D2D2D');
  _ccResolvedColors[cssValue] = result;
  return result;
}

// ---------- Draw primitives ----------
//   drawLineCanvas(ctx, [{x,y},...], { color, width, dashed });
function drawLineCanvas(ctx, points, opts) {
  if (!points || points.length < 2) return;
  opts = opts || {};
  ctx.save();
  ctx.strokeStyle = resolveCSSColor(opts.color || 'var(--text)');
  ctx.lineWidth = opts.width || 1.5;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  if (opts.dashed) ctx.setLineDash(Array.isArray(opts.dashed) ? opts.dashed : [4, 4]);
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (var i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
  ctx.stroke();
  ctx.restore();
}

//   drawPointCanvas(ctx, x, y, 4, 'var(--accent)');
function drawPointCanvas(ctx, x, y, r, color, strokeColor) {
  ctx.save();
  ctx.fillStyle = resolveCSSColor(color || 'var(--accent)');
  ctx.beginPath();
  ctx.arc(x, y, r || 3, 0, Math.PI * 2);
  ctx.fill();
  if (strokeColor) {
    ctx.strokeStyle = resolveCSSColor(strokeColor);
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }
  ctx.restore();
}

//   drawTextCanvas(ctx, 100, 50, 'Hello', { fontSize: 14, align: 'center' });
function drawTextCanvas(ctx, x, y, text, opts) {
  opts = opts || {};
  ctx.save();
  var size = opts.fontSize || 12;
  var family = opts.font || 'Figtree, system-ui, sans-serif';
  var weight = opts.weight || '400';
  ctx.font = weight + ' ' + size + 'px ' + family;
  ctx.fillStyle = resolveCSSColor(opts.color || 'var(--text)');
  ctx.textAlign = opts.align || 'center';
  ctx.textBaseline = opts.baseline || 'middle';
  ctx.fillText(text, x, y);
  ctx.restore();
}

//   drawRectCanvas(ctx, 10, 10, 80, 40, 'var(--accent)', 6);
function drawRectCanvas(ctx, x, y, w, h, fill, radius, stroke) {
  ctx.save();
  ctx.fillStyle = resolveCSSColor(fill || 'var(--accent)');
  if (radius && ctx.roundRect) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, radius);
    ctx.fill();
    if (stroke) {
      ctx.strokeStyle = resolveCSSColor(stroke);
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  } else {
    ctx.fillRect(x, y, w, h);
    if (stroke) {
      ctx.strokeStyle = resolveCSSColor(stroke);
      ctx.lineWidth = 1;
      ctx.strokeRect(x, y, w, h);
    }
  }
  ctx.restore();
}

// ---------- Axes (mirrors SVG drawAxes API where reasonable) ----------
//   drawAxesCanvas(ctx, w, h, { padding, xLabels, yMin, yMax, ySteps, yFmt });
function drawAxesCanvas(ctx, w, h, opts) {
  opts = opts || {};
  var pad = opts.padding || { top: 16, right: 16, bottom: 32, left: 44 };
  var axisColor = resolveCSSColor(opts.axisColor || 'var(--text-secondary)');
  var gridColor = resolveCSSColor(opts.gridColor || 'var(--border)');
  var labelColor = resolveCSSColor(opts.labelColor || 'var(--text-secondary)');

  ctx.save();
  // Baselines
  ctx.strokeStyle = axisColor;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad.left, pad.top);
  ctx.lineTo(pad.left, h - pad.bottom);
  ctx.lineTo(w - pad.right, h - pad.bottom);
  ctx.stroke();

  // Y gridlines + labels
  if (opts.yMin !== undefined && opts.yMax !== undefined) {
    var steps = opts.ySteps || 4;
    var plotH = h - pad.top - pad.bottom;
    var fmt = opts.yFmt || function(v) { return Number.isInteger(v) ? v.toString() : v.toFixed(1); };
    for (var i = 0; i <= steps; i++) {
      var val = opts.yMin + (opts.yMax - opts.yMin) * (i / steps);
      var yPos = h - pad.bottom - (i / steps) * plotH;
      ctx.strokeStyle = gridColor;
      ctx.setLineDash([3, 4]);
      ctx.beginPath();
      ctx.moveTo(pad.left, yPos);
      ctx.lineTo(w - pad.right, yPos);
      ctx.stroke();
      ctx.setLineDash([]);
      drawTextCanvas(ctx, pad.left - 8, yPos, fmt(val), {
        fontSize: 10, align: 'right', baseline: 'middle', color: labelColor
      });
    }
  }

  // X labels
  if (opts.xLabels && opts.xLabels.length) {
    var plotW = w - pad.left - pad.right;
    var maxLabels = Math.floor(plotW / 60);
    var step = Math.max(1, Math.ceil(opts.xLabels.length / maxLabels));
    for (var j = 0; j < opts.xLabels.length; j += step) {
      var xPos = pad.left + (j / (opts.xLabels.length - 1)) * plotW;
      drawTextCanvas(ctx, xPos, h - pad.bottom + 14, opts.xLabels[j], {
        fontSize: 10, align: 'center', baseline: 'middle', color: labelColor
      });
    }
  }
  ctx.restore();
  return pad;
}

// ---------- Coordinate helpers ----------
function mapX(val, vMin, vMax, w, pad) {
  pad = pad || { left: 44, right: 16, top: 16, bottom: 32 };
  if (vMax === vMin) return pad.left + (w - pad.left - pad.right) / 2;
  return pad.left + ((val - vMin) / (vMax - vMin)) * (w - pad.left - pad.right);
}

function mapY(val, vMin, vMax, h, pad) {
  pad = pad || { left: 44, right: 16, top: 16, bottom: 32 };
  if (vMax === vMin) return pad.top + (h - pad.top - pad.bottom) / 2;
  return h - pad.bottom - ((val - vMin) / (vMax - vMin)) * (h - pad.top - pad.bottom);
}

function mapRange(val, inMin, inMax, outMin, outMax) {
  if (inMax === inMin) return outMin;
  var t = (val - inMin) / (inMax - inMin);
  return outMin + t * (outMax - outMin);
}

function clamp(val, lo, hi) { return Math.max(lo, Math.min(hi, val)); }

// ---------- Easing + interpolation ----------
function lerp(a, b, t) { return a + (b - a) * t; }
function easeInOutCubic(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
function easeOutQuad(t) { return 1 - (1 - t) * (1 - t); }

// ---------- Animation loop ----------
// Returns { start, stop, running }. fn receives (elapsedMs, dtMs).
//   const a = animate(function(t, dt) { ...redraw... });
//   a.start();  // a.stop();
function animate(fn) {
  var raf = null;
  var startTime = 0;
  var lastTime = 0;
  var handle = { running: false };

  function tick(now) {
    if (!handle.running) return;
    if (!startTime) { startTime = now; lastTime = now; }
    var elapsed = now - startTime;
    var dt = now - lastTime;
    lastTime = now;
    fn(elapsed, dt);
    raf = requestAnimationFrame(tick);
  }
  handle.start = function() {
    if (handle.running) return;
    handle.running = true;
    startTime = 0;
    raf = requestAnimationFrame(tick);
  };
  handle.stop = function() {
    handle.running = false;
    if (raf) cancelAnimationFrame(raf);
    raf = null;
  };
  return handle;
}

// ---------- Slider binding ----------
// Wires <input type="range"> elements to a callback. Updates a label span
// on every change. Pass an array of { el, label, format(val) } descriptors.
//   attachSliders([
//     { el: document.getElementById('s1'), label: document.getElementById('s1-val'),
//       format: function(v){ return v.toFixed(2); } }
//   ], function(values){ /* values = { s1: 0.5 } */ redraw(); });
function attachSliders(descriptors, onChange) {
  function snapshot() {
    var out = {};
    descriptors.forEach(function(d) {
      var v = parseFloat(d.el.value);
      out[d.el.id || d.name] = v;
      if (d.label) d.label.textContent = d.format ? d.format(v) : v;
    });
    return out;
  }
  descriptors.forEach(function(d) {
    d.el.addEventListener('input', function() {
      onChange(snapshot());
    });
  });
  onChange(snapshot()); // initial paint
  return snapshot;
}

// ---------- Button binding ----------
//   attachButton('#play-btn', function(btn){ ... });
function attachButton(elOrSelector, onClick) {
  var el = typeof elOrSelector === 'string'
    ? document.querySelector(elOrSelector) : elOrSelector;
  if (!el) return;
  el.addEventListener('click', function(e) { onClick(el, e); });
  return el;
}

// ---------- Random utilities (for simulations) ----------
// Box-Muller normal sample. Mean 0, stddev 1 by default.
function randn(mean, stddev) {
  mean = mean || 0;
  stddev = stddev === undefined ? 1 : stddev;
  var u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  var z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  return mean + z * stddev;
}

// Simulate geometric Brownian motion path. Returns array of prices.
//   gbmPath({ S0: 100, mu: 0.07, sigma: 0.2, T: 1, steps: 252 });
function gbmPath(opts) {
  var S0 = opts.S0 || 100;
  var mu = opts.mu === undefined ? 0.07 : opts.mu;
  var sigma = opts.sigma === undefined ? 0.2 : opts.sigma;
  var T = opts.T || 1;
  var steps = opts.steps || 252;
  var dt = T / steps;
  var path = [S0];
  var s = S0;
  for (var i = 0; i < steps; i++) {
    var z = randn();
    s = s * Math.exp((mu - 0.5 * sigma * sigma) * dt + sigma * Math.sqrt(dt) * z);
    path.push(s);
  }
  return path;
}
