"""Geometry of the `svg` field: path of a ShapePath in its parent's coordinates.

Rectangles use Sketch's smooth (continuous) corners, which is the figma-squircle
construction: three cubic Beziers per corner.
"""
import math


def num(v):
    s = '%.9g' % v
    if 'e' in s:
        s = ('%.9f' % v).rstrip('0').rstrip('.')
    if s in ('-0', ''):
        s = '0'
    return s


def pt(p):
    return num(p[0]) + ',' + num(p[1])


def side_params(r, smoothing, limit):
    """Curve parameters of one side of a corner: the side is `limit` long at most."""
    s = min(smoothing, max(limit / r - 1, 0))
    p = min((1 + s) * r, limit) if False else min((1 + smoothing) * r, limit)
    arc_measure = 90 * (1 - s)
    arc_len = math.sin(math.radians(arc_measure / 2)) * r * math.sqrt(2)
    alpha = (90 - arc_measure) / 2
    p3p4 = r * math.tan(math.radians(alpha / 2))
    beta = 45 * s
    c = p3p4 * math.cos(math.radians(beta))
    d = c * math.tan(math.radians(beta))
    b = (p - arc_len - c - d) / 3
    return p, 2 * b, b, c, d, beta


def corner_curves(r, smoothing, lim_in, lim_out, max_r, smooth):
    """Canonical top-right corner at the origin: (start, [bezier...], end)."""
    r = min(r, lim_in, lim_out)
    if not smooth or smoothing <= 0:
        k = 0.5522847498 * r
        return (-r, 0), [((-r + k, 0), (0, r - k), (0, r))], (0, r), 0.0
    p1, a1, b1, c1, d1, be1 = side_params(r, smoothing, lim_in)
    p2, a2, b2, c2, d2, be2 = side_params(r, smoothing, lim_out)
    a0 = (-p1 + a1 + b1 + c1, d1)
    e1 = (-d2, p2 - a2 - b2 - c2)
    arc = 90 - be1 - be2
    k = 4.0 / 3 * math.tan(math.radians(arc / 4)) * r
    t1, t2 = math.radians(be1), math.radians(be2)
    cu1 = ((-p1 + a1, 0), (-p1 + a1 + b1, 0), a0)
    cu2 = ((a0[0] + k * math.cos(t1), a0[1] + k * math.sin(t1)),
           (e1[0] - k * math.sin(t2), e1[1] - k * math.cos(t2)), e1)
    cu3 = ((0, p2 - a2 - b2), (0, p2 - a2), (0, p2))
    return (-p1, 0), [cu1, cu2, cu3], (0, p2), be2 / 45.0


def rot(p, q):
    x, y = p
    return {0: (x, y), 1: (-y, x), 2: (-x, -y), 3: (y, -x)}[q]


def rect_path(x, y, w, h, radii, smoothing, smooth, rotation):
    if not radii:
        radii = [0, 0, 0, 0]
    radii = list(radii) + [radii[-1]] * (4 - len(radii)) if len(radii) < 4 else list(radii)
    verts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    segs = []
    if max(radii) <= 0:
        pts = verts
        segs = [('M', [pts[0]])] + [('L', [q]) for q in pts[1:]]
    else:
        items = []
        for i in range(4):
            r = radii[i]
            if r <= 0:
                items.append(('P', verts[i]))
                continue
            rr = list(radii)
            ln_in, ln_out = (w, h) if i % 2 else (h, w)
            prev_r, next_r = rr[(i - 1) % 4], rr[(i + 1) % 4]
            lim_in = ln_in * rr[i] / (rr[i] + prev_r)
            lim_out = ln_out * rr[i] / (rr[i] + next_r)
            st, cs, en, sv = corner_curves(r, smoothing, lim_in, lim_out, min(w, h) / 2.0, smooth)
            q = i - 1
            tx = lambda p: (verts[i][0] + rot(p, q % 4)[0], verts[i][1] + rot(p, q % 4)[1])
            items.append(('C', tx(st), [[tx(z) for z in cu] for cu in cs], tx(en), sv))
        first = items[0]
        if first[0] == 'P':
            segs.append(('M', [first[1]]))
        else:
            segs.append(('M', [first[3]]))
        for it in items[1:]:
            if it[0] == 'P':
                segs.append(('L', [it[1]]))
            else:
                segs.append(('L', [it[1]]))
                for cu in it[2]:
                    segs.append(('C', cu))
        if first[0] == 'C':
            segs.append(('L', [first[1]]))
            for cu in first[2]:
                segs.append(('C', cu))
        else:
            segs.append(('L', [verts[0]]))
    return fmt(segs, True, (x + w / 2.0, y + h / 2.0), rotation)


def oval_path(x, y, w, h, rotation):
    rx, ry = w / 2.0, h / 2.0
    cx, cy = x + rx, y + ry
    k = 0.5522847498
    segs = [('M', [(cx, y + h)]),
            ('C', [(cx + k * rx, y + h), (x + w, cy + k * ry), (x + w, cy)]),
            ('C', [(x + w, cy - k * ry), (cx + k * rx, y), (cx, y)]),
            ('C', [(cx - k * rx, y), (x, cy - k * ry), (x, cy)]),
            ('C', [(x, cy + k * ry), (cx - k * rx, y + h), (cx, y + h)])]
    return fmt(segs, True, (cx, cy), rotation)


def custom_path(x, y, w, h, points, closed, rotation):
    def a(p):
        return (x + p[0] * w, y + p[1] * h)
    segs = [('M', [a(points[0]['p'])])]
    n = len(points)
    last = n if closed else n - 1
    for i in range(last):
        p0, p1 = points[i], points[(i + 1) % n]
        f, t = points[i]['f'], p1['t']
        if f == points[i]['p'] and t == p1['p']:
            segs.append(('L', [a(p1['p'])]))
        else:
            segs.append(('C', [a(f), a(t), a(p1['p'])]))
    return fmt(segs, closed, (x + w / 2.0, y + h / 2.0), rotation)


def fmt(segs, closed, centre, rotation):
    cs = sn = None
    if rotation:
        ph = math.radians(rotation)
        cs, sn = math.cos(ph), math.sin(ph)

    def tr(p):
        if cs is None:
            return p
        dx, dy = p[0] - centre[0], p[1] - centre[1]
        return (centre[0] + dx * cs - dy * sn, centre[1] + dx * sn + dy * cs)
    out = []
    cur = None
    for op, pts in segs:
        q = tr(pts[-1])
        if op == 'L' and cur is not None and abs(q[0] - cur[0]) < 1e-9 and abs(q[1] - cur[1]) < 1e-9:
            continue
        if op == 'C' and cur is not None and all(abs(tr(z)[0] - cur[0]) < 1e-9 and abs(tr(z)[1] - cur[1]) < 1e-9 for z in pts):
            continue
        cur = q
        out.append(op.rstrip('!') + ' '.join(pt(tr(q)) for q in pts))
    return ' '.join(out) + (' Z' if closed else '')
