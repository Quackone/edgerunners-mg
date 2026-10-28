# -*- coding: utf-8 -*-
"""第六段：位深削减（数字） → 人味儿（模拟）。

148.58—162.90  塔莉雅调钢丝：原片直出。1920×1080 原生分辨率，1:1 贴片，
               不做量化、不做调色、不缩放。曲卡只出现一次，右下，小、不透明。
162.90—169.75  金拆除义体：全屏，恢复色彩，零文字。残留的块在 0.5 秒内退掉，
               像数字终于让位给胶片。
169.75—178.42  信号链：吉他 → 音箱 → 混响。三个细描边模块、一条横贯的线、
               按顺序亮起，最后整体推近一点点。
"""
import math
from PIL import Image, ImageDraw

import design as G
import prep
from design import (W, H, INK, INK2, PAPER, AMBER, RED, CYAN, WHITE,
                    mono, serif, text, cover, seg, clamp01, lerp,
                    eo_expo, eo_quart, eo_cubic, steps,
                    contrast, desat, tint, pixelate, posterize)

A0, A1 = 148.58, 162.90
B0, B1 = 162.90, 169.75

MX = 88
BAR = 2.0          # 一小节 = 2 秒（120bpm 的 4/4）
GRAY = (96, 90, 77)   # 模块未点亮时的深灰描边


def _mix(a, b, k):
    k = clamp01(k)
    return (int(a[0] + (b[0] - a[0]) * k),
            int(a[1] + (b[1] - a[1]) * k),
            int(a[2] + (b[2] - a[2]) * k))


# ================================================================== ① 位深削减
_LIFT = [min(255, int((i / 255.0) ** 1.08 * 255)) for i in range(256)] * 3


def case_a(c, t, idx):
    """原片是什么样就是什么样：1:1 贴片，不缩放、不量化、不调色。"""
    k = idx - int(round(A0 * 30))
    c.paste(prep.frame("talia_wire", k), (0, 0))
    if 154.0 <= t < 157.02:
        _track_card(c, t)


CARD_W, CARD_H = 480, 160
CARD_X, CARD_Y = W - MX - 480, 900 - 160


def _track_card(c, t):
    """只出现一次的小曲卡：墨底、两条曲名、滑入 0.25s、3 秒后淡出。"""
    p = seg(t, 154.0, 154.25)
    a = 1.0 - eo_cubic(seg(t, 156.70, 157.00))
    if p <= 0 or a <= 0.004:
        return
    dx = int(round(74 * (1 - eo_expo(p))))
    x, y = CARD_X + dx, CARD_Y

    lay = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rectangle([0, 0, CARD_W - 1, CARD_H - 1], fill=INK + (255,))
    dl.rectangle([0, 0, CARD_W - 1, 3], fill=AMBER + (255,))     # 顶沿一条琥珀
    dl.rectangle([0, 0, CARD_W - 1, CARD_H - 1], outline=(74, 67, 55, 255), width=2)
    text(dl, (30, 72), "ZERO WARNING", mono(38, True), PAPER, 1.0)
    text(dl, (30, 126), "OUT OF BOUNDS", mono(38, True), PAPER, 1.0)
    dl.rectangle([30, 96, 30 + 96, 99], fill=(92, 84, 68, 255))  # 分隔线

    if a < 0.999:
        lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    c.paste(lay, (x, y), lay)


# ================================================================== ② 人味儿
def case_b(c, t, idx):
    if t < B1:
        _real(c, t, idx)
    else:
        _chain(c, t)


def _real(c, t, idx):
    """全屏。前一秒半还是数字的块，然后颜色回来——这是全片的落点。

    原素材（金拆除义体）本身构图有问题：一个头吊在大片空天底下。
    换成《金_夕阳》：0—6 秒是街道全景（正好配"罗曼的取景框"），
    4 秒起切到两人近景（配"只剩肉身的金"），切点落在口播换句的地方。
    """
    CUT = 166.42                      # 口播"或者失去了所有义体…"的起点
    if t < CUT:
        k = 6 + int(round((t - B0) * 30))          # 街道全景
        zoom, fy = 1.02, 0.46
    else:
        k = 122 + int(round((t - CUT) * 30))       # 两人近景
        zoom, fy = 1.04 + 0.05 * seg(t, CUT, B1), 0.44
    fr = prep.frame("jin_sunset", k)
    pim = cover(fr, (-6, -6, W + 12, H + 12), zoom=zoom, fx=0.50, fy=fy)

    melt = 1.0 - eo_quart(seg(t, B0, B0 + 0.28))
    if melt > 0.02:
        pim = pixelate(pim, int(round(lerp(1, 14, melt))))
        pim = posterize(pim, int(round(lerp(20, 8, melt))))
        pim = contrast(pim, 1.0 + 0.22 * melt)
    pim = tint(pim, (255, 238, 214), 0.055)
    c.paste(pim, (-6, -6))


# ================================================================== ③ 信号链
MOD_W, MOD_H, GAP = 380, 300, 120
CH_Y = 290
MID = CH_Y + MOD_H / 2                      # 440：连线与所有图标的水平轴
CH_X = [(W - (MOD_W * 3 + GAP * 2)) // 2 + i * (MOD_W + GAP) for i in range(3)]

T_GTR, T_L1, T_AMP, T_L2, T_REV = 169.72, 171.20, 172.60, 174.20, 175.40
T_PUSH = 176.50
COLORS = (AMBER, CYAN, RED)


class _Pen(object):
    """画在链上的笔：所有坐标先过一遍推镜变换，1.03 的推近不需要重画。"""

    def __init__(self, d, z=1.0, cx=960.0, cy=MID, ox=0.0, oy=0.0):
        self.d = d
        self.z = z
        self.cx = cx
        self.cy = cy
        self.ox = ox
        self.oy = oy

    def p(self, x, y):
        return (self.cx + (x - self.cx) * self.z - self.ox,
                self.cy + (y - self.cy) * self.z - self.oy)

    def pts(self, ps):
        return [self.p(x, y) for x, y in ps]

    def line(self, ps, col, th=2, joint=None):
        q = self.pts(ps)
        if len(q) < 2:
            return
        if joint and len(q) > 2:
            self.d.line(q, fill=col, width=int(round(th)), joint=joint)
        else:
            self.d.line(q, fill=col, width=int(round(th)))

    def poly(self, ps, col, th=2, close=True):
        q = self.pts(ps)
        if close:
            q = q + [q[0]]
        self.d.line(q, fill=col, width=int(round(th)), joint="curve")

    def rect(self, box, col, th=2):
        x, y, w, h = box
        if th <= 0:
            a, b = self.p(x, y)
            e, f = self.p(x + w, y + h)
            self.d.rectangle([a, b, e, f], fill=col)
            return
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], col, th)

    def rrect(self, box, r, col, th=2, gap=0.0):
        x, y, w, h = box
        x1, y1 = x + w, y + h
        d = self.d
        th = int(round(th))
        if gap <= 0:
            a, b = self.p(x, y)
            e, f = self.p(x1, y1)
            d.rounded_rectangle([a, b, e, f], int(round(r * self.z)), outline=col, width=th)
            return
        kk = math.cos(math.radians(gap))
        ins = r * (1 - kk)
        self.line([(x + ins, y), (x1 - ins, y)], col, th)
        self.line([(x1, y + ins), (x1, y1 - ins)], col, th)
        self.line([(x1 - ins, y1), (x + ins, y1)], col, th)
        self.line([(x, y1 - ins), (x, y + ins)], col, th)
        for (ccx, ccy, a0, a1) in ((x + r, y + r, 180 + gap, 270 - gap),
                                   (x1 - r, y + r, 270 + gap, 360 - gap),
                                   (x1 - r, y1 - r, gap, 90 - gap),
                                   (x + r, y1 - r, 90 + gap, 180 - gap)):
            a, b = self.p(ccx - r, ccy - r)
            e, f = self.p(ccx + r, ccy + r)
            d.arc([a, b, e, f], a0, a1, fill=col, width=th)

    def arc(self, box, a0, a1, col, th=2):
        x, y, w, h = box
        a, b = self.p(x, y)
        e, f = self.p(x + w, y + h)
        self.d.arc([a, b, e, f], a0, a1, fill=col, width=int(round(th)))

    def circle(self, xy, r, col, th=2):
        x, y = xy
        a, b = self.p(x - r, y - r)
        e, f = self.p(x + r, y + r)
        self.d.ellipse([a, b, e, f], outline=col, width=int(round(th)))

    def dot(self, x, y, r, col):
        a, b = self.p(x - r, y - r)
        e, f = self.p(x + r, y + r)
        self.d.ellipse([a, b, e, f], fill=col)


_RRM = {}


def _rr_mask(w, h, r):
    key = (w, h, r)
    m = _RRM.get(key)
    if m is None:
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
        _RRM[key] = m
    return m


def _fill_wipe(c, box, r, col, p):
    """模块点亮：墨色底从左往右灌进去。"""
    if p <= 0:
        return
    x, y, w, h = [int(round(v)) for v in box]
    m = _rr_mask(w, h, r)
    if p >= 0.995:
        c.paste(Image.new("RGBA", (w, h), col + (255,)), (x, y), m)
        return
    m2 = Image.new("L", (w, h), 0)
    m2.paste(m.crop((0, 0, max(1, int(w * p)), h)), (0, 0))
    c.paste(Image.new("RGBA", (w, h), col + (255,)), (x, y), m2)


def _catmull(ps, sub=8, closed=True):
    n = len(ps)
    out = []
    idx = (lambda i: ps[i % n]) if closed else (lambda i: ps[min(max(i, 0), n - 1)])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1, p2, p3 = idx(i - 1), idx(i), idx(i + 1), idx(i + 2)
        for s in range(sub):
            u = s / float(sub)
            u2, u3 = u * u, u * u * u
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * u
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * u
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)
            out.append((x, y))
    if closed:
        out.append(out[0])
    return out


# ------------------------------------------------------------------ 图标：Strat
def _ico_strat(pen, cx, cy, col, th=2):
    """Stratocaster 线条轮廓：双缺角琴身 + 琴颈 + 6 弦钮 + 3 单线圈 + 摇把。"""
    S, TH = 86.0, math.radians(-15.0)
    ca, sa = math.cos(TH), math.sin(TH)
    CXY = (cx, cy)

    def T(u, v):
        return (CXY[0] + (u * ca - v * sa) * S, CXY[1] - (u * sa + v * ca) * S)

    BODY = [(0.00, -0.660), (0.10, -0.655), (0.20, -0.635), (0.28, -0.580), (0.35, -0.480),
            (0.39, -0.360), (0.40, -0.260), (0.36, -0.160), (0.29, -0.060), (0.26, 0.020),
            (0.30, 0.120), (0.35, 0.220), (0.39, 0.320), (0.42, 0.410), (0.41, 0.480),
            (0.35, 0.520), (0.28, 0.460), (0.20, 0.360), (0.13, 0.280), (0.11, 0.260),
            (-0.11, 0.260), (-0.13, 0.290), (-0.20, 0.400), (-0.28, 0.480), (-0.36, 0.500),
            (-0.42, 0.400), (-0.42, 0.260), (-0.38, 0.140), (-0.31, 0.040), (-0.30, -0.040),
            (-0.35, -0.140), (-0.39, -0.260), (-0.38, -0.380), (-0.33, -0.490), (-0.25, -0.580),
            (-0.14, -0.645)]
    pen.poly([T(u, v) for u, v in BODY], col, th, close=True)

    def half_w(v):
        return lerp(0.105, 0.084, clamp01((v - 0.26) / 1.06))

    # 琴颈（两条边 + 品丝 + 上弦枕）
    pen.line([T(-0.105, 0.22), T(-0.084, 1.28)], col, th)
    pen.line([T(0.105, 0.22), T(0.084, 1.28)], col, th)
    for i in range(5):
        v = 0.34 + i * 0.142
        w = half_w(v)
        pen.line([T(-w, v), T(w, v)], col, 1)
    pen.line([T(-0.084, 1.28), T(0.084, 1.28)], col, th)

    # 琴头（6 弦钮在左缘，一排圆点）
    HEAD = [(-0.084, 1.28), (0.084, 1.28), (0.118, 1.44), (0.114, 1.64),
            (0.050, 1.76), (-0.050, 1.76), (-0.114, 1.64), (-0.118, 1.44)]
    pen.poly([T(u, v) for u, v in HEAD], col, th, close=True)
    for i in range(6):
        v = 1.36 + i * 0.070
        pen.dot(T(-0.168, v)[0], T(-0.168, v)[1], 2.3, col)

    # 三个单线圈拾音器
    for v in (-0.345, -0.070, 0.160):
        pen.poly([T(-0.135, v - 0.040), T(0.135, v - 0.040),
                  T(0.135, v + 0.040), T(-0.135, v + 0.040)], col, th, close=True)
    # 琴桥
    pen.poly([T(-0.150, -0.535), T(0.150, -0.535), T(0.150, -0.472), T(-0.150, -0.472)],
             col, th, close=True)
    # 摇把（末端一个小头，读起来是根杆子而不是游丝）
    trem = _catmull([(0.14, -0.50), (0.26, -0.56), (0.31, -0.66), (0.30, -0.76)], 6, False)
    pen.line([T(u, v) for u, v in trem], col, th, joint="curve")
    pen.dot(*T(0.30, -0.775), 2.6, col)
    # 六根弦：只画在琴身上，压在拾音器上
    for i in range(6):
        u = -0.075 + i * 0.030
        pen.line([T(u, -0.47), T(u, 0.26)], col, 1)


# ------------------------------------------------------------------ 图标：音箱
def _ico_amp(pen, cx, cy, col, th=2):
    """combo 音箱：箱体 + 控制面板（三个旋钮）+ 喇叭 + 提手。"""
    w, h = 186.0, 156.0
    x0, y0 = cx - w / 2, cy - h / 2
    pen.rrect((x0, y0, w, h), 10, col, th)
    # 控制面板
    pen.rect((x0 + 13, y0 + 13, w - 26, 36), col, th - 1)
    for i, kx in enumerate((cx - 46, cx, cx + 46)):
        pen.circle((kx, y0 + 31), 9, col, th - 1)
        a = -1.1 + i * 0.85
        pen.line([(kx, y0 + 31), (kx + 9 * math.cos(a), y0 + 31 + 9 * math.sin(a))], col, 1)
    # 喇叭
    pen.circle((cx, y0 + h - 56), 44, col, th)
    pen.circle((cx, y0 + h - 56), 13, col, th - 1)
    # 提手
    pen.arc((cx - 51, y0 - 36, 102, 72), 180, 360, col, th)
    pen.rect((cx - 61, y0 - 12, 15, 12), col, th - 1)
    pen.rect((cx + 46, y0 - 12, 15, 12), col, th - 1)
    # 脚
    pen.rect((x0 + 10, y0 + h, 22, 9), col, th - 1)
    pen.rect((x0 + w - 32, y0 + h, 22, 9), col, th - 1)


# ------------------------------------------------------------------ 图标：混响
def _spring(pen, x0, x1, y, amp, col, th=1.5):
    n = max(3, int(round((x1 - x0) / (amp * 0.74))))
    d = (x1 - x0) / float(n)
    for i in range(n):
        xa = x0 + i * d
        if i % 2 == 0:
            pen.arc((xa, y - amp, d, amp * 2), 180, 360, col, th)
        else:
            pen.arc((xa, y - amp, d, amp * 2), 0, 180, col, th)


def _ico_reverb(pen, cx, cy, col, th=2):
    """弹簧混响箱：外壳 + 三条弹簧 + 两端母线 + 两只脚。"""
    w, h = 226.0, 114.0
    x0, y0 = cx - w / 2, cy - h / 2
    pen.rrect((x0, y0, w, h), 11, col, th)
    pen.rrect((x0 + 12, y0 + 12, w - 24, h - 24), 7, col, th - 1)
    for y in (cy - 25, cy, cy + 25):
        _spring(pen, cx - 77, cx + 77, y, 7.4, col, th - 1)
    pen.line([(cx - 82, cy - 25), (cx - 82, cy + 25)], col, th - 1)
    pen.line([(cx + 82, cy - 25), (cx + 82, cy + 25)], col, th - 1)
    pen.line([(x0 + 12, cy), (cx - 82, cy)], col, th - 1)
    pen.line([(cx + 82, cy), (x0 + w - 12, cy)], col, th - 1)
    for fx in (x0 + 30, x0 + w - 48):
        pen.rect((fx, y0 + h, 18, 8), col, th - 1)


# ------------------------------------------------------------------ 模块
def _module_body(c, pen, i, on):
    x0, y0 = CH_X[i], CH_Y
    col_i = COLORS[i]
    lit = _mix(GRAY, col_i, on)
    ax, ay = pen.p(x0, y0)
    bx, by = pen.p(x0 + MOD_W, y0 + MOD_H)
    _fill_wipe(c, (ax, ay, bx - ax, by - ay), 16, INK2, on)

    pen.rrect((x0, y0, MOD_W, MOD_H), 16, lit, 2.4, gap=17)
    pen.rect((x0 + MOD_W / 2 - 62, y0 - 3, 124, 6), col_i, 0)      # 顶边彩条

    icol = WHITE if on > 0.5 else INK
    icx, icy = x0 + MOD_W / 2, CH_Y + 150
    if i == 0:
        _ico_strat(pen, icx - 2, icy + 46, icol, 2)
    elif i == 1:
        _ico_amp(pen, icx, icy, icol, 2)
    else:
        _ico_reverb(pen, icx, icy, icol, 2)

    # 脚踏开关
    fx, fy = x0 + MOD_W - 62, y0 + MOD_H - 44
    pen.rrect((fx, fy, 36, 21), 6, lit, 2)
    pen.dot(fx + 18, fy + 10.5, 3.2, lit)


def _module(c, pen, i, on, ap):
    """模块入场：0.3 秒从小到大、从虚到实。"""
    if ap >= 0.999:
        _module_body(c, pen, i, on)
        return
    x0 = CH_X[i]
    ox, oy = x0 - 8, CH_Y - 14
    lay = Image.new("RGBA", (MOD_W + 16, MOD_H + 30), (0, 0, 0, 0))
    p2 = _Pen(ImageDraw.Draw(lay), 0.94 + 0.06 * eo_expo(ap),
              cx=x0 + MOD_W / 2, cy=MID, ox=ox, oy=oy)
    _module_body(lay, p2, i, on)
    if ap < 0.999:
        lay.putalpha(lay.split()[3].point(lambda v: int(v * ap)))
    c.paste(lay, (int(ox), int(oy)), lay)


def _chain(c, t):
    z = 1.0 + 0.03 * eo_quart(seg(t, T_PUSH, 179.2))
    pen = _Pen(ImageDraw.Draw(c), z)

    on = [eo_expo(seg(t, T_GTR + 0.30, T_GTR + 0.52)),
          eo_expo(seg(t, T_AMP, T_AMP + 0.22)),
          eo_expo(seg(t, T_REV, T_REV + 0.22))]
    ap = [eo_expo(seg(t, T_GTR, T_GTR + 0.42)),
          eo_expo(seg(t, T_AMP - 1.28, T_AMP - 0.88)),
          eo_expo(seg(t, T_REV - 1.08, T_REV - 0.68))]

    # 连线：先在模块之间的空当里生长，再画模块（模块的边框盖住端口）
    link = [(CH_X[0] + MOD_W, CH_X[1], T_L1, 1),
            (CH_X[1] + MOD_W, CH_X[2], T_L2, 2)]
    prog = []
    for (xa, xb, t0, ci) in link:
        p = eo_expo(seg(t, t0, t0 + 0.45))
        prog.append(p)
        if p <= 0:
            continue
        xe = xa + (xb - xa) * p
        pen.line([(xa, MID), (xe, MID)], INK, 2)
        if p < 0.999:
            pen.dot(xe, MID, 4.5, COLORS[ci])

    for i in range(3):
        _module(c, pen, i, on[i], ap[i])

    # 端口：像真的插座，线到了才亮
    for (x, ci, p) in ((CH_X[0] + MOD_W, 1, prog[0]), (CH_X[1], 1, prog[0]),
                       (CH_X[1] + MOD_W, 2, prog[1]), (CH_X[2], 2, prog[1])):
        if p > 0:
            pen.circle((x, MID), 4.0, _mix(GRAY, COLORS[ci], p * on[ci]), 2)

    # 唯一的一行字：整条链下方，居中
    a = eo_expo(seg(t, 176.10, 176.62))
    if a > 0:
        dy = 42 * (1 - a)
        text(ImageDraw.Draw(c), (W // 2, 736 + dy), "人味儿特别足",
             serif(64), INK, 10.0, anchor="ms", alpha=a)
