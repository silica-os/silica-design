#!/usr/bin/env python3
"""Compare freshly converted masters with the committed ones: schema and values.

usage: diff_format.py <stage-dir> <kit/symbols dir> [max-lines]
"""
import json
import os
import sys


def cmp(a, b, path, out):
    if type(a) != type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        out.append((path, 'type', repr(a)[:60], repr(b)[:60]))
    elif isinstance(a, dict):
        if list(a.keys()) != list(b.keys()):
            out.append((path, 'keys', list(a.keys()), list(b.keys())))
        for k in a:
            if k in b:
                cmp(a[k], b[k], path + '/' + k, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((path, 'len', len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            cmp(x, y, path + '[%d]' % i, out)
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        if abs(a - b) > 1e-6 * max(1, abs(b)):
            out.append((path, 'val', a, b))
    elif a != b:
        out.append((path, 'val', repr(a)[:80], repr(b)[:80]))


if __name__ == '__main__':
    stage, old = sys.argv[1], sys.argv[2]
    mx = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    tot = same = 0
    shown = 0
    for r, _, fs in os.walk(stage):
        for f in sorted(fs):
            if not f.endswith('.json'):
                continue
            rel = os.path.relpath(os.path.join(r, f), stage)
            o = os.path.join(old, rel)
            if not os.path.exists(o):
                print('NEW', rel)
                continue
            out = []
            cmp(json.load(open(os.path.join(r, f))), json.load(open(o)), '', out)
            tot += 1
            if not out:
                same += 1
            elif shown < mx:
                print(rel, len(out))
                for x in out[:6]:
                    print('   ', *x)
                shown += 1
    print('compared', tot, 'identical', same)
