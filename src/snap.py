# -*- coding: utf-8 -*-
"""调试：渲染若干指定时间点的单帧，用于看版式。"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib
import frame as F
from design import W, H


def grab(t, name=None):
    import film
    importlib.reload(film)
    t0 = time.time()
    im = film.draw(t, int(round(t * 30)))
    dt = time.time() - t0
    name = name or ("f_%06.2f" % t).replace(".", "_")
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work", "prev", name + ".png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out)
    print("%-28s %5.1fms  %s" % (name, dt * 1000, out))
    return out


if __name__ == "__main__":
    ts = [float(x) for x in sys.argv[1:]] or [5.0]
    for t in ts:
        grab(t)
