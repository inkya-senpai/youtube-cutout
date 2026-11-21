# パターン1（通常の長尺動画）のショートを書き出す：字幕とアイコンを追加
# 使い方: python3 scripts/build_short_p1.py config.json
# config: {"src","out","crop":[w,h,x,y] or null,"segments":[[s,e],...],
#          "title1","title2","subs":[[s,e,"1行目\\N2行目"],...]（元動画の時刻）,"icon","speed"}
import json, subprocess, sys, os, tempfile
c = json.load(open(sys.argv[1]))
SP = c.get("speed", 1.25); F = 0.04
font = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
MAXW = 940
def fit(text, size):
    from PIL import ImageFont
    while size > 60 and ImageFont.truetype(font, size, index=0).getlength(text) > MAXW:
        size -= 2
    return size
s1, s2 = fit(c["title1"], 88), fit(c["title2"], 112)
VY, VH = 600, 608          # 動画の位置と高さ
SUB_Y = VY + VH + 30       # 字幕の上端
ICON_D, ICON_Y = 240, 1430 # アイコンの直径と上端

# 字幕を出力の時間軸に変換してASSを作る
def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
segs = c["segments"]; offs = []; cum = 0
for s, e in segs:
    offs.append(cum); cum += e - s
lines = []
for s, e, text in c["subs"]:
    for (a, b), o in zip(segs, offs):
        if a - 0.01 <= s < b:
            os_ = (o + s - a) / SP; oe = (o + min(e, b) - a) / SP
            lines.append(f"Dialogue: 0,{ts(os_)},{ts(oe)},S,,0,0,0,,{text}")
            break
    else:
        print("字幕が区間外:", s, e, text)
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: S,Noto Sans CJK JP Black,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,8,60,60,{SUB_Y},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(lines) + "\n"
tmp = tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8"); tmp.write(ass); tmp.close()

crop = c.get("crop")
vf0 = (f"crop={crop[0]}:{crop[1]}:{crop[2]}:{crop[3]}," if crop else "") + f"scale=1080:{VH},setsar=1"
ins = []
for s_, e_ in segs:
    ins += ["-ss", f"{s_:.3f}", "-t", f"{e_ - s_ + 0.5:.3f}", "-i", c["src"]]
fc = []
for i, (s, e) in enumerate(segs):
    d = e - s
    fc.append(f"[{i}:v]trim=0:{d:.3f},setpts=PTS-STARTPTS,{vf0}[v{i}]")
    fc.append(f"[{i}:a]atrim=0:{d:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={F},afade=t=out:st={d-F:.3f}:d={F}[a{i}]")
n = len(segs)
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")
fc.append(f"[cv]setpts=PTS/{SP},fps=30[sv]")
fc.append(f"[ca]atempo={SP}[outa]")
fc.append(f"[{len(segs)}:v]scale={ICON_D}:{ICON_D}[ic]")
fc.append("color=black:s=1080x1920:r=30[bg]")
fc.append(f"[bg][sv]overlay=0:{VY}:shortest=1[b1];[b1][ic]overlay=(W-w)/2:{ICON_Y}[b2];"
          f"[b2]drawtext=fontfile={font}:text='{c['title1']}':expansion=none:fontsize={s1}:fontcolor=#FFE600:borderw=6:bordercolor=black:x=(w-tw)/2:y=330,"
          f"drawtext=fontfile={font}:text='{c['title2']}':expansion=none:fontsize={s2}:fontcolor=#FFE600:borderw=6:bordercolor=black:x=(w-tw)/2:y=445,"
          f"subtitles={tmp.name}[outv]")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + [ "-i", c.get("icon", "assets/inkya_icon.png"),
                "-filter_complex", ";".join(fc), "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-preset", "medium",
                "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", c["out"]], check=True)
os.unlink(tmp.name)
