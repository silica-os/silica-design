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

Symbol names follow `Category/Component/Variant/Size/State/Appearance` (3015 masters, Light and Dark).

## JSON format

Each file is one symbol master: `{ id, symbolId, name, type, frame, style, stack?, children[] }`.

- `frame`: `{x, y, w, h}` in pt, relative to the parent. 1 pt = 1 logical px.
- `style.fills[]`: `{color}` or `{gradient: {type, from, to, stops: [[position, color]]}}`, with `swatch`
  = the token name (`Light/Surface/Raised` …) when the colour comes from a token. Colours are `#rrggbbaa`.
- `style.borders[]`: `{color, thickness, position: Inside|Center|Outside, swatch}`.
- `style.shadows[]`, `style.innerShadows[]`: `{color, x, y, blur, spread}`.
- `style.blurs[]`: `{type: Background|Glass, radius, saturation, brightness, distortion, depth,
  chromaticAberration, specular}`. Background radius uses CSS `blur()` semantics (σ = radius).
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

## Licence

[CC BY-SA 4.0](LICENSE), like `silica-icons`. App, file and folder icons inside the PNGs come from
[`silica-icons`](https://github.com/silica-os/silica-icons) under the same licence.
