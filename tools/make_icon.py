"""App / tray icon from the mochi sprite. Run after make_sprites.py:
python3 tools/make_icon.py  -> tools/icon-src.png (1024), plus hand-tuned 16/24/32/48 px frames.
Then: npx tauri icon tools/icon-src.png  and  python3 tools/make_icon.py --ico  (rewrites icons/icon.ico + small pngs)
"""
import os, sys, importlib.util
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('SPRITE_OUT', '/tmp/_spr'); os.environ.setdefault('SPRITE_PREVIEW', '/tmp/_spr.png')
spec = importlib.util.spec_from_file_location('ms', os.path.join(HERE, 'make_sprites.py'))
ms = importlib.util.module_from_spec(spec); spec.loader.exec_module(ms)
ICONS = os.path.join(HERE, '..', 'src-tauri', 'icons')

def small(n):
    """Pixel-exact icon of size n (16/24/32): mochi body, face scaled to stay readable."""
    c = ms.C()
    cfg = {16: (16, 12, 1), 24: (22, 16, 2), 32: (29, 21, 2)}[n]
    w, h, sp = cfg
    cx = n / 2; by = n - 1 - (0 if n == 16 else 1)
    m = ms.tidy({(x, y) for y in range(n) for x in range(n) if ms.shape_mochi(cx, by + .99, w, h)(x + .5, y + .5)})
    x0, y0, x1, y1 = ms.paint_body(c, m)
    top = min(y for (x, y) in m if abs(x + .5 - cx) <= 1)
    mid = int(cx)
    L = ms.LEAF
    if n == 16:   # stem + two leaf pixels
        for p in ((mid, top-1),): c.put(*p, L['stem'])
        c.put(mid-1, top-2, L['l2']); c.put(mid+1, top-2, L['l1']); c.put(mid-2, top-2, L['l2']); c.put(mid+1, top-3, L['l1'])
        ey = y0 + 4
        for X in (mid - 3, mid + 3): c.put(X, ey, 'eye'); c.put(X, ey+1, 'eye')
        c.put(mid-5, ey+2, 'blush'); c.put(mid+5, ey+2, 'blush')
        c.put(mid-1, ey+2, 'eye'); c.put(mid+1, ey+2, 'eye'); c.put(mid, ey+3, 'eye')  # tiny smile
    else:
        ms.sprout(c, mid, top, 0) if n == 32 else (c.put(mid, top-1, L['stem']), c.put(mid, top-2, L['stem']),
            [c.put(x, y, L['l2']) for x, y in ((mid-1, top-3), (mid-2, top-3), (mid-3, top-4))],
            [c.put(x, y, L['l1']) for x, y in ((mid+1, top-3), (mid+2, top-4), (mid+3, top-4))])
        ey = y0 + int((y1 - y0) * 0.38)
        if n == 32:
            ms.eye_open(c, mid - 7, ey); ms.eye_open(c, mid + 4, ey)
            ms.blush(c, mid, ey + 5, 8); ms.mouth(c, mid, ey + 4, 'w')
        else:
            for X in (mid - 5, mid + 3):
                for a, b in ((0,0),(1,0),(0,1),(1,1),(0,2),(1,2)): c.put(X+a, ey+b, 'eye')
                c.put(X, ey, 'white')
            ms.blush(c, mid, ey + 3, 6, 2); c.pts([(-1,0),(0,1),(1,0)], 'eye', mid, ey + 3)
    return c.im.crop((0, 0, n, n))

def sprite48():
    im = ms.frame(); px = im.load()
    for y in range(48):
        for x in range(48):
            if px[x, y] == ms.SHADOW: px[x, y] = (0, 0, 0, 0)
    bb = im.getbbox(); cimg = im.crop(bb); w, h = cimg.size; n = max(w, h) + 2
    sq = Image.new('RGBA', (n, n), (0,0,0,0)); sq.paste(cimg, ((n-w)//2, (n-h)//2))
    out48 = Image.new('RGBA', (48, 48), (0,0,0,0)); out48.paste(sq, ((48-n)//2, (48-n)//2))
    return sq, out48

if __name__ == '__main__':
    sq, s48 = sprite48()
    k = 1024 // sq.width; big = sq.resize((sq.width*k, sq.width*k), Image.NEAREST)
    src = Image.new('RGBA', (1024, 1024), (0,0,0,0)); src.paste(big, ((1024-big.width)//2, (1024-big.height)//2))
    src.save(os.path.join(HERE, 'icon-src.png'))
    sm = {n: small(n) for n in (16, 24, 32)}
    if '--ico' in sys.argv:
        def up(im, n): return im.resize((n, n), Image.NEAREST)
        s64 = up(sq, sq.width*1) ; s64 = Image.new('RGBA', (64, 64), (0,0,0,0)); s64.paste(up(s48, 64) if False else s48.resize((64,64), Image.NEAREST) , (0, 0))
        s256 = Image.new('RGBA', (256, 256), (0,0,0,0)); b = sq.resize((sq.width*7, sq.width*7), Image.NEAREST); s256.paste(b, ((256-b.width)//2, (256-b.height)//2))
        frames = [sm[16], sm[24], sm[32], s48, s64, s256]
        s256.save(os.path.join(ICONS, 'icon.ico'), sizes=[(f.width, f.height) for f in frames], append_images=frames[:-1])
        sm[32].save(os.path.join(ICONS, '32x32.png'))
        s64.save(os.path.join(ICONS, '64x64.png'))
    sheet = Image.new('RGBA', (16*8+24*8+32*8+48*8+40, 48*8), (40, 20, 40, 255)); x = 0
    for im in (sm[16], sm[24], sm[32], s48):
        sheet.alpha_composite(im.resize((im.width*8, im.height*8), Image.NEAREST), (x, 0)); x += im.width*8 + 10
    sheet.save('/tmp/icon/small_check.png')
