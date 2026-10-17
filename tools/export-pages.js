const sketch = require('sketch');

module.exports = function (CFG) {
const DOC_ID = 'DEB2F9E8-966A-4E25-A6AF-6BAF189DD87E';
const doc = sketch.getDocuments().find(function (d) { return d.id === DOC_ID; });
const rows = [];
const errs = [];
doc.pages.forEach(function (p) {
  if (p.name.indexOf('-----') === 0 || p.name === 'Symbols') return;
  p.canvasLevelFrames.forEach(function (l) {
    rows.push([p.name, l.name, l.id]);
    if (CFG.png) {
      try {
        sketch.export(l, { formats: 'png', scales: '1', output: CFG.out, 'use-id-for-name': true, overwriting: true });
      } catch (e) {
        errs.push(l.name + ': ' + String(e));
      }
    }
  });
});
let txt = '@@' + JSON.stringify({ ok: true, n: rows.length, errs: errs, rows: rows }) + '@@';
while (txt.length < 120000) txt += 'x';
console.log(txt);
};
