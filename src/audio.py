# -*- coding: utf-8 -*-
"""声音：口播+伴奏（用户已混好，一个采样都不动）+ 纯音效轨。

不再铺 OST、不做闪避、不做低切、不做 tanh 限幅、不做整体淡出。
唯一处理：若叠加后总峰值超过 -0.3 dBFS，只给音效轨一个静态增益。

输出 work/sfx.wav（纯音效轨）与 work/master.wav（48k / 立体声 / 24bit）。
"""
import os
import subprocess
import wave
import numpy as np

import data as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
N = int(round(D.DUR * SR))
rng = np.random.default_rng(20261028)

# 24bit 满刻度
FULL = 8388607.0
TARGET_DB = -0.3
# 口播+伴奏 已顶到 0 dBFS，音效没有余量。给整条伴奏一个静态推子（不是效果器），
# 让出 3 dB 头room，音效才听得见。人声不动。
BED_TRIM_DB = -3.0
TARGET = 10 ** (TARGET_DB / 20.0)
# 数字满刻度（留 1 LSB/16 的余量，保证 24bit 落盘不溢出）
CEILING = 1.0 - 1e-6


# ------------------------------------------------------------------ 读音频
def db(x):
    return 10 ** (x / 20.0)


def dbfs(x):
    return 20 * np.log10(max(float(x), 1e-9))


def _read24(path):
    """按 s32 读回（ffmpeg 把 s24 左移 8 位），再右移还原成精确的 24bit 整数值。

    这样人声既能参与 float64 运算，又能逐比特还原，不会被 float32 舍入动到。
    """
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path,
                          "-ac", "2", "-ar", str(SR), "-f", "s32le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(out, np.int32)
    if a.size % 2:
        a = a[:-1]
    return (a.reshape(-1, 2).astype(np.int32) >> 8).astype(np.int32)


def _write24(path, x):
    """写 24bit PCM。不做任何限幅以外的处理，调用方保证 |x| <= 1。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = np.round(np.clip(x, -1, 1) * FULL).astype(np.int32).reshape(-1)
    b = np.zeros((pcm.size, 3), np.uint8)
    b[:, 0] = (pcm & 0xFF).astype(np.uint8)
    b[:, 1] = ((pcm >> 8) & 0xFF).astype(np.uint8)
    b[:, 2] = ((pcm >> 16) & 0xFF).astype(np.uint8)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(b.tobytes())
    return pcm.size / 2 / SR


# ------------------------------------------------------------------ 音效合成
def _env(n, a=0.002, d=0.06):
    t = np.arange(n) / SR
    at = np.clip(t / max(a, 1e-4), 0, 1)
    dc = np.exp(-t / max(d, 1e-4))
    return at * dc


def sfx_tick(gain=0.5):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    s = rng.normal(0, 1, n) * np.exp(-t / 0.004) * 0.55
    s += np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.012) * 0.35
    s += np.sin(2 * np.pi * 620 * t) * np.exp(-t / 0.02) * 0.30
    return _st(s * gain)


def sfx_click(gain=0.5):
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    s = rng.normal(0, 1, n) * np.exp(-t / 0.006)
    s = s - np.concatenate([[0], s[:-1]]) * 0.7
    return _st(s * gain * 0.8)


def sfx_thump(gain=0.7):
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    f = 84 * np.exp(-t / 0.12) + 42
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.16)
    s += rng.normal(0, 1, n) * np.exp(-t / 0.008) * 0.35
    return _st(s * gain)


def sfx_whoosh(gain=0.35, dur=0.42):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    # 简易带通：差分的滑动平均
    k = max(2, int(SR / 900))
    sm = np.convolve(x, np.ones(k) / k, mode="same")
    ampe = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    return _st(sm * ampe * gain * 6.0)


def sfx_riser(gain=0.3, dur=1.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    k = 24
    sm = np.convolve(x, np.ones(k) / k, mode="same")
    sweep = np.sin(2 * np.pi * (200 * t + 900 * t * t / dur)) * 0.4
    ampe = np.clip(t / dur, 0, 1) ** 2
    return _st((sm * 4.0 + sweep) * ampe * gain)


def sfx_tape(gain=0.3, dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = rng.normal(0, 1, n) * 0.25
    s *= 1 + 0.8 * np.sin(2 * np.pi * 7.3 * t)
    s *= np.exp(-t / (dur * 0.5))
    return _st(s * gain)


def sfx_shutter(gain=0.5):
    n = int(0.14 * SR)
    t = np.arange(n) / SR
    s = rng.normal(0, 1, n) * np.exp(-t / 0.008)
    s += rng.normal(0, 1, n) * np.exp(-np.clip(t - 0.06, 0, None) / 0.01) * (t > 0.06)
    return _st(s * gain * 0.7)


def sfx_drone(gain=0.30, dur=10.0):
    """工业底噪：低频轰 + 金属摩擦。不按小节，故意没有拍子。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    k = 320
    sm = np.convolve(x, np.ones(k) / k, mode="same")
    low = np.sin(2 * np.pi * 38.0 * t + 0.6 * np.sin(2 * np.pi * 0.13 * t))
    body = sm * 3.2 + low * 0.5
    ampe = 1.0 + 0.35 * np.sin(2 * np.pi * 0.09 * t)
    return _st(body * ampe * gain)


def sfx_clank(gain=0.4):
    """砸钢管：多个非谐分音的金属回声。"""
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f, d, a in ((412, 0.42, 0.5), (946, 0.28, 0.30), (1583, 0.18, 0.18),
                    (2417, 0.10, 0.10), (67, 0.55, 0.30)):
        s += np.sin(2 * np.pi * f * t) * np.exp(-t / d) * a
    s += rng.normal(0, 1, n) * np.exp(-t / 0.006) * 0.5
    return _st(s * gain * 0.55)


def _st(s, pan=0.0):
    if s.ndim == 1:
        l = s * (1 - max(0, pan))
        r = s * (1 + min(0, pan))
        return np.stack([l, r], 1)
    return s


# ------------------------------------------------------------------ 事件表
def events():
    """(时间, 类型, 增益dB, 声像)"""
    ev = []
    # 每条字幕一次极轻的落点
    for c in D.CUES:
        ev.append((c["t0"], "tick", -31.0, 0.0))
    # 段落切换
    for sid, t0, t1, code, name in D.SECTIONS:
        if t0 > 0.1:
            ev.append((t0, "click", -24.0, -0.15))
    # 幕界
    for code, a0, a1 in D.ACTS:
        if a0 > 0.1:
            ev.append((a0, "thump", -15.0, 0.0))
    # 手工强调
    for t, k, g, p in [
        (0.10, "whoosh", -20.0, 0.0),
        (3.60, "click", -18.0, -0.3),
        (6.14, "click", -18.0, 0.3),
        (8.80, "thump", -12.0, 0.0),
        (11.42, "riser", -16.0, 0.0),
        (17.44, "whoosh", -16.0, 0.0),
        (19.56, "click", -16.0, 0.0),
        (24.10, "thump", -9.0, 0.0),
        (24.10, "shutter", -12.0, 0.0),
        (25.30, "whoosh", -17.0, 0.2),
        (35.48, "whoosh", -14.0, -0.2),
        (38.05, "whoosh", -16.0, 0.2),
        (40.76, "whoosh", -16.0, -0.2),
        (42.34, "whoosh", -16.0, 0.2),
        (44.50, "tape", -14.0, 0.0),
        (47.26, "thump", -14.0, 0.0),
        (50.72, "thump", -11.0, 0.0),
        (52.42, "click", -12.0, 0.0),
        (55.01, "riser", -20.0, 0.0),
        (64.56, "shutter", -10.0, -0.2),
        (65.86, "shutter", -10.0, 0.2),
        (67.70, "click", -14.0, 0.0),
        (70.04, "thump", -13.0, 0.0),
        (73.02, "whoosh", -11.0, 0.0),
        (75.62, "tape", -16.0, 0.0),
        (78.02, "click", -13.0, 0.0),
        (86.20, "thump", -13.0, 0.0),
        (90.66, "tape", -15.0, 0.0),
        (93.40, "click", -12.0, -0.4),
        (94.42, "click", -12.0, 0.4),
        (95.20, "thump", -12.0, 0.0),
        (97.18, "whoosh", -14.0, 0.0),
        (104.96, "thump", -13.0, 0.0),
        (106.30, "riser", -14.0, 0.0),
        (118.86, "shutter", -12.0, 0.0),
        (123.14, "tape", -14.0, 0.0),
        (126.10, "thump", -12.0, 0.0),
        (129.04, "riser", -16.0, 0.0),
        (135.94, "thump", -10.0, 0.0),
        (140.10, "click", -13.0, 0.0),
        (148.58, "click", -13.0, 0.0),
        (160.84, "click", -12.0, 0.0),
        (162.90, "tape", -14.0, 0.0),
        (166.50, "shutter", -13.0, 0.0),
        (169.75, "whoosh", -15.0, 0.0),
        (175.70, "tape", -16.0, 0.0),
        (178.42, "thump", -12.0, 0.0),
        (179.80, "riser", -15.0, 0.0),
        (181.02, "thump", -6.0, 0.0),
        (183.38, "click", -14.0, 0.0),
        (195.40, "thump", -13.0, 0.0),
        (204.62, "tape", -15.0, 0.0),
        (206.20, "thump", -11.0, 0.0),
        (214.34, "tape", -18.0, 0.0),
        (217.74, "click", -16.0, 0.0),
        (218.30, "whoosh", -17.0, 0.0),
        (222.90, "tape", -18.0, 0.0),
    ]:
        ev.append((t, k, g, p))
    return ev


KINDS = {
    "tick": sfx_tick,
    "click": sfx_click,
    "thump": sfx_thump,
    "whoosh": sfx_whoosh,
    "riser": sfx_riser,
    "tape": sfx_tape,
    "shutter": sfx_shutter,
    "clank": sfx_clank,
}


# ------------------------------------------------------------------ 静态增益
def solve_static_gain(bed, sfx, ceiling):
    """求音效轨可用的最大静态增益 g∈[0,1]，使 max|bed + g*sfx| <= ceiling。

    叠加对 g 是线性的，所以逐采样的可行域是一个区间：
        -c <= b + g*s <= c
    对所有采样、两个声道求交集，取上界即为精确解（无需迭代）。

    返回 (g, feasible)。
    """
    hi, lo = np.inf, -np.inf
    chunk = 1 << 21
    for ch in range(2):
        b_all = bed[:, ch].astype(np.float64)
        s_all = sfx[:, ch].astype(np.float64)
        for i in range(0, b_all.size, chunk):
            b = b_all[i:i + chunk]
            s = s_all[i:i + chunk]
            ok = np.abs(s) > 1e-12
            # s == 0 的采样不能被 g 影响，只能靠 ceiling 本身兜住
            if np.any(~ok & (np.abs(b) > ceiling)):
                return 0.0, False
            b, s = b[ok], s[ok]
            if b.size == 0:
                continue
            u1 = (ceiling - b) / s
            u2 = (-ceiling - b) / s
            # 每个采样可接受的 g 是两根之间的闭区间
            hi = min(hi, float(np.maximum(u1, u2).min()))
            lo = max(lo, float(np.minimum(u1, u2).max()))
    if lo > hi:
        return 0.0, False
    g = min(1.0, hi)
    if g < 0.0:
        return 0.0, False
    return g, True


# ------------------------------------------------------------------ 主工程
def build():
    print("读口播+伴奏…")
    bed_i = _read24(os.path.join(ROOT, "audio", "口播+伴奏.wav"))
    nb = len(bed_i)
    n = max(nb, N)
    bed = np.zeros((n, 2), np.float64)
    bed[:nb] = bed_i.astype(np.float64) / FULL
    peak_bed = np.abs(bed).max()
    print("  长度 %.6f s / %d 采样" % (nb / SR, nb))
    print("  口播峰值 %.2f dBFS" % dbfs(peak_bed))

    print("渲染音效轨（无 EQ / 无压缩 / 无混响）…")
    sfx = np.zeros((n, 2), np.float32)

    # 山冈晃段落：没有配乐，只有机器。
    t0, t1 = 50.72, 78.02
    d = sfx_drone(0.30, t1 - t0 + 0.2) * db(-26.0)
    i0 = int(t0 * SR)
    m = min(len(d), n - i0)
    sfx[i0:i0 + m] += d[:m]
    for tt, gg, pp in ((52.42, -19, -0.3), (55.20, -24, 0.3), (57.90, -22, -0.2),
                       (61.30, -17, 0.2), (64.56, -14, -0.35), (65.90, -14, 0.35),
                       (67.75, -18, 0.0), (70.10, -15, 0.0), (73.05, -13, 0.0),
                       (75.70, -16, 0.0)):
        s = sfx_clank() * db(gg)
        i0 = int(tt * SR)
        m = min(len(s), n - i0)
        s = s[:m].copy()
        s[:, 0] *= (1 - max(0, pp) * 0.6)
        s[:, 1] *= (1 + min(0, pp) * 0.6)
        sfx[i0:i0 + m] += s

    for t, kind, gdb, pan in events():
        s = KINDS[kind]()
        s = s * db(gdb)
        i0 = int(t * SR)
        m = min(len(s), n - i0)
        if m > 0:
            if pan:
                s[:, 0] *= (1 - max(0, pan) * 0.5)
                s[:, 1] *= (1 + min(0, pan) * 0.5)
            sfx[i0:i0 + m] += s[:m]

    bed = bed * db(BED_TRIM_DB)
    print("  伴奏静态推子 %.1f dB → 峰值 %.2f dBFS" % (BED_TRIM_DB, dbfs(np.abs(bed).max())))
    peak_sfx = np.abs(sfx).max()
    print("  音效轨峰值 %.2f dBFS（未加增益）" % dbfs(peak_sfx))

    # ------------------------------------------------ 只对音效轨做静态增益
    g, ok = solve_static_gain(bed, sfx, TARGET)
    if ok:
        print("  静态增益 %.2f dB（系数 %.6f），总峰值 %.2f dBFS <= %.1f dBFS"
              % (dbfs(g), g, dbfs(np.abs(bed + sfx * g).max()), TARGET_DB))
    else:
        # 口播+伴奏本身已越过 -0.3 dBFS，-0.3 目标在不动人声的前提下无解。
        # 退而求其次：只给音效轨降增益，保证叠加后不超过数字满刻度、绝不削波。
        print("  [警告] 口播+伴奏自身峰值 %.2f dBFS（真峰值同量级），"
              % dbfs(peak_bed))
        print("         零余量：不动人声时 -0.3 dBFS 无解，音效只能压到「恰好不溢出」。")
        g, _ = solve_static_gain(bed, sfx, CEILING)
        print("  静态增益 %.2f dB（系数 %.6f），总峰值 %.3f dBFS（未削波）"
              % (dbfs(g), g, dbfs(np.abs(bed + sfx * g).max())))
        # 供决策参考：不同音效增益下音效与成品的电平
        print("  备选（人工指定音效增益时）：")
        for alt in (0.0, -6.0, -12.0, -20.0):
            k = db(alt)
            print("    音效 %6.1f dB → 音效峰值 %6.2f dBFS / 成品峰值 %+6.3f dBFS"
                  % (alt, dbfs(np.abs(sfx).max() * k),
                     dbfs(np.abs(bed + sfx * k).max())))
    sfx = (sfx * g).astype(np.float64)

    # float64 求和：音效为 0 的采样与人声逐比特一致
    master = bed + sfx
    peak_mix = np.abs(master).max()
    print("  成品峰值 %.2f dBFS" % dbfs(peak_mix))
    if peak_mix > 1.0:
        print("  [错误] 成品溢出！")

    # ------------------------------------------------ 输出
    p_sfx = os.path.join(ROOT, "work", "sfx.wav")
    dur = _write24(p_sfx, sfx)
    print("→", p_sfx, "%.6f s" % dur, "峰值 %.2f dBFS" % dbfs(np.abs(sfx).max()))

    p_mix = os.path.join(ROOT, "work", "master.wav")
    dur = _write24(p_mix, master)
    print("→", p_mix, "%.6f s" % dur, "峰值 %.2f dBFS" % dbfs(peak_mix))


if __name__ == "__main__":
    build()
