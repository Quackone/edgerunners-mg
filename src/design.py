# -*- coding: utf-8 -*-
"""设计系统：色板、字体、绘图基元、颗粒与调色。

════════════════════════════════════════════════════════════
两秒法则（本片唯一的美学纪律）

观众在一个版面上只会停留一到两秒，而且多半在手机上看。
由此推出三条，违反任何一条就是在做海报，不是在做视频：

1. 一个镜头只有一个可读层。
   两秒内人只能读懂一样东西。字号 < 40px 的中文、< 34px 的拉丁文
   在手机上是看不见的——它不是在传达信息，是在给版面配重。
   所以：不许"大字 + 小字注脚"。注脚是海报语法，它假设观众会停下来读。

2. 空出来的地方不给文字，给三样东西：
   尺寸（主角做到出血，让画面被"物体"占满）
   运动（推镜/横扫/走带/切片/替换，画面里必须一直有东西在动）
   材质（照片视频铺满，字压在画面上，而不是字下面垫一块干净的白）

3. 真需要留白就真的留白，但必须由运动支撑——
   一个慢慢推近的镜头、一段横扫、一个逐渐熄灭的东西。
   静止的空版是海报；运动中的空版才是节奏。

推论：全片"大字复述"每段至多一次，用来打点。字幕已经说过的话，
不要再在画面上说一遍——那是把观众当读者。
════════════════════════════════════════════════════════════
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
ASSETS = os.path.join(ROOT, "assets")
WORK = os.path.join(ROOT, "work")

W, H = 1920, 1080
FPS = 30

# ---------------------------------------------------------------- 色板
INK    = (18, 15, 11)
INK2   = (30, 26, 20)
PAPER  = (232, 223, 201)
PAPER2 = (211, 199, 173)
DIM    = (140, 130, 112)
AMBER  = (255, 176, 46)
RED    = (226, 64, 31)
CYAN   = (72, 208, 214)
WHITE  = (247, 242, 230)
BAND   = (11, 9, 6)

BAND_TOP = 922


# ---------------------------------------------------------------- 字体
_FC = {}


def _f(name, size):
    key = (name, int(size))
    if key in _FC:
        return _FC[key]
    path = os.path.join(FONTS, name)
    f = ImageFont.truetype(path, int(size))
    _FC[key] = f
    return f


def sans(size, weight="regular"):
    return _f({"regular": "NotoSansSC-Regular.otf",
               "medium": "NotoSansSC-Medium.otf",
               "bold": "NotoSansSC-Bold.otf"}[weight], size)


def serif(size):
    return _f("SourceHanSerif-Heavy.ttf", size)


def mono(size, bold=False):
    return _f("consolab.ttf" if bold else "consola.ttf", size)


# ---------------------------------------------------------------- 数学
def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, a, b):
    """t 在 [a,b] 内的归一化进度，含边界钳制。"""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp01((t - a) / (b - a))


def eo_quart(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 4


def eo_expo(x):
    x = clamp01(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def eo_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ei_cubic(x):
    x = clamp01(x)
    return x ** 3


def ei_expo(x):
    x = clamp01(x)
    return 0.0 if x <= 0 else 2 ** (10 * (x - 1))


def eio(x):
    x = clamp01(x)
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.10):
    x = clamp01(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def steps(x, n):
    """量化：把连续进度切成 n 级台阶（数字世界的运动方式）。"""
    if n <= 0:
        return clamp01(x)
    return min(1.0, np.floor(clamp01(x) * n + 0.5) / n)


def pulse(t, a, b, fade=0.12):
    """在 [a,b] 区间内为 1，两端带快速淡入淡出。"""
    if t < a or t > b:
        return 0.0
    return min(clamp01((t - a) / fade), clamp01((b - t) / fade))


# ---------------------------------------------------------------- 文字
def _adv(font, s, tracking=0.0):
    if not s:
        return 0.0
    w = font.getlength(s)
    return w + tracking * (len(s) - 1)


def text(d, xy, s, font, fill, tracking=0.0, anchor="ls", alpha=255):
    """带字距的文本。anchor 只支持 'l*' 系（左对齐）+ 垂直 l/m/s/a。"""
    if alpha <= 0 or not s:
        return
    if isinstance(fill, tuple) and len(fill) == 3 and alpha < 255:
        fill = fill + (int(alpha),)
    x, y = xy
    if anchor[0] == "r":
        x -= _adv(font, s, tracking)
    elif anchor[0] == "m":
        x -= _adv(font, s, tracking) / 2
    va = anchor[1]
    bb = font.getbbox("国Hg")
    asc, desc = font.getmetrics()
    if va == "s":          # y 是基线
        pass
    elif va == "t":        # y 是顶部
        y = y + asc
    elif va == "m":        # y 是视觉中心
        y = y + (asc + desc) / 2 - desc * 0.35
    elif va == "a":        # y 是 bbox 顶部
        y = y - bb[1]
    if tracking == 0:
        d.text((x, y), s, font=font, fill=fill, anchor="ls")
    else:
        cx = x
        for ch in s:
            d.text((cx, y), ch, font=font, fill=fill, anchor="ls")
            cx += font.getlength(ch) + tracking


def text_w(font, s, tracking=0.0):
    return _adv(font, s, tracking)


def wrap(font, s, maxw, tracking=0.0):
    """按像素宽折行，返回行列表（不拆标点、不拆英文词）。"""
    out, cur = [], ""
    for ch in s:
        if _adv(font, cur + ch, tracking) > maxw and cur:
            cut = len(cur)
            while cut > 1 and cur[cut - 1] in "，。、；：！？）」』":
                cut -= 1
            out.append(cur[:cut])
            cur = cur[cut:] + ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out or [""]


# ---------------------------------------------------------------- 材质底
_PAPER_CACHE = {}


def paper(size=(W, H), seed=7):
    key = (size, seed)
    if key in _PAPER_CACHE:
        return _PAPER_CACHE[key].copy()
    rng = np.random.default_rng(seed)
    w, h = size
    base = np.empty((h, w, 3), np.float32)
    base[:] = PAPER
    # 极轻的大尺度明暗（纸张厚度不匀）
    k = 6
    small = rng.normal(0, 1, (h // k + 2, w // k + 2)).astype(np.float32)
    lay = Image.fromarray(((small - small.min()) / (float(small.max() - small.min()) + 1e-6) * 255).astype(np.uint8))
    lay = lay.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    lo = np.asarray(lay, np.float32)
    lo = (lo - lo.mean()) / (lo.std() + 1e-6)
    base += (lo * 1.25)[:, :, None]
    # 细颗粒
    base += rng.normal(0, 0.95, (h, w, 1)).astype(np.float32)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    fr = np.random.default_rng(seed + 1)
    for _ in range(int(w * h / 9000)):
        x = fr.uniform(0, w)
        y = fr.uniform(0, h)
        ln = fr.uniform(4, 26)
        a = fr.uniform(-0.16, 0.16)
        d.line([(x, y), (x + ln, y + ln * a)], fill=(156, 144, 122, int(fr.integers(5, 13))), width=1)
    _PAPER_CACHE[key] = img
    return img.copy()


def wave_mask(rel):
    """取波形图的 alpha 作为形状遮罩（L 模式）。"""
    p = rel if os.path.isabs(rel) else os.path.join(ASSETS, rel)
    im = Image.open(p).convert("RGBA")
    return im.split()[-1]


def paste_mask(canvas, mask, box, col, alpha=1.0):
    x, y, w, h = [int(round(v)) for v in box]
    if w <= 0 or h <= 0:
        return
    m = mask.resize((w, h), Image.LANCZOS)
    if alpha < 1:
        m = m.point(lambda v: int(v * alpha))
    lay = Image.new("RGB", (w, h), col)
    canvas.paste(lay, (x, y), m)


_VIG = {}


def vignette(img, strength=0.22):
    key = (img.size, strength)
    if key not in _VIG:
        w, h = img.size
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = w / 2, h / 2
        r = np.sqrt(((xx - cx) / (w * 0.62)) ** 2 + ((yy - cy) / (h * 0.62)) ** 2)
        m = np.clip(1.0 - strength * np.clip(r - 0.42, 0, None) ** 1.5, 0, 1)
        _VIG[key] = m.astype(np.float32)
    m = _VIG[key]
    a = np.asarray(img, np.float32) * m[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


_GRAIN_BANK = []


def _grain_bank(n=10, size=384):
    if _GRAIN_BANK:
        return _GRAIN_BANK
    for k in range(n):
        rng = np.random.default_rng(1000 + k)
        t = rng.normal(0, 1, (size, size)).astype(np.float32)
        # 略去极端值，让颗粒不刺眼
        t = np.clip(t, -2.6, 2.6)
        _GRAIN_BANK.append(t)
    return _GRAIN_BANK


def grain_tile(h, w, seed, amount=1.0, chroma=0.0):
    """拼贴缓存颗粒，返回 (h,w,1) 或 (h,w,3) 的增量。"""
    bank = _grain_bank()
    t = bank[seed % len(bank)]
    th, tw = t.shape
    oy = (seed * 97) % th
    ox = (seed * 61) % tw
    reps_y = h // th + 2
    reps_x = w // tw + 2
    big = np.tile(t, (reps_y, reps_x))[oy:oy + h, ox:ox + w]
    out = big[:, :, None] * amount
    if chroma > 0:
        t2 = bank[(seed + 3) % len(bank)]
        b2 = np.tile(t2, (reps_y, reps_x))[oy:oy + h, ox:ox + w][:, :, None] * amount * chroma
        out = out + b2
    return out


def grain(img, seed, amount=8.0, chroma=0.35):
    a = np.asarray(img, np.float32)
    h, w = a.shape[:2]
    a = a + grain_tile(h, w, seed, amount, chroma)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- 图像处理
def cover(img, box, zoom=1.0, fx=0.5, fy=0.5):
    """把 img 以 cover 方式填进 box=(x,y,w,h)。zoom>1 放大，fx/fy 为取景中心。"""
    x, y, bw, bh = box
    bw, bh = int(round(bw)), int(round(bh))
    if bw <= 0 or bh <= 0:
        return None
    iw, ih = img.size
    s = max(bw / iw, bh / ih) * zoom
    nw, nh = max(bw, int(round(iw * s))), max(bh, int(round(ih * s)))
    im = img.resize((nw, nh), Image.LANCZOS)
    cx = (nw - bw) * clamp01(fx)
    cy = (nh - bh) * clamp01(fy)
    return im.crop((int(cx), int(cy), int(cx) + bw, int(cy) + bh))


def desat(img, amt=1.0):
    if amt <= 0:
        return img
    a = np.asarray(img.convert("RGB"), np.float32)
    g = a @ np.array([0.299, 0.587, 0.114], np.float32)
    a = a + (g[:, :, None] - a) * amt
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def contrast(img, amt=1.0, pivot=118.0):
    if abs(amt - 1) < 1e-3:
        return img
    a = np.asarray(img.convert("RGB"), np.float32)
    a = (a - pivot) * amt + pivot
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def tint(img, col, amt=0.18):
    if amt <= 0:
        return img
    a = np.asarray(img.convert("RGB"), np.float32)
    c = np.array(col, np.float32)
    a = a * (1 - amt) + c * amt
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def duotone(img, dark, light, amt=1.0):
    a = np.asarray(img.convert("RGB"), np.float32)
    g = (a @ np.array([0.299, 0.587, 0.114], np.float32)) / 255.0
    g = np.clip(g, 0, 1)
    g = g ** 0.92
    d = np.array(dark, np.float32)
    l = np.array(light, np.float32)
    out = d + (l - d) * g[:, :, None]
    if amt < 1:
        out = a * (1 - amt) + out * amt
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def lum(img):
    return (np.asarray(img.convert("RGB"), np.float32) @ np.array([0.299, 0.587, 0.114], np.float32))


def pixelate(img, blocks):
    """块状量化：blocks 越小越碎。"""
    blocks = max(1, int(blocks))
    if blocks <= 1:
        return img
    w, h = img.size
    small = img.resize((max(1, w // blocks), max(1, h // blocks)), Image.BOX)
    return small.resize((w, h), Image.NEAREST)


def posterize(img, levels=6):
    a = np.asarray(img.convert("RGB"), np.float32)
    q = 255.0 / (levels - 1)
    a = np.round(a / q) * q
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- 图像缓存
_IC = {}


def load(rel, mode="RGB"):
    key = (rel, mode)
    if key in _IC:
        return _IC[key]
    p = rel if os.path.isabs(rel) else os.path.join(ASSETS, rel)
    im = Image.open(p)
    im = im.convert("RGBA" if mode == "RGBA" else "RGB")
    _IC[key] = im
    return im


# ---------------------------------------------------------------- 基元
def plate(canvas, img, box, border=None, bt=2, shadow=False):
    """把图贴进 box，可选硬边描边。"""
    p = cover(img, box)
    if p is None:
        return
    canvas.paste(p, (int(box[0]), int(box[1])))
    if border:
        d = ImageDraw.Draw(canvas)
        x, y, w, h = box
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=border, width=bt)


def solid(canvas, box, col):
    x, y, w, h = [int(round(v)) for v in box]
    if w <= 0 or h <= 0:
        return
    ImageDraw.Draw(canvas).rectangle([x, y, x + w - 1, y + h - 1], fill=col)


def rule(canvas, x, y, w, col, th=1):
    w = int(round(w))
    if w <= 0:
        return
    ImageDraw.Draw(canvas).rectangle([x, y, x + w - 1, y + th - 1], fill=col)


def vrule(canvas, x, y, h, col, th=1):
    h = int(round(h))
    if h <= 0:
        return
    ImageDraw.Draw(canvas).rectangle([x, y, x + th - 1, y + h - 1], fill=col)


def hatch(canvas, box, col, gap=10, th=2, diag=1):
    """斜线填充块。"""
    d = ImageDraw.Draw(canvas)
    x, y, w, h = box
    d.rectangle([x, y, x + w, y + h], fill=None, outline=None)
    step = gap
    off = -(h + w)
    i = off
    while i < w + h:
        if diag > 0:
            d.line([(x + i, y + h), (x + i + h, y)], fill=col, width=th)
        else:
            d.line([(x + i, y), (x + i + h, y + h)], fill=col, width=th)
        i += step
    # 裁掉越界部分
    return


def clipbox(canvas, box):
    return canvas.crop((int(box[0]), int(box[1]), int(box[0] + box[2]), int(box[1] + box[3])))


def paste_clip(canvas, im, box):
    canvas.paste(im, (int(box[0]), int(box[1])))


def reg_mark(canvas, x, y, s=14, col=AMBER, th=2):
    """对位十字标。"""
    d = ImageDraw.Draw(canvas)
    d.line([x - s, y, x + s, y], fill=col, width=th)
    d.line([x, y - s, x, y + s], fill=col, width=th)


def grid(canvas, step=48, col=(56, 50, 40), alpha=26, x0=0, y0=0, x1=None, y1=None):
    x1 = W if x1 is None else x1
    y1 = H if y1 is None else y1
    d = ImageDraw.Draw(canvas, "RGBA")
    x = x0
    while x <= x1:
        d.line([(x, y0), (x, y1)], fill=col + (alpha,), width=1)
        x += step
    y = y0
    while y <= y1:
        d.line([(x0, y), (x1, y)], fill=col + (alpha,), width=1)
        y += step


def text_sh(d, xy, s, font, fill, tracking=0.0, sh=None, off=3, anchor="ls", alpha=255):
    """带硬阴影的字，用于压在人像/照片上的标题。"""
    sh = sh or INK
    x, y = xy
    a = anchor
    for dx, dy in ((off, off), (off, 0), (0, off)):
        text(d, (x + dx, y + dy), s, font, sh, tracking, anchor=a, alpha=alpha)
    text(d, (x, y), s, font, fill, tracking, anchor=a, alpha=alpha)


def two_part(d, xy, a, b, fa, fb, col, colb=None, ta=0.0, tb=2.0, gap=14, anchor="ls", alpha=255):
    """拉丁用等宽、中文用黑体，左右拼在一行。"""
    x, y = xy
    wa = _adv(fa, a, ta)
    wb = _adv(fb, b, tb)
    if anchor[0] == "r":
        x -= (wa + (gap + wb if b else 0))
    elif anchor[0] == "m":
        x -= (wa + (gap + wb if b else 0)) / 2
    if a:
        text(d, (x, y), a, fa, col, ta, alpha=alpha)
    if b:
        text(d, (x + wa + gap, y), b, fb, colb or col, tb, alpha=alpha)


def blur(img, r=18.0):
    if r <= 0:
        return img
    return img.filter(ImageFilter.GaussianBlur(r))


def overlay(canvas, color, amt):
    """整帧压一层色。"""
    return Image.blend(canvas.convert("RGB"), Image.new("RGB", canvas.size, color), amt)
