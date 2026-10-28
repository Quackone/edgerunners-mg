# -*- coding: utf-8 -*-
"""场景共用零件：评论卡池、流动带、冲压入场、标题块。"""
import os
import glob
import numpy as np
from PIL import Image, ImageDraw

import design as G
from design import (W, H, INK, PAPER, PAPER2, DIM, AMBER, RED, CYAN, WHITE,
                    sans, mono, serif, text, text_w, wrap, cover, plate, rule,
                    vrule, solid, seg, clamp01, lerp, eo_expo, eo_quart, eo_cubic,
                    back_out, eio, steps, grain, pixelate)

ASSETS = G.ASSETS
_CM = sorted(glob.glob(os.path.join(ASSETS, "评论", "*.jpg")))


def cf(part):
    for p in _CM:
        if part in os.path.basename(p):
            return p
    raise KeyError(part)


def comment_crop(path, top=118, bot=44):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    return im.crop((22, top, w - 22, h - bot))


_CARD_CACHE = {}


def card(path, w, h, key=None, top=118, bot=44, fy=0.0):
    """按宽度等比缩放后取竖直窗口——绝不横向裁字。"""
    k = (path, w, h, key, top, bot, fy)
    if k in _CARD_CACHE:
        return _CARD_CACHE[k]
    src = comment_crop(path, top, bot)
    s = w / float(src.width)
    nh = int(round(src.height * s))
    im = src.resize((w, max(1, nh)), Image.LANCZOS)
    if nh >= h:
        y = int((nh - h) * fy)
        out = im.crop((0, y, w, y + h))
    else:
        bg = src.getpixel((3, 3))
        out = Image.new("RGB", (w, h), bg)
        out.paste(im, (0, int((h - nh) * fy)))
    _CARD_CACHE[k] = out
    return out


def cardfade(im, k):
    """k=1 原样，k=0 全暗。"""
    if k >= 0.999:
        return im
    a = np.asarray(im, np.float32) * k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ 流动带
def stream(t, widths, gap, speed, offset=0.0, span=3800):
    """一条无限向左流动的带子。返回每张卡的 x。"""
    P = sum(widths) + gap * len(widths)
    x = []
    c = 0.0
    for w in widths:
        p = (c + offset - speed * t) % P
        if p > span:
            p -= P
        x.append(p)
        c += w + gap
    return x


# ------------------------------------------------------------------ 入场
def rise(box, p, dist=90):
    """从下方升起，返回 (dx,dy) 偏移。"""
    return 0, dist * (1 - eo_expo(p))


def stamp_scale(p, from_s=1.06):
    return lerp(from_s, 1.0, eo_expo(p))


def alpha_of(p, a=0.0, b=1.0):
    return clamp01((p - a) / max(1e-6, b - a))


# ------------------------------------------------------------------ 字块
def label(c, x, y, s, col=DIM, size=17, track=4.0, alpha=1.0):
    d = ImageDraw.Draw(c)
    text(d, (x, y), s, mono(size), col, track, alpha=int(255 * alpha))


def tick_label(c, x, y, s, col=AMBER, size=15):
    """带前置小方块的说明标签。"""
    d = ImageDraw.Draw(c)
    d.rectangle([x, y - 7, x + 6, y - 1], fill=col)
    text(d, (x + 14, y), s, mono(size), col, 3.0)


def big(c, x, y, s, size, col=INK, weight="bold", track=-2.0, font=None, anchor="ls", alpha=255):
    f = font or sans(size, weight)
    text(ImageDraw.Draw(c), (x, y), s, f, col, track, anchor=anchor, alpha=alpha)
    return f


def num(c, x, y, s, size, col=AMBER):
    text(ImageDraw.Draw(c), (x, y), s, mono(size, True), col, 0, anchor="ls")


# ------------------------------------------------------------------ 细网格
def grid(c, step=40, col=None, alpha=16, x0=0, y0=0, x1=W, y1=H):
    if col is None:
        col = (120, 110, 92)
    d = ImageDraw.Draw(c, "RGBA")
    x = x0
    while x <= x1:
        d.line([(x, y0), (x, y1)], fill=col + (alpha,), width=1)
        x += step
    y = y0
    while y <= y1:
        d.line([(x0, y), (x1, y)], fill=col + (alpha,), width=1)
        y += step


def corner_marks(c, box, ln=16, col=None, th=2, inset=0):
    if col is None:
        col = AMBER
    d = ImageDraw.Draw(c)
    x, y, w, h = box
    x0, y0, x1, y1 = x - inset, y - inset, x + w + inset, y + h + inset
    for (px, py, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(px, py), (px + dx * ln, py)], fill=col, width=th)
        d.line([(px, py), (px, py + dy * ln)], fill=col, width=th)
