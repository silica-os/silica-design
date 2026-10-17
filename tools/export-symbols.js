const sketch = require('sketch');

module.exports = function (CFG) {
const START = CFG.start;
const COUNT = CFG.count;
const PNG = CFG.png;
const OUT = CFG.out;
const DOC_ID = 'DEB2F9E8-966A-4E25-A6AF-6BAF189DD87E';
const doc = sketch.getDocuments().find(function (d) { return d.id === DOC_ID; });
const page = doc.pages.find(function (p) { return p.name === 'Symbols'; });
const masters = page.layers.filter(function (l) { return l.type === 'SymbolMaster'; });
masters.sort(function (a, b) { return a.name < b.name ? -1 : (a.name > b.name ? 1 : 0); });
const textStyles = {};
doc.sharedTextStyles.forEach(function (s) { textStyles[s.id] = s.name; });
const layerStyles = {};
doc.sharedLayerStyles.forEach(function (s) { layerStyles[s.id] = s.name; });

function xy(p) { return { x: p.x, y: p.y }; }

function serFills(list) {
  return list.filter(function (f) { return f.enabled; }).map(function (f) {
    if (f.fillType === 'Gradient') {
      const g = f.gradient;
      return { gradient: { type: g.gradientType, from: xy(g.from), to: xy(g.to), stops: g.stops.map(function (s) { return [s.position, s.color]; }) } };
    }
    const o = { color: f.color };
    if (f.swatch) o.swatch = f.swatch.name;
    return o;
  });
}

function serBorders(list) {
  return list.filter(function (b) { return b.enabled; }).map(function (b) {
    const o = { color: b.color, thickness: b.thickness, position: b.position };
    if (b.swatch) o.swatch = b.swatch.name;
    return o;
  });
}

function serShadows(list) {
  return list.filter(function (s) { return s.enabled; }).map(function (s) {
    return { color: s.color, x: s.x, y: s.y, blur: s.blur, spread: s.spread };
  });
}

function serBlurs(list) {
  return list.filter(function (b) { return b.enabled; }).map(function (b) {
    return { type: b.blurType, radius: b.radius, saturation: b.saturation, brightness: b.brightness, distortion: b.distortion, depth: b.depth, chromaticAberration: b.chromaticAberration, specular: b.hasSpecularHighlights };
  });
}

function serStyle(st) {
  const c = st.corners || {};
  const bo = st.borderOptions;
  return {
    opacity: st.opacity,
    fills: serFills(st.fills),
    borders: serBorders(st.borders),
    shadows: serShadows(st.shadows),
    innerShadows: serShadows(st.innerShadows),
    blurs: serBlurs(st.blurs),
    corners: { radii: c.hasRadii ? c.radii : [], smoothing: c.smoothing, style: c.style },
    borderOptions: { dashPattern: bo.dashPattern, lineEnd: bo.lineEnd, lineJoin: bo.lineJoin, startArrowhead: bo.startArrowhead, endArrowhead: bo.endArrowhead }
  };
}

function serFrame(f) { return { x: f.x, y: f.y, w: f.width, h: f.height }; }

function serStack(sl) {
  const p = sl.padding;
  let pad = p;
  if (typeof p === 'object') {
    pad = (p.top === 0 && p.bottom === 0 && p.left === 0 && p.right === 0) ? 0 : { top: p.top, bottom: p.bottom, left: p.left, right: p.right };
  }
  return { direction: sl.direction, gap: sl.gap, padding: pad, align: sl.alignItems, justify: sl.justifyContent };
}

function hasStack(l) {
  return l.stackLayout && l.stackLayout.direction !== undefined && l.stackLayout.direction !== null && l.stackLayout.enabled !== false;
}

function serTransform(l) {
  const t = l.transform;
  if (!t) return null;
  if (!t.rotation && !t.flippedHorizontally && !t.flippedVertically) return null;
  return { rotation: t.rotation, flipH: t.flippedHorizontally, flipV: t.flippedVertically };
}

function serShape(l) {
  const o = { name: l.name, type: 'ShapePath', frame: serFrame(l.frame) };
  if (l.sharedStyleId && layerStyles[l.sharedStyleId]) o.sharedStyle = layerStyles[l.sharedStyleId];
  const t = serTransform(l);
  if (t) o.transform = t;
  o.style = serStyle(l.style);
  o.shapeType = l.shapeType;
  const g = { closed: l.closed };
  if (l.shapeType === 'Custom' || l.shapeType === 'Triangle' || l.shapeType === 'Polygon' || l.shapeType === 'Star') {
    g.points = l.points.map(function (p) { return { p: [p.point.x, p.point.y], f: [p.curveFrom.x, p.curveFrom.y], t: [p.curveTo.x, p.curveTo.y] }; });
  }
  o.geom = g;
  return o;
}

function serText(l) {
  const s = l.style;
  return {
    name: l.name, type: 'Text', frame: serFrame(l.frame),
    sharedStyle: l.sharedStyleId ? (textStyles[l.sharedStyleId] || null) : null,
    style: serStyle(s),
    text: l.text,
    font: { family: s.fontFamily, size: s.fontSize, weight: s.fontWeight, lineHeight: s.lineHeight, kerning: s.kerning, align: s.alignment, verticalAlign: s.verticalAlignment, color: s.textColor },
    fixedWidth: l.fixedWidth
  };
}

function serInstance(l) {
  const o = { name: l.name, type: 'SymbolInstance', frame: serFrame(l.frame) };
  const m = l.master;
  o.master = m ? m.name : null;
  let lib = null;
  try { lib = m ? m.getLibrary() : null; } catch (e) { lib = null; }
  if (lib) o.library = lib.name;
  o.overrides = l.overrides.filter(function (v) { return !v.isDefault; }).map(function (v) { return { path: v.path, property: v.property, value: String(v.value) }; });
  return o;
}

function serLayer(l) {
  if (l.type === 'ShapePath') return serShape(l);
  if (l.type === 'Text') return serText(l);
  if (l.type === 'SymbolInstance') return serInstance(l);
  if (l.type === 'Image') return { name: l.name, type: 'Image', frame: serFrame(l.frame), style: serStyle(l.style), image: true };
  if (l.type === 'Group' || l.type === 'Frame' || l.type === 'Graphic') {
    const o = { name: l.name, type: 'Group', frame: serFrame(l.frame) };
    const t = serTransform(l);
    if (t) o.transform = t;
    o.style = serStyle(l.style);
    if (hasStack(l)) o.stack = serStack(l.stackLayout);
    o.children = l.layers.map(serLayer).filter(function (c) { return c; });
    return o;
  }
  return null;
}

function serMaster(m) {
  const o = { id: m.id, symbolId: m.symbolId, name: m.name, type: 'SymbolMaster', frame: serFrame(m.frame), style: serStyle(m.style) };
  if (hasStack(m)) o.stack = serStack(m.stackLayout);
  o.children = m.layers.map(serLayer).filter(function (c) { return c; });
  return o;
}

const slice = masters.slice(START, START + COUNT);
const out = [];
const errs = [];
slice.forEach(function (m) {
  try {
    out.push(serMaster(m));
    if (PNG) sketch.export(m, { formats: 'png', scales: '2', output: OUT, 'use-id-for-name': true, overwriting: true });
  } catch (e) {
    errs.push(m.name + ': ' + String(e));
  }
});
let txt = '@@' + JSON.stringify({ ok: true, start: START, n: out.length, total: masters.length, errs: errs, masters: out }) + '@@';
while (txt.length < 120000) txt += 'x';
console.log(txt);
};
