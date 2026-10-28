# -*- coding: utf-8 -*-
"""第四段：今堀的保守 → 套五套七 → 融合 → 二元对立。

纪律：拍子这一段由"刻度的分组"说话，不由文字说话。
"""
import numpy as np
from PIL import Image, ImageDraw

import design as G
import sutil as U
from design import (W, H, INK, PAPER, PAPER2, DIM, AMBER, RED, CYAN, WHITE,
                    sans, mono, serif, text, text_w, cover, plate, rule, vrule, solid,
                    seg, clamp01, lerp, eo_expo, eo_quart, eo_cubic, eio, ei_expo,
                    pulse, grain, contrast, desat, tint, hatch)
import data as D

MX = 88


# ------------------------------------------------------------------ 保守
def imahori(c, t, idx):
    """保守不需要写出来：颜色一点点退掉，就是保守。"""
    d = ImageDraw.Draw(c)
    if t < 86.20:
        _scrape(c, d, t)
    else:
        _covers(c, d, t)


def _scrape(c, d, t):
    # 一整段一个镜头：慢慢推近，饱和度一路退到零
    p = eo_expo(seg(t, 80.66, 81.14))
    push = eo_quart(seg(t, 80.66, 86.10))
    if t < 84.26:
        zoom = lerp(1.02, 1.20, push)
        fxc, fyc = lerp(0.46, 0.52, push), lerp(0.50, 0.54, push)
        sat = 1.0 - 0.30 * push
    else:
        zoom = lerp(1.24, 1.34, seg(t, 84.26, 86.10))
        fxc, fyc = 0.56, 0.58
        sat = 0.12
    im = G.load("素材_外部/05_设备乐器/image.jpg")
    yy = int(60 * (1 - p))
    pim = G.cover(im, (0, yy, W, H - yy), zoom=zoom, fx=fxc, fy=fyc)
    pim = G.desat(pim, 1.0 - sat)
    if sat < 0.5:
        pim = G.contrast(pim, 1.14)
    c.paste(pim, (0, yy))
    # 一条细线在下方横向扫过，给静止画面一个动作
    if t < 84.26:
        xw = int(W * eo_quart(seg(t, 81.0, 84.2)))
        d.rectangle([0, 864, xw, 868], fill=AMBER)


def _covers(c, d, t):
    """两张唱片缩小成纸上的两件实物：一大块干净的纸，两张反向漂移。

    不说话——封面自己写着名字。留白靠"尺寸（相对纸面变小）+ 运动（反向漂移、
    一张缓慢下沉、内部极慢推近）"撑住，不加任何注脚。
    """
    p = eo_quart(seg(t, 86.20, 86.78))
    u = eio(seg(t, 86.20, 90.66))
    z = lerp(1.0, 1.035, eo_quart(seg(t, 86.20, 90.66)))
    kc = G.load("素材_外部/04_其他作品/专辑_KingCrimson_InTheCourt.jpg")
    zp = G.load("素材_外部/04_其他作品/专辑_Zappa_HotRats.jpg")

    T = 600
    dy = 40 * (1 - p)
    lx = 290 + int(lerp(34, -26, u))
    ly = 126 + int(lerp(0, -12, u) + dy)
    rx = 1030 + int(lerp(-34, 26, u))
    ry = 232 + int(lerp(0, 20, u) + dy)

    sh = ImageDraw.Draw(c, "RGBA")
    for x, y in ((lx, ly), (rx, ry)):
        sh.rectangle([x + 16, y + 16, x + T + 16, y + T + 16], fill=(58, 48, 34, 58))
    c.paste(G.cover(kc, (lx, ly, T, T), zoom=z, fx=0.5, fy=0.44), (lx, ly))
    c.paste(G.cover(zp, (rx, ry, T, T), zoom=z, fx=0.5, fy=0.5), (rx, ry))
    for x, y in ((lx, ly), (rx, ry)):
        d.rectangle([x, y, x + T - 1, y + T - 1], outline=(52, 46, 36), width=2)


# ------------------------------------------------------------------ 套五套七
def five(c, t, idx):
    d = ImageDraw.Draw(c)
    by, bh = 470, 300

    if t < 93.40:
        grp = 4.0
    elif t < 94.42:
        grp = lerp(4, 5, eo_quart(seg(t, 93.40, 93.72)))
    else:
        grp = lerp(5, 7, eo_quart(seg(t, 94.42, 94.74)))
    gi = 4 if t < 93.40 else (5 if t < 94.42 else 7)
    n = max(2, int(round(grp * 2)))

    # 条子从底部升起来
    pr = eo_expo(seg(t, 90.66, 91.16))
    yb = int(1150 - (1150 - by) * pr)
    if pr < 1.0:
        d.rectangle([0, yb, W, yb + bh], fill=INK)
        d.rectangle([0, yb, W, yb + 4], fill=AMBER)
        return

    d.rectangle([0, by, W, by + bh], fill=INK)
    d.rectangle([0, by, W, by + 4], fill=AMBER)

    x0, x1 = MX, W - MX - 150
    span = x1 - x0
    step = span / float(n)
    # 重拍像节拍器一样起伏：静止的刻度条才是海报
    beat = 0.5 + 0.5 * np.sin(2 * np.pi * 1.45 * t)
    for i in range(n + 1):
        x = x0 + step * i
        accent = (abs((i / float(gi)) - round(i / float(gi))) < 1e-6)
        hh = (96 + 22 * beat) if accent else 42
        d.rectangle([x, by + 34, x + (6 if accent else 2), by + 34 + hh],
                    fill=AMBER if accent else (150, 140, 120))

    for gstart in range(0, n - 1, gi):
        gend = min(n, gstart + gi)
        bx0 = x0 + step * gstart + 4
        bx1 = x0 + step * gend - 4
        d.rectangle([bx0, by + 168, bx1, by + 171], fill=(186, 176, 154))
        d.rectangle([bx0, by + 168, bx0 + 3, by + 180], fill=(186, 176, 154))
        d.rectangle([bx1 - 3, by + 168, bx1, by + 180], fill=(186, 176, 154))
        U.text(d, ((bx0 + bx1) / 2, by + 232), "×%d" % (gend - gstart),
               mono(44, True), (206, 196, 174), 2.0, anchor="ms")

    # 右侧大数字：分组变了它就变
    num = str(gi)
    jump = eo_expo(seg(t, 93.40, 93.62)) if t < 94.42 else eo_expo(seg(t, 94.42, 94.64))
    d.text((W - MX + 26, by + bh - 26), num, font=mono(190, True), fill=PAPER, anchor="rs")

    # 95.20 起：拍子散掉
    if t >= 95.20:
        ph = t - 95.20
        for i in range(n + 1):
            x = x0 + step * i
            jx = int(30 * np.sin(ph * 9.0 + i * 1.3))
            d.rectangle([x + jx, by + 34, x + jx + 3, by + 168], fill=(232, 223, 201))
            d.rectangle([x, by + 34, x + 3, by + 168], fill=INK)
        # 数字开始乱跳
        k = int((ph * 7.0)) % 9
        d.rectangle([W - MX - 30, by + 20, W, by + bh - 10], fill=INK)
        d.text((W - MX + 26, by + bh - 26), str((k * 3 + 4) % 9 + 2),
               font=mono(190, True), fill=RED, anchor="rs")

    # 只有分组变化时才出现"套五套七"
    if 93.36 <= t < 95.20:
        a = clamp01((t - 93.36) / 0.26)
        U.text(d, (MX, 396), "套五", sans(132, "bold"), INK, 8.0, alpha=a)
        a2 = clamp01((t - 94.38) / 0.26)
        U.text(d, (MX + 420, 396), "套七", sans(132, "bold"), AMBER, 8.0, alpha=a2)


# ------------------------------------------------------------------ 融合
def fuse(c, t, idx):
    d = ImageDraw.Draw(c)
    if t < 104.96:
        _meld(c, d, t)
    else:
        _war(c, d, t)


def _meld(c, d, t):
    p = eo_quart(seg(t, 97.60, 98.60))
    halfw = 830
    xL = MX
    xR = W - MX - halfw
    shift = int(40 * (1 - p))
    y, h = 120, 700

    d.rectangle([xL, y, xL + halfw, y + h], fill=INK)
    im = G.load("素材_外部/05_设备乐器/images.jpg")
    c.paste(G.cover(im, (xR + shift, y, halfw, h), zoom=1.05, fx=0.5, fy=0.5), (xR + shift, y))

    xm = xR + shift
    S = 110
    if p > 0.25:
        for i in range(6):
            y0 = y + i * (h / 6.0)
            y1 = y0 + h / 6.0
            if i % 2 == 0:
                d.rectangle([xm - S / 2, y0, xm, y1], fill=PAPER)
            else:
                d.rectangle([xm, y0, xm + S / 2, y1], fill=INK)

    # 一对词，同一基线：VINTAGE 站在黑块里，MODERN 压在照片上（硬阴影保证可读）
    fv = mono(185, True)
    text(d, (xL + (halfw - text_w(fv, "VINTAGE")) / 2, y + 425),
         "VINTAGE", fv, PAPER)
    fm = mono(185, True)
    G.text_sh(d, (xR + (halfw - text_w(fm, "MODERN")) / 2, y + 425),
              "MODERN", fm, PAPER, off=7)


def _war(c, d, t):
    p = eo_quart(seg(t, 106.30, 106.85))
    if p <= 0:
        a = clamp01((t - 105.05) / 0.30)
        U.text(d, (W // 2, 540), "为什么", sans(150, "bold"), INK, 16.0, anchor="ms", alpha=a)
        return

    sx = int(lerp(0, 960, p))
    d.rectangle([0, 0, sx, H], fill=INK)
    if t > 107.20:
        a = clamp01((t - 107.20) / 0.30)
        dz = int(24 * (1 - eo_expo(a)))
        U.text(d, (MX + dz, 560), "数字", sans(250, "bold"), PAPER, 12.0, alpha=a)
        U.text(d, (MX + 10 + dz, 660), "DIGITAL", mono(58), CYAN, 14.0, alpha=a)
        U.text(d, (W - MX - dz, 560), "模拟", sans(250, "bold"), INK, 12.0, anchor="rs", alpha=a)
        U.text(d, (W - MX - 10 - dz, 660), "ANALOG", mono(58), RED, 14.0, anchor="rs", alpha=a)
        d.rectangle([sx - 3, 0, sx + 3, H], fill=AMBER)
