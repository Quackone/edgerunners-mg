# -*- coding: utf-8 -*-
"""渲染：多进程逐帧绘制 → RGB 原始字节灌进 ffmpeg → 一次编码出片。

用法：
  python render.py               全片
  python render.py --a 1500 --b 2100 --out work/seg.mp4   只渲一段（改画面时用）
"""
import os
import sys
import subprocess
import argparse
import multiprocessing as mp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from design import W, H, FPS
import data as D


def _init():
    global _film
    import film
    _film = film


def _draw(i):
    return _film.draw(i / float(FPS), i).tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=int, default=0)
    ap.add_argument("--b", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--audio", default=None)
    ap.add_argument("--jobs", type=int, default=0)
    ap.add_argument("--no-audio", action="store_true")
    a = ap.parse_args()

    total = int(round(D.DUR * FPS))
    f0 = a.a
    f1 = a.b if a.b > 0 else total
    out = a.out or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "out", "成片.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    wav = a.audio or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "work", "master.wav")
    jobs = a.jobs or max(1, min(14, (os.cpu_count() or 4) - 2))

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-"]
    if not a.no_audio:
        cmd += ["-i", wav,
                "-ss", "%.4f" % (f0 / float(FPS)), "-t", "%.4f" % ((f1 - f0) / float(FPS))]
    cmd += ["-c:v", "h264_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr",
            "-b:v", "10M", "-maxrate", "12M", "-bufsize", "20M", "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-g", "60", "-bf", "2"]
    if not a.no_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [out]

    print("帧 %d → %d  共 %d 帧  %d 进程" % (f0, f1, f1 - f0, jobs))
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    idx = range(f0, f1)
    n = 0
    with mp.Pool(jobs, initializer=_init) as pool:
        for buf in pool.imap(_draw, idx, chunksize=3):
            p.stdin.write(buf)
            n += 1
            if n % 300 == 0:
                print("  %d / %d" % (n, f1 - f0), flush=True)
    p.stdin.close()
    rc = p.wait()
    print("ffmpeg rc=%d → %s" % (rc, out))
    return rc


if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())
