// ============================================================
// chart-helpers.js — Shared SVG utility functions (vanilla JS)
// Embedded inline in each page. No external dependencies.
// ============================================================

var SVG_NS = 'http://www.w3.org/2000/svg';

// --- CSS variable resolution cache ---
// SVG attributes don't support CSS custom properties, so we resolve them once.
var _resolvedColors = {};
function resolveColor(cssValue) {
  if (!cssValue || cssValue.indexOf('var(') === -1) return cssValue;
  if (_resolvedColors[cssValue]) return _resolvedColors[cssValue];
  var match = cssValue.match(/var\(--([^,)]+)(?:,\s*([^)]+))?\)/);
  if (!match) return cssValue;
  var propName = '--' + match[1].trim();
  var fallback = match[2] ? match[2].trim() : '#2D2D2D';
  var resolved = getComputedStyle(document.documentElement).getPropertyValue(propName).trim();
  var result = resolved || fallback;
  _resolvedColors[cssValue] = result;
  return result;
}

// --- SVG namespace helper ---
function createSVGElement(tag) {
  return document.createElementNS(SVG_NS, tag);
}

// --- Drawing primitives ---

function drawLine(svg, x1, y1, x2, y2, color, width, dashArray) {
  var line = createSVGElement('line');
  line.setAttribute('x1', x1);
  line.setAttribute('y1', y1);
  line.setAttribute('x2', x2);
  line.setAttribute('y2', y2);
  line.setAttribute('stroke', resolveColor(color || 'var(--text)'));
  line.setAttribute('stroke-width', width || 1);
  if (dashArray) {
    line.setAttribute('stroke-dasharray', dashArray);
  }
  svg.appendChild(line);
  return line;
}

function drawPath(svg, d, color, width, fill, opacity) {
  var path = createSVGElement('path');
  path.setAttribute('d', d);
  path.setAttribute('stroke', color || 'none');
  path.setAttribute('stroke-width', width || 1);
  path.setAttribute('fill', fill || 'none');
  if (opacity !== undefined && opacity !== null) {
    path.setAttribute('opacity', opacity);
  }
  svg.appendChild(path);
  return path;
}

function buildPathD(points, svgWidth, svgHeight, padding) {
  if (!points || points.length === 0) return '';
  var pad = padding || { top: 20, right: 20, bottom: 40, left: 50 };
  var xs = points.map(function(p) { return p.x; });
  var ys = points.map(function(p) { return p.y; });
  var minX = Math.min.apply(null, xs);
  var maxX = Math.max.apply(null, xs);
  var minY = Math.min.apply(null, ys);
  var maxY = Math.max.apply(null, ys);

  var parts = [];
  for (var i = 0; i < points.length; i++) {
    var sx = scaleX(points[i].x, minX, maxX, svgWidth, pad);
    var sy = scaleY(points[i].y, minY, maxY, svgHeight, pad);
    parts.push((i === 0 ? 'M' : 'L') + sx.toFixed(2) + ',' + sy.toFixed(2));
  }
  return parts.join(' ');
}

function drawText(svg, x, y, text, opts) {
  opts = opts || {};
  var el = createSVGElement('text');
  el.setAttribute('x', x);
  el.setAttribute('y', y);
  el.textContent = text;
  el.setAttribute('font-size', opts.fontSize || 12);
  el.setAttribute('fill', resolveColor(opts.fill || 'var(--text)'));
  el.setAttribute('text-anchor', opts.anchor || 'middle');
  el.setAttribute('font-family', opts.fontFamily || 'inherit');
  if (opts.fontWeight) el.setAttribute('font-weight', opts.fontWeight);
  if (opts.dy) el.setAttribute('dy', opts.dy);
  if (opts.transform) el.setAttribute('transform', opts.transform);
  svg.appendChild(el);
  return el;
}

function drawRect(svg, x, y, w, h, fill, radius) {
  var rect = createSVGElement('rect');
  rect.setAttribute('x', x);
  rect.setAttribute('y', y);
  rect.setAttribute('width', w);
  rect.setAttribute('height', h);
  rect.setAttribute('fill', resolveColor(fill || 'var(--accent)'));
  if (radius) {
    rect.setAttribute('rx', radius);
    rect.setAttribute('ry', radius);
  }
  svg.appendChild(rect);
  return rect;
}

function drawCircle(svg, x, y, r, fill, stroke) {
  var circle = createSVGElement('circle');
  circle.setAttribute('cx', x);
  circle.setAttribute('cy', y);
  circle.setAttribute('r', r);
  circle.setAttribute('fill', resolveColor(fill || 'var(--accent)'));
  if (stroke) {
    circle.setAttribute('stroke', stroke);
    circle.setAttribute('stroke-width', 1.5);
  }
  svg.appendChild(circle);
  return circle;
}

// --- Axis helpers ---

function drawXAxis(svg, labels, svgWidth, svgHeight, padding) {
  var pad = padding || { top: 20, right: 20, bottom: 40, left: 50 };
  var plotW = svgWidth - pad.left - pad.right;
  var y = svgHeight - pad.bottom;

  // Axis baseline
  drawLine(svg, pad.left, y, svgWidth - pad.right, y, 'var(--text)', 1);

  if (!labels || labels.length === 0) return;

  // Determine how many labels to show to avoid overlap
  var maxLabels = Math.floor(plotW / 60);
  var step = Math.max(1, Math.ceil(labels.length / maxLabels));

  for (var i = 0; i < labels.length; i += step) {
    var x = pad.left + (i / (labels.length - 1)) * plotW;
    // Tick mark
    drawLine(svg, x, y, x, y + 5, 'var(--text)', 1);
    // Label
    drawText(svg, x, y + 18, labels[i], {
      fontSize: 10,
      fill: 'var(--text-secondary, var(--text))',
      anchor: 'middle'
    });
  }
}

function drawYAxis(svg, minVal, maxVal, steps, svgWidth, svgHeight, padding) {
  var pad = padding || { top: 20, right: 20, bottom: 40, left: 50 };
  var plotH = svgHeight - pad.top - pad.bottom;
  steps = steps || 5;

  // Axis baseline
  drawLine(svg, pad.left, pad.top, pad.left, svgHeight - pad.bottom, 'var(--text)', 1);

  var range = maxVal - minVal;
  for (var i = 0; i <= steps; i++) {
    var val = minVal + (range * i) / steps;
    var y = svgHeight - pad.bottom - (i / steps) * plotH;

    // Grid line
    drawLine(svg, pad.left, y, svgWidth - pad.right, y, 'var(--text)', 0.3, '4,4');

    // Label
    var label;
    if (Math.abs(val) >= 1e6) {
      label = (val / 1e6).toFixed(1) + 'M';
    } else if (Math.abs(val) >= 1e3) {
      label = (val / 1e3).toFixed(1) + 'K';
    } else if (Number.isInteger(val)) {
      label = val.toString();
    } else {
      label = val.toFixed(1);
    }
    drawText(svg, pad.left - 8, y, label, {
      fontSize: 10,
      fill: 'var(--text-secondary, var(--text))',
      anchor: 'end',
      dy: '0.35em'
    });
  }
}

// --- Data scaling ---

function scaleX(val, minVal, maxVal, svgWidth, padding) {
  var pad = padding || { top: 20, right: 20, bottom: 40, left: 50 };
  var plotW = svgWidth - pad.left - pad.right;
  if (maxVal === minVal) return pad.left + plotW / 2;
  return pad.left + ((val - minVal) / (maxVal - minVal)) * plotW;
}

function scaleY(val, minVal, maxVal, svgHeight, padding) {
  var pad = padding || { top: 20, right: 20, bottom: 40, left: 50 };
  var plotH = svgHeight - pad.top - pad.bottom;
  if (maxVal === minVal) return pad.top + plotH / 2;
  // Invert: higher values map to lower y (top of chart)
  return svgHeight - pad.bottom - ((val - minVal) / (maxVal - minVal)) * plotH;
}

// --- Tooltip helper ---

function createTooltip(container) {
  var tooltip = document.createElement('div');
  tooltip.style.cssText = [
    'position:absolute',
    'display:none',
    'background:#fff',
    'border:1px solid var(--border, #e5e5e0)',
    'color:var(--text, #2D2D2D)',
    'padding:6px 10px',
    'border-radius:6px',
    'font-size:12px',
    'pointer-events:none',
    'z-index:100',
    'white-space:nowrap',
    'box-shadow:0 2px 8px rgba(0,0,0,0.1)',
    'font-family:inherit'
  ].join(';');
  container.style.position = 'relative';
  container.appendChild(tooltip);
  return tooltip;
}

// --- Color helpers ---

function hexToRGBA(hex, alpha) {
  hex = hex.replace('#', '');
  if (hex.length === 3) {
    hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
  }
  var r = parseInt(hex.substring(0, 2), 16);
  var g = parseInt(hex.substring(2, 4), 16);
  var b = parseInt(hex.substring(4, 6), 16);
  return 'rgba(' + r + ',' + g + ',' + b + ',' + (alpha !== undefined ? alpha : 1) + ')';
}
