#!/usr/bin/env python3
"""Karo launch-style reel builder.

usage: python3 build.py spec.json OUT_DIR [--preview]

Pipeline (same look and sound as the launch video):
  1. Kokoro TTS, voice am_michael at speed 1.3, one natural sentence per scene
  2. schedule scenes from the voice lengths
  3. synthesised music + SFX (kick/clap/hats/arps, whooshes, booms, risers) on those cuts
  4. voice EQ/compress/room + music ducking under the voice
  5. Chromium renders the motion-graphics page (template.html) frame by frame, 1080x1920 @30
  6. ffmpeg mux -> reel.mp4 (H.264 + AAC, faststart) and cover.jpg
Writes OUT_DIR/reel.mp4, cover.jpg, reel.json (duration, thumb_offset_ms, schedule).
--preview renders a contact sheet of key frames only (fast, no audio) so you can check layout.
"""
import json, os, sys, subprocess, shutil, math, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SR = 44100
FPS = 30
VOICE, SPEED = "am_michael", 1.3
MODEL_DIR = os.environ.get("KARO_MODELS", os.path.expanduser("~/.cache/karo-models"))
MODEL_URLS = {
    "kokoro.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}


def sh(cmd, **kw):
    print("+", cmd if isinstance(cmd, str) else " ".join(cmd), flush=True)
    subprocess.run(cmd, shell=isinstance(cmd, str), check=True, **kw)


def ensure_models():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, url in MODEL_URLS.items():
        p = os.path.join(MODEL_DIR, name)
        if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
            print("downloading", name, flush=True)
            urllib.request.urlretrieve(url, p + ".part")
            os.replace(p + ".part", p)
    return os.path.join(MODEL_DIR, "kokoro.onnx"), os.path.join(MODEL_DIR, "voices.bin")


# ---------------------------------------------------------------- voice
def make_voice(spec, wd):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    onnx, voices = ensure_models()
    k = Kokoro(onnx, voices)

    def trim(x):
        i = np.where(np.abs(x) > 0.01)[0]
        return x[max(0, i[0] - 100): i[-1] + 200]

    out = []
    for i, s in enumerate(spec["scenes"]):
        text = s.get("voice")
        if s["kind"] == "langs" and not text:
            text = "And it understands you in eight languages, including Hindi and Telugu."
            a, sr = k.create("And it understands you in eight languages, including", voice=VOICE, speed=SPEED, lang="en-us")
            h, _ = k.create("hˈɪndi", voice=VOICE, speed=SPEED, lang="en-us", is_phonemes=True)
            n, _ = k.create("and", voice=VOICE, speed=SPEED, lang="en-us")
            t, _ = k.create("tˈɛlʊɡˌu", voice=VOICE, speed=SPEED, lang="en-us", is_phonemes=True)
            g = np.zeros(int(sr * 0.04), dtype=np.float32)
            wav = np.concatenate([trim(a), g, trim(h), g, trim(n), g, trim(t)])
        elif text:
            wav, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us")
        else:
            out.append(None)
            continue
        idx = np.where(np.abs(wav) > 0.01)[0]
        wav = wav[max(0, idx[0] - 150): idx[-1] + 500]
        p = os.path.join(wd, f"v{i:02d}.wav")
        sf.write(p, wav, sr)
        out.append({"path": p, "dur": len(wav) / sr, "text": text})
        print(f"voice {i} {len(wav)/sr:.2f}s {text}", flush=True)
    return out


# ---------------------------------------------------------------- schedule
def make_schedule(spec, voices):
    sc = spec["scenes"]
    n = len(sc)
    kinds = [s["kind"] for s in sc]
    r = kinds.index("reveal") if "reveal" in kinds else -1
    m = kinds.index("morning")
    c = kinds.index("cta")
    S = [0.0] * n
    st = [None] * n
    for i in range(n):
        d = voices[i]["dur"] if voices[i] else 0.0
        kd = kinds[i]
        if i == 0:
            lead, gap, mn = 0.8, 0.05, 0.0
        elif kd == "cta":
            lead, gap, mn = 0.2, 0, 0
        elif kd == "morning":
            lead, gap, mn = 0.45, 1.2, 4.2
        elif kd == "reveal":
            lead, gap, mn = 0.10, 0.3, 3.2
        elif r >= 0 and i < r:
            lead, gap, mn = 0.08, (0.20 if i == r - 1 else 0.05), 0.0
        else:
            lead, gap, mn = 0.18, 0.3, 3.5
        if voices[i]:
            st[i] = S[i] + lead
        if kd == "cta":
            total = S[i] + 4.5
            break
        S[i + 1] = S[i] + max(mn, lead + d + gap)
    # cutaways (hard-cut punch-ins)
    cw = []
    for i, s in enumerate(sc):
        end = S[i + 1] if i + 1 < n else total
        kd = s["kind"]
        if kd == "flood":
            t = max(S[i] + 2.0, end - 1.35)
            cw.append(dict(t=t, k="A", badge=str(s["num"]),
                           notifs=s.get("cut_notifs") or [["Stripe", "Your receipt from Stripe"], ["Chase", "Your statement is ready"], ["Uber Eats", "20% off your next order"]]))
        elif kd == "calendar":
            t = min(S[i] + 1.6, end - 0.85)
            cw.append(dict(t=t, k="B", label=s.get("clash_label", "3 meetings. Same hour."),
                           events=s.get("clash") or [["Team sync", "10:00 AM"], ["Client call", "10:00 AM"], ["Quarterly review", "10:30 AM"]]))
        elif kd == "phone":
            t = min(S[i] + 1.9, end - 0.85)
            cw.append(dict(t=t, k="C", text=s.get("typed", "Hi Sarah, following up on the proposal we discussed"),
                           sub=s.get("typed_sub", "Reply number 61 today.")))
        elif kd == "ask" and s["reply"]["type"] in ("draft", "book", "reschedule"):
            ty = s["reply"]["type"]
            dflt = {"draft": ["Reply drafted", "Ready for your approval"],
                    "book": ["Meeting booked", "Invite sent"],
                    "reschedule": ["Meeting moved", "Everyone notified"]}[ty]
            a, b = s.get("done", dflt)
            cw.append(dict(t=min(S[i] + 1.8, end - 0.85), k="D", a=a, b=b))
    return dict(S=S[: n], voice=st, total=total, cw=cw, reveal=r, morning=m, cta=c)


# ---------------------------------------------------------------- mix
def mix(voices, sched, music_wav, out_wav):
    import soundfile as sf
    from scipy import signal
    from scipy.io import wavfile
    sr_m, music = wavfile.read(music_wav)
    music = music.astype(np.float64) / 32768
    N = len(music)
    vo = np.zeros(N)
    for v, st in zip(voices, sched["voice"]):
        if not v:
            continue
        s, sr = sf.read(v["path"])
        if s.ndim > 1:
            s = s.mean(axis=1)
        s = signal.resample_poly(s, SR, sr)
        f = int(0.008 * SR)
        s[:f] *= np.linspace(0, 1, f)
        s[-f:] *= np.linspace(1, 0, f)
        i = int(st * SR)
        vo[i:i + len(s)] += s[: N - i]
    b, a = signal.butter(2, 90 / (SR / 2), "high")
    vo = signal.lfilter(b, a, vo)
    bq, aq = signal.iirpeak(3000 / (SR / 2), 1.2)
    vo = vo + 0.4 * signal.lfilter(bq, aq, vo)
    env = np.abs(vo)
    blk = 256
    bm = np.array([env[i:i + blk].max() for i in range(0, N, blk)])
    sm = np.zeros_like(bm); c = 0.0
    for i, v in enumerate(bm):
        c = v if v > c else c * 0.9
        sm[i] = c
    gain_blk = np.where(sm > 0.25, (0.25 / np.maximum(sm, 1e-6)) ** 0.55, 1.0)
    vo = vo * np.repeat(gain_blk, blk)[:N]
    vo = vo / np.max(np.abs(vo)) * 0.92
    room = vo.copy()
    for ms, g in ((23, 0.10), (41, 0.07), (67, 0.05)):
        d = int(SR * ms / 1000)
        room[d:] += vo[:-d] * g
    vo = room / np.max(np.abs(room)) * 0.92
    act = np.abs(vo); blk = 441
    am = np.array([act[i:i + blk].max() for i in range(0, N, blk)])
    thr = (am > 0.04).astype(float)
    d = np.zeros_like(thr); c = 0.0
    for i, v in enumerate(thr):
        c = v if v > c else c * 0.88
        d[i] = c
    duck = np.repeat(1 - 0.58 * d, blk)[:N]
    duck = np.convolve(duck, np.ones(2205) / 2205, mode="same")
    m = music * duck[:, None]
    out = m.copy(); out[:, 0] += vo; out[:, 1] += vo
    out = out / np.max(np.abs(out)) * 0.89
    wavfile.write(out_wav, SR, (out * 32767).astype(np.int16))
    sp = np.abs(vo) > 0.02
    rms = lambda x: float(np.sqrt((x ** 2).mean()))
    print("VO rms", round(rms(vo[sp]), 3), "music-under-VO rms", round(rms(m[:, 0][sp]), 3), flush=True)


# ---------------------------------------------------------------- frames
SHOOT = r'''
import sys, os, asyncio, json
from playwright.async_api import async_playwright
html, outdir, mode = sys.argv[1], sys.argv[2], sys.argv[3]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("file://" + html)
        await pg.evaluate("document.fonts.ready")
        if mode == "keys":
            for t in [float(x) for x in sys.argv[4].split(",")]:
                await pg.evaluate(f"render({t})")
                await pg.screenshot(path=f"{outdir}/k_{t:06.2f}.jpg", type="jpeg", quality=88)
        else:
            s, e, step = int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
            for i in range(s, e, step):
                await pg.evaluate(f"render({i / 30})")
                await pg.screenshot(path=f"{outdir}/f{i:05d}.jpg", type="jpeg", quality=90)
        if errs: print("PAGE ERRORS", errs[:3])
        await b.close()
asyncio.run(main())
'''


def write_page(spec, sched, wd):
    html = open(os.path.join(HERE, "template.html")).read()
    html = html.replace("/*SPEC*/null", json.dumps(spec)).replace("/*SCHED*/null", json.dumps(sched))
    for f in ("fonts", "karo_ui.png"):
        dst = os.path.join(wd, f)
        if not os.path.exists(dst):
            (shutil.copytree if f == "fonts" else shutil.copy)(os.path.join(HERE, f), dst)
    p = os.path.join(wd, "page.html")
    open(p, "w").write(html)
    open(os.path.join(wd, "shoot.py"), "w").write(SHOOT)
    return p


def preview(spec, sched, wd, out):
    page = write_page(spec, sched, wd)
    S = sched["S"] + [sched["total"]]
    ts = []
    inw = lambda t: any(c["t"] - 0.05 <= t < c["t"] + 0.75 for c in sched["cw"])
    for i in range(len(spec["scenes"])):
        for off in (1.3, 2.9):
            t = S[i] + off
            if t < S[i + 1] - 0.2 and not inw(t):
                ts.append(t)
    for c in sched["cw"]:
        ts.append(c["t"] + 0.45)
    ts = sorted(set(round(t, 2) for t in ts))
    kd = os.path.join(wd, "keys"); os.makedirs(kd, exist_ok=True)
    sh([sys.executable, os.path.join(wd, "shoot.py"), page, kd, "keys", ",".join(str(t) for t in ts)])
    from PIL import Image
    files = sorted(os.listdir(kd))
    ims = [Image.open(os.path.join(kd, f)).resize((270, 480)) for f in files]
    cols = 8
    rows = math.ceil(len(ims) / cols)
    sheet = Image.new("RGB", (cols * 270, rows * 480))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
    sheet.save(out)
    print("preview", out, files)


def main():
    spec = json.load(open(sys.argv[1]))
    out_dir = os.path.abspath(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    wd = os.path.join(out_dir, "work"); os.makedirs(wd, exist_ok=True)
    voices = make_voice(spec, wd)
    sched = make_schedule(spec, voices)
    json.dump(sched, open(os.path.join(wd, "schedule.json"), "w"))
    print("schedule", [round(x, 2) for x in sched["S"]], "total", round(sched["total"], 2), flush=True)
    if not (29.0 <= sched["total"] <= 36.0) and "--force" not in sys.argv:
        raise SystemExit(f"DURATION {sched['total']:.1f}s is outside 29-36s: remove or add an ask/chips/langs scene or shorten voice lines, then rebuild")
    if "--preview" in sys.argv:
        preview(spec, sched, wd, os.path.join(out_dir, "preview.jpg"))
        return
    import sound
    sound.render_music(sched, os.path.join(wd, "music.wav"), seed=spec.get("seed", 7), key=spec.get("key", 0))
    mix(voices, sched, os.path.join(wd, "music.wav"), os.path.join(wd, "mix.wav"))
    page = write_page(spec, sched, wd)
    fr = os.path.join(wd, "frames"); shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
    nfr = int(math.ceil(sched["total"] * FPS))
    nw = int(os.environ.get("KARO_WORKERS", "3"))
    procs = [subprocess.Popen([sys.executable, os.path.join(wd, "shoot.py"), page, fr, "frames", str(w), str(nfr), str(nw)]) for w in range(nw)]
    for p in procs:
        if p.wait() != 0:
            raise SystemExit("frame worker failed")
    mp4 = os.path.join(out_dir, "reel.mp4")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{fr}/f%05d.jpg", "-i", os.path.join(wd, "mix.wav"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-maxrate", "4500k", "-bufsize", "9000k", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", mp4])
    cover_t = spec.get("cover_t")
    if cover_t is None:
        cover_t = S0 = sched["S"][0] + 2.0
    shutil.copy(os.path.join(fr, f"f{int(round(cover_t * FPS)):05d}.jpg"), os.path.join(out_dir, "cover.jpg"))
    info = dict(duration=round(sched["total"], 2), thumb_offset_ms=int(cover_t * 1000), schedule=sched,
                size_mb=round(os.path.getsize(mp4) / 1e6, 2))
    json.dump(info, open(os.path.join(out_dir, "reel.json"), "w"), indent=1)
    print("DONE", mp4, info["size_mb"], "MB", info["duration"], "s thumb_offset_ms", info["thumb_offset_ms"], flush=True)


if __name__ == "__main__":
    main()
