#!/usr/bin/env python3
"""Organise the raw output of the Sketch export scripts into the kit/ layout.

usage:
  build_kit.py master <batch.json> <stage-dir>   convert one export-symbols.js batch (JSON files only)
  build_kit.py finish <scratch-dir> <repo-dir> <label>   place PNGs, pages, index.json; remove stale files
  build_kit.py merge <scratch-dir> <repo-dir> <label>    add or replace only the exported masters and artboards

See README.md, "Regenerating the kit".
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitpath as K  # noqa: E402


def add_svg(n):
    if n['type'] == 'ShapePath':
        g = n.pop('geom', None)
        f = n['frame']
        rot = n.get('transform', {}).get('rotation', 0)
        t = n['shapeType']
        if t == 'Rectangle':
            co = n['style']['corners']
            n['svg'] = K.rect_path(f['x'], f['y'], f['w'], f['h'], co['radii'], co['smoothing'], co['style'] == 1, rot)
        elif t == 'Oval':
            n['svg'] = K.oval_path(f['x'], f['y'], f['w'], f['h'], rot)
        else:
            n['svg'] = K.custom_path(f['x'], f['y'], f['w'], f['h'], g['points'], g['closed'], rot)
    for c in n.get('children', []):
        add_svg(c)


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, separators=(',', ':'), ensure_ascii=False)


def cmd_master(batch, stage):
    d = json.load(open(batch))
    for m in d['masters']:
        add_svg(m)
        dump(os.path.join(stage, m['name'] + '.json'), m)
    print('converted', len(d['masters']), 'errors', d['errs'])


def sanitize(name):
    return name.replace(' / ', ' - ').replace('\u203a', '_').replace('/', '-')


def cmd_finish(scratch, repo, label):
    import glob
    import shutil
    masters = []
    for b in sorted(glob.glob(os.path.join(scratch, 'b[0-9]*.json'))):
        for m in json.load(open(b))['masters']:
            masters.append((m['name'], m['id']))
    masters.sort()
    names = [n for n, _ in masters]
    assert len(set(names)) == len(names), 'duplicate master names'
    kit = os.path.join(repo, 'kit')
    old = json.load(open(os.path.join(kit, 'index.json')))
    old_names = {s['name'] for s in old['symbols']}
    old_pages = {(p['page'], p['artboard']) for p in old['pages']}
    shutil.rmtree(os.path.join(kit, 'symbols'))
    shutil.rmtree(os.path.join(kit, 'pages'))
    symbols = []
    for name, mid in masters:
        rel = 'kit/symbols/' + name
        dst = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(scratch, 'stage', name + '.json'), dst + '.json')
        shutil.copy(os.path.join(scratch, 'png', mid + '@2x.png'), dst + '@2x.png')
        symbols.append({'name': name, 'id': mid, 'json': rel + '.json', 'png': rel + '@2x.png'})
    rows = json.load(open(os.path.join(scratch, 'pages.json')))['rows']
    pages = []
    for page, art, aid in rows:
        rel = 'kit/pages/%s/%s.png' % (page, sanitize(art))
        dst = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(scratch, 'pages', aid + '.png'), dst)
        pages.append({'page': page, 'artboard': art, 'png': rel})
    index = {'source': old['source'], 'exported': label, 'symbols': symbols, 'pages': pages, 'note': old['note']}
    with open(os.path.join(kit, 'index.json'), 'w', encoding='utf-8') as fh:
        json.dump(index, fh, indent=1, ensure_ascii=False)
    new_pages = {(p['page'], p['artboard']) for p in pages}
    print('masters', len(symbols), 'artboards', len(pages))
    print('added masters', len(set(names) - old_names), 'removed masters', len(old_names - set(names)))
    print('added artboards', len(new_pages - old_pages), 'removed artboards', len(old_pages - new_pages))


def cmd_merge(scratch, repo, label):
    """Add or replace only the masters and page artboards exported in scratch (see README, partial update)."""
    import glob
    import shutil
    kit = os.path.join(repo, 'kit')
    index = json.load(open(os.path.join(kit, 'index.json')))
    symbols = {s['name']: s for s in index['symbols']}
    for b in sorted(glob.glob(os.path.join(scratch, 'b[0-9]*.json'))):
        for m in json.load(open(b))['masters']:
            name, mid = m['name'], m['id']
            rel = 'kit/symbols/' + name
            dst = os.path.join(repo, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(scratch, 'stage', name + '.json'), dst + '.json')
            shutil.copy(os.path.join(scratch, 'png', mid + '@2x.png'), dst + '@2x.png')
            symbols[name] = {'name': name, 'id': mid, 'json': rel + '.json', 'png': rel + '@2x.png'}
    pages = {(p['page'], p['artboard']): p for p in index['pages']}
    for page, art, aid in json.load(open(os.path.join(scratch, 'pages.json')))['rows']:
        rel = 'kit/pages/%s/%s.png' % (page, sanitize(art))
        dst = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(scratch, 'pages', aid + '.png'), dst)
        pages[(page, art)] = {'page': page, 'artboard': art, 'png': rel}
    index['symbols'] = [symbols[k] for k in sorted(symbols)]
    index['pages'] = list(pages.values())
    index['exported'] = label
    with open(os.path.join(kit, 'index.json'), 'w', encoding='utf-8') as fh:
        json.dump(index, fh, indent=1, ensure_ascii=False)
    print('masters', len(index['symbols']), 'artboards', len(index['pages']))


if __name__ == '__main__':
    if sys.argv[1] == 'master':
        cmd_master(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'merge':
        cmd_merge(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == 'finish':
        cmd_finish(sys.argv[2], sys.argv[3], sys.argv[4])
