# -*- coding: utf-8 -*-
"""第三段：山冈晃 —— 工业噪音、绞肉机。底色是墨。

纪律：这一整段几乎不写字。机器用画面和声音说话。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import design as G
import sutil as U
import prep
from design import (W, H, INK, INK2, PAPER, PAPER2, DIM, AMBER, RED, CYAN, WHITE,
                    sans, mono, text, text_w, cover, plate, rule, vrule, solid,
                    seg, clamp01, lerp, eo_expo, eo_quart, eo_cubic, eio, ei_cubic,
                    pulse, grain, contrast, desat, tint, duotone, grid)
import data as D

MX = 88


def yamaoka(c, t, idx):
    d = ImageDraw.Draw(c)
    if t < 50.72:
        _three(c, d, t)
    elif t < 52.42:
        _only_him(c, d, t)
    elif t < 55.01:
        _aesthetic(c, d, t)
    elif t < 61.14:
        _synth(c, d, t)
    elif t < 70.04:
        _chain(c, d, t, idx)
    else:
        _machine(c, d, t, idx)


# ------------------------------------------------------------------ 三个名字位
# 三个位置：前两个被 CD PROJEKT RED 的铭牌压住（只留字头残影，不辨认），
# 第三个在 48.90 由虚变实，写成「今堀恒雄」。两个被闭嘴，一个被点名。
SLOT_X0, SLOT_W, SLOT_GAP, SLOT_Y, SLOT_H = 150, 760, 60, 300, 250
PLATE_TOP = 84          # 铭牌压住的位置（相对卡位顶部），上面留一截字头


def _ghost(c, box, n, seed, col=(102, 92, 75), alpha=0.55, blur=6.0):
    """不是字的字：几根笔画粗细的模糊竖块，读作"这里有名字"，但不可辨认。"""
    if alpha <= 0.01:
        return
    x, y, w, h = [int(round(v)) for v in box]
    if w <= 0 or h <= 0:
        return
    rng = np.random.default_rng(seed)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    cw = w / float(n)
    for i in range(n):
        ox = i * cw + cw * 0.10
        for _ in range(int(rng.integers(2, 5))):
            bw = cw * rng.uniform(0.05, 0.14)
            bx = ox + rng.uniform(0, cw * 0.74)
            bh = h * rng.uniform(0.40, 0.84)
            by = h * 0.14 + rng.uniform(0, h * 0.86 - bh)
            dl.rectangle([bx, by, bx + bw, by + bh], fill=col + (255,))
        for _ in range(int(rng.integers(1, 3))):
            bw = cw * rng.uniform(0.16, 0.62)
            by = h * rng.uniform(0.22, 0.76)
            dl.rectangle([ox, by, ox + bw, by + h * rng.uniform(0.03, 0.07)], fill=col + (255,))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    c.paste(lay, (x, y), lay)


def _mark(c, d, x, y, a):
    """仓库里没有 CDPR 的鸟，用字体搭一个识别标记：红方块 + 无衬线大写 + 红线。"""
    if a <= 0:
        return
    s = 56
    solid(c, (x, y, s, s), RED)
    f = sans(46, "bold")
    tx, ty = x + s + 26, y + s - 6
    text(ImageDraw.Draw(c, "RGBA"), (tx, ty), "CD PROJEKT RED", f, INK, 7.0, alpha=255 * a)
    solid(c, (tx, ty + 14, int(text_w(f, "CD PROJEKT RED", 7.0)), 4), RED)


def _name_row(c, d, t, y, name, t_in, a_max=1.0):
    """一个作曲家的名字：等宽大写 + 一条细线。名字要真的写出来。"""
    a = eo_expo(seg(t, t_in, t_in + 0.34)) * a_max
    if a <= 0.004:
        return
    dx = int(26 * (1 - a))
    f = mono(72, True)
    d.ellipse([SLOT_X0 - 26 + dx, y - 26, SLOT_X0 - 10 + dx, y - 10], fill=RED)
    text(ImageDraw.Draw(c, "RGBA"), (SLOT_X0 + dx, y), name, f, INK, 4.0, alpha=255 * a)
    w = int(text_w(f, name, 4.0))
    solid(c, (SLOT_X0 + dx, y + 24, int(w * a), 2), (168, 156, 132))


def _three(c, d, t):
    out = eio(seg(t, 49.85, 50.45))
    p = eo_expo(seg(t, 47.30, 47.75))
    if p <= 0:
        return
    dx = int(-2200 * out) + int(80 * (1 - p))

    if out < 1.0:
        # CD PROJEKT RED 标记（字体搭的，不是伪造的鸟标）
        _mark(c, d, SLOT_X0 + dx, 120, p)
        # 两位 CDPR 配乐师：名字写出来，尺寸压小，用红色圆点归属到上面的标记
        _name_row(c, d, t, 340, "MARCIN PRZYBYŁOWICZ", 47.52)
        _name_row(c, d, t, 460, "P.T. ADAMCZYK", 47.72)

        # 红线：把"那两个"和"这一个"分开
        rw = 1580 * eo_quart(seg(t, 48.55, 49.05))
        rw *= 1 - eo_quart(seg(t, 50.42, 50.68))
        if rw > 0:
            solid(c, (SLOT_X0 + dx, 566, rw, 6), RED)

        # 右边把人放出来：纸左、人右，名字压在空处——纸不再空，也不用再加字
        pi = eo_expo(seg(t, 49.05, 49.62))
        if pi > 0:
            bx = int(1084 + 836 * (1 - pi))
            im = G.load("素材_外部/03_人物/山冈晃.jpg")
            pim = G.cover(im, (bx, 0, 836, H), zoom=1.06, fx=0.62, fy=0.38)
            pim = G.desat(pim, 0.55)
            pim = G.contrast(pim, 1.08)
            pim = G.tint(pim, (30, 28, 24), 0.14)
            c.paste(pim, (bx, 0))
            solid(c, (bx - 5, 0, 5, H), INK)

        # 我们要聊的这一个
        a = eo_expo(seg(t, 48.90, 49.34))
        if a > 0:
            text(ImageDraw.Draw(c, "RGBA"), (SLOT_X0 - 12 + dx - 24 * (1 - a), 836), "山冈晃",
                 sans(240, "bold"), INK, 8.0, alpha=255 * a)


def _only_him(c, d, t):
    """一帧人，不说话。"""
    p = eo_expo(seg(t, 50.72, 51.14))
    z = lerp(1.08, 1.0, p)
    im = G.load("素材_外部/03_人物/山冈晃.jpg")
    pim = G.cover(im, (0, 0, W, H), zoom=z, fx=0.58, fy=0.40)
    pim = desat(pim, 0.72)
    pim = contrast(pim, 1.10)
    pim = tint(pim, (24, 28, 34), 0.22)
    c.paste(pim, (0, 0))


# ------------------------------------------------------------------ 工业噪音美学
def _aesthetic(c, d, t):
    # 底：合成器面板斜压进来，只当材质
    im = G.load("素材_外部/05_设备乐器/合成器面板_2.jpg")
    pim = G.cover(im, (0, 0, W, H), zoom=1.25, fx=0.72, fy=0.5)
    pim = desat(pim, 0.7)
    pim = contrast(pim, 1.15)
    pim = tint(pim, (16, 18, 22), 0.42)
    c.paste(pim, (0, 0))
    ov = Image.new("RGB", (W, H), (6, 6, 6))
    c.paste(Image.blend(c.copy(), ov, 0.38), (0, 0))

    s = "工业噪音"
    for i, ch in enumerate(s):
        t0 = 52.42 + i * 0.05
        p = eo_expo(seg(t, t0, t0 + 0.20))
        if p <= 0:
            continue
        fs = sans(210 * lerp(1.18, 1.0, p), "bold")
        d.text((MX + i * 216, 430 + 40 * (1 - p)), ch, font=fs, fill=PAPER, anchor="ls")
    p2 = eo_expo(seg(t, 53.32, 53.72))
    if p2 > 0:
        d.text((MX + 4, 620 + 30 * (1 - p2)), "美学", font=sans(210, "bold"), fill=PAPER, anchor="ls")
        d.rectangle([MX, 660, MX + int(880 * p2), 668], fill=AMBER)
    for i in range(7):
        y = int((i * 137 + (t * 24)) % H)
        d.rectangle([0, y, W, y + 1], fill=(40, 36, 30))


# ------------------------------------------------------------------ 合成器
def _synth(c, d, t):
    """只有面板：横移 + 极慢推近，一直不停。这里不需要文字解释。"""
    im = G.load("素材_外部/05_设备乐器/合成器面板_1.jpg")
    ph = max(0.0, t - 55.01)
    pan = ph * 30.0
    pim = G.cover(im, (0, 0, W, H), zoom=1.30 + 0.008 * ph,
                  fx=min(0.95, max(0.05, 0.08 + pan / 860.0)), fy=0.40 + 0.012 * ph)
    pim = desat(pim, 0.55)
    pim = contrast(pim, 1.22)
    pim = tint(pim, (18, 22, 28), 0.30)
    c.paste(pim, (0, 0))
    ov = Image.new("RGB", (W, H), (8, 8, 8))
    c.paste(Image.blend(c.copy(), ov, 0.24), (0, 0))


# ------------------------------------------------------------------ 采集
# 没有序号、没有 FIG 标签：图片自己居中站着，靠替换制造节奏。
BOX = (400, 66, 1120, 700)


def _fig(c, d, t, im_rel, t_in):
    if t < t_in:
        return
    x, y, w, h = BOX
    src = G.load(im_rel)
    # 快推入：入场 0.16 秒推 5%，之后一路极慢推，画面始终在动
    z = 1.0 + 0.05 * eo_expo(seg(t, t_in, t_in + 0.16)) + 0.055 * seg(t, t_in + 0.16, t_in + 2.7)
    c.paste(G.cover(src, (x, y, w, h), zoom=z), (x, y))
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=(74, 67, 54), width=2)


def _chain(c, d, t, idx):
    if t < 64.56:
        _fig(c, d, t, "素材_外部/07_场景/工业厂房_现代_3.jpg", 61.14)
    elif t < 65.86:
        _fig(c, d, t, "素材_外部/07_场景/电锯_1.jpg", 64.56)
    elif t < 67.70:
        _fig(c, d, t, "素材_外部/07_场景/钢管_1.jpg", 65.86)
    else:
        _rec(c, d, t, idx)


def _rec(c, d, t, idx):
    x, y, w, h = 275, 255, 1370, 400
    c.paste(Image.new("RGB", (w, h), (22, 19, 14)), (x, y))
    d.rectangle([x, y, x + w, y + h], outline=(90, 82, 66), width=3)
    if int(t * 3) % 2 == 0 or t < 68.3:
        d.ellipse([x + 30, y + 30, x + 56, y + 56], fill=RED)
    U.text(d, (x + 74, y + 54), "REC", mono(40, True), PAPER, 4.0)
    ff = int(t * 30) % 30
    U.text(d, (x + w - 30, y + 54), "%02d:%02d:%02d" % (int(t) // 60, int(t) % 60, ff),
           mono(40), (162, 152, 132), 2.0, anchor="rs")

    for i, rel in enumerate(("素材_外部/07_场景/电锯_1.jpg", "素材_外部/07_场景/钢管_1.jpg")):
        th = G.load(rel)
        bx, by = x + 30 + i * 300, y + 100
        c.paste(G.cover(th, (bx, by, 270, 152)), (bx, by))
        d.rectangle([bx, by, bx + 270, by + 152], outline=(70, 62, 48), width=1)

    pw = clamp01((t - 68.62) / 0.9)
    if pw > 0:
        m = G.wave_mask("素材_外部/09_原声带_47首/配乐30_Digital Parasite - 今堀恒雄_wave.png")
        bw, bh = 660, 190
        bx, by = x + 660, y + 100
        vwid = max(2, int(bw * (0.35 + 0.65 * pw)))
        sub = m.crop((int(m.width * 0.10), 0, int(m.width * (0.10 + 0.30 * pw)), m.height)).resize((vwid, bh), Image.LANCZOS)
        lay = Image.new("RGB", (vwid, bh), AMBER)
        c.paste(lay, (bx, by), sub)
        d.rectangle([bx, by + bh // 2, bx + bw, by + bh // 2], fill=(70, 62, 48))
        d.rectangle([bx + vwid - 2, by - 14, bx + vwid, by + bh + 14], fill=PAPER)

    # 走带
    vx, vy, vw = x + 30, y + 300, w - 60
    n = 44
    for i in range(n):
        aa = 0.2 + 0.8 * abs(np.sin(t * 3.1 + i * 0.7)) * abs(np.cos(t * 1.3 + i * 0.21))
        bx = vx + i * (vw / n)
        hh = int(64 * aa)
        d.rectangle([bx + 1, vy + 64 - hh, bx + vw / n - 4, vy + 64],
                    fill=RED if i > n - 7 else AMBER)


# ------------------------------------------------------------------ 机器
def _machine(c, d, t, idx):
    if t < 73.02:
        fr = prep.frame("body", idx - int(70.04 * 30))
        pim = G.cover(fr, (0, 0, W, H))
        pim = desat(pim, 0.30)
        pim = contrast(pim, 1.14)
        c.paste(pim, (0, 0))
        return

    if t < 75.62:
        fr = prep.frame("body", idx - int(70.04 * 30))
        pim = G.cover(fr, (0, 0, W, H))
        pim = desat(pim, 0.35)
        pim = contrast(pim, 1.16)
        pim = tint(pim, (20, 18, 16), 0.12)
        ph = (t - 73.02)
        out = Image.new("RGB", (W, H), (8, 7, 6))
        n = 18
        sh = H // n + 1
        for i in range(n):
            y0 = i * sh
            amp = (0.5 + 0.5 * np.sin(i * 1.7 + ph * 26.0)) * (150 + 420 * min(1.0, ph * 1.6))
            off = int(amp * (1 if i % 2 == 0 else -1))
            sl = pim.crop((0, y0, W, min(H, y0 + sh)))
            out.paste(sl, (off, y0))
            if off > 0:
                out.paste(sl.crop((W - off, 0, W, sl.height)), (0, y0))
            elif off < 0:
                out.paste(sl.crop((0, 0, -off, sl.height)), (W + off, y0))
        c.paste(out, (0, 0))
        for i in range(n):
            d.rectangle([0, i * sh, W, i * sh], fill=(10, 9, 7))
        return

    im = G.load("素材_外部/07_场景/霓虹街景_1.jpg")
    grid(c, 48, (56, 50, 40), 26)
    s = eo_quart(seg(t, 75.62, 76.10))
    bw = int(lerp(900, 360, s))
    bh = int(bw * 0.5625)
    bx, by = (W - bw) // 2, int(470 - bh / 2)
    pim = G.cover(im, (bx, by, bw, bh))
    pim = desat(pim, 0.55)
    pim = tint(pim, (26, 30, 34), 0.28)
    c.paste(pim, (bx, by))
    d.rectangle([bx, by, bx + bw, by + bh], outline=AMBER, width=2)
