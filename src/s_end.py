# -*- coding: utf-8 -*-
"""第七段：结尾很烂 → 编剧的意图 → 复古主义 → 悬崖 → 沉默 → 收尾。

178.42–216.88 是一段连续的全屏剪辑：只剪画面，不写字。
手段只有三样——画面自身的运动（推/回拉/硬切/压暗/画幅收缩）、色彩、剪辑点。
216.88–217.74 留黑；217.74 之后是 outro()。

素材注意：
  talia 与 romanup/romancall 的旷野段，原片左右各有 146px 内嵌黑边，
  这些镜头标 crop=True，先切掉黑边再铺满（否则画面像一台小电视）；
  每条素材内部有切点，每个镜头的入点都挑在两刀之间，
  时长也不超过那一段的长度——prep.frame 按帧数取模回绕，超了会跳。
"""
import numpy as np
from PIL import Image, ImageDraw

import design as G
import sutil as U
import prep
from design import (W, H, INK, PAPER, PAPER2, DIM, AMBER, RED, CYAN, WHITE,
                    sans, mono, serif, text, text_w, cover, plate, rule, vrule, solid,
                    seg, clamp01, lerp, eo_expo, eo_quart, eo_cubic, eio, ei_cubic,
                    pulse, grain, contrast, desat, tint, grid, wave_mask, vignette)
import data as D

MX = 88

# 收束段结束点：之后到 217.74 一片黑
CUT_BLACK = 216.88

# 原片自带的内嵌黑边（左, 上, 右, 下）。talia、romanup/romancall 的旷野段都是这个数，
# 不切掉就铺不满——画面会变成一台小电视。镜头表里 crop=True 才切。
BOX = (146, 23, 1466, 900)


# ------------------------------------------------------------------ 镜头表
# t0/t1 时间 · clip 素材 · kin 入点帧 · z 推拉 · fx/fy 取景漂移 · rate 放片速率
# kind: live 满幅 / punch 撞进来 / squeeze 画幅收缩 / fade 压到黑
SHOTS = [
    # 但是说到结尾啊 / 这个结尾他妈的也够烂的
    dict(t0=178.42, t1=181.06, clip="talia", kin=199, crop=True, z=(1.03, 1.17),
         fx=(0.50, 0.54), fy=(0.50, 0.47), ct=1.04,
         tn=((255, 224, 184), 0.10), vg=0.20),
    # 181.06 一帧黑 —— "烂"这个字用剪辑给
    dict(t0=181.06, t1=181.10, kind="blink"),
    # 猛推：同一张脸，撞到眼前
    dict(t0=181.10, t1=182.92, clip="talia", kin=278, crop=True, kind="punch",
         z=(1.02, 1.60), fx=(0.46, 0.50), fy=(0.54, 0.44), ct=1.12,
         tn=((255, 216, 172), 0.12), vg=0.28),
    # 183.38 血肉苦弱 / 机械飞升 … 另一种活法：拆下来的那堆东西
    dict(t0=182.92, t1=186.20, clip="jin_sunset", kin=150, rate=0.90,
         z=(1.04, 1.16), fx=(0.48, 0.54), fy=(0.46, 0.42), ct=1.08, ds=0.18,
         tn=((214, 206, 194), 0.08), vg=0.18),
    # 另一种人的活法：回到旷野，回拉
    dict(t0=186.20, t1=189.62, clip="romanup", kin=40, crop=True, z=(1.18, 1.04),
         fx=(0.56, 0.50), fy=(0.46, 0.52), ct=1.06,
         tn=((255, 226, 186), 0.10), dk=0.10, vg=0.22),
    # 190.14 仿佛只要不用新技术 / 退回最原始的肉身
    dict(t0=189.62, t1=193.20, clip="jin_sunset", kin=8, rate=0.86,
         z=(1.10, 1.28), fx=(0.50, 0.52), fy=(0.46, 0.50), ct=1.10, ds=0.32,
         tn=((176, 178, 180), 0.10), dk=0.14, vg=0.24),
    # 就能保住人类的尊严 —— 压暗：她瘫在车门上，只剩肉身
    dict(t0=193.20, t1=195.40, clip="talia", kin=409, crop=True, z=(1.02, 1.14),
         fx=(0.52, 0.46), fy=(0.44, 0.50), ct=1.04,
         tn=((215, 208, 192), 0.08), dk=0.20, vg=0.26),
    # 195.40 但这种复古主义并不能解决问题（反打：冷、机器）
    dict(t0=195.40, t1=199.20, clip="body", kin=40, z=(1.02, 1.14),
         fx=(0.50, 0.44), fy=(0.54, 0.48), ct=1.16, gm=0.70, ds=0.26,
         tn=((118, 138, 150), 0.10), vg=0.24),
    # 198.90~ AI 的浪潮 —— 全身义体
    dict(t0=199.20, t1=202.16, clip="shell", kin=90, z=(1.18, 1.04),
         fx=(0.54, 0.46), fy=(0.50, 0.54), ct=1.16, ds=0.22,
         tn=((118, 158, 176), 0.12), vg=0.22),
    # 202.36 那迟早是要被时代淘汰的 —— 短镜，压到一双红眼睛上
    dict(t0=202.16, t1=204.62, clip="body", kin=172, kind="punch",
         z=(1.06, 1.42), fx=(0.50, 0.50), fy=(0.50, 0.42), ct=1.20, gm=0.78,
         ds=0.36, dk=0.06, vg=0.28),
    # 204.62 那该怎么办呢
    dict(t0=204.62, t1=207.20, clip="talia", kin=331, crop=True, z=(1.04, 1.20),
         fx=(0.50, 0.46), fy=(0.52, 0.46), ct=1.04,
         tn=((255, 224, 186), 0.12), dk=0.04, vg=0.20),
    # 207.20 加入 AI / 然后让 AI 更快地淘汰自己吗 —— 义体的脸，贴到最近
    dict(t0=207.20, t1=209.30, clip="shell", kin=196,
         z=(1.86, 1.70), fx=(0.28, 0.32), fy=(0.34, 0.42), ct=1.18, ds=0.34,
         tn=((112, 156, 174), 0.16), dk=0.10, vg=0.34),
    # 209.64 前后都是悬崖 —— 画幅一路收到一条缝
    dict(t0=209.30, t1=213.88, clip="talia", kin=0, kind="squeeze", crop=True,
         z=(1.04, 1.42), fx=(0.50, 0.46), fy=(0.50, 0.44), ct=1.08, ds=0.20,
         tn=((236, 214, 184), 0.06), vg=0.24, dk=0.20),
    # 214.34 我觉得制作组没有给出一个很好的回答 —— 举着机器，慢慢暗下去
    dict(t0=213.88, t1=CUT_BLACK, clip="romanup", kin=180, kind="fade",
         rate=0.83, z=(1.04, 1.16), fx=(0.48, 0.54), fy=(0.52, 0.46), ct=1.10,
         tn=((228, 216, 194), 0.10), dk=0.10, vg=0.26),
]


# ------------------------------------------------------------------ 取帧
def _src(sh, idx):
    k = sh["kin"] + int(round((idx - int(round(sh["t0"] * 30))) * sh.get("rate", 1.0)))
    fr = prep.frame(sh["clip"], k)
    if sh.get("crop"):
        fr = fr.crop(BOX)
    return fr


# ------------------------------------------------------------------ 调色
def _grade(im, sh, p, extra_dk=0.0):
    ds = sh.get("ds", 0.0)
    if ds > 0:
        im = desat(im, ds)
    tn = sh.get("tn")
    if tn:
        im = tint(im, tn[0], tn[1])
    ct = sh.get("ct", 1.0)
    if abs(ct - 1.0) > 1e-3:
        im = contrast(im, ct)
    gm = sh.get("gm", 1.0)
    if abs(gm - 1.0) > 1e-3:
        # 提亮暗部，别让冷场的黑把画面吃空
        lut = [min(255, int(255.0 * (i / 255.0) ** gm)) for i in range(256)]
        im = im.point(lut * 3)
    vg = sh.get("vg", 0.0)
    if vg > 0:
        im = vignette(im, vg)
    dk = min(0.92, sh.get("dk", 0.0) + extra_dk)
    if dk > 0:
        # 往墨色里沉，接得住 216.88 的黑场
        im = G.overlay(im, (10, 9, 7), dk)
    return im


def _view(sh, p):
    fx0, fx1 = sh.get("fx", (0.5, 0.5))
    fy0, fy1 = sh.get("fy", (0.5, 0.5))
    return lerp(fx0, fx1, p), lerp(fy0, fy1, p)


# ------------------------------------------------------------------ 四种放法
def _live(c, sh, t, idx):
    p = eio(seg(t, sh["t0"], sh["t1"]))
    fr = _src(sh, idx)
    fx, fy = _view(sh, p)
    z = lerp(sh["z"][0], sh["z"][1], p)
    im = _grade(cover(fr, (0, 0, W, H), zoom=z, fx=fx, fy=fy), sh, p)
    c.paste(im, (0, 0))


def _punch(c, sh, t, idx):
    """0.22 秒推到顶，然后继续慢慢爬——撞进来之后还在走。"""
    p = seg(t, sh["t0"], sh["t1"])
    q = eo_expo(seg(t, sh["t0"], sh["t0"] + 0.22))
    fr = _src(sh, idx)
    fx, fy = _view(sh, eio(p))
    z = lerp(sh["z"][0], sh["z"][1], q) + 0.05 * q * eio(p)
    im = _grade(cover(fr, (0, 0, W, H), zoom=z, fx=fx, fy=fy), sh, p)
    c.paste(im, (0, 0))


def _squeeze(c, sh, t, idx):
    """画幅从满幅一路收到一条缝：上下加黑，越收越暗。"""
    p = seg(t, sh["t0"], sh["t1"])
    sq = eio(seg(t, sh["t0"] + 0.26, 213.66))
    h = lerp(H, 148.0, sq)
    cy = lerp(H * 0.5, 468.0, sq)
    fr = _src(sh, idx)
    fx, fy = _view(sh, eio(p))
    z = lerp(sh["z"][0], sh["z"][1], eio(p))
    im = _grade(cover(fr, (0, 0, W, H), zoom=z, fx=fx, fy=fy), sh, p,
                extra_dk=0.14 * sq)

    y0 = max(0, min(H, int(round(cy - h / 2))))
    y1 = max(0, min(H, int(round(cy + h / 2))))
    if y1 - y0 < 4:
        y1 = y0 + 4
    c.paste(im.crop((0, y0, W, y1)), (0, y0))
    if y0 > 0 or y1 < H:
        d = ImageDraw.Draw(c)
        bar = (7, 6, 5)
        if y0 > 0:
            d.rectangle([0, 0, W, y0], fill=bar)
            d.rectangle([0, y0, W, y0 + 1], fill=(52, 46, 36))
        if y1 < H:
            d.rectangle([0, y1, W, H], fill=bar)
            d.rectangle([0, y1 - 1, W, y1], fill=(52, 46, 36))


def _fade(c, sh, t, idx):
    """最后一镜：慢推，然后一路沉到黑，216.88 正好归零。"""
    p = seg(t, sh["t0"], sh["t1"])
    e = eio(p)
    fr = _src(sh, idx)
    fx, fy = _view(sh, e)
    z = lerp(sh["z"][0], sh["z"][1], e)
    im = _grade(cover(fr, (0, 0, W, H), zoom=z, fx=fx, fy=fy), sh, p)
    im = G.overlay(im, (10, 9, 7), eio(seg(t, 214.96, CUT_BLACK)))
    c.paste(im, (0, 0))


# ------------------------------------------------------------------ 总线
def _ending(c, t, idx):
    """178.42–216.88：按镜头表放画面。216.88 之后什么都不画。"""
    if t >= CUT_BLACK:
        return
    for sh in SHOTS:
        if not (sh["t0"] <= t < sh["t1"]):
            continue
        kind = sh.get("kind", "live")
        if kind == "blink":
            ImageDraw.Draw(c).rectangle([0, 0, W, H], fill=(6, 5, 4))
        elif kind == "punch":
            _punch(c, sh, t, idx)
        elif kind == "squeeze":
            _squeeze(c, sh, t, idx)
        elif kind == "fade":
            _fade(c, sh, t, idx)
        else:
            _live(c, sh, t, idx)
        return


# ------------------------------------------------------------------ 对外五个口（film.py 注册名，必须保留）
def end_(c, t, idx):
    _ending(c, t, idx)


def crit(c, t, idx):
    _ending(c, t, idx)


def rebut(c, t, idx):
    _ending(c, t, idx)


def cliff(c, t, idx):
    _ending(c, t, idx)


def silence(c, t, idx):
    # 214.34–216.88 是最后一镜的暗场；216.88–217.74 什么都不画。这是回答。
    _ending(c, t, idx)


# ------------------------------------------------------------------ 收尾
def outro(c, t, idx):
    d = ImageDraw.Draw(c)
    p = eo_quart(seg(t, 218.30, 220.20))
    if p > 0:
        bw = W
        vw = max(2, int(bw * p))
        for rel, col, yy, hh in (
            ("素材_外部/09_原声带_47首/配乐23_Analog Solitude - 今堀恒雄_wave.png", (226, 160, 40), 230, 150),
            ("素材_外部/09_原声带_47首/配乐30_Digital Parasite - 今堀恒雄_wave.png", (52, 176, 182), 400, 150),
        ):
            m = wave_mask(rel)
            sub = m.crop((0, 0, int(m.width * p), m.height)).resize((vw, hh), Image.LANCZOS)
            lay = Image.new("RGB", (vw, hh), col)
            c.paste(lay, (0, yy), sub)
            d.rectangle([0, yy + hh // 2, vw, yy + hh // 2], fill=(184, 172, 148))

    if t > 220.60:
        a = clamp01((t - 220.60) / 0.4)
        U.text(d, (MX, 640), "一条来自模拟，一条来自数字。", sans(44, "medium"), (86, 78, 64), 4.0, alpha=a)
        U.text(d, (MX, 706), "这部剧把它们放在一起，然后就没有答案了。", sans(44, "medium"), INK, 4.0, alpha=a)

    if t > 222.90:
        a = eo_expo(seg(t, 222.90, 223.44))
        U.text(d, (MX - 6, 880), "我是尤里", sans(110, "bold"), INK, 8.0, alpha=a)

    if t > 227.20:
        a = eo_expo(seg(t, 227.20, 227.82))
        text(d, (W - MX + 6, 880), "下次再见", serif(104), INK, 10.0, anchor="rs", alpha=a)
