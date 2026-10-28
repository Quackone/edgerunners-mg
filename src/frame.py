# -*- coding: utf-8 -*-
"""画框层：底色、HUD、字幕带、字幕。场景只画自己的内容，这一层负责全片一致的外框。"""
import numpy as np
from PIL import Image, ImageDraw

import data as D
from design import (W, H, INK, INK2, PAPER, PAPER2, DIM, AMBER, RED, CYAN, WHITE,
                    BAND, BAND_TOP, sans, serif, mono, text, text_w, wrap,
                    paper, seg, eo_quart, eo_expo, clamp01, lerp, rule, vrule)

MX = 88
HUD_Y = 52

CAP_SIZE = 37
CAP_MAXW = 1420
CAP_LH = 52


# ------------------------------------------------------------------ 底色
_GROUNDS = {}


def ground(kind="paper", t=None, dark=0.0, seed=7):
    """kind: paper / ink / plate。返回新画布。"""
    if kind == "paper":
        im = paper(seed=seed)
        if dark > 0:
            a = np.asarray(im, np.float32)
            a = a * (1 - dark)
            im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        return im
    return Image.new("RGB", (W, H), INK)


# ------------------------------------------------------------------ HUD
def hud(canvas, t, on_dark, rev=1.0, sec=None):
    """只留一道 3px 琥珀短线。序号、曲目名那套全删——没有数字，没有字母。"""
    if rev <= 0.001:
        return
    d = ImageDraw.Draw(canvas)
    w = int(round(26 * rev))
    if w <= 0:
        return
    d.rectangle([MX, HUD_Y - 2, MX + w - 1, HUD_Y], fill=AMBER)


def section_at(t):
    lst = D.SECTIONS
    for i, s in enumerate(lst):
        if s[1] <= t < s[2]:
            return {"id": s[0], "t0": s[1], "t1": s[2], "code": s[3],
                    "name": s[4], "idx": i + 1}
    s = lst[-1]
    return {"id": s[0], "t0": s[1], "t1": s[2], "code": s[3], "name": s[4], "idx": len(lst)}


# ------------------------------------------------------------------ 字幕带
def band(canvas, t, rev=1.0, dark_ground=False, alpha=1.0):
    """底部字幕带。rev=0 时整条沉在画外。"""
    if rev <= 0.001:
        return
    h = int(round(158 * rev))
    y0 = H - h
    d = ImageDraw.Draw(canvas, "RGBA")
    # 带体
    d.rectangle([0, y0, W, H], fill=BAND + (int(255 * alpha),))
    if rev < 0.999:
        return
    # 上沿 1px
    d.rectangle([0, y0, W, y0], fill=(72, 65, 53, 255))
    # 进度
    p = clamp01(t / D.DUR)
    xp = int(W * p)
    d.rectangle([0, y0 - 1, xp, y0], fill=AMBER + (255,))
    # 刻线：全片秒刻度
    for s in range(0, int(D.DUR) + 1, 2):
        x = int(W * s / D.DUR)
        maj = (s % 20 == 0)
        d.rectangle([x, y0 + 1, x, y0 + (10 if maj else 5)],
                    fill=(134, 122, 102, 255) if maj else (78, 71, 59, 255))
    # 幕界
    for code, a0, a1 in D.ACTS:
        x = int(W * a0 / D.DUR)
        d.rectangle([x, y0 + 1, x, y0 + 15], fill=(170, 120, 40, 255))
    # 播放头
    d.polygon([(xp - 5, y0 - 12), (xp + 5, y0 - 12), (xp, y0 - 4)], fill=AMBER + (255,))
    # 右下署名
    text(d, (W - 48, H - 22), "YURI0", mono(17), (196, 186, 166), 3.0, anchor="rs")
    d.rectangle([W - 40, H - 29, W - 34, H - 23], fill=AMBER + (255,))


# ------------------------------------------------------------------ 字幕
def _cue_at(t):
    for c in D.CUES:
        if c["t0"] <= t < c["t1"]:
            return c
    return None


def caption(canvas, t, centered=True, col=None):
    c = _cue_at(t)
    if not c:
        return
    lines = c["lines"]
    n = len(lines)
    f = sans(CAP_SIZE, "medium")
    cy = 1000 - (n - 1) * CAP_LH / 2
    d = ImageDraw.Draw(canvas)
    for i, ln in enumerate(lines):
        y = cy + i * CAP_LH
        text(d, (W // 2, y), ln, f, col or WHITE, 1.2, anchor="ms")


def caption_plate(canvas, t):
    """冷开场用：紧跟文字的实底黑条，像素材自带的字幕。"""
    c = _cue_at(t)
    if not c:
        return
    lines = c["lines"]
    n = len(lines)
    f = sans(CAP_SIZE, "medium")
    lh = CAP_LH
    wmax = max(text_w(f, l, 1.2) for l in lines)
    pad = 22
    bw = wmax + pad * 2
    bh = n * lh + 26
    x0 = (W - bw) / 2
    y0 = 1002 - bh / 2
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([x0, y0, x0 + bw, y0 + bh], fill=(8, 7, 5, 214))
    cy = 1000 - (n - 1) * lh / 2
    for i, ln in enumerate(lines):
        text(d, (W // 2, cy + i * lh), ln, f, WHITE, 1.2, anchor="ms")
