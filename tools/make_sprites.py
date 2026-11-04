"""Pixel-art sprite strips for the pet ("团子", a mochi blob with a leaf sprout).
48x48 frames, drawn at 3x in the app. Run: python3 tools/make_sprites.py
Outputs src/sprites/<anim>.png (horizontal strips), sprites.json, tools/preview.png
"""
from PIL import Image
import os, json

S = 48
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'src', 'sprites')
os.makedirs(OUT, exist_ok=True)

P = dict(
    ol=(122, 74, 64), ol2=(150, 96, 80),                # warm outlines
    hi=(255, 253, 240), lt=(255, 241, 196), base=(255, 222, 150),
    sh=(244, 185, 112), sh2=(226, 154, 98),
    belly=(255, 247, 226),
    blush=(255, 146, 158), blush2=(255, 190, 196),
    eye=(58, 38, 52), eye2=(104, 70, 110), white=(255, 255, 255),
    leaf=(132, 206, 112), leaf2=(84, 160, 92), stem=(96, 150, 80),
    mouth=(196, 82, 96), tongue=(255, 128, 140),
    sweat=(140, 204, 255), sweat2=(88, 156, 230),
    zz=(140, 160, 255), red=(240, 84, 84), red2=(170, 50, 60),
    gray=(176, 180, 200), gold=(255, 210, 70), pink=(255, 120, 150),
    bag=(110, 170, 210), bag2=(70, 120, 170), strap=(80, 110, 150),
    # v0.6 sprout stages: tired, wilting, withered
    leafy=(190, 196, 96), leafy2=(140, 146, 62), wither=(184, 136, 84), wither2=(124, 86, 56),
)

# v0.6: the sprout is the stress meter. 0 = perky, 1 = drooping, 2 = wilting, 3 = withered.
STAGE = 0

class F:
    def __init__(self):
        self.im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); self.px = self.im.load()
    def put(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < S and 0 <= y < S: self.px[x, y] = P[c] + (255,)
    def rect(self, x, y, w, h, c):
        for i in range(w):
            for j in range(h): self.put(x + i, y + j, c)
    def blob(self, cx, cy, rx, ry, fill, ol='ol', shade=None):
        """Filled ellipse with a 1px outline; optional shading callback(nx, ny)->color."""
        pts = set()
        for y in range(S):
            for x in range(S):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1: pts.add((x, y))
        for (x, y) in pts:
            edge = any((x + a, y + b) not in pts for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge: self.put(x, y, ol)
            else:
                nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
                self.put(x, y, shade(nx, ny) if shade else fill)
        return pts

def hang(f, x0, y0, d, col, ol, short=False):
    """A pixel leaf hanging down and outward from (x0, y0); d = -1 left, 1 right."""
    core = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (2, 3), (3, 3)] if not short else [(0, 0), (0, 1), (1, 1), (1, 2), (0, 2)]
    pts = {(x0 + d * a, y0 + b) for a, b in core}
    ring = {(x + a, y + b) for x, y in pts for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))} - pts
    for x, y in ring: f.put(x, y, ol)
    for x, y in pts: f.put(x, y, col)

def body_shade(nx, ny):
    # soft spherical light from the top-left
    if (nx + .42) ** 2 / .045 + (ny + .55) ** 2 / .025 <= 1: return 'hi'
    r = (nx + .22) ** 2 + (ny + .30) ** 2
    if r > 1.62: return 'sh2'
    if r > 1.22: return 'sh'
    if ny > .3 and nx * nx / .3 + (ny - .7) ** 2 / .14 <= 1: return 'belly'
    if (nx + .3) ** 2 / .22 + (ny + .38) ** 2 / .14 <= 1: return 'lt'
    return 'base'

def frame(dx=0, dy=0, sq=0, eyes='open', mouth='w', sweat=0, arms='down', fx=(),
          feet='stand', flat=False, tears=False, look=0, bag=False, facing=0):
    f = F()
    if flat: cx, cy, rx, ry = 24 + dx, 39, 20, 7
    else:    cx, cy, rx, ry = 24 + dx, 30 + dy + sq * .5, 17 + sq * .6, 14 - sq * .6
    bottom = cy + ry

    # backpack (behind body, peeks out on one side)
    if bag and not flat:
        bx = cx - rx - 3 if facing >= 0 else cx + rx - 5
        f.blob(bx + 4, cy + 1, 6, 8, 'bag', shade=lambda nx, ny: 'bag2' if nx > .3 else 'bag')

    # feet
    if not flat:
        fy = bottom - 1
        if feet == 'stand': L, R = (cx - 8, fy), (cx + 8, fy)
        elif feet == 'walkA': L, R = (cx - 10, fy - 1), (cx + 7, fy + 1)
        elif feet == 'walkB': L, R = (cx - 7, fy + 1), (cx + 10, fy - 1)
        elif feet == 'air': L, R = (cx - 6, fy + 2), (cx + 6, fy + 2)
        for (x, y) in (L, R): f.blob(x, y, 4, 2.6, 'sh', ol='ol')
    else:
        for x in (cx - 15, cx + 15): f.blob(x, cy - 7, 3, 3.5, 'sh')

    # arms behind body edge
    ay = cy + 2
    def nub(x, y, rx_=3, ry_=3.5): f.blob(x, y, rx_, ry_, 'base', shade=lambda nx, ny: 'sh' if ny > .2 else 'base')
    if not flat:
        if arms == 'down':   nub(cx - rx, ay); nub(cx + rx, ay)
        elif arms == 'up':   nub(cx - rx - 2, ay - 11); nub(cx + rx + 2, ay - 11)
        elif arms == 'flailA': nub(cx - rx - 3, ay - 8); nub(cx + rx + 2, ay + 3)
        elif arms == 'flailB': nub(cx - rx - 2, ay + 3); nub(cx + rx + 3, ay - 8)
        elif arms == 'wave1': nub(cx - rx, ay); nub(cx + rx + 3, ay - 10)
        elif arms == 'wave2': nub(cx - rx, ay); nub(cx + rx + 5, ay - 7)
        elif arms == 'thumb': nub(cx - rx, ay)

    # body
    f.blob(cx, cy, rx, ry, 'base', shade=body_shade)

    # sprout: stem + two leaves, drooping as stress rises (STAGE)
    if not flat:
        top = cy - ry
        leafshade = lambda nx, ny: 'lt' if nx < -.3 and ny < 0 else 'leaf'
        if STAGE == 0:
            for k in range(4): f.put(cx, top - k, 'stem')
            f.blob(cx - 4, top - 4, 4, 2.2, 'leaf', ol='leaf2', shade=leafshade)
            f.blob(cx + 4, top - 5, 4, 2.2, 'leaf', ol='leaf2', shade=leafshade)
        elif STAGE == 1:   # leaves sag to the sides
            for k in range(3): f.put(cx, top - k, 'stem')
            f.blob(cx - 5, top - 1.5, 4, 2, 'leaf', ol='leaf2')
            f.blob(cx + 5, top - 2, 4, 2, 'leaf', ol='leaf2')
        elif STAGE == 2:   # yellowing, both leaves hanging down from a tired stem
            for k in range(4): f.put(cx, top - k, 'stem')
            hang(f, cx - 1, top - 3, -1, 'leafy', 'leafy2'); hang(f, cx + 1, top - 3, 1, 'leafy', 'leafy2')
        else:              # withered: stem bent over, one dry brown leaf left
            for k in range(3): f.put(cx, top - k, 'wither2')
            for k in range(1, 4): f.put(cx + k, top - 3, 'wither2')
            hang(f, cx + 4, top - 2, 1, 'wither', 'wither2', short=True)

    # face
    ex = cx + look + (2 if facing > 0 else -2 if facing < 0 else 0)
    ey = cy - 1 if not flat else cy - 2
    EL, ER = int(ex) - 8, int(ex) + 5   # left edge of each eye (3 wide)

    # blush
    if eyes != 'x':
        for X in (EL - 3, ER + 2):
            f.rect(X, int(ey) + 5, 4, 2, 'blush'); f.put(X, int(ey) + 5, 'blush2')

    for X in (EL, ER):
        Y = int(ey)
        if eyes == 'open':
            f.rect(X, Y - 1, 4, 6, 'eye'); f.rect(X, Y + 3, 4, 2, 'eye2')
            f.rect(X, Y - 1, 2, 2, 'white'); f.put(X + 3, Y + 3, 'white')
            f.put(X, Y - 1, 'eye'); f.put(X + 3, Y - 1, 'eye'); f.put(X, Y + 4, 'eye'); f.put(X + 3, Y + 4, 'eye')
        elif eyes == 'blink':
            f.rect(X, Y + 3, 4, 1, 'eye'); f.put(X - 1, Y + 2, 'eye')
        elif eyes == 'happy':   # ^ ^
            f.put(X, Y + 2, 'eye'); f.put(X + 1, Y + 1, 'eye'); f.put(X + 2, Y + 1, 'eye'); f.put(X + 3, Y + 2, 'eye')
            f.put(X - 1, Y + 3, 'eye'); f.put(X + 4, Y + 3, 'eye')
        elif eyes == 'sleep':   # u u
            f.put(X - 1, Y + 1, 'eye'); f.put(X, Y + 2, 'eye'); f.rect(X + 1, Y + 3, 2, 1, 'eye'); f.put(X + 3, Y + 2, 'eye'); f.put(X + 4, Y + 1, 'eye')
        elif eyes == 'look':    # alert, small pupils glancing down
            f.rect(X - 1, Y - 1, 6, 6, 'white'); f.rect(X + 1, Y + 2, 3, 3, 'eye'); f.put(X + 1, Y + 2, 'white')
            for a in range(6): f.put(X - 1 + a, Y - 2, 'ol')
            f.put(X - 2, Y - 1, 'ol'); f.put(X + 5, Y - 1, 'ol')
        elif eyes == 'wide':    # shaking pinpoint pupils
            f.rect(X - 1, Y - 2, 6, 7, 'white'); f.rect(X + 1, Y + 1, 2, 2, 'eye')
            for a in range(6): f.put(X - 1 + a, Y - 3, 'ol'); f.put(X - 1 + a, Y + 5, 'ol')
            for b in range(7): f.put(X - 2, Y - 2 + b, 'ol'); f.put(X + 5, Y - 2 + b, 'ol')
        elif eyes == 'swirl':   # panic: > <
            f.put(X, Y, 'eye'); f.put(X + 1, Y + 1, 'eye'); f.put(X + 2, Y + 2, 'eye'); f.put(X + 1, Y + 3, 'eye'); f.put(X, Y + 4, 'eye')
        elif eyes == 'x':
            for k in range(4): f.put(X + k, Y + k, 'eye'); f.put(X + 3 - k, Y + k, 'eye')
        elif eyes == 'dot':
            f.rect(X + 1, Y + 2, 2, 2, 'eye')
    if eyes == 'swirl':  # mirror the right eye into "<"
        X, Y = ER, int(ey)
        for (a, b) in ((0, 0), (1, 1), (2, 2), (1, 3), (0, 4)): f.put(X + a, Y + b, 'base')
        for (a, b) in ((3, 0), (2, 1), (1, 2), (2, 3), (3, 4)): f.put(X + a, Y + b, 'eye')

    # mouth
    mx, my = int(ex), int(ey) + 6
    if mouth == 'w':      # ω
        for (a, b) in ((-3, 0), (-2, 1), (-1, 0), (0, 1), (1, 0)): f.put(mx + a, my + b, 'ol')
    elif mouth == 'flat': f.rect(mx - 2, my, 3, 1, 'ol')
    elif mouth == 'o':    f.rect(mx - 2, my, 3, 2, 'mouth'); f.rect(mx - 2, my - 1, 3, 1, 'ol'); f.rect(mx - 2, my + 2, 3, 1, 'ol')
    elif mouth == 'wave':
        for k, o in enumerate((0, 1, 0, 1, 0, 1)): f.put(mx - 3 + k, my + o, 'ol')
    elif mouth == 'scream':
        f.rect(mx - 3, my - 1, 5, 4, 'mouth'); f.rect(mx - 2, my + 2, 3, 1, 'tongue')
        f.rect(mx - 3, my - 2, 5, 1, 'ol'); f.rect(mx - 3, my + 3, 5, 1, 'ol'); f.put(mx - 4, my, 'ol'); f.put(mx + 2, my, 'ol')
    elif mouth == 'open': # happy open D
        f.rect(mx - 3, my, 5, 2, 'mouth'); f.rect(mx - 2, my + 2, 3, 1, 'mouth'); f.rect(mx - 3, my, 5, 1, 'ol'); f.put(mx - 1, my + 2, 'tongue')
    elif mouth == 'tongue':
        f.rect(mx - 2, my, 4, 1, 'ol'); f.rect(mx, my + 1, 2, 3, 'tongue'); f.put(mx + 1, my + 3, 'mouth')

    # sweat drops (outlined teardrops)
    def drop(x, y):
        f.put(x + 1, y, 'sweat2'); f.rect(x, y + 1, 3, 3, 'sweat'); f.put(x, y + 1, 'white')
        f.put(x - 1, y + 2, 'sweat2'); f.put(x + 3, y + 2, 'sweat2'); f.rect(x, y + 4, 3, 1, 'sweat2')
    spots = [(cx + rx - 2, cy - ry + 2), (cx - rx - 2, cy - ry + 5), (cx + rx + 2, cy - 2)]
    for (x, y) in spots[:sweat]: drop(int(x), int(y))
    if tears:
        for X in (EL + 1, ER + 2):
            for k in range(5): f.put(X, int(ey) + 5 + k, 'sweat')
            f.put(X, int(ey) + 10, 'sweat2')

    # thumb in front of body
    if arms == 'thumb':
        tx, ty = int(cx + rx) - 2, int(ay) - 2
        f.blob(tx + 2, ty + 2, 3.5, 3.5, 'base', shade=lambda nx, ny: 'sh' if ny > .2 else 'base')
        f.rect(tx + 1, ty - 4, 3, 4, 'base'); f.rect(tx, ty - 5, 5, 1, 'ol')
        for k in range(5): f.put(tx, ty - 4 + k, 'ol'); f.put(tx + 4, ty - 4 + k, 'ol')
    if arms == 'ears':  # both paws pressed to the sides of the head
        for X in (cx - rx + 3, cx + rx - 3):
            f.blob(X, cy - 5, 3.5, 4, 'base', shade=lambda nx, ny: 'sh' if ny > .3 else 'base')
    if arms == 'face':  # paw over the right eye
        nub(cx - rx, ay)
        f.blob(ER + 2, int(ey) + 1, 5, 4.5, 'base', shade=lambda nx, ny: 'sh' if ny > .3 else 'base')

    # effects
    def Z(x, y, n):
        f.rect(x, y, n, 1, 'zz'); f.rect(x, y + n - 1, n, 1, 'zz')
        for k in range(1, n - 1): f.put(x + n - 1 - k, y + k, 'zz')
    if 'z1' in fx: Z(36, 9, 4)
    if 'z2' in fx: Z(35, 11, 4); Z(40, 3, 6)
    if 'excl' in fx:
        f.rect(39, 3, 3, 7, 'red'); f.rect(39, 11, 3, 3, 'red')
        for y in range(2, 15):
            if y not in (10,): f.put(38, y, 'red2'); f.put(42, y, 'red2')
    if 'lines' in fx:
        for y in (20, 28, 36): f.rect(0, y, 5, 1, 'gray')
    if 'lines2' in fx:
        for y in (24, 32): f.rect(1, y, 6, 1, 'gray')
    if 'linesR' in fx:
        for y in (22, 30, 38): f.rect(43, y, 5, 1, 'gray')
    if 'soul1' in fx or 'soul2' in fx:
        sy = 22 if 'soul1' in fx else 15
        f.blob(24, sy, 4, 4, 'white', ol='gray'); f.rect(23, sy + 3, 3, 3, 'white')
        f.put(22, sy + 6, 'white'); f.put(25, sy + 6, 'white'); f.put(23, sy - 1, 'eye'); f.put(25, sy - 1, 'eye')
    if 'star' in fx:
        x, y = 40, 8
        f.put(x, y - 2, 'gold'); f.put(x, y + 2, 'gold'); f.put(x - 2, y, 'gold'); f.put(x + 2, y, 'gold')
        f.rect(x - 1, y - 1, 3, 3, 'gold'); f.put(x, y, 'white')
    if 'heart' in fx:
        x, y = 8, 8
        for (a, b) in ((0, 0), (1, 0), (3, 0), (4, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
                       (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3), (2, 4)): f.put(x + a, y + b, 'pink')
        f.put(x, y + 1, 'white')
    if 'gloom' in fx:
        for x in range(10, 38, 4): f.rect(x, 4, 1, 3, 'gray')
    if 'heart2' in fx:
        for (x, y) in ((36, 6), (6, 14)):
            for (a, b) in ((0, 0), (1, 0), (3, 0), (4, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
                           (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3), (2, 4)): f.put(x + a, y + b, 'pink')
            f.put(x, y + 1, 'white')
    if 'heart3' in fx:
        for (x, y) in ((40, 12), (3, 6)):
            for (a, b) in ((0, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (1, 3)): f.put(x + a, y + b, 'pink')
    if 'dizzyA' in fx or 'dizzyB' in fx:
        pts = ((12, 6), (24, 2), (36, 6)) if 'dizzyA' in fx else ((16, 3), (30, 3), (40, 9))
        for (x, y) in pts:
            f.put(x, y - 1, 'gold'); f.put(x, y + 1, 'gold'); f.put(x - 1, y, 'gold'); f.put(x + 1, y, 'gold'); f.put(x, y, 'white')
    if 'cookie' in fx or 'cookie2' in fx:
        x, y = 24, 38
        f.blob(x, y, 5.5, 4.5, 'gold', ol='ol', shade=lambda nx, ny: 'sh' if ny > .3 else 'gold')
        for (a, b) in ((-2, -1), (1, 0), (-1, 2), (2, -2)): f.put(x + a, y + b, 'ol2')
        if 'cookie2' in fx:  # bitten
            for (a, b) in ((3, -3), (4, -2), (4, -3), (5, -1), (3, -2)): f.put(x + a, y + b, 'base')
    if 'crumbs' in fx:
        for (x, y) in ((12, 40), (35, 42), (16, 44), (32, 38)): f.put(x, y, 'gold')
    if 'confA' in fx or 'confB' in fx:
        cs = ('pink', 'gold', 'leaf', 'sweat', 'red')
        pts = ((5, 4), (14, 10), (33, 3), (42, 12), (9, 18), (38, 20)) if 'confA' in fx else ((7, 9), (18, 3), (30, 9), (40, 4), (4, 22), (43, 18))
        for i, (x, y) in enumerate(pts): f.rect(x, y, 2, 2, cs[i % 5])
    if 'qmark' in fx:
        for (a, b) in ((1, 0), (2, 0), (3, 1), (3, 2), (2, 3), (1, 4), (1, 5), (1, 7)): f.put(38 + a, 4 + b, 'ol2')
    if 'tilde' in fx:
        for k, o in enumerate((0, 1, 1, 0, 0, 1)): f.put(36 + k, 10 + o, 'ol2')
    return f.im

STRIP_FNS = {
    'idle':     [lambda: frame(), lambda: frame(sq=1, dy=1), lambda: frame(), lambda: frame(eyes='blink')],
    'alert':    [lambda: frame(eyes='look', mouth='flat', fx=('excl',), dy=-1), lambda: frame(eyes='look', mouth='flat', look=1)],
    'nervous':  [lambda: frame(dx=-1, eyes='wide', mouth='wave', sweat=1), lambda: frame(dx=1, eyes='wide', mouth='wave', sweat=2),
                 lambda: frame(dx=-1, eyes='wide', mouth='wave', sweat=2), lambda: frame(dx=1, eyes='wide', mouth='wave', sweat=1)],
    'panic':    [lambda: frame(eyes='swirl', mouth='scream', sweat=3, arms='flailA', feet='walkA', fx=('lines',), tears=True, facing=1),
                 lambda: frame(dy=-3, eyes='swirl', mouth='scream', sweat=2, arms='flailB', feet='walkB', fx=('lines2',), tears=True, facing=1),
                 lambda: frame(eyes='swirl', mouth='scream', sweat=3, arms='flailA', feet='walkA', fx=('lines',), tears=True, facing=1),
                 lambda: frame(dy=-3, eyes='swirl', mouth='scream', sweat=2, arms='flailB', feet='walkB', fx=('lines2',), tears=True, facing=1)],
    'collapse': [lambda: frame(flat=True, eyes='x', mouth='tongue', fx=('soul1',)), lambda: frame(flat=True, eyes='x', mouth='tongue', fx=('soul2',))],
    'sleep':    [lambda: frame(eyes='sleep', mouth='flat', sq=1, dy=1, fx=('z1',)), lambda: frame(eyes='sleep', mouth='o', fx=('z2',))],
    'jump':     [lambda: frame(sq=4, dy=3, eyes='happy', mouth='open'), lambda: frame(dy=-7, sq=-2, eyes='happy', mouth='open', arms='up', feet='air', fx=('star',)),
                 lambda: frame(dy=-4, eyes='open', mouth='w', arms='up', feet='air')],
    'thumbs':   [lambda: frame(eyes='happy', mouth='open', arms='thumb', fx=('star',)), lambda: frame(eyes='happy', mouth='w', arms='thumb', fx=('heart',))],
    'facepalm': [lambda: frame(eyes='dot', mouth='flat', arms='face', fx=('gloom',)), lambda: frame(eyes='dot', mouth='wave', arms='face', dy=1, fx=('gloom',))],
    # 17:30: puts on the backpack, waves, then walks off to the right
    'offwork':  [lambda: frame(eyes='happy', mouth='open', arms='wave1', bag=True), lambda: frame(eyes='happy', mouth='open', arms='wave2', bag=True)],
    'walk':     [lambda: frame(eyes='happy', mouth='w', feet='walkA', bag=True, facing=1),
                 lambda: frame(dy=-1, eyes='happy', mouth='w', feet='walkB', bag=True, facing=1)],
    # v0.5 interactions
    'poke':     [lambda: frame(sq=4, dy=2, dx=2, eyes='blink', mouth='o', fx=('linesR',)), lambda: frame(sq=2, dy=1, dx=1, eyes='dot', mouth='o')],
    'dizzy':    [lambda: frame(dx=-1, eyes='swirl', mouth='wave', fx=('dizzyA',)), lambda: frame(dx=1, eyes='swirl', mouth='wave', fx=('dizzyB',))],
    'happy':    [lambda: frame(dx=-1, eyes='happy', mouth='w', fx=('heart2',)), lambda: frame(sq=1, dy=1, eyes='happy', mouth='open', fx=('heart3',)),
                 lambda: frame(dx=1, eyes='happy', mouth='w', fx=('heart2',))],
    'eat':      [lambda: frame(eyes='open', mouth='o', fx=('cookie',)), lambda: frame(sq=1, dy=1, eyes='happy', mouth='open', fx=('cookie2',)),
                 lambda: frame(eyes='happy', mouth='w', fx=('crumbs',)), lambda: frame(sq=1, dy=1, eyes='happy', mouth='open', fx=('crumbs', 'heart'))],
    'held':     [lambda: frame(dy=-2, sq=-2, eyes='wide', mouth='o', arms='up', feet='air', fx=('lines2',)),
                 lambda: frame(dy=-3, sq=-2, dx=1, eyes='wide', mouth='o', arms='up', feet='air', fx=('linesR',))],
    'stretch':  [lambda: frame(sq=-3, dy=-2, eyes='sleep', mouth='o', arms='up'), lambda: frame(sq=-1, eyes='happy', mouth='w', arms='up', fx=('tilde',))],
    # v0.6: no keyboard permission yet (macOS) - covers its ears, can't hear you
    'deaf':     [lambda: frame(eyes='dot', mouth='wave', arms='ears', fx=('qmark',)),
                 lambda: frame(dy=1, sq=1, eyes='blink', mouth='wave', arms='ears', fx=('qmark',))],
    'cheer':    [lambda: frame(dy=-6, sq=-2, eyes='happy', mouth='open', arms='up', feet='air', fx=('confA',)),
                 lambda: frame(sq=2, dy=1, eyes='happy', mouth='open', arms='up', fx=('confB',))],
}

STRIP_ARGS = None  # filled below; strips are rebuilt per sprout stage

def build():
    return {k: [fn() for fn in v] for k, v in STRIP_FNS.items()}

meta = {}
NO_SPROUT = {'collapse'}
for stage in range(4):
    STAGE = stage
    strips = build()
    for name, frames in strips.items():
        if stage and name in NO_SPROUT: continue
        strip = Image.new('RGBA', (S * len(frames), S), (0, 0, 0, 0))
        for i, im in enumerate(frames): strip.paste(im, (i * S, 0))
        strip.save(os.path.join(OUT, f'{name}.png' if stage == 0 else f'{name}-s{stage}.png'))
        meta[name] = len(frames)
STAGE = 0
STRIPS = build()
with open(os.path.join(OUT, 'sprites.json'), 'w') as fp: json.dump({'size': S, 'frames': meta, 'stages': 4}, fp)

Z = 4; cols = max(meta.values())
prev = Image.new('RGBA', (cols * S * Z, len(STRIPS) * S * Z), (238, 232, 246, 255))
for r, frames in enumerate(STRIPS.values()):
    for i, im in enumerate(frames):
        prev.alpha_composite(im.resize((S * Z, S * Z), Image.NEAREST), (i * S * Z, r * S * Z))
prev.save(os.path.join(HERE, 'preview.png'))
print(meta)
