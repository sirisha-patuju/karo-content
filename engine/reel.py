#!/usr/bin/env python3
"""Build a silent-music-free text reel from a spec. Usage: python3 engine/reel.py spec.json out.mp4
Slides are rendered 1080x1920; slide 1 is a bold hook frame shown from frame 0 (use thumb_offset 0 as cover).
Each slide 2.6s, 0.4s crossfade, slow zoom. Output H.264 + silent AAC, faststart, <5Mbps."""
import sys, json, subprocess, tempfile, os
spec=json.load(open(sys.argv[1])); out=sys.argv[2]; d=tempfile.mkdtemp()
subprocess.run([sys.executable,os.path.join(os.path.dirname(__file__),"render.py"),sys.argv[1],d,"1920"],check=True)
names=[s["name"] for s in spec["slides"]]; n=len(names); L=2.6; X=0.4
inp=[];flt=[]
for i,nm in enumerate(names):
    inp+=["-framerate","30","-loop","1","-t",str(L+X),"-i",f"{d}/{nm}.jpg"]
    flt.append(f"[{i}:v]scale=1188:2112,zoompan=z='1+0.0006*on':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,format=yuv420p,setsar=1[v{i}]")
cur="v0"; t=0
for i in range(1,n):
    t+=L; flt.append(f"[{cur}][v{i}]xfade=transition=fade:duration={X}:offset={t:.2f}[x{i}]"); cur=f"x{i}"
tot=L*n+X
cmd=["ffmpeg","-y","-v","error",*inp,"-f","lavfi","-t",f"{tot:.2f}","-i","anullsrc=r=44100:cl=stereo","-filter_complex",";".join(flt),"-map",f"[{cur}]","-map",f"{n}:a","-c:v","libx264","-crf","20","-maxrate","4M","-bufsize","8M","-preset","veryfast","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","96k","-shortest","-movflags","+faststart",out]
subprocess.run(cmd,check=True); print(out,round(tot,1),"s")
