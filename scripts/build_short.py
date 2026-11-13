# パターン2（取材動画）のショートを書き出す
# 使い方: python3 scripts/build_short.py config.json
# config: {"src": 元動画, "out": 出力, "crop": [w,h,x,y] or null, "segments": [[開始,終了],...],
#          "title1": 白の1行目, "title2": 黄色の2行目, "speed": 1.25}
import json, subprocess, sys
c = json.load(open(sys.argv[1]))
SP = c.get("speed", 1.25); F = 0.04
font = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
crop = c.get("crop")
MAXW = 940  # 左右60pxの安全範囲に収める

def fit(text, size):
    """文字幅がMAXWを超える場合だけフォントサイズを小さくする"""
    try:
        from PIL import ImageFont
        while size > 60 and ImageFont.truetype(font, size, index=0).getlength(text) > MAXW:
            size -= 2
    except ImportError:
        pass
    return size

s1, s2 = fit(c["title1"], 88), fit(c["title2"], 112)
vf0 = (f"crop={crop[0]}:{crop[1]}:{crop[2]}:{crop[3]}," if crop else "") + "scale=1080:608,setsar=1"
fc = []
for i, (s, e) in enumerate(c["segments"]):
    d = e - s
    fc.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,{vf0}[v{i}]")
    fc.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d={F},afade=t=out:st={d-F:.3f}:d={F}[a{i}]")
n = len(c["segments"])
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")
fc.append(f"[cv]setpts=PTS/{SP},fps=30[sv]")
fc.append(f"[ca]atempo={SP}[outa]")
fc.append("color=black:s=1080x1920:r=30[bg]")
fc.append("[bg][sv]overlay=0:600:shortest=1,"
          f"drawtext=fontfile={font}:text='{c['title1']}':fontsize={s1}:fontcolor=white:borderw=6:bordercolor=black:x=(w-tw)/2:y=330,"
          f"drawtext=fontfile={font}:text='{c['title2']}':fontsize={s2}:fontcolor=#FFE600:borderw=6:bordercolor=black:x=(w-tw)/2:y=445[outv]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c["src"], "-filter_complex", ";".join(fc),
                "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", c["out"]], check=True)
