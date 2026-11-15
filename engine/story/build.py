#!/usr/bin/env python3
"""Karo STORY reel builder. python3 engine/story/build.py spec.json outdir [--preview] [--force]
Spec: {"seed":int,"key":0-2,"theme":"indigo|midnight|violet|ocean","voice":"af_heart","speed":1.0,
       "scenes":[{"kind":"calendar|inbox|chat|mail|notifs|moment|cta","kicker":"Saturday, 9:02 AM","line":"voice line", ...visual fields}]}
Each scene = one short voice line + one visual (see template.html builders). Total must be under 30 s.
Voice: Kokoro (default af_heart, warm). Captions follow the voice word by word. Output: reel.mp4, cover.jpg, reel.json."""
import json, os, sys, subprocess, shutil, math, re, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FPS = 30; SR = 44100
MODEL_DIR = os.environ.get("KARO_MODELS", os.path.expanduser("~/.cache/karo-models"))
MODEL_URLS = {
    "kokoro.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
def sh(cmd):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    subprocess.run(cmd, shell=isinstance(cmd, str), check=True)
def ensure_models():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, url in MODEL_URLS.items():
        p = os.path.join(MODEL_DIR, name)
        if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
            print("downloading", name, flush=True); urllib.request.urlretrieve(url, p + ".part"); os.replace(p + ".part", p)
    return os.path.join(MODEL_DIR, "kokoro.onnx"), os.path.join(MODEL_DIR, "voices.bin")
# ------------------------------------------------------------ voice
def env10(w, sr):
    n = int(sr * .01); k = len(w) // n
    return np.sqrt((w[:k * n].reshape(k, n) ** 2).mean(1)) if k else np.zeros(1)
def trim(w, sr):
    e = env10(w, sr); thr = max(e.max() * .04, 1e-4); idx = np.where(e > thr)[0]
    a = max(0, idx[0] - 4) * int(sr * .01); b = min(len(e), idx[-1] + 8) * int(sr * .01)
    return w[a:b]
def word_times(text, wav, sr):
    words = text.split(); dur = len(wav) / sr
    wt = lambda w: max(1.0, len(re.sub(r"[^A-Za-z0-9']", "", w)) ** 0.9)
    e = env10(wav, sr); thr = max(e.max() * .05, 1e-4); sil = e < thr
    pauses = []; i = 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]: j += 1
            if (j - i) >= 11 and i > 5 and j < len(sil) - 5: pauses.append((i * .01, j * .01))
            i = j
        else: i += 1
    punct = [k for k, w in enumerate(words[:-1]) if w[-1] in ",;:.?!"]
    if len(pauses) > len(punct) and punct:
        pauses = sorted(sorted(pauses, key=lambda p: p[1] - p[0], reverse=True)[:len(punct)])
    def spread(ws, t0, t1):
        tot = sum(wt(w) for w in ws); out = []; c = t0
        for w in ws:
            d = (t1 - t0) * wt(w) / tot; out.append((w, c, c + d)); c += d
        return out
    res = []
    if punct and len(pauses) == len(punct):
        st = 0; t0 = 0.0
        for pi, k in enumerate(punct):
            res += spread(words[st:k + 1], t0, pauses[pi][0]); st = k + 1; t0 = pauses[pi][1]
        res += spread(words[st:], t0, dur)
    else:
        ws = [wt(w) + (0.7 if (w[-1] in ",;:.?!" and k < len(words) - 1) else 0) for k, w in enumerate(words)]
        tot = sum(ws); c = 0.0
        for w, x in zip(words, ws):
            d = dur * x / tot; res.append((w, c, c + d * (0.85 if x > wt(w) else 1.0))); c += d
    return res
def make_voice(spec, wd):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    m, v = ensure_models(); k = Kokoro(m, v)
    voice = spec.get("voice", "af_heart"); speed = spec.get("speed", 1.0); out = []
    for i, s in enumerate(spec["scenes"]):
        wav, sr = k.create(s["line"], voice=voice, speed=speed, lang="en-us")
        wav = trim(np.asarray(wav, dtype=np.float32), sr)
        if sr != SR:
            from scipy.signal import resample_poly
            g = math.gcd(sr, SR); wav = resample_poly(wav, SR // g, sr // g).astype(np.float32)
        wt = word_times(s["line"], wav, SR)
        sf.write(os.path.join(wd, f"v{i}.wav"), wav, SR)
        out.append(dict(wav=wav, words=wt, len=len(wav) / SR))
    return out
# ------------------------------------------------------------ schedule
def make_schedule(spec, voices):
    S = 0.0; T = []; lines = []
    for i, (s, v) in enumerate(zip(spec["scenes"], voices)):
        lead = 0.12 if i == 0 else 0.42
        v0 = S + lead; v1 = v0 + v["len"]
        tail = 1.5 if s["kind"] == "cta" else (0.38 if i < len(voices) - 1 else 0.5)
        end = v1 + tail
        ty0 = S + 0.3; ty1 = max(ty0 + 1.2, min(v1 - 0.5, v0 + v["len"] * 0.62))
        proof = max(ty1 + 0.9, v0 + 0.5) if s["kind"] in ("chat",) else (ty1 + 0.4 if s["kind"] == "mail" else v0 + min(0.9, v["len"] * .3))
        t = dict(S=S, v0=v0, v1=v1, end=end, ty0=ty0, ty1=ty1, proof=proof)
        ticks = []
        if s["kind"] in ("chat", "mail"):
            txt = s.get("user") or s.get("mail_body", ""); n = len(txt)
            for c in range(0, n, 3): ticks.append(ty0 + (ty1 - ty0) * c / max(1, n))
        t["ticks"] = ticks
        if s["kind"] in ("chat", "mail", "calendar", "inbox") and (s["kind"] != "inbox" or s.get("clear_to") is not None) and (s["kind"] != "calendar" or s.get("done")):
            t["chime"] = proof + (0.1 if s["kind"] == "chat" else 0.0)
        elif s["kind"] == "notifs" and s.get("check"): t["chime"] = proof
        T.append(t)
        lines.append(dict(end=v1, words=[dict(w=w, t0=v0 + a, t1=v0 + b) for (w, a, b) in v["words"]]))
        S = end
    return dict(T=T, lines=lines, total=S, S=[t["S"] for t in T])
# ------------------------------------------------------------ audio mix
def compress(x, thr=0.10, ratio=3.0):
    from scipy.signal import lfilter
    k = math.exp(-1 / (0.04 * SR)); env = np.maximum(lfilter([1 - k], [1, -k], np.abs(x)), 1e-5)
    g = np.where(env > thr, (env / thr) ** (1 / ratio - 1), 1.0)
    k2 = math.exp(-1 / (0.02 * SR)); g = lfilter([1 - k2], [1, -k2], g)
    return x * g * 1.7
def mix(voices, sched, music_path, out_wav):
    import soundfile as sf
    from scipy.signal import butter, lfilter
    total = sched["total"]; n = int((total + .3) * SR)
    vo = np.zeros(n, dtype=np.float32)
    for v, T in zip(voices, sched["T"]):
        i = int(T["v0"] * SR); w = v["wav"]; vo[i:i + len(w)] += w[:n - i]
    b, a = butter(2, 85 / (SR / 2), "high"); vo = lfilter(b, a, vo)
    b, a = butter(2, [2200 / (SR / 2), 5200 / (SR / 2)], "band"); vo = vo + 0.22 * lfilter(b, a, vo)
    vo = compress(vo); vo = vo / (np.abs(vo).max() + 1e-9) * 0.85
    m, sr = sf.read(music_path); m = m.T if m.ndim == 2 else np.stack([m, m])
    ev = np.load(music_path + ".ev.npy")
    mm = np.zeros((2, n)); L = min(n, m.shape[1]); mm[:, :L] = m[:, :L]
    e = np.zeros((2, n)); L2 = min(n, ev.shape[1]); e[:, :L2] = ev[:, :L2]
    # duck music under voice
    env = np.abs(vo); k = int(.02 * SR); env = np.convolve(env, np.ones(k) / k, "same"); env = np.convolve(env, np.ones(int(.25 * SR)) / int(.25 * SR), "same")
    duck = 1 - 0.62 * np.clip(env / 0.12, 0, 1)
    mus = mm * duck * 0.55
    # music swells softly in the last scene
    ct = sched["T"][-1]["S"]; sw = np.clip((np.arange(n) / SR - ct) / 1.2, 0, 1); mus *= (1 + 0.35 * sw)
    st = np.stack([vo, vo]) + mus + e * 0.9
    fade = np.minimum(1, (total + .3 - np.arange(n) / SR) / .6); st *= fade
    st = st / max(1.0, np.abs(st).max() / 0.95)
    sf.write(out_wav, st.T, SR)
    sp = np.abs(vo) > .05
    print("VO rms", round(float(np.sqrt((vo[sp] ** 2).mean())), 3), "music rms under VO", round(float(np.sqrt((mus[0][sp] ** 2).mean())), 3), flush=True)
# ------------------------------------------------------------ frames
SHOOT = r'''
import sys, asyncio
from playwright.async_api import async_playwright
html, outdir, mode = sys.argv[1], sys.argv[2], sys.argv[3]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("file://" + html); await pg.evaluate("document.fonts.ready")
        if mode == "keys":
            for t in [float(x) for x in sys.argv[4].split(",")]:
                await pg.evaluate(f"render({t})"); await pg.screenshot(path=f"{outdir}/k_{t:06.2f}.jpg", type="jpeg", quality=88)
        else:
            s, e, step = int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
            for i in range(s, e, step):
                await pg.evaluate(f"render({i / 30})"); await pg.screenshot(path=f"{outdir}/f{i:05d}.jpg", type="jpeg", quality=90)
        if errs: print("PAGE ERRORS", errs[:3])
        await b.close()
asyncio.run(main())
'''
def write_page(spec, sched, wd):
    html = open(os.path.join(HERE, "template.html")).read()
    html = html.replace("/*SPEC*/null", json.dumps(spec)).replace("/*SCHED*/null", json.dumps(sched))
    if not os.path.exists(os.path.join(wd, "fonts")): shutil.copytree(os.path.join(HERE, "fonts"), os.path.join(wd, "fonts"))
    p = os.path.join(wd, "page.html"); open(p, "w").write(html); open(os.path.join(wd, "shoot.py"), "w").write(SHOOT); return p
def preview(spec, sched, wd, out):
    page = write_page(spec, sched, wd); ts = []
    for T in sched["T"]:
        for off in (0.9, 2.4, 4.2):
            t = T["S"] + off
            if t < T["end"] - .1: ts.append(round(t, 2))
    kd = os.path.join(wd, "keys"); shutil.rmtree(kd, ignore_errors=True); os.makedirs(kd)
    sh([sys.executable, os.path.join(wd, "shoot.py"), page, kd, "keys", ",".join(str(t) for t in sorted(set(ts)))])
    from PIL import Image
    files = sorted(os.listdir(kd)); ims = [Image.open(os.path.join(kd, f)).resize((270, 480)) for f in files]
    cols = 8; rows = math.ceil(len(ims) / cols); sheet = Image.new("RGB", (cols * 270, rows * 480))
    for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
    sheet.save(out); print("preview", out, len(files), "frames")
def main():
    spec = json.load(open(sys.argv[1])); out_dir = os.path.abspath(sys.argv[2]); os.makedirs(out_dir, exist_ok=True)
    wd = os.path.join(out_dir, "work"); os.makedirs(wd, exist_ok=True)
    voices = make_voice(spec, wd); sched = make_schedule(spec, voices)
    json.dump(sched, open(os.path.join(wd, "schedule.json"), "w"))
    print("scenes", [round(x, 2) for x in sched["S"]], "total", round(sched["total"], 2), flush=True)
    words = sum(len(v["words"]) for v in voices); print("words", words, flush=True)
    if not (20.0 <= sched["total"] <= 29.8) and "--force" not in sys.argv:
        raise SystemExit(f"DURATION {sched['total']:.1f}s must be 20 to 29.8 s: shorten or lengthen the voice lines (about 2.5 words per second) and rebuild")
    if "--preview" in sys.argv:
        preview(spec, sched, wd, os.path.join(out_dir, "preview.jpg")); return
    import sound
    sound.render_music(sched, os.path.join(wd, "music.wav"), seed=spec.get("seed", 7), key=spec.get("key", 0))
    mix(voices, sched, os.path.join(wd, "music.wav"), os.path.join(wd, "mix_raw.wav"))
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(wd, "mix_raw.wav"), "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "44100", os.path.join(wd, "mix.wav")])
    page = write_page(spec, sched, wd); fr = os.path.join(wd, "frames"); shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
    nfr = int(math.ceil(sched["total"] * FPS)); nw = int(os.environ.get("KARO_WORKERS", "3"))
    procs = [subprocess.Popen([sys.executable, os.path.join(wd, "shoot.py"), page, fr, "frames", str(w), str(nfr), str(nw)]) for w in range(nw)]
    for p in procs:
        if p.wait() != 0: raise SystemExit("frame worker failed")
    mp4 = os.path.join(out_dir, "reel.mp4")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{fr}/f%05d.jpg", "-i", os.path.join(wd, "mix.wav"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-maxrate", "4500k", "-bufsize", "9000k", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", mp4])
    cover_t = spec.get("cover_t", sched["T"][0]["S"] + 1.8)
    shutil.copy(os.path.join(fr, f"f{int(round(cover_t * FPS)):05d}.jpg"), os.path.join(out_dir, "cover.jpg"))
    info = dict(duration=round(sched["total"], 2), thumb_offset_ms=int(cover_t * 1000), size_mb=round(os.path.getsize(mp4) / 1e6, 2))
    json.dump(info, open(os.path.join(out_dir, "reel.json"), "w"), indent=1)
    print("DONE", mp4, info["size_mb"], "MB", info["duration"], "s thumb_offset_ms", info["thumb_offset_ms"], flush=True)
if __name__ == "__main__":
    main()
