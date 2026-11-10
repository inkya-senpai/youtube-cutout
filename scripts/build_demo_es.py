import subprocess,sys
src,out=sys.argv[1],sys.argv[2]
segs=[(40.90,45.33),(0.30,8.23),(13.73,21.80),(21.80,25.03),(27.57,40.90)]
SP=1.25; F=0.04
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
fc=[]
for i,(s,e) in enumerate(segs):
    d=e-s
    fc.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,crop=1080:608:0:420[v{i}]")
    fc.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d={F},afade=t=out:st={d-F:.3f}:d={F}[a{i}]")
n=len(segs)
fc.append(''.join(f"[v{i}][a{i}]" for i in range(n))+f"concat=n={n}:v=1:a=1[cv][ca]")
fc.append(f"[cv]setpts=PTS/{SP},fps=30[sv]")
fc.append(f"[ca]atempo={SP}[outa]")
fc.append("color=black:s=1080x1920:r=30[bg]")
fc.append("[bg][sv]overlay=0:600:shortest=1,"
  f"drawtext=fontfile={font}:text='ベンチャーは通るのに':fontsize=88:fontcolor=white:borderw=6:bordercolor=black:x=(w-tw)/2:y=330,"
  f"drawtext=fontfile={font}:text='大手ESだけ落ちる':fontsize=112:fontcolor=#FFE600:borderw=6:bordercolor=black:x=(w-tw)/2:y=445[outv]")
cmd=['ffmpeg','-v','error','-y','-i',src,'-filter_complex',';'.join(fc),'-map','[outv]','-map','[outa]',
     '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',out]
subprocess.run(cmd,check=True)
