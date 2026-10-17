# silica-design

The **Silica 1.0 "Amalfi"** UI kit, exported for code: every component as a JSON layer tree plus a 2× PNG,
and every page of the kit (components laid out, app screens) as a PNG. It is the geometry reference for
`silica_ui`, the shell and the apps. The design rules, tokens, materials and motion live in
[`silica-desktop/docs/design/amalfi`](https://github.com/silica-os/silica-desktop/tree/main/docs/design/amalfi).

## Layout

```
kit/
  index.json                         every symbol (name, Sketch id, json, png) and every page artboard
  symbols/<Category>/<Component>/…/<Light|Dark>.json   layer tree of the symbol master
  symbols/<Category>/<Component>/…/<Light|Dark>@2x.png  the master rendered at 2×
  pages/<Page>/<Artboard>.png        each page artboard at 1× (component sheets, app screens)
```

Symbol names follow `Category/Component/Variant/Size/State/Appearance` (2817 Amalfi masters, Light and Dark; local copies of library glyphs and app icons are left out — take those from silica-icons).

## JSON format

Each file is one symbol master: `{ id, symbolId, name, type, frame, style, stack?, children[] }`.

- `frame`: `{x, y, w, h}` in pt, relative to the parent. 1 pt = 1 logical px.
- `style.fills[]`: `{color}` or `{gradient: {type, from, to, stops: [[position, color]]}}`, with `swatch`
  = the token name (`Light/Surface/Raised` …) when the colour comes from a token. Colours are `#rrggbbaa`.
- `style.borders[]`: `{color, thickness, position: Inside|Center|Outside, swatch}`.
- `style.shadows[]`, `style.innerShadows[]`: `{color, x, y, blur, spread}`.
- `style.blurs[]`: `{type: Background|Glass, radius, saturation, brightness, distortion, depth,
  chromaticAberration, specular}`. Background radius uses CSS `blur()` semantics (σ = radius).
- `style.borderOptions`: `{dashPattern, lineEnd, lineJoin, startArrowhead, endArrowhead}` on every layer (`dashPattern: []` when solid).
- `style.corners`: `{radii[], smoothing, style}`; smoothing 0.6 = Amalfi smooth (continuous) corners.
- `sharedStyle`: the shared layer or text style name (`Light/Glass/Thick`, `Light/Body/Primary` …).
- Text: `text`, `font {family, size, weight, lineHeight, kerning, align, verticalAlign, color}`.
  `weight` is Sketch's 0–12 scale: 5 Regular, 6 Medium, 8 Semibold, 9 Bold.
- `ShapePath`: `shapeType` and `svg` (path in the layer's own frame).
- `SymbolInstance`: `master` (the nested symbol's name, its own file in `kit/symbols`), `library`
  (`Silica 1.0 Amalfi Icon Kit` for glyphs, `app-icons` for icons), `overrides[]`.
- `stack`: Sketch stack layout (`direction` 0 horizontal / 1 vertical, `gap`, `padding`, `align`, `justify`).
- `clipsContent`: the group clips its children.

## Rules

- The kit is regenerated from the Sketch source; do not edit these files by hand.
- Text in the PNGs is rasterised by Sketch: compare geometry from the JSON exactly, pixels with a tolerance.

## Regenerating the kit

The scripts live in `tools/`. They need Sketch with the MCP server enabled (Settings, General, Allow AI tools to
interact with open documents) and the document "Silica 1.0 Amalfi UI Kit" open; they only read and export, nothing is
saved in the document. Never open another kit in the same session.

1. Pick an empty scratch folder `$S` with the sub-folders `png` and `pages`.
2. Masters, in batches of about 500 (one `run_code` call each; `start` is the offset in the name-sorted master list,
   2817 at the time of writing). The script returns the JSON layer trees and writes the 2x PNGs, named by id, to `png`:
   ```js
   const sketch = require('sketch');
   const fn = require('/path/to/silica-design/tools/export-symbols.js');
   fn({ start: 0, count: 500, png: true, out: '/path/to/S/png' });
   ```
   The output is padded past the size limit on purpose, so Claude Code saves it to a file instead of printing it.
   After each call run `tools/ingest.sh $S b<start>`: it takes the newest saved `run_code` result, stores it as
   `$S/b<start>.json` and converts the masters into `$S/stage/` (it adds the `svg` path of every shape, see
   `tools/kitpath.py`).
3. Page artboards, in one call (1x PNGs by id into `pages`, separator pages and the Symbols page skipped):
   ```js
   const sketch = require('sketch');
   const fn = require('/path/to/silica-design/tools/export-pages.js');
   fn({ png: true, out: '/path/to/S/pages' });
   ```
   Save the saved result with `python3 tools/grab.py <result-file> $S/pages.json`.
4. `python3 tools/build_kit.py finish $S . '<date> (<label>)'` rewrites `kit/symbols`, `kit/pages` and
   `kit/index.json` (masters and artboards that no longer exist disappear, new ones appear) and prints the counts.
5. Optional format check: `python3 tools/diff_format.py $S/stage kit/symbols` (run it before step 4) lists, per file,
   the keys and values that differ from the committed export; only real design changes should show up.

Partial update (a few new or changed masters and artboards): pass `names` (exact master names) to `export-symbols.js`
and `only` (`'<Page>|<Artboard>'` strings) to `export-pages.js`, ingest as above (`ingest.sh $S b0`, `grab.py` for the
pages), then run `python3 tools/build_kit.py merge $S . '<label>'` instead of `finish`: it adds or replaces only those
files and keeps everything else.

Notes: the bridge doubles backslashes in saved results (`grab.py` undoes it); the `svg` paths are computed in
`kitpath.py` (Sketch continuous corners, as in figma-squircle) because Sketch's own SVG export insets paths for inside
borders.

## Licence

[CC BY-SA 4.0](LICENSE), like `silica-icons`. App, file and folder icons inside the PNGs come from
[`silica-icons`](https://github.com/silica-os/silica-icons) under the same licence.
