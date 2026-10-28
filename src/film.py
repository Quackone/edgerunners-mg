# -*- coding: utf-8 -*-
"""驱动器：把时间点变成一张 1920x1080 的图。纯函数，不碰时钟、不碰文件。"""
import sys
import os
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data as D
import frame as F
import design as G
from design import (W, H, INK, PAPER, AMBER, RED, CYAN, PAPER2, DIM,
                    seg, clamp01, eo_quart, eo_expo, eio, lerp)

import s_open
import s_people
import s_yamaoka
import s_imahori
import s_two
import s_binary
import s_case
import s_end

SCENES = {
    "open": s_open.open_,
    "boot": s_open.boot,
    "title": s_open.title,
    "q1": s_people.q1,
    "who": s_people.who,
    "letgo": s_people.letgo,
    "yamaoka": s_yamaoka.yamaoka,
    "imahori": s_imahori.imahori,
    "five": s_imahori.five,
    "fuse": s_imahori.fuse,
    "two": s_two.two,
    "list": s_two.tracklist,
    "dig": s_binary.dig,
    "ana": s_two.ana,
    "caseA": s_case.case_a,
    "caseB": s_case.case_b,
    "end": s_end.end_,
    "crit": s_end.crit,
    "rebut": s_end.rebut,
    "cliff": s_end.cliff,
    "silence": s_end.silence,
    "outro": s_end.outro,
}

# 底色：纸（模拟/印刷）与墨（数字/工业）的交替就是全片的论点。
GROUND = [
    ("ink",   0.00,  11.42, 0.00),
    ("paper", 11.42, 50.72, 0.00),
    ("ink",   50.72, 78.02, 0.00),
    ("paper", 78.02, 123.14, 0.00),
    ("ink",  123.14, 129.04, 0.00),
    ("ink",  129.04, 140.10, 0.00),
    ("paper",140.10, 148.58, 0.00),
    ("ink",  148.58, 162.90, 0.00),
    ("paper",162.90, 178.42, 0.00),
    ("paper",178.42, 195.40, 0.00),
    ("paper",195.40, 204.62, 0.07),
    ("ink",  204.62, 217.74, 0.00),
    ("paper",217.74, 229.80, 0.00),
]

# 硬切条擦：(t0, t1, 颜色, 方向)
WIPES = [
    (11.42, 11.92, PAPER, "up"),
    (50.72, 51.02, INK,   "ltr"),
    (78.02, 78.32, PAPER, "up"),
    (123.14, 123.40, INK, "rtl"),
    (178.42, 178.70, INK, "down"),
    (217.74, 218.04, PAPER, "up"),
]


def ground_at(t):
    for k, a, b, dk in GROUND:
        if a <= t < b:
            return k, dk
    return GROUND[-1][0], GROUND[-1][3]


def sec_at(t):
    return F.section_at(t)


def _wipe(c, t):
    for t0, t1, col, dr in WIPES:
        if t0 <= t < t1:
            p = eo_quart(seg(t, t0, t1))
            d = ImageDraw.Draw(c)
            bw = int(W * 1.02)
            bh = int(H * 1.02)
            if dr == "up":
                y = int(H - bh * p)
                if y < H:
                    d.rectangle([0, max(0, y), W, H], fill=col)
            elif dr == "down":
                y = int(bh * p)
                if y > 0:
                    d.rectangle([0, 0, W, min(H, y)], fill=col)
            elif dr == "ltr":
                x = int(-bw + bw * p)
                if x > 0:
                    d.rectangle([0, 0, min(W, x), H], fill=col)
            else:
                x = int(W - bw * p)
                if x < W:
                    d.rectangle([max(0, x), 0, W, H], fill=col)
            return


def draw(t, idx):
    t = max(0.0, min(D.DUR - 1e-4, t))
    kind, dark = ground_at(t)
    c = F.ground(kind, dark=dark)
    sec = sec_at(t)
    on_dark = (kind == "ink")

    fn = SCENES.get(sec["id"])
    if fn:
        fn(c, t, idx)

    # HUD 在 11.42 处开机，收尾时关机
    rev = eo_expo(seg(t, 11.42, 12.15)) * (1.0 - eo_quart(seg(t, 217.74, 218.30)))
    F.hud(c, t, on_dark, rev, sec)

    band_rev = eo_expo(seg(t, 11.55, 12.35)) * (1.0 - eo_quart(seg(t, 228.30, 228.85)))
    F.band(c, t, band_rev)

    _wipe(c, t)

    if t < 11.42:
        F.caption_plate(c, t)
    else:
        F.caption(c, t, col=(G.INK if band_rev < 0.45 else None))
    return c
