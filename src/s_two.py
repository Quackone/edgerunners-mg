# -*- coding: utf-8 -*-
"""第五段：持机实录（曲目表）/ 数字 / 模拟。

纪律：数字与模拟这两个词就是这半场的全部文字。其余靠雨、波形、照片。
"""
import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import design as G
import sutil as U
import prep
import s_imahori
from design import (W, H, INK, PAPER, PAPER2, DIM, AMBER, RED, CYAN, WHITE,
                    sans, mono, serif, text, text_w, cover, plate, rule, vrule, solid,
                    seg, clamp01, lerp, eo_expo, eo_quart, eo_cubic, eio,
                    pulse, grain, contrast, desat, tint, grid, wave_mask, paste_mask,
                    pixelate, posterize)
import data as D

MX = 88


def _tracks():
    p = os.path.join(G.ASSETS, "素材_外部/09_原声带_47首/titles.txt")
    out = []
    for line in open(p, encoding="utf-8"):
        m = re.match(r"(\d\d)\|.*?p\d\d\s+(\d\d)\.\s*(.+?)\s+-\s*今堀恒雄", line)
        if m:
            out.append((int(m.group(2)), m.group(3).strip()))
    return out


TRACKS = _tracks()


# ------------------------------------------------------------------ 持机实录
# 这一段只有一个镜头：罗曼扛着机器在录。文字一个字都不给——字幕已经说完了。
T_CLIP0 = 110.94          # "数字与模拟的战争"说到这句才切，早切就抢话
T_REV = 120.15            # "索尼的破 VX2000"
T_CLIP1 = 123.14

# 素材 10.3 秒要铺 12.2 秒：放慢到 0.84 倍，既不回绕也不跳帧（手持镜头看不出来）
CLIP_RATE = 309 / 366.0


def two(c, t, idx):
    if t < T_CLIP0:
        # 上一段的数字/模拟对切继续持住，交接在这一句口播落地上
        s_imahori.fuse(c, t, idx)
        return

    push = eo_quart(seg(t, T_CLIP0, T_CLIP1))
    k = int((t - T_CLIP0) * 30.0 * CLIP_RATE)
    fr = prep.frame("roman", k)
    c.paste(G.cover(fr, (0, 0, W, H), zoom=lerp(1.02, 1.07, push), fx=0.5, fy=0.46), (0, 0))

    if t >= T_REV:
        _device(c, t)


# 实物块：预先裁好，按尺寸缓存（0.3 秒的冲压只有 9 个尺寸）
_DEV = {}
_DEV_CROP = (170, 50, 1540, 1180)   # 机身+握机的手，两头都切在画面外
_DEV_W = 850
_DEV_CX, _DEV_CY = 1180, 452      # 居中偏右


def _device_plate(w, h):
    """裁出一块硬边的实拍机身，带一层散开的投影，像从画面里浮起来的东西。"""
    key = (w, h)
    if key in _DEV:
        return _DEV[key]
    src = G.load("素材_外部/05_设备乐器/VX2000_1.jpg").crop(_DEV_CROP)
    plate = src.resize((w, h), Image.LANCZOS)
    pad = 52
    sh = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad, pad, pad + w, pad + h], fill=(4, 3, 2, 210))
    sh = sh.filter(ImageFilter.GaussianBlur(30))
    out = (sh, pad, plate)
    _DEV[key] = out
    return out


def _device(c, t):
    """动画整帧模糊 + 褪色压暗，实物压在上面成为唯一的焦点。"""
    p = seg(t, T_REV, T_REV + 0.30)
    q = eo_quart(p)
    fr = c.copy()
    fr = G.blur(fr, 26.0 * q)
    fr = G.desat(fr, 0.35 * q)
    fr = G.overlay(fr, (8, 7, 5), 0.46 * q)
    c.paste(fr, (0, 0))

    if p <= 0:
        return
    sc = lerp(1.06, 1.0, eo_expo(p))
    w = int(round(_DEV_W * sc))
    h = int(round(_DEV_W * sc * (_DEV_CROP[3] - _DEV_CROP[1]) / (_DEV_CROP[2] - _DEV_CROP[0])))
    sh, pad, plate = _device_plate(w, h)
    x = _DEV_CX - w // 2
    y = _DEV_CY - h // 2
    c.paste(sh, (x - pad + 14, y - pad + 26), sh)
    c.paste(plate, (x, y))
    d = ImageDraw.Draw(c)
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=(24, 20, 15), width=2)


# ------------------------------------------------------------------ 曲目表
def tracklist(c, t, idx):
    d = ImageDraw.Draw(c)
    ROW = 58
    tgt = (23 + 30) / 2.0 - 1
    scroll = lerp(0, tgt, eo_quart(seg(t, 123.20, 125.10)))
    y0 = 250 - int(scroll * ROW)

    for i, (no, name) in enumerate(TRACKS):
        y = y0 + i * ROW
        if y < 190 or y > 900:
            continue
        hot = no in (23, 30)
        if hot and t > 126.10:
            continue
        col = AMBER if no == 23 else (CYAN if no == 30 else (120, 112, 96))
        a = 1.0
        if y < 250:
            a = clamp01((y - 190) / 60.0)
        if y > 800:
            a = clamp01((900 - y) / 100.0)
        U.text(d, (MX, y), "%02d" % no, mono(26), col, 2.0, alpha=a)
        U.text(d, (MX + 90, y), name, mono(30), (210, 202, 184) if hot else (150, 142, 124),
               2.0, alpha=a)
        d.rectangle([MX, y + 20, W - MX, y + 21], fill=(38, 34, 28))

    if t > 126.10:
        p = eo_expo(seg(t, 126.10, 126.55))
        _pair(c, d, p, t)


def _pair(c, d, p, t):
    y, h = 300, 380
    off = int(360 * (1 - p))
    fs = sans(40, "medium")
    for x, no, name, cn, col in ((MX - off, "23", "ANALOG SOLITUDE", "模拟信号的孤独", AMBER),
                                 (W - MX - 830 + off, "30", "DIGITAL PARASITE", "数字寄生虫", CYAN)):
        d.rectangle([x, y, x + 830, y + h], fill=(22, 19, 14))
        d.rectangle([x, y, x + 830, y + h], outline=col, width=4)
        U.text(d, (x + 46, y + 150), no, mono(110, True), col, 0)
        U.text(d, (x + 46, y + 268), name, sans(62, "bold"), PAPER, 5.0)
        U.text(d, (x + 46, y + 338), cn, fs, (183, 172, 149), 6.0)


# ------------------------------------------------------------------ 数字
def dig(c, t, idx):
    d = ImageDraw.Draw(c)
    for x in range(MX, W - MX + 1, 72):
        d.rectangle([x, 0, x, H], fill=(28, 25, 20))

    # 0/1 雨：越下越密
    dens = int(lerp(2, 9, eo_quart(seg(t, 129.10, 136.0))))
    rng = np.random.default_rng(5)
    cols = [(1310 + i * 68, rng.uniform(0, 900), rng.uniform(90, 260)) for i in range(9)]
    for ci, (cx, ph, sp) in enumerate(cols):
        if ci >= dens:
            continue
        for k in range(18):
            y = (ph + k * 52 + t * sp) % 1080 - 40
            if y < -30 or y > 900:
                continue
            ch = "1" if (k + int(ph)) % 3 else "0"
            a = clamp01((900 - y) / 480.0)
            U.text(d, (cx, y), ch, mono(34), CYAN, 0, alpha=a)

    # 大字：唯一可读层
    p = eo_expo(seg(t, 129.12, 129.60))
    if p > 0:
        dy = 40 * (1 - p)
        G.text_sh(d, (MX - 12, 600 + dy), "数字", sans(280, "bold"), PAPER, 14.0, off=0, alpha=p)

    # 波形：从下往上压过来
    a = clamp01((t - 130.30) / 0.9)
    if a > 0:
        m = wave_mask("素材_外部/09_原声带_47首/配乐30_Digital Parasite - 今堀恒雄_wave.png")
        bw, bh = 1500, 200
        bx, by = 0, 780
        sub = m.crop((0, 0, int(m.width * 0.6 * a), m.height)).resize((max(2, int(bw * a)), bh), Image.LANCZOS)
        lay = Image.new("RGB", (max(2, int(bw * a)), bh), CYAN)
        c.paste(lay, (bx, by), sub)
        d.rectangle([0, by + bh // 2, int(bw * a), by + bh // 2], fill=(60, 96, 98))

    if t > 135.94:
        a = clamp01((t - 135.94) / 0.32)
        im = G.load("素材_外部/07_场景/代码雨_2.jpg")
        pim = G.cover(im, (0, 0, W, H), zoom=1.18, fx=0.5, fy=0.5)
        pim = tint(pim, (4, 26, 30), 0.55)
        pim = contrast(pim, 0.5)
        c.paste(pim, (0, 0))
        U.text(d, (W // 2, 580), "CAPRI", mono(300, True), CYAN, 8.0, anchor="ms", alpha=a)


# ------------------------------------------------------------------ 模拟
def ana(c, t, idx):
    d = ImageDraw.Draw(c)
    p = eo_expo(seg(t, 140.12, 140.60))
    if p > 0:
        dy = 34 * (1 - p)
        G.text_sh(d, (W - MX + 12, 380 + dy), "模拟", sans(280, "bold"), INK, 14.0,
                  off=0, anchor="rs", alpha=p)

    items = [("素材_外部/07_场景/磁带_1.jpg", 140.85),
             ("素材_外部/07_场景/胶片_1.jpg", 143.35),
             ("素材_外部/05_设备乐器/image.jpg", 145.45)]
    bw, bh, gap = 540, 380, 60
    x = 90
    for i, (rel, t0) in enumerate(items):
        q = eo_expo(seg(t, t0, t0 + 0.34))
        if q <= 0:
            x += bw + gap
            continue
        y = int(440 + 50 * (1 - q))
        im = G.load(rel)
        c.paste(G.cover(im, (x, y, bw, bh), zoom=1.03), (x, y))
        d.rectangle([x, y, x + bw, y + bh], outline=(48, 42, 32), width=2)
        d.rectangle([x, y + bh + 8, x + int(bw * q), y + bh + 14], fill=AMBER)
        x += bw + gap
