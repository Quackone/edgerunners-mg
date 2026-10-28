# edgerunners-mg

一个**逐帧用代码画出来**的音乐解析影片引擎。整片 3 分 50 秒、1920×1080、30fps，没有一帧是在剪辑软件里拖出来的——每一帧都是 Python 算出来的图，再由 ffmpeg 编码成片。

原本用来做一支《赛博朋克：边缘行者》两季配乐的解析视频（B 站 up 主 Yuri0）。视频本体和素材不在这个仓库里，见下面「为什么不含素材」。

## 它是什么样的

片子由 **97 条时间码**驱动：字幕、章节、每一次镜头切换都写在 `data.py` 里，画面是 `t` 的纯函数。

```python
film.draw(t, idx)  ->  PIL.Image(1920×1080)
```

纯函数意味着同一时刻永远画出同一张图，可以多进程并行、可以单帧回放调试、可以只重渲一段。

```
src/
  design.py     色板 / 字体 / 绘图基元 / 颗粒 / 调色 / 「两秒法则」
  data.py       97 条字幕、章节表、曲目表
  film.py       驱动器：时间 → 画面；段落派发、纸墨底切换、转场、字幕带
  frame.py      底部信息带、字幕、遮幅
  prep.py       把视频素材切成逐帧 JPEG（带裁剪/缩放/调色）
  s_open.py     序：评论洪流 / 开机 / 片名
  s_people.py   两位作曲家 / 四大 OP
  s_yamaoka.py  工业噪音段落
  s_imahori.py  拍子、套五套七、二元对立
  s_two.py      老派摄影机 / 曲目表 / 模拟
  s_binary.py   0-1 网格、复制重影、撕裂、CAPRI
  s_case.py     位深削减 / 信号链 UI
  s_end.py      结尾
  sutil.py      文字与卡片的小工具
  audio.py      音效合成、混音、出母带
  render.py     多进程渲染 → ffmpeg rawvideo 管道
  snap.py       单帧/多帧快照，改画面时用
```

## 三个我觉得值得抄走的东西

**1. 帧 → ffmpeg stdin 管道，不落 PNG 序列。**
`render.py` 把每帧的 RGB 字节直接灌进 ffmpeg：

```python
ffmpeg -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 30 -i - ...
```

PNG 压缩会吃掉三分之二的渲染时间，而且几十万个小文件写盘会触发各种配额限制。走管道，5 分钟出一部 4 分钟的片子。

**2. 纯函数 + 多进程。**
`draw(t, idx)` 不碰时钟、不碰全局状态，所以 `multiprocessing.Pool` 是免费的。确定性也让「改一个 2 秒的镜头」变成「只重渲那 60 帧」。

**3. 「两秒法则」（写在 `design.py` 文档头）。**
这套东西最初做成了「海报」——大字上下都垫小字注脚、编号、英文对译、规格表。问题在于：观众在一个版面上只停一到两秒，而且多半在手机上看；小于 40px 的中文在手机上是看不见的，它不是信息，是给版面配重。

于是定了三条：

- 一个镜头只有一个可读层；
- 空出来的地方给**尺寸**（主角做到出血）、**运动**（推镜/走带/切片）、**材质**（图铺满，字压上去），不给文字；
- 真需要留白就真的留白，但必须由运动支撑。

代码里注释都在按这条写。如果你要做类似的片子，这条比任何代码都有用。

## 跑起来

需要 Python 3.10+、`ffmpeg` 在 PATH 里。

```bash
pip install -r requirements.txt
```

然后准备素材目录（仓库里没有，见下节）：

```
assets/
  素材_外部/…     图片、OST 波形图、人物照
  work/clips/…    由 prep.py 从视频切片生成的逐帧 JPEG
```

```bash
python src/prep.py                  # 切素材
python src/snap.py 12.0 45.5 133   # 抽几帧看看
python src/render.py                # 全片
python src/render.py --a 4500 --b 4700 --out work/seg.mp4   # 只渲一段
python src/audio.py                 # 混音
```

`snap.py` 是开发时最有用的东西：给它秒数，它把帧吐到 `work/prev/`，你看着改。

## 为什么不含素材

这个仓库**只有代码**，没有一帧画面、没有一个音符。原因很直接：

- 片中引用的动画画面、原声带音频、游戏美术，版权属于 Studio TRIGGER / CD PROJEKT RED / 各自的唱片公司；
- 评论截图里是真实用户的 ID 和头像；
- 字体里 Consolas 是微软的商业字体，不可再分发（Noto Sans SC 和 Source Han Serif 是 OFL，可以）。

所以这是一个**渲染引擎**，不是一个可复现的成品。你要用它，得自己准备素材，并且自己承担素材的版权。

## 许可

GPL-3.0。见 [LICENSE](LICENSE)。

---

做过的东西里，代码可以开源，画面不行。这个仓库就是那条线左边的部分。
