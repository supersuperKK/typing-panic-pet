"""团子 v0.7 sprites: daifuku mochi (direction A). 48x48 frames, drawn at 3x in the app.
Run: python3 tools/make_sprites.py
Outputs src/sprites/<anim>.png (+ -s1..s3 sprout stages), sprites.json, tools/preview.png
"""
from PIL import Image
import os, json, math, sys

S = 48
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('SPRITE_OUT') or os.path.join(HERE, '..', 'src', 'sprites')
PREVIEW = os.environ.get('SPRITE_PREVIEW') or os.path.join(HERE, 'preview.png')
os.makedirs(OUT, exist_ok=True)

def hx(h, a=255):
    if isinstance(h, tuple): return h
    h = h.lstrip('#'); return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16), a)

# hue-shifted ramps: shadows cooler/purpler, highlights warmer; plum selective outline
P = dict(hi='#FFFFFF', lt='#FFF8EC', base='#FBE9D7', sh='#EBC9BE', sh2='#C99CA6',
         ol='#6E4458', ol2='#A06F82', eye='#2E1F33', blush='#FF8FA8', mouth='#B8475F',
         maw='#5A2236', tongue='#FF8FA0', tongue2='#E5677F', white='#FFFFFF', glint2='#DDEFFF',
         sw1='#BFE6FF', sw2='#6AAEF0', sw3='#3B6FB8',
         gold='#FFD34E', gold2='#FFF6C2', gold3='#E0A93A', dgold='#E8C778', dgold2='#F3E3B0', dgold3='#C9A56A',
         pink='#FF7FA0', pink2='#FFC2D1', red='#F05454', red2='#A8323C', gray='#B9B3D0', zz='#8C9CFF',
         bag='#6EAAD2', bag2='#4A7FB0', bag3='#2F4F7A', mint='#7FD6A0', cookie='#E8B46A', cookie2='#B97D44')
LEAF = dict(l1='#B9F07A', l2='#6FCB5C', stem='#3E8A4A', ol='#24553A',
            y1='#E8E07A', y2='#C2B44E', w1='#C9A06A', w2='#93683F', wol='#5E4030')
SHADOW = (70, 40, 70, 70)
GROUND = 43
STAGE = 0   # sprout = stress meter: 0 perky, 1 sagging, 2 yellow droop, 3 withered

class C:
    def __init__(s): s.im = Image.new('RGBA', (S, S), (0,0,0,0)); s.p = s.im.load()
    def put(s, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < S and 0 <= y < S and c is not None: s.p[x, y] = hx(P.get(c, c) if isinstance(c, str) else c)
    def get(s, x, y): return s.p[x, y] if 0 <= x < S and 0 <= y < S else (0,0,0,0)
    def pts(s, pts, c, ox=0, oy=0):
        for x, y in pts: s.put(x+ox, y+oy, c)
    def under(s, x, y, c):   # paint only on empty pixels
        if s.get(x, y)[3] == 0: s.put(x, y, c)

N4 = ((1,0),(-1,0),(0,1),(0,-1))
def ring_of(pts): return {(a+i, b+j) for a, b in pts for i, j in N4} - set(pts)

# ---------- body ----------
def shape_mochi(cx, by, w, h):
    cy = by - h*0.42
    def inside(x, y):
        if y > by: return False
        if y <= cy: return ((x-cx)/(w/2))**2 + ((y-cy)/(h*0.58))**2 <= 1
        t = (y - cy) / (by - cy); half = w/2 * (1 - 0.10*t**3); r = 3.5
        if by - y < r:
            ex = half - r
            return abs(x-cx) <= ex or (abs(x-cx)-ex)**2 + (y-(by-r))**2 <= r*r
        return abs(x-cx) <= half
    return inside

def tidy(m):
    for _ in range(2):
        m |= {(x, y) for y in range(S) for x in range(S) if (x, y) not in m and sum((x+a, y+b) in m for a, b in N4) >= 3}
        m -= {(x, y) for (x, y) in m if sum((x+a, y+b) in m for a, b in N4) <= 1}
    return m

def paint_body(c, m):
    xs = [x for x, _ in m]; ys = [y for _, y in m]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); w, h = x1-x0+1, y1-y0+1
    edge = {(x, y) for (x, y) in m if any((x+a, y+b) not in m for a, b in N4)}
    for (x, y) in m:
        nx = (x + .5 - (x0 + w/2)) / (w/2); ny = (y + .5 - (y0 + h/2)) / (h/2)
        if (x, y) in edge:
            lit = (x, y-1) not in m and ny < 0.2 or (x-1, y) not in m and nx < 0 and ny < .3
            c.put(x, y, 'ol2' if lit else 'ol'); continue
        r = (nx + .35)**2 + (ny + .45)**2
        col = 'base'
        if r > 1.85: col = 'sh2'
        elif r > 1.30: col = 'sh'
        elif (nx + .25)**2/0.42 + (ny + .2)**2/0.36 <= 1: col = 'lt'
        c.put(x, y, col)
    hx0, hy0 = x0 + int(w*0.24), y0 + int(h*0.20)
    for (a, b) in ((0,0),(1,0),(0,1),(2,-1)):
        if (hx0+a, hy0+b) in m and (hx0+a, hy0+b) not in edge: c.put(hx0+a, hy0+b, 'hi')
    return x0, y0, x1, y1

def oval(c, cx, cy, rx, ry, fill='base', shade='sh', ol='ol', behind=False):
    pts = {(x, y) for y in range(S) for x in range(S) if ((x+.5-cx)/rx)**2 + ((y+.5-cy)/ry)**2 <= 1}
    edge = {p for p in pts if any((p[0]+a, p[1]+b) not in pts for a, b in N4)}
    for (x, y) in pts:
        col = ol if (x, y) in edge else (shade if y + .5 > cy + ry*0.25 else fill)
        (c.under if behind else c.put)(x, y, col)
    return pts

def shadow(c, cx, w):
    for x in range(int(cx - w/2), int(cx + w/2) + 1):
        for y in (GROUND + 1, GROUND + 2):
            if ((x + .5 - cx)/(w/2))**2 + ((y - GROUND - 1.5)/1.3)**2 <= 1: c.under(x, y, SHADOW)

# ---------- sprout ----------
def sprout(c, x, y, stage):
    L = LEAF
    if stage == 0:
        stem = [(x, y-1), (x, y-2), (x, y-3)]
        left = [(x-1,y-4),(x-2,y-4),(x-3,y-4),(x-4,y-5),(x-2,y-5),(x-3,y-5),(x-1,y-5)]
        right= [(x+1,y-4),(x+2,y-5),(x+3,y-5),(x+4,y-6),(x+1,y-5),(x+2,y-6),(x+3,y-6),(x+5,y-7)]
        f1, f2, sc, ol = L['l1'], L['l2'], L['stem'], L['ol']
    elif stage in (1, 2):
        stem = [(x, y-1), (x, y-2), (x, y-3), (x+1, y-4)]
        left = [(x-1,y-4),(x-2,y-4),(x-3,y-3),(x-4,y-2),(x-2,y-3),(x-3,y-2),(x-4,y-1)]
        right= [(x+2,y-4),(x+3,y-4),(x+4,y-3),(x+5,y-2),(x+3,y-3),(x+4,y-2),(x+5,y-1)]
        if stage == 1: f1, f2, sc, ol = L['l1'], L['l2'], L['stem'], L['ol']
        else:          f1, f2, sc, ol = L['y1'], L['y2'], L['y2'], L['ol']
    else:
        stem = [(x, y-1), (x+1, y-2), (x+2, y-2)]
        left = [(x+3,y-1),(x+4,y-1),(x+4,y)]
        right= [(x+3,y-2),(x+4,y-2),(x+5,y-1)]
        f1, f2, sc, ol = L['w1'], L['w2'], L['w2'], L['wol']
    allp = set(stem) | set(left) | set(right)
    for p in ring_of(allp): c.under(*p, ol)
    c.pts(stem, sc); c.pts(left, f2); c.pts(right, f1)
    if stage == 0: c.put(x+3, y-6, L['l2'])

# ---------- face parts ----------
EYE_OPEN = [(1,0),(0,1),(1,1),(2,1),(0,2),(1,2),(2,2),(0,3),(1,3),(2,3)]
EYE_ROUND = [(1,0),(2,0),(0,1),(1,1),(2,1),(3,1),(0,2),(1,2),(2,2),(3,2),(0,3),(1,3),(2,3),(3,3),(1,4),(2,4)]
SPIRAL7 = [".XXXXX.", "X.....X", "X.XXX.X", "X.X.X.X", "X.X...X", "X..XXX.", ".X....."]

def eye_open(c, ex, ey):
    c.pts(EYE_OPEN, 'eye', ex, ey); c.put(ex, ey+1, 'white'); c.put(ex+1, ey+1, 'white')

def eye_round(c, ex, ey, px=0, wet=False):
    c.pts(EYE_ROUND, 'eye', ex, ey); c.put(ex+1+px, ey+1, 'white')
    if wet: c.put(ex+1+px, ey+2, 'white'); c.put(ex+2, ey+3, 'glint2')

def brows(c, lx, rx, y):
    c.pts([(0,1),(1,1),(2,0)], 'eye', lx, y); c.pts([(0,0),(1,1),(2,1)], 'eye', rx, y)

def eye_spiral(c, ex, ey):
    for b, row in enumerate(SPIRAL7):
        for a, ch in enumerate(row):
            if ch == 'X': c.put(ex+a, ey+b, 'eye')

def eye_x(c, ex, ey):
    for k in range(4): c.put(ex+k, ey+k, 'eye'); c.put(ex+3-k, ey+k, 'eye')

def blush(c, cx, y, gap, w=3):
    for side in (-1, 1):
        bx = cx + side*gap - (w-1 if side < 0 else 0)
        for a in range(w): c.put(bx+a, y, 'blush')

def mouth(c, mx, my, kind):
    e = 'eye'
    if kind == 'w':      c.pts([(-1,0),(0,1),(1,0)], e, mx, my)
    elif kind == 'flat': c.pts([(-1,0),(0,0),(1,0)], e, mx, my)
    elif kind == 'wave': c.pts([(-2,1),(-1,0),(0,1),(1,0),(2,1)], e, mx, my)
    elif kind == 'o':
        c.pts([(0,0),(-1,1),(1,1),(0,2)], e, mx, my); c.put(mx, my+1, 'mouth')
    elif kind == 'open':
        c.pts([(-2,0),(-1,0),(0,0),(1,0),(2,0),(-2,1),(2,1),(-1,2),(0,2),(1,2)], e, mx, my)
        c.pts([(-1,1),(1,1)], 'maw', mx, my); c.put(mx, my+1, 'tongue')
    elif kind == 'scream':
        rim = [(-2,0),(-1,0),(0,0),(1,0),(2,0),(-3,1),(3,1),(-3,2),(3,2),(-2,3),(2,3),(-1,4),(0,4),(1,4)]
        inner = [(-2,1),(-1,1),(0,1),(1,1),(2,1),(-2,2),(-1,2),(0,2),(1,2),(2,2),(-1,3),(0,3),(1,3)]
        c.pts(rim, e, mx, my); c.pts(inner, 'maw', mx, my); c.pts([(-1,3),(0,3),(1,3),(0,2)], 'tongue', mx, my)
    elif kind == 'tongue':
        c.pts([(-1,0),(0,0),(1,0)], e, mx, my); c.put(mx+1, my+1, 'tongue'); c.put(mx+1, my+2, 'tongue2')

def drop(c, x, y):
    pts = [(x, y), (x-1, y+1), (x, y+1), (x+1, y+1), (x-1, y+2), (x, y+2), (x+1, y+2), (x, y+3)]
    for p in ring_of(pts): c.under(*p, 'sw3')
    c.pts(pts, 'sw2'); c.put(x-1, y+1, 'sw1'); c.put(x, y, 'sw1')

def tear(c, x, y, n=4):
    for i in range(n): c.put(x, y+i, 'sw2' if i else 'sw1')

def star(c, x, y, bright=True, small=False):
    g, w, d = ('gold', 'gold2', 'gold3') if bright else ('dgold', 'dgold2', 'dgold3')
    if small:
        c.pts([(0,-1),(0,1),(-1,0),(1,0)], g, x, y); c.put(x, y, w); return
    c.pts([(0,-2),(0,2),(-2,0),(2,0)], d, x, y)
    c.pts([(a, b) for a in (-1,0,1) for b in (-1,0,1)], g, x, y); c.put(x, y, w)

def star_ring(c, cx, cy, rx, ry, phase=0, n=3):
    for i in range(n):
        t = phase + i * 2*math.pi/n
        x = cx + rx*math.cos(t); y = cy + ry*math.sin(t) - 2*math.cos(t)
        front = math.sin(t) > 0
        if front or c.get(int(x), int(y))[3] == 0: star(c, int(round(x)), int(round(y)), front)

def ghost(c, x, y):
    pts = [(1,0),(2,0),(3,0),(0,1),(1,1),(2,1),(3,1),(4,1),(0,2),(1,2),(2,2),(3,2),(4,2),(0,3),(1,3),(2,3),(3,3),(4,3),(0,4),(2,4),(4,4)]
    for a, b in ring_of(pts): c.put(x+a, y+b, 'gray')
    for a, b in pts: c.put(x+a, y+b, (255,255,255,230))
    c.put(x+1, y+2, 'eye'); c.put(x+3, y+2, 'eye')

HEART = [(0,0),(1,0),(3,0),(4,0),(-1,1),(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(0,2),(1,2),(2,2),(3,2),(4,2),(1,3),(2,3),(3,3),(2,4)]
HEART_S = [(0,0),(2,0),(-1,1),(0,1),(1,1),(2,1),(3,1),(0,2),(1,2),(2,2),(1,3)]
def heart(c, x, y, small=False):
    pts = HEART_S if small else HEART
    for p in ring_of(pts): c.under(p[0]+x, p[1]+y, 'red2')
    c.pts(pts, 'pink', x, y); c.put(x, y+1, 'pink2')

# ---------- frame ----------
def frame(dx=0, dy=0, sq=0, eyes='open', mouth_='w', sweat=0, arms=None, fx=(), feet=None,
          flat=False, look=0, bag=False, facing=0):
    c = C()
    cx = 24 + dx
    if flat: w, h, by = 44, 11, GROUND
    else:    w, h, by = 34 + sq*1.2, 26 - sq*1.0, GROUND + dy
    m = tidy({(x, y) for y in range(S) for x in range(S) if shape_mochi(cx, by + .99, w, h)(x + .5, y + .5)})
    shadow(c, cx, int(w*0.8*(1 - max(0, -dy)*0.05)))
    rows = {}
    for (x, y) in m: rows.setdefault(y, [x, x]); rows[y][0] = min(rows[y][0], x); rows[y][1] = max(rows[y][1], x)
    y0 = min(rows); y1 = max(rows); bh = y1 - y0
    def edge(y, side): y = max(y0, min(y1, int(y))); return rows[y][0] if side < 0 else rows[y][1]
    mid = y0 + int(bh*0.55)

    # behind the body: backpack, side arms, feet
    if bag:
        bx = edge(mid, -1) if facing >= 0 else edge(mid, 1)
        oval(c, bx + (1 if facing >= 0 else -1), mid, 5, 7, 'bag', 'bag2', 'bag3')
    def nub(side, yy, out=1):
        oval(c, edge(yy, side) + side*out + .5, yy + .5, 3, 3)
    if not flat:
        A = {'down': ((-1, mid+3, 0), (1, mid+3, 0)),
             'up': ((-1, y0+8, 3), (1, y0+8, 3)),
             'flailA': ((-1, y0+5, 2), (1, mid+5, 1)),
             'flailB': ((-1, mid+5, 1), (1, y0+5, 2)),
             'wave1': ((-1, mid+3, 0), (1, y0+3, 3)),
             'wave2': ((-1, mid+3, 0), (1, y0+7, 4)),
             'thumb': ((-1, mid+3, 0),),
             'face': ((-1, mid+3, 0),)}.get(arms, ())
        for side, yy, out in A: nub(side, yy, out)
        if feet:
            fy = y1 + 1
            off = {'walkA': ((-9, -1), (6, 1)), 'walkB': ((-6, 1), (9, -1)), 'air': ((-6, 1), (6, 1))}[feet]
            for ox, oy in off: oval(c, cx + ox + .5, fy + oy, 3, 2, 'sh', 'sh2')

    x0, y0, x1, y1 = paint_body(c, m)
    top = min(y for (x, y) in m if abs(x - cx) <= 1)

    # sprout
    if flat: sprout(c, cx + 1, top, 3)
    else:    sprout(c, cx, top, STAGE)

    fcx = cx + look + (2 if facing > 0 else -2 if facing < 0 else 0)
    if flat: ey = y0 + 3
    else:    ey = y0 + int((y1 - y0)*0.42)
    L3, R3 = fcx - 7, fcx + 6         # 3-wide eyes
    L4, R4 = fcx - 8, fcx + 6         # 4-wide eyes
    my = ey + 5; bly = ey + 5; bgap = 8

    if eyes == 'open':
        eye_open(c, L3, ey); eye_open(c, R3, ey); my = ey + 4
    elif eyes == 'blink':
        for X in (L3, R3): c.pts([(0,2),(1,2),(2,2)], 'eye', X, ey)
        my = ey + 4
    elif eyes == 'happy':
        for X in (L4, R4): c.pts([(0,2),(1,1),(2,1),(3,2)], 'eye', X, ey)
        my = ey + 4
    elif eyes == 'sleep':
        for X in (L4, R4): c.pts([(0,1),(1,2),(2,2),(3,1)], 'eye', X, ey)
        my = ey + 4
    elif eyes in ('look', 'round'):       # alert glance / surprised
        px = 1 if eyes == 'look' else 0
        eye_round(c, L4 + px, ey, px=px); eye_round(c, R4 + px, ey, px=px); bly = ey + 6; my = ey + 6
    elif eyes == 'wide':                  # nervous 1: glance + worried brows
        eye_round(c, L4 + 1, ey + 1, px=1); eye_round(c, R4 + 1, ey + 1, px=1)
        brows(c, L4, R4 + 2, ey - 2); bly = ey + 7; my = ey + 6; fcx += 1
    elif eyes == 'teary':                 # panic 2
        eye_round(c, L4, ey, wet=True); eye_round(c, R4, ey, wet=True)
        brows(c, L4, R4 + 1, ey - 3)
        tear(c, L4, ey + 4); tear(c, R4 + 3, ey + 4); bly = ey + 6; my = ey + 5; bgap = 10
    elif eyes == 'spiral':
        eye_spiral(c, fcx - 11, ey - 1); eye_spiral(c, fcx + 4, ey - 1); bly = ey + 7; my = ey + 6; bgap = 10
    elif eyes == 'x':
        eye_x(c, fcx - 9, ey); eye_x(c, fcx + 5, ey); my = ey + 3; bly = ey + 4; bgap = 13
    elif eyes == 'dot':
        for X in (L3, R3): c.pts([(0,1),(1,1),(0,2),(1,2)], 'eye', X + 1, ey)
        my = ey + 4

    if arms != 'face' or True:
        blush(c, fcx, bly, bgap, 3)
    mouth(c, fcx if mouth_ != 'tongue' else fcx - 1, my, mouth_)

    spots = [(x1 - 2, y0 + 1), (x0, y0 + 4), (x1 + 1, y0 + 8)]
    for (x, y) in spots[:sweat]: drop(c, x, y)

    # in front of the body
    if arms == 'thumb':
        tx, ty = edge(mid, 1) - 2, mid
        oval(c, tx + .5, ty + .5, 3.5, 3.5)
        thumb = [(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)]
        for p in ring_of(thumb): c.put(p[0] + tx - 1, p[1] + ty - 6, 'ol')
        c.pts(thumb, 'base', tx - 1, ty - 6); c.put(tx - 1, ty - 6, 'lt')
    if arms == 'ears':
        for side in (-1, 1): oval(c, edge(ey, side) - side*1 + .5, ey + .5, 3, 4)
    if arms == 'face':
        px_, py_ = R3 + 2, ey + 2
        oval(c, px_ + .5, py_ + .5, 4, 3.5, 'lt', 'sh')
        for k in (-1, 1): c.put(px_ + k, py_ - 2, 'ol2'); c.put(px_ + k, py_ - 1, 'ol2')

    # effects
    def Z(x, y, n):
        for k in range(n): c.put(x+k, y, 'zz'); c.put(x+k, y+n-1, 'zz')
        for k in range(1, n-1): c.put(x+n-1-k, y+k, 'zz')
    if 'z1' in fx: Z(37, 9, 4)
    if 'z2' in fx: Z(36, 11, 4); Z(40, 3, 6)
    if 'excl' in fx:
        bar = [(x, y) for x in range(39, 42) for y in range(2, 9)] + [(x, y) for x in range(39, 42) for y in range(10, 13)]
        for p in ring_of(bar): c.put(*p, 'red2')
        c.pts(bar, 'red'); c.put(39, 2, 'pink2')
    if 'lines' in fx:
        for y in (22, 30, 38):
            for k in range(5): c.put(k, y, 'gray')
    if 'lines2' in fx:
        for y in (26, 34):
            for k in range(6): c.put(k + 1, y, 'gray')
    if 'linesR' in fx:
        for y in (24, 32, 40):
            for k in range(5): c.put(43 + k, y, 'gray')
    if 'soul1' in fx: ghost(c, cx + 5, y0 - 11)
    if 'soul2' in fx: ghost(c, cx + 7, y0 - 17)
    if 'star' in fx: star(c, 40, 8)
    if 'heart' in fx: heart(c, 6, 8)
    if 'heart2' in fx: heart(c, 37, 6); heart(c, 5, 13)
    if 'heart3' in fx: heart(c, 40, 11, True); heart(c, 4, 6, True)
    if 'gloom' in fx:
        for x in range(12, 38, 4):
            for k in range(3): c.put(x, 3 + k + (x // 4) % 2, 'gray')
    if 'ringA' in fx: star_ring(c, cx, y0 - 2, 19, 4, phase=0.9)
    if 'ringB' in fx: star_ring(c, cx, y0 - 2, 19, 4, phase=0.9 + math.pi/3)
    if 'cookie' in fx or 'cookie2' in fx:
        x, y = 24, 38
        pts = oval(c, x, y, 4.5, 3.5, 'cookie', 'cookie2', 'ol')
        for (a, b) in ((-2, -1), (1, 0), (-1, 1), (2, -1)): c.put(x + a, y + b, 'cookie2')
        if 'cookie2' in fx:
            for (a, b) in ((3, -3), (4, -2), (3, -2), (4, -1)): c.put(x + a, y + b, 'base')
            c.put(2 + x, y - 3, 'ol'); c.put(3 + x, y - 1, 'ol'); c.put(4 + x, y, 'ol')
    if 'crumbs' in fx:
        for (x, y) in ((12, 41), (35, 42), (16, 44), (32, 40)): c.put(x, y, 'cookie')
    if 'confA' in fx or 'confB' in fx:
        cs = ('pink', 'gold', 'mint', 'sw2', 'red')
        pts = ((5, 4), (14, 10), (33, 3), (42, 12), (9, 18), (38, 20)) if 'confA' in fx else ((7, 9), (18, 3), (30, 9), (40, 4), (4, 22), (43, 18))
        for i, (x, y) in enumerate(pts):
            for a in (0, 1):
                for b in (0, 1): c.put(x + a, y + b, cs[i % 5])
    if 'qmark' in fx:
        q = [(1,0),(2,0),(3,1),(3,2),(2,3),(1,4),(1,5),(1,7)]
        c.pts(q, 'ol', 39, 3); c.pts([(2,0)], 'ol2', 39, 3)
    if 'tilde' in fx:
        for k, o in enumerate((0, 1, 1, 0, 0, 1)): c.put(37 + k, 9 + o, 'ol2')
    return c.im

F = frame
STRIP_FNS = {
    'idle':     [lambda: F(), lambda: F(sq=1, dy=0), lambda: F(), lambda: F(eyes='blink')],
    'alert':    [lambda: F(eyes='look', mouth_='flat', fx=('excl',), dy=-1), lambda: F(eyes='look', mouth_='flat', look=1)],
    'nervous':  [lambda: F(dx=-1, eyes='wide', mouth_='wave', sweat=1), lambda: F(dx=1, eyes='wide', mouth_='wave', sweat=1),
                 lambda: F(dx=-1, eyes='wide', mouth_='wave', sweat=2), lambda: F(dx=1, eyes='wide', mouth_='wave', sweat=1)],
    'panic':    [lambda: F(sq=1, eyes='teary', mouth_='scream', sweat=2, arms='flailA', feet='walkA', fx=('lines',)),
                 lambda: F(sq=1, dy=-3, eyes='teary', mouth_='scream', sweat=1, arms='flailB', feet='walkB', fx=('lines2',)),
                 lambda: F(sq=1, eyes='teary', mouth_='scream', sweat=3, arms='flailA', feet='walkA', fx=('lines',)),
                 lambda: F(sq=1, dy=-3, eyes='teary', mouth_='scream', sweat=1, arms='flailB', feet='walkB', fx=('lines2',))],
    'collapse': [lambda: F(flat=True, eyes='x', mouth_='tongue', fx=('soul1',)), lambda: F(flat=True, eyes='x', mouth_='tongue', fx=('soul2',))],
    'sleep':    [lambda: F(eyes='sleep', mouth_='flat', sq=1, fx=('z1',)), lambda: F(eyes='sleep', mouth_='o', fx=('z2',))],
    'jump':     [lambda: F(sq=4, eyes='happy', mouth_='open'), lambda: F(dy=-7, sq=-2, eyes='happy', mouth_='open', arms='up', feet='air', fx=('star',)),
                 lambda: F(dy=-4, eyes='open', mouth_='w', arms='up', feet='air')],
    'thumbs':   [lambda: F(eyes='happy', mouth_='open', arms='thumb', fx=('star',)), lambda: F(eyes='happy', mouth_='w', arms='thumb', fx=('heart',))],
    'facepalm': [lambda: F(eyes='dot', mouth_='flat', arms='face', fx=('gloom',)), lambda: F(eyes='dot', mouth_='wave', arms='face', sq=1, fx=('gloom',))],
    'offwork':  [lambda: F(eyes='happy', mouth_='open', arms='wave1', bag=True), lambda: F(eyes='happy', mouth_='open', arms='wave2', bag=True)],
    'walk':     [lambda: F(eyes='happy', mouth_='w', feet='walkA', bag=True, facing=1),
                 lambda: F(dy=-1, eyes='happy', mouth_='w', feet='walkB', bag=True, facing=1)],
    'poke':     [lambda: F(sq=4, dx=2, eyes='blink', mouth_='o', fx=('linesR',)), lambda: F(sq=2, dx=1, eyes='dot', mouth_='o')],
    'dizzy':    [lambda: F(dx=-1, eyes='spiral', mouth_='wave', fx=('ringA',)), lambda: F(dx=1, eyes='spiral', mouth_='wave', fx=('ringB',))],
    'happy':    [lambda: F(dx=-1, eyes='happy', mouth_='w', fx=('heart2',)), lambda: F(sq=1, eyes='happy', mouth_='open', fx=('heart3',)),
                 lambda: F(dx=1, eyes='happy', mouth_='w', fx=('heart2',))],
    'eat':      [lambda: F(eyes='open', mouth_='o', fx=('cookie',)), lambda: F(sq=1, eyes='happy', mouth_='open', fx=('cookie2',)),
                 lambda: F(eyes='happy', mouth_='w', fx=('crumbs',)), lambda: F(sq=1, eyes='happy', mouth_='open', fx=('crumbs', 'heart'))],
    'held':     [lambda: F(dy=-2, sq=-2, eyes='round', mouth_='o', arms='up', feet='air', fx=('lines2',)),
                 lambda: F(dy=-3, sq=-2, dx=1, eyes='round', mouth_='o', arms='up', feet='air', fx=('linesR',))],
    'stretch':  [lambda: F(sq=-3, dy=-1, eyes='sleep', mouth_='o', arms='up'), lambda: F(sq=-1, eyes='happy', mouth_='w', arms='up', fx=('tilde',))],
    'deaf':     [lambda: F(eyes='dot', mouth_='wave', arms='ears', fx=('qmark',)),
                 lambda: F(sq=1, eyes='blink', mouth_='wave', arms='ears', fx=('qmark',))],
    'cheer':    [lambda: F(dy=-6, sq=-2, eyes='happy', mouth_='open', arms='up', feet='air', fx=('confA',)),
                 lambda: F(sq=2, eyes='happy', mouth_='open', arms='up', fx=('confB',))],
}
NO_SPROUT = {'collapse'}

def build(): return {k: [fn() for fn in v] for k, v in STRIP_FNS.items()}

if __name__ == '__main__':
    meta = {}
    for stage in range(4):
        STAGE = stage
        for name, frames in build().items():
            if stage and name in NO_SPROUT: continue
            strip = Image.new('RGBA', (S*len(frames), S), (0,0,0,0))
            for i, im in enumerate(frames): strip.paste(im, (i*S, 0))
            strip.save(os.path.join(OUT, f'{name}.png' if stage == 0 else f'{name}-s{stage}.png'))
            meta[name] = len(frames)
    STAGE = 0; STRIPS = build()
    with open(os.path.join(OUT, 'sprites.json'), 'w') as fp: json.dump({'size': S, 'frames': meta, 'stages': 4}, fp)
    Z = 4; cols = max(meta.values())
    prev = Image.new('RGBA', (cols*S*Z, len(STRIPS)*S*Z), (233, 230, 242, 255))
    for r, frames in enumerate(STRIPS.values()):
        for i, im in enumerate(frames): prev.alpha_composite(im.resize((S*Z, S*Z), Image.NEAREST), (i*S*Z, r*S*Z))
    prev.save(PREVIEW)
    print(meta)
