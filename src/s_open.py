# -*- coding: utf-8 -*-
"""序幕：评论洪流 → 开机 → 片名。"""
import numpy as np
from PIL import Image, ImageDraw

import design as G
import sutil as U
from design import (W, H, INK, PAPER, PAPER2, DIM, AMBER, RED, CYAN, WHITE,
                    sans, mono, serif, text, text_w, cover, plate, rule, solid,
                    seg, clamp01, lerp, eo_expo, eo_quart, eo_cubic, eio,
                    pulse, grain, contrast, wave_mask, paste_mask)
import data as D

POS_CARD = "20-15-20"     # Liza：今年看到最感动
NEG_CARD = "20-14-04"     # 未注销：别说复制第 1 季

PAPER_INK = (126, 116, 95)    # 印在纸上的暖灰褐

COL_X, COL_W = 96, 700
CLIP_Y0, CLIP_Y1 = 84, 906

STACK = ["20-09-31", "20-13-40", "20-15-20", "20-11-25", "20-14-25",
         "20-09-48", "20-16-19", "20-12-29", "20-13-18", "20-14-04",
         "20-10-59", "20-16-29", "20-12-14", "20-15-54"]


def _stack():
    out, y = [], 0.0
    for i, k in enumerate(STACK):
        p = U.cf(k)
        src = U.comment_crop(p)
        h = int(round(src.height * COL_W / src.width))
        out.append((U.card(p, COL_W, h, key="col%d" % i), h))
        y += h + 24
    return out, y


# ------------------------------------------------------------------ 焦点卡：按内容定高
_TEXT_TOP = 152      # 正文第一行之上（头像 / 昵称之下）
_FIT = {}


def _fit(path, w, key=None, top=_TEXT_TOP, pad=18):
    """按目标宽度缩放整张正文区，用内容自然高度当卡片高度——绝不硬裁行。"""
    k = (path, w, key, top, pad)
    if k in _FIT:
        return _FIT[k]
    src = U.comment_crop(path, top, 0)
    s = w / float(src.width)
    im = src.resize((w, max(1, int(round(src.height * s)))), Image.LANCZOS)
    a = np.asarray(im, np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    rows = (a < 190).sum(1)
    ys = np.where(rows > 2)[0]
    bot = im.height if len(ys) == 0 else min(im.height, int(ys[-1]) + 1 + pad)
    out = im.crop((0, 0, w, max(1, bot)))
    _FIT[k] = out
    return out


_ST = None


def _vel(t):
    if t < 3.26:
        return 330.0
    if t < 3.64:
        return 330.0 * (1 - (t - 3.26) / 0.38)
    if t < 6.14:
        return 24.0
    if t < 6.40:
        return 24.0 + 760.0
    if t < 6.72:
        return 784.0 * (1 - (t - 6.40) / 0.32)
    if t < 8.60:
        return 20.0
    if t < 8.86:
        return 20.0 + 1400.0
    if t < 9.10:
        return 1420.0 * (1 - (t - 8.86) / 0.24)
    return 0.0


_SCROLL = None


def _scroll():
    global _SCROLL
    if _SCROLL is None:
        n = int(D.DUR * 30) + 4
        v = np.array([_vel((i + 0.5) / 30.0) for i in range(n)], np.float64)
        _SCROLL = np.cumsum(v) / 30.0
    return _SCROLL


# ------------------------------------------------------------------ 评论洪流
def open_(c, t, idx):
    global _ST
    if _ST is None:
        _ST = _stack()
    stack, TH = _ST
    d = ImageDraw.Draw(c)

    hero = None
    if 3.64 <= t < 6.14:
        hero = "pos"
    elif 6.14 <= t < 8.80:
        hero = "neg"

    sc = _scroll()
    off = float(sc[min(len(sc) - 1, idx)])
    dimk = 1.0
    if hero:
        t0 = 3.64 if hero == "pos" else 6.14
        dimk = lerp(1.0, 0.16, eo_quart(seg(t, t0, t0 + 0.30)))
    if t >= 8.80:
        dimk = 0.0

    base = off % TH
    for rep in (0, 1):
        y = CLIP_Y0 + rep * TH - base
        for im, h in stack:
            if y > CLIP_Y1:
                break
            if y + h >= CLIP_Y0 and y < CLIP_Y1 and dimk > 0.02:
                yy = int(y)
                top = max(CLIP_Y0, yy)
                bot = min(CLIP_Y1, yy + h)
                if bot > top:
                    src = im.crop((0, top - yy, im.width, bot - yy))
                    c.paste(U.cardfade(src, dimk), (COL_X, top))
                    if dimk > 0.5:
                        d.rectangle([COL_X, top, COL_X + COL_W - 1, bot - 1],
                                    outline=(44, 39, 32), width=2)
            y += h + 24

    if dimk > 0.5:
        d.rectangle([0, CLIP_Y0 - 1, W, CLIP_Y0], fill=(30, 27, 22))

    _words(c, d, t)

    if hero:
        _hero_one(c, d, t, hero)
    elif t >= 8.80:
        _dual(c, d, t)




def _words(c, d, t):
    pa = clamp01((t - 1.0) / 0.5)
    if pa <= 0:
        return
    # 8.80 起：两派分开站到各自一边，字缩小
    psep = 1.0 if t >= 8.80 else 0.0
    size = lerp(176, 132, psep)
    f = sans(size, "bold")
    x1 = lerp(962, 96, psep)
    y1 = lerp(296, 326, psep)
    x2 = lerp(962, 1064, psep)
    y2 = lerp(646, 326, psep)
    pf = eo_expo(seg(t, 3.64, 4.10))
    pf2 = eo_expo(seg(t, 6.14, 6.60))
    if pf > 0:
        _mixstroke(d, (x1, y1), "喜欢", f, AMBER, (86, 76, 58), pf, 3)
    else:
        d.text((x1, y1), "喜欢", font=f, fill=INK, stroke_width=3,
               stroke_fill=(74, 68, 54), anchor="ls")
    if pf2 > 0:
        _mixstroke(d, (x2, y2), "失望", f, RED, (86, 76, 58), pf2, 3)
    else:
        d.text((x2, y2), "失望", font=f, fill=INK, stroke_width=3,
               stroke_fill=(74, 68, 54), anchor="ls")




def _mixstroke(d, xy, s, font, col_on, col_off, p, sw):
    if p >= 0.999:
        d.text(xy, s, font=font, fill=col_on, anchor="ls")
        return
    d.text(xy, s, font=font, fill=col_on, anchor="ls")
    wdt = int(round(sw * (1 - p)))
    if wdt > 0:
        d.text(xy, s, font=font, fill=INK, stroke_width=wdt, stroke_fill=col_off, anchor="ls")


def _box(c, d, x, y, w, h, pad=18, col=(72, 64, 50)):
    d.rectangle([x - pad, y - pad, x + w + pad, y + h + pad], fill=(9, 8, 6))
    d.rectangle([x - pad, y - pad, x + w + pad, y + h + pad], outline=col, width=2)


def _hero_one(c, d, t, which):
    if which == "pos":
        im = _fit(U.cf(POS_CARD), 820, key="hp", pad=18)
        t0, tag, col = 3.64, "喜欢的人", AMBER
    else:
        im = _fit(U.cf(NEG_CARD), 820, key="hn", pad=18)
        t0, tag, col = 6.14, "失望的人", RED
    p = eo_expo(seg(t, t0, t0 + 0.30))
    x = 96
    y = int(292 + 56 * (1 - p))
    w, h = im.size
    _box(c, d, x, y, w, h)
    c.paste(im, (x, y))
    d.rectangle([x, y, x + w, y + h], outline=(80, 72, 56), width=2)
    U.corner_marks(c, (x, y, w, h), 20, col, 3, inset=18)



def _dual(c, d, t):
    a = eo_expo(seg(t, 8.80, 9.10))
    im1 = _fit(U.cf(POS_CARD), 760, key="hp2", pad=12)
    im2 = _fit(U.cf(NEG_CARD), 760, key="hn2", pad=12)
    y = 350
    off = 250 * (1 - a)
    x1, x2 = int(96 - off), int(1064 + off)
    for im, x in ((im1, x1), (im2, x2)):
        w, h = im.size
        _box(c, d, x, y, w, h, 12)
        c.paste(im, (x, y))
        d.rectangle([x, y, x + w, y + h], outline=(80, 72, 56), width=2)
    if a > 0.55:
        al = (a - 0.55) / 0.45
        d.rectangle([959, 340, 960, 340 + int(400 * al)], fill=(70, 62, 48))
        for i in range(int(4 * al) + 1):
            d.rectangle([956, 340 + i * 100, 963, 344 + i * 100], fill=AMBER)
    # 第一季：一条横向的记忆带
    ps = eo_expo(seg(t, 9.74, 10.18))
    if ps > 0:
        yb = int(700 + 220 * (1 - ps))
        im = G.load("素材_外部/01_口碑截图/海报_第一季.jpg")
        strip = G.cover(im, (0, 0, W, 220), zoom=1.0, fy=0.42)
        c.paste(U.cardfade(strip, 0.44), (0, yb))
        d.rectangle([0, yb, W, yb + 2], fill=(70, 62, 48))
        U.text(d, (96, yb + 172), "大卫", sans(64, "bold"), AMBER, 6.0, alpha=ps)


# ------------------------------------------------------------------ 开机
def boot(c, t, idx):
    """开机：让波形占满画面。字只有一行，而且压在波形上。"""
    d = ImageDraw.Draw(c)

    # 全宽波形，从 11.55 就开始扫，扫满整个下半幅
    pw = eo_quart(seg(t, 11.55, 13.10))
    if pw > 0:
        bx, bw, bh, by = 0, W, 330, 470
        m = G.wave_mask("素材_外部/09_原声带_47首/配乐01_Welcome Back to Night City - 今堀恒雄_wave.png")
        vw = max(2, int(bw * pw))
        sub = m.crop((0, 0, int(m.width * pw), m.height)).resize((vw, bh), Image.LANCZOS)
        lay = Image.new("RGB", (vw, bh), (150, 138, 116))
        c.paste(lay, (bx, by), sub)
        d.rectangle([0, by + bh // 2, vw, by + bh // 2], fill=(120, 110, 92))
        d.rectangle([vw - 2, by - 34, vw - 1, by + bh + 34], fill=AMBER)

    # 封面：从上方出血
    pc = eo_expo(seg(t, 12.20, 12.85))
    if pc > 0:
        bw = 430
        bx, by = 1500, int(-150 + 150 * pc)
        im = G.load("素材_外部/02_原声带/Score封面.jpg")
        plate(c, im, (bx, by, bw, bw), border=(28, 24, 18), bt=3)

    # 一行标题，压在波形上
    a2 = eo_expo(seg(t, 12.55, 13.05))
    if a2 > 0:
        dy = int(30 * (1 - a2))
        G.text_sh(d, (88, 300 + dy), "原声带", sans(150, "bold"), INK, 10.0, off=3, alpha=a2)
        G.text(d, (88 + 504, 300 + dy), "39 首", sans(64, "medium"), PAPER_INK, 6.0, alpha=a2)

    # 三处彩蛋：只留琥珀刻线，不要编号
    for i, tx in enumerate((0.185, 0.472, 0.781)):
        t0 = 14.30 + i * 0.26
        aa = clamp01((t - t0) / 0.20)
        if aa <= 0:
            continue
        x = int(W * tx)
        d.rectangle([x, 470 - 12, x + 3, 470 + 330 + 12], fill=AMBER)
        d.ellipse([x - 7, 470 - 22, x + 9, 470 - 6], fill=AMBER)


# ------------------------------------------------------------------ 片名
def title(c, t, idx):
    """片名：封面从右边出血，字压在它上面。没有注脚，没有章节表。"""
    d = ImageDraw.Draw(c)
    MX = 88

    # 封面：右缘出血，缓慢内推
    p0 = eo_expo(seg(t, 17.44, 18.10))
    if p0 > 0:
        z = lerp(1.10, 1.0, eo_quart(seg(t, 17.44, 19.30)))
        bw = 940
        bx = int(1180 + 160 * (1 - p0))
        im = G.load("素材_外部/02_原声带/Score封面.jpg")
        c.paste(G.cover(im, (bx, -120, bw, 1200), zoom=z, fx=0.5, fy=0.5), (bx, -120))
        d.rectangle([bx, 0, bx + 2, H], fill=AMBER)

    pw = eo_quart(seg(t, 17.40, 17.86))
    rule(c, MX, 250, int(150 * pw), AMBER, 5)

    p2 = eo_expo(seg(t, 17.50, 18.10))
    if p2 > 0:
        dy = 34 * (1 - p2)
        U.text(d, (MX - 4, 396 + dy), "藏在配乐里的", sans(92, "bold"), INK, 6.0, alpha=p2)

    p3 = eo_expo(seg(t, 17.66, 18.28))
    if p3 > 0:
        dy = 60 * (1 - p3)
        f = sans(400, "bold")
        G.text_sh(d, (MX - 18, 812 + dy), "彩蛋", f, INK, -16.0, off=0, alpha=p3)


