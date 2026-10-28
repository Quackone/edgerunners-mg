# -*- coding: utf-8 -*-
"""第二段：换人（推子）→ 今堀恒雄 → 四大 OP。

纪律：每格只有一个可读层。人像 / 一个名字 / 一条带子。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageChops

import design as G
import sutil as U
import prep
from design import (W, H, INK, PAPER, PAPER2, DIM, AMBER, RED, CYAN, WHITE,
                    sans, mono, text, text_w, cover, plate, rule, vrule, solid,
                    seg, clamp01, lerp, eo_expo, eo_quart, eo_cubic, eio,
                    pulse, grain, contrast, desat, tint)
import data as D

MX = 88
NAME = 150


# ------------------------------------------------------------------ Q1
def q1(c, t, idx):
    d = ImageDraw.Draw(c)
    if t < 24.10:
        _yamaoka(c, d, t)
        return
    if t < 25.24:
        _boom(c, d, t, idx)
        return
    _fader(c, d, t)


def _yamaoka(c, d, t):
    p = eo_expo(seg(t, 20.82, 21.30))
    # 人像：右缘出血，缓慢推近
    z = lerp(1.0, 1.09, eo_quart(seg(t, 19.60, 25.0)))
    bx, bw = 1010, 910
    by = int(-70 + 70 * p)
    im = G.load("素材_外部/03_人物/山冈晃.jpg")
    c.paste(G.cover(im, (bx, by, bw, 1150), zoom=z, fx=0.62, fy=0.40), (bx, by))
    # 人像压边留一条黑，让纸与照片断开
    d.rectangle([bx - 4, 0, bx - 1, H], fill=INK)

    q = eo_expo(seg(t, 21.02, 21.60))
    if q > 0:
        dy = 40 * (1 - q)
        G.text_sh(d, (MX - 6, 600 + dy), "山冈晃", sans(NAME, "bold"), INK, 8.0, off=0, alpha=q)


def _boom(c, d, t, idx):
    tt = t - 24.10
    if tt < 0.20:
        base = G.load("素材_外部/03_人物/山冈晃.jpg")
        bx, bw = 1010, 910
        p = G.cover(base, (bx, 0, bw, 1150), fx=0.62, fy=0.40)
        c.paste(ImageChops.invert(p), (bx, 0))
        d.rectangle([bx - 4, 0, bx - 1, H], fill=AMBER)
        for i in range(6):
            y = int(H * (0.10 + 0.155 * i))
            hh = 10 + (i * 9) % 26
            d.rectangle([0, y, W, y + hh], fill=AMBER)
        return
    fr = prep.frame("sh_fog", idx - int(24.30 * 30))
    c.paste(G.cover(fr, (0, 0, W, H), zoom=1.04), (0, 0))
    ov = Image.new("RGB", (W, H), (10, 12, 12))
    c.paste(Image.blend(c.copy(), ov, 0.26), (0, 0))


def _fader(c, d, t):
    sx = int(lerp(1904, 10, eo_quart(seg(t, 25.30, 26.55))))
    imA = G.load("素材_外部/03_人物/山冈晃.jpg")
    imB = G.load("素材_外部/03_人物/今堀恒雄.jpg")
    a = G.cover(imA, (0, 0, W, H), zoom=1.02, fx=0.60, fy=0.42)
    b = G.cover(imB, (0, 0, W, H), zoom=1.00, fx=0.50, fy=0.09)
    if sx > 1:
        c.paste(a.crop((0, 0, min(W, sx), H)), (0, 0))
    if sx < W - 1:
        c.paste(b.crop((max(0, sx), 0, W, H)), (max(0, sx), 0))
    if 0 < sx < W:
        d.rectangle([sx - 2, 0, sx + 2, H], fill=AMBER)
        d.polygon([(sx - 20, H // 2), (sx - 4, H // 2 - 16), (sx - 4, H // 2 + 16)], fill=AMBER)
        d.polygon([(sx + 20, H // 2), (sx + 4, H // 2 - 16), (sx + 4, H // 2 + 16)], fill=AMBER)

    if t < 25.90:
        G.text_sh(d, (MX - 4, 250), "S01", mono(64, True), AMBER, 3.0, off=4)
        G.text_sh(d, (MX - 6, 400), "山冈晃", sans(124, "bold"), PAPER, 8.0, off=5)
    else:
        G.text_sh(d, (W - MX + 4, 250), "S02", mono(64, True), AMBER, 3.0, off=4, anchor="rs")
        G.text_sh(d, (W - MX + 6, 400), "今堀恒雄", sans(124, "bold"), PAPER, 8.0, off=5, anchor="rs")


# ------------------------------------------------------------------ 今堀是谁
def who(c, t, idx):
    d = ImageDraw.Draw(c)
    if t < 35.48:
        _portrait(c, d, t)
    else:
        _strips(c, d, t, idx)


def _portrait(c, d, t):
    p = eo_expo(seg(t, 28.06, 28.50))
    pin = eo_quart(seg(t, 31.78, 35.30))
    zoom = lerp(1.02, 1.54, pin)
    fx = lerp(0.50, 0.56, pin)
    fy = lerp(0.34, 0.90, pin)
    im = G.load("素材_外部/03_人物/今堀恒雄.jpg")
    bx, bw = 900, 1080
    by = int(-80 + 80 * p)
    c.paste(G.cover(im, (bx, by, bw, 1320), zoom=zoom, fx=fx, fy=fy), (bx, by))
    d.rectangle([bx - 4, 0, bx - 1, H], fill=INK)

    q = eo_expo(seg(t, 28.20, 28.78))
    if q > 0:
        dy = 40 * (1 - q)
        G.text_sh(d, (MX - 6, 620 + dy), "今堀恒雄", sans(NAME, "bold"), INK, 8.0, off=0, alpha=q)


# ------------------------------------------------------------------ 四大 OP
LANES = [
    ("COWBOY BEBOP", "op_bebop", 108),
    ("GHOST IN THE SHELL SAC", "op_gits", 252),
    ("TRIGUN", "op_trigun", 396),
    ("GUNGRAVE", "op_grave", 40),
]
CUE_OPEN = [(35.48, 35.82), (38.00, 38.34), (42.66, 42.98), (43.88, 44.18)]


def _openness(t):
    """同一时刻只有一条带子是主角，上一条收回去。"""
    idx = -1
    for i, (a, b) in enumerate(CUE_OPEN):
        if t >= a:
            idx = i
    if idx < 0:
        return [0.0] * 4, -1
    if idx == 0:
        return [1.0, 0.0, 0.0, 0.0], 0
    sw = eo_quart(seg(t, CUE_OPEN[idx][0], CUE_OPEN[idx][0] + 0.36))
    w = [0.0] * 4
    w[idx - 1] = 1.0 - sw
    w[idx] = sw
    return w, idx


def _strips(c, d, t, idx, collapse=None):
    y0, gap, tot = 104, 12, 800
    w, cur = _openness(t)
    if collapse is not None:
        w = [x * (1 - collapse) for x in w]
    ssum = sum(w)
    base = 116
    extra = tot - 4 * base - 3 * gap
    hs = [(tot - 3 * gap) / 4.0] * 4 if ssum < 0.02 else [base + extra * (x / ssum) for x in w]

    y = y0
    for i, (title, clip, off) in enumerate(LANES):
        h = int(round(hs[i]))
        if h < 2:
            y += h + gap
            continue
        fr = prep.frame(clip, idx - int(35.48 * 30) + off)
        c.paste(G.cover(fr, (0, 0, W, h), fy=0.45), (0, y))
        d.rectangle([0, y, W, y + 1], fill=(16, 14, 10))
        d.rectangle([0, y + h - 2, W, y + h - 1], fill=(16, 14, 10))
        # 只有当下这条配字——全画框只许一个可读层
        if i == cur and w[i] > 0.6:
            a = clamp01((w[i] - 0.6) / 0.4)
            G.text_sh(d, (MX - 4, y + h - 54), title, sans(62, "bold"), PAPER, 5.0, off=5, alpha=a)
        y += h + gap


S2_ON = 44.68
S2_K0 = int(44.50 * 30)
SL_Y = 504


def letgo(c, t, idx):
    """第二季开场动画全屏。这一格没有可读层——画面自己就是论点。

    44.50–44.62：四条带收拢，被裁成一条横线；
    44.56–44.74：同一条线上第二季把缝撕开到底，之后铺满 0..1080 直到 47.26。
    """
    d = ImageDraw.Draw(c)
    fr = G.cover(prep.frame("s2op", idx - S2_K0), (0, 0, W, H))

    if t >= S2_ON:
        c.paste(fr, (0, 0))
        return

    q = eo_quart(seg(t, 44.50, 44.56))
    tmp = c.copy()
    _strips(tmp, ImageDraw.Draw(tmp), t, idx, collapse=q)
    hh = max(2, int(800 * (1 - q)))
    y0 = int(SL_Y - hh / 2)
    c.paste(tmp.crop((0, y0, W, y0 + hh)), (0, y0))

    op = seg(t, 44.50, S2_ON)
    if op <= 0:
        return
    hh = int((H + 120) * op)
    y0, y1 = int(SL_Y - hh / 2), int(SL_Y + hh / 2)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rectangle([0, y0, W, y1], fill=255)
    c.paste(fr, (0, 0), m)
    if op < 1.0:
        d.rectangle([0, y0, W, y0 + 4], fill=AMBER)
        d.rectangle([0, y1 - 4, W, y1], fill=AMBER)
