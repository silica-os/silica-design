#!/usr/bin/env python3
"""Extract the @@...@@ JSON payload from a saved run_code result file.

usage: grab.py <result-file> <out.json>
"""
import json
import sys

t = open(sys.argv[1]).read().replace('\\\\', '\\')
a = t.index('@@') + 2
b = t.index('@@', a)
d = json.loads(t[a:b])
json.dump(d, open(sys.argv[2], 'w'))
print(sys.argv[2], {k: (v if not isinstance(v, (list, dict)) else len(v)) for k, v in d.items()})
