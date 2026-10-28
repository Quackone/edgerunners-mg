# -*- coding: utf-8 -*-
"""数字：0/1 故障网格 → CAPRI。占 129.04—140.10。

观感移植自另一工程的 grid01（字符阵列 / 复制重影 / 横向撕裂 / 发光点阵字），
但一律用本工程的基元重写：没有 color_ops、draw_tracked、vignette 那套 API。

纪律：全段只有两个可读文字——开场的「数字」与 CAPRI。
其余 0/1 是材质，不承载语义，也绝不配注脚。
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from design import (W, H, INK, PAPER, CYAN, sans, mono, text_w, seg,
                    clamp01, lerp, eo_expo, eo_quart, eio, contrast, tint,
                    vignette)

CELL = 26          # 网格字符步距
STRIP = 1860       # 预渲染竖条（够 11 秒 26px/s 的位移）
T0 = 129.04

# ================================================================== 底子
_GRID = {}


def _grid_frames():
    """三帧 0/1 阵列，固定 seed 预生成。帧间只有字与亮度不同，位置不变。"""
    if "f" in _GRID:
        return _GRID["f"]
    rng = np.random.default_rng(2029)
    fnt = mono(24)
    cols = W // CELL + 2
    rows = STRIP // CELL + 2
    frames = []
    for _ in range(3):
        im = Image.new("RGB", (cols * CELL, rows * CELL), INK)
        d = ImageDraw.Draw(im)
        # 低频明暗场：让阵列有深有浅，不是一张均匀的噪声纸
        nz = rng.random((rows // 4 + 2, cols // 4 + 2)).astype(np.float32)
        nz = np.kron(nz, np.ones((4, 4), np.float32))[:rows, :cols]
        for r in range(rows):
            for c in range(cols):
                if rng.random() < 0.11:          # 空位 = 层次
                    continue
                ch = "1" if rng.random() > 0.50 else "0"
                v = 22 + rng.random() * 92 + 76 * float(nz[r, c])
                # 青绿：绿最高、蓝略高、红压到几乎没有
                col = (int(v * 0.26) + 5, int(v * 0.95) + 24, int(v * 1.02) + 30)
                d.text((c * CELL + 4, r * CELL + 1), ch, font=fnt, fill=col)
        frames.append(im)
    # 统一调色（只做一次，相当于 color_ops）
    frames = [contrast(tint(fr, CYAN, 0.07), 1.16) for fr in frames]
    _GRID["f"] = frames
    return frames


def _grid_img(t, y_extra=0):
    fr = _grid_frames()
    fi = int(round(t * 30)) % 3          # 10Hz 三帧循环 = 轻微闪烁
    y = int((t - T0) * 26.0) + y_extra   # 26px/s 纵向滚动
    y = max(0, min(STRIP - H - 2, y))
    return fr[fi].crop((0, y, W, y + H))


# ---------------------------------------------------------------- 复制重影
_GBOX = (200, 302, 360, 330)
_PULSE = (133.30, 133.88, 134.36)


def _hot(patch):
    """复制件的字形：把原件拉成高对比的白字，黑底留空。"""
    a = (np.asarray(patch, np.float32) - 34.0) * 2.4
    a[:, :, 0] *= 0.55
    return np.clip(a, 0, 255)


def _copy_ghost(im, t):
    """同一块画面被横向复制、错位、叠回原处——「无限复制」的翻译。

    阵列本身是同质噪声，单纯位移看不出来；复制件因此自带一层更亮的底，
    像一整块"图层"被抠出来贴在旁边，并且一份一份地落下来（一、二、三）。
    """
    x, y, w, h = _GBOX
    lift = np.array([8.0, 50.0, 55.0], np.float32)   # 复制件的底
    for t0 in _PULSE:
        p = (t - t0) / 0.66
        if p < 0 or p > 1:
            continue
        fade = 1 - clamp01((p - 0.70) / 0.30)
        dx = int(372 + 40 * eo_expo(p))
        oa = _hot(im.crop((x, y, x + w, y + h)))
        bg = im.copy()
        for k in (1, 2, 3):
            ak = clamp01((p - (k - 1) * 0.15) / 0.06) * fade
            if ak <= 0.02:
                continue
            ox = min(W - w, x + dx * k)
            dst = np.asarray(bg.crop((ox, y, ox + w, y + h)), np.float32)
            new = dst + (oa + lift) * ak
            im.paste(Image.fromarray(np.clip(new, 0, 255).astype(np.uint8)), (ox, y))
    return im


# ---------------------------------------------------------------- 横向撕裂
_TW = (0.92, 0.34, 0.71, 0.46, 1.00, 0.55, 0.82, 0.40, 0.96, 0.62, 0.76)
_TS = (0.361, 0.705, 0.244, 0.588, 0.83, 0.12, 0.66, 0.47, 0.9, 0.29, 0.55)


def _tear(im, t):
    """切成 11 条横带，每条再崩成 3 段：各自左右错位，缝里露出黑。
    幅度先涨后落——篡改是一次发作，不是常态。
    """
    k = eo_expo(seg(t, 134.52, 135.00)) * (1 - eio(seg(t, 135.10, 135.86)))
    if k <= 0.002:
        return im
    n = len(_TW)
    out = Image.new("RGB", (W, H), INK)
    od = ImageDraw.Draw(out, "RGBA")
    ea = int(150 * min(1.0, k * 1.2))
    for i in range(n):
        y0 = i * H // n
        y1 = min(H, (i + 1) * H // n + 3)
        amp = 170 * k * _TW[i]
        xa = int(W * (0.12 + 0.56 * _TS[i]))
        xb = min(W - 80, xa + int(W * (0.14 + 0.26 * _TS[(i + 5) % n])) + 60)
        g = int(6 + 22 * k * _TW[(i + 3) % n])
        band = im.crop((0, y0, W, y1))
        b = 1.0 + 0.13 * math.sin(i * 2.1 + 0.6) * min(1.0, k * 1.5)
        band = Image.fromarray(np.clip(np.asarray(band, np.float32) * b, 0, 255).astype(np.uint8))
        segs = ((0, xa, math.sin(t * 12.5 + i * 2.3) * amp),
                (xa, xb, math.sin(t * 9.7 + i * 3.1 + 1.7) * amp),
                (xb, W, math.sin(t * 7.3 + i * 4.7 + 3.1) * amp))
        for j, (s0, s1, d) in enumerate(segs):
            out.paste(band.crop((s0, 0, s1, band.height)), (s0 + int(d) + j * g, y0))
            if j:
                # 撕口的一道亮边，只有右段有
                px = s0 + int(d) + j * g
                od.rectangle([px - 2, y0, px, y1], fill=(96, 226, 222, ea))
        od.rectangle([0, y0, W, y0 + 1], fill=(96, 226, 222, int(ea * 0.30)))
    return out


# ---------------------------------------------------------------- CAPRI
_CAP = {}


def _layer(mask, col, k):
    a = mask.point(lambda v: int(min(255, v * k)))
    lay = Image.new("RGBA", mask.size, col + (0,))
    lay.putalpha(a)
    return lay


def _capri_base():
    if _CAP:
        return _CAP
    size, track = 470, 23.0
    fnt = mono(size, True)
    wtxt = text_w(fnt, "CAPRI", track)
    tmp = Image.new("L", (int(wtxt) + 220, int(size * 1.5)), 0)
    d = ImageDraw.Draw(tmp)
    cx = 110.0
    for ch in "CAPRI":
        d.text((cx, 60), ch, font=fnt, fill=255)
        cx += fnt.getlength(ch) + track
    m = tmp.crop(tmp.getbbox())
    pad = 110
    mask = Image.new("L", (m.width + 2 * pad, m.height + 2 * pad), 0)
    mask.paste(m, (pad, pad))
    # 垫在字下面的暗场：比字大一圈，光才浮得出来
    cush = mask.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(22))

    _CAP["mask"] = mask
    _CAP["cush"] = cush
    _CAP["ns"] = 14
    _CAP["seed"] = np.random.default_rng(4242).random(14)
    _CAP["ord"] = np.random.default_rng(99).permutation(14)
    # 横穿字身的数据带：(y, 高, 速度, 相位)
    hh = mask.height
    _CAP["bands"] = ((0.28, 26, 760, 0.0),
                     (0.40, 32, -560, 130.0),
                     (0.52, 24, 980, 320.0),
                     (0.63, 30, -700, 60.0),
                     (0.71, 22, 640, 470.0))
    _CAP["hh"] = hh
    return _CAP


def _capri(im, t):
    g = _capri_base()
    mask = g["mask"]
    tw, _h = mask.size
    hh = g["hh"]

    k_out = 1 - eo_quart(seg(t, 139.74, 140.08))
    a_dim = eo_expo(seg(t, 135.94, 136.10))
    a_rev = seg(t, 136.16, 136.74)
    k_glow = eo_expo(seg(t, 136.32, 136.88)) * k_out
    k_core = k_out

    # 1) 先把字形区域的底噪压暗——字是一个洞，然后才亮
    jx = int(round(math.sin(t * 27.0) * 3 + math.sin(t * 8.0) * 4))
    pos = ((W - tw) // 2 + jx, 500 - hh // 2)
    if a_dim > 0:
        hole = Image.new("L", (W, H), 0)
        hole.paste(g["cush"], pos)
        arr = np.asarray(im, np.float32)
        mm = np.asarray(hole, np.float32) / 255.0
        arr *= (1.0 - mm[:, :, None] * 0.94 * a_dim * k_out)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # 2) 分片：横向错位 + 逐片点亮
    arr = np.asarray(mask).copy()
    ns = g["ns"]
    for i in range(ns):
        y0, y1 = i * hh // ns, (i + 1) * hh // ns
        sl = arr[y0:y1]
        dx = int(round(math.sin(t * 8.6 + i * 1.9) * 22 * (0.35 + g["seed"][i])))
        if dx:
            new = np.zeros_like(sl)
            if dx > 0:
                new[:, dx:] = sl[:, :-dx]
            else:
                new[:, :dx] = sl[:, -dx:]
            sl[:] = new
        # 点亮的顺序是打乱的，硬切不淡入：字像被一块块砸进来
        rank = int(np.where(g["ord"] == i)[0][0])
        r = 1.0 if a_rev > rank * 0.055 + 0.045 else 0.0
        if r < 1:
            sl[:] = 0

    # 3) 数据带把字切开：带内的笔画压到 22%，由 0/1 顶替
    bands = []
    for bi, (yf, bh, sp, ph) in enumerate(g["bands"]):
        if ((t * 1.35 + bi * 0.37) % 1.0) > 0.74:
            continue
        by = int(yf * hh)
        arr[by:by + bh] = (arr[by:by + bh] * 0.22).astype(np.uint8)
        bands.append((by, bh, sp * (1.0 + 2.4 * seg(t, 139.50, 140.02)), ph))

    mk = Image.fromarray(arr)
    sm = mk.resize((tw // 4, hh // 4), Image.BILINEAR)
    gA = sm.filter(ImageFilter.GaussianBlur(17)).resize((tw, hh), Image.BILINEAR)
    gB = sm.filter(ImageFilter.GaussianBlur(5.0)).resize((tw, hh), Image.BILINEAR)

    out = Image.new("RGBA", (tw, hh), (0, 0, 0, 0))
    out = Image.alpha_composite(out, _layer(gA, (16, 96, 112), 1.45 * k_glow))
    out = Image.alpha_composite(out, _layer(gB, (70, 212, 212), 1.55 * k_glow))
    out = Image.alpha_composite(out, _layer(mk, (182, 252, 244), k_core))

    # 4) 带内 0/1：只在笔画上落字，所以看起来是字被拆成数据
    if bands and k_core > 0.02:
        bd = ImageDraw.Draw(out, "RGBA")
        fnt = mono(24)
        for (by, bh, sp, ph) in bands:
            off = (t * sp + ph) % 26.0
            x = -26 + off
            while x < tw:
                col = int(x)
                if 0 <= col < tw:
                    hit = arr[min(hh - 1, by + bh // 2), col]
                    if hit > 55:
                        ch = "1" if ((col // 26 + int(by)) + int(t * 7)) % 2 else "0"
                        bd.text((col - 6, by + bh // 2 - 13), ch, font=fnt,
                                fill=(214, 255, 250, int(238 * k_core)))
                x += 26
    # 5) 叠回画面
    im.paste(out, pos, out)
    return im


# ================================================================== 开场
_ZH = {}


def _zh():
    if "im" in _ZH:
        return _ZH["im"]
    fnt = sans(300, "bold")
    im = Image.new("RGBA", (int(text_w(fnt, "数字", 14.0)) + 60, 480), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = 12.0
    for ch in "数字":
        d.text((cx, 50), ch, font=fnt, fill=PAPER + (255,))
        cx += fnt.getlength(ch) + 14.0
    im = im.crop(im.getbbox())
    _ZH["im"] = im
    _ZH["slice"] = (0.9, 0.35, 0.72, 0.5, 1.0, 0.44, 0.8, 0.3, 0.95, 0.6, 0.68, 0.4)
    return im


def _opener(c, t):
    d = ImageDraw.Draw(c, "RGBA")

    # 背景种子：右侧几列 0/1 先渗进来
    fnt = mono(24)
    rng = np.random.default_rng(31)
    xc = 1210.0
    while xc < W - 20:
        cx = xc
        sp = rng.uniform(46, 88)
        ph = rng.uniform(0, 600)
        a0 = rng.uniform(0.20, 0.55)
        for k in range(40):
            y = (ph + k * 34 + t * sp) % (H + 60) - 30
            if y > 890:
                continue
            ch = "1" if (k * 7 + int(cx)) % 3 else "0"
            fade = clamp01((890 - y) / 620.0) * a0
            d.text((cx, y), ch, font=fnt, fill=(26, 92, 100, int(255 * fade)))
        xc += rng.uniform(76, 148)

    zi = _zh()
    zw, zh = zi.size
    x0, y0 = 78, 706 - zh

    # 入场：整字被切成横条，各自错位，0.30s 内归位
    gl = 1 - eo_expo(seg(t, 129.04, 129.34))
    body = zi
    if gl > 0.004:
        a = np.asarray(zi).copy()
        n = 12
        for i in range(n):
            p0, p1 = i * zh // n, (i + 1) * zh // n
            sl = a[p0:p1]
            dx = int(round(math.sin(i * 3.7 + 1.1) * 74 * gl * _ZH["slice"][i % 12]))
            if dx:
                new = np.zeros_like(sl)
                if dx > 0:
                    new[:, dx:, :] = sl[:, :-dx, :]
                else:
                    new[:, :dx, :] = sl[:, -dx:, :]
                sl[:] = new
        body = Image.fromarray(a)

    # 数据带自上而下把字逐行"数字化"
    by = lerp(y0 - 60, y0 + zh + 30, eio(seg(t, 129.72, 130.18)))
    cut = int(clamp01((by - y0) / max(1, zh)) * zh)

    if cut > 0:
        a = np.asarray(body).copy()
        a[:min(cut, zh), :, 3] = 0
        body = Image.fromarray(a)
    c.paste(body, (x0, y0), body)

    if cut > 0:
        src = np.asarray(zi)[:, :, 3]
        fnt2 = mono(24)
        yy = 0
        while yy < min(cut, zh):
            for xx in range(0, zw, 30):
                if src[yy, xx] > 120:
                    ch = "1" if ((xx // 3) + (yy // 5)) % 3 else "0"
                    d.text((x0 + xx - 7, y0 + yy - 4), ch, font=fnt2,
                           fill=(228, 246, 238, 240))
            yy += 34
        # 正在扫描的那一道
        sy = y0 + cut
        d.rectangle([0, sy - 30, W, sy - 2], fill=(72, 208, 214, 22))
        d.rectangle([0, sy - 3, W, sy], fill=(110, 236, 232, 210))

    # 左侧那根线：从窄到宽，是这一段的"开机"
    p = eo_expo(seg(t, 129.10, 129.70))
    d.rectangle([78, 742, 78 + int(320 * p), 745], fill=(72, 208, 214, 220))


# ================================================================== 总装
def dig(c, t, idx):
    if t < 130.22:
        _opener(c, t)
        return

    # 硬切入网格：先滚进来 46px，落定
    ye = int(46 * (1 - eo_expo(seg(t, 130.22, 130.60))))
    im = _grid_img(t, ye)
    im = _copy_ghost(im, t)
    im = _tear(im, t)

    # CAPRI 段落：先把网格压暗，让字成为唯一亮面（压暗在贴字之前做）
    if t >= 135.92:
        dk = eo_expo(seg(t, 135.92, 136.16))
        im = Image.blend(im, Image.new("RGB", (W, H), INK), 0.34 * dk)
    if t >= 135.94:
        im = _capri(im, t)

    # 一条极慢的下行扫描亮带：静止网格里始终有东西在走
    yb = int((t * 150) % (H + 400)) - 200
    od = ImageDraw.Draw(im, "RGBA")
    od.rectangle([0, yb, W, yb + 190], fill=(120, 230, 226, 9))
    od.rectangle([0, yb, W, yb + 2], fill=(150, 240, 236, 26))

    # 收尾：到 140.10 之前沉下去，接纸面的「模拟」
    dk = eo_quart(seg(t, 139.84, 140.10))
    if dk > 0:
        im = Image.blend(im, Image.new("RGB", (W, H), INK), 0.88 * dk)

    im = vignette(im, 0.42)
    c.paste(im, (0, 0))
