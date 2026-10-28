# -*- coding: utf-8 -*-
"""预处理：把要用的视频片段切成定尺寸 JPEG 序列，顺手把字幕条与黑边裁掉、统一调色。

渲染时不碰视频解码，只读 JPEG 帧 → 帧耗时可控、结果确定。
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
W = os.path.join(ROOT, "work", "clips")

# name, 源文件, 入点, 时长, 裁掉底部px, 裁掉顶部px, 输出尺寸, 调色滤镜
J = [
    # 四大 OP：宽条用，1280 够
    ("op_bebop", "素材_外部/04_其他作品/星际牛仔_OP_Tank.mp4",        3.0, 14.0, 0, 0, (1280, 720), None),
    ("op_gits",  "素材_外部/04_其他作品/攻壳SAC_EP01含OP.mp4",         2.0, 14.0, 0, 0, (1280, 720), None),
    ("op_trigun","素材_外部/04_其他作品/Trigun_EP01_OP_去黑边去水印.mp4", 1.0, 10.0, 0, 0, (1280, 720), None),
    ("op_grave", "素材_外部/04_其他作品/铳墓_OP.mp4",                  1.0, 10.0, 0, 0, (1280, 720), None),
    # 寂静岭
    ("sh_fog",   "素材_外部/10_寂静岭/寂静岭_雾镇人影.mp4",             0.0, 8.0, 0, 78, (1280, 720),
     "eq=contrast=1.14:brightness=-0.04:saturation=0.28"),
    # 正片切片
    ("body",     "素材切片/S10_义体压迫感_01.mp4",                     0.0, 8.3, 140, 0, (1600, 900),
     "eq=contrast=1.12:brightness=-0.05:saturation=0.55"),
    ("roman",    "素材切片/S14_罗曼持机_04.mp4",                       0.5, 10.3, 140, 0, (1600, 900), None),
    ("finder",   "素材切片/S15_摄像取景框_04.mp4",                     0.0, 8.3, 140, 0, (1600, 900), None),
    ("eye",      "素材切片/S17_义眼特写_01.mp4",                       0.0, 8.3, 140, 0, (1600, 900),
     "eq=contrast=1.10:saturation=0.72"),
    ("squad",    "素材切片/S19_D与小队_06.mp4",                        0.3, 6.0, 140, 0, (1600, 900), None),
    ("shell",    "素材切片/S19_塔莉雅义体vs罗曼_07.mp4",               0.5, 13.0, 140, 0, (1600, 900), None),
    ("talia",    "素材切片/S22_塔莉雅结局_10.mp4",                     1.0, 16.5, 140, 0, (1600, 900), None),
    ("romanup",  "素材切片/S24_罗曼举机告别_10.mp4",                   0.5, 12.3, 140, 0, (1600, 900), None),
    ("romancall","素材切片/S24_罗曼喊话_10.mp4",                       0.0, 7.0, 140, 0, (1600, 900), None),
    # 用户指定：结尾/案例段的全屏素材
    ("talia_wire",  "素材切片/塔利亚调钢丝.mp4",                      0.0, 17.5, 140, 0, (1920, 1080),
     None),
    ("jin_sunset",  "素材切片/金_夕阳.mp4",                          0.0, 24.4, 140, 0, (1920, 1080), None),
    ("s2op",        "素材切片/S07_第二季开场OP_01.mp4",               28.5, 9.0, 200, 0, (1600, 900), None),
]


# 少数素材自带左右/上下留白（4:3 或 2:1 嵌在 16:9 里），先显式切掉再缩放
CROP_EXTRA = {
    "s2op": (1376, 1032, 272, 26),
}


# 少数素材自带左右/上下留白（4:3 或 2:1 嵌在 16:9 里），先显式切掉再缩放
CROP_EXTRA = {
    "s2op": (1376, 1032, 272, 26),
}


def build(only=None):
    os.makedirs(W, exist_ok=True)
    for name, rel, ss, dur, bot, top, (ow, oh), flt in J:
        if only and name not in only:
            continue
        src = os.path.join(A, rel)
        if not os.path.exists(src):
            print("MISSING", src)
            continue
        out = os.path.join(W, name)
        if os.path.isdir(out) and len(os.listdir(out)) > int(dur * 29):
            print("skip", name)
            continue
        os.makedirs(out, exist_ok=True)
        ch = "ih-%d-%d" % (bot, top)
        if name in CROP_EXTRA:
            cw, cy, cx0, cy0 = CROP_EXTRA[name]
            vf = "crop=%d:%d:%d:%d" % (cw, cy, cx0, cy0)
        else:
            vf = "crop=iw:%s:0:%d" % (ch, top)
        vf += ",scale=%d:%d:force_original_aspect_ratio=increase" % (ow, oh)
        vf += ",crop=%d:%d" % (ow, oh)
        if flt:
            vf += "," + flt
        vf += ",fps=30"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(ss), "-t", str(dur),
               "-i", src, "-vf", vf, "-q:v", "3",
               os.path.join(out, "%04d.jpg").replace("\\", "/")]
        print("->", name, dur, "s")
        subprocess.run(cmd, check=True)
        n = len(os.listdir(out))
        print("   %d frames" % n)


def count(name):
    p = os.path.join(W, name)
    return len(os.listdir(p)) if os.path.isdir(p) else 0


def frame(name, k):
    """按 30fps 取第 k 帧（自动回绕），给渲染用。"""
    from PIL import Image
    n = count(name)
    if n == 0:
        raise RuntimeError("clip %s 未预处理" % name)
    k = int(k) % n
    return Image.open(os.path.join(W, name, "%04d.jpg" % (k + 1))).convert("RGB")


if __name__ == "__main__":
    build(sys.argv[1:] or None)
