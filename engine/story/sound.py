"""Soft, clean sound for story reels: warm piano-like bed, gentle swishes, tiny typing ticks, a soft chime on success.
No drums, no risers, no loud effects."""
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve
SR = 44100
def bpf(x, f1, f2, o=2):
    b, a = butter(o, [f1 / (SR / 2), f2 / (SR / 2)], "band"); return lfilter(b, a, x)
def lpf(x, fc, o=2):
    b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)
def hpf(x, fc, o=2):
    b, a = butter(o, fc / (SR / 2), "high"); return lfilter(b, a, x)
def put(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i < 0 or i >= buf.shape[1]: return
    n = min(len(sig), buf.shape[1] - i)
    buf[0, i:i + n] += sig[:n] * gain * (1 - max(0, pan))
    buf[1, i:i + n] += sig[:n] * gain * (1 + min(0, pan))
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
def epiano(f, dur, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.exp(-t * 2.4) * np.minimum(1, t / 0.006)
    s = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 7) + 0.18 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 12)
    s += 0.25 * np.sin(2 * np.pi * f * 1.003 * t)
    s *= 1 + 0.06 * np.sin(2 * np.pi * 4.5 * t)
    return s * env * vel * 0.5
def pad(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for f in freqs:
        for d in (0.996, 1.004):
            out += np.sin(2 * np.pi * f * d * t) + 0.3 * np.sin(2 * np.pi * 2 * f * d * t)
    env = np.minimum(1, t / 0.9) * np.minimum(1, (dur - t) / 1.0)
    return lpf(out, 1400) * env * 0.05
def reverb(x, wet=0.22, rt=1.5, seed=3):
    rng = np.random.default_rng(seed); n = int(rt * SR)
    ir = rng.standard_normal((2, n)) * np.exp(-np.arange(n) / (rt * SR / 5)); ir[:, :int(.012 * SR)] *= 0
    ir = np.array([lpf(c, 4500) for c in ir]); ir /= np.abs(ir).max() * 6
    w = np.array([fftconvolve(x[c], ir[c])[:x.shape[1]] for c in range(2)])
    return x * (1 - wet) + w * wet * 3
PROG = [  # (root midi, chord offsets) per bar, four-bar loops, warm major-7 feel
    [(48, [0, 7, 11, 16]), (45, [0, 7, 10, 15]), (41, [0, 7, 11, 16]), (43, [0, 7, 9, 14])],
    [(50, [0, 7, 11, 16]), (47, [0, 7, 10, 15]), (43, [0, 7, 11, 16]), (45, [0, 7, 10, 14])],
    [(46, [0, 7, 11, 16]), (43, [0, 7, 10, 15]), (39, [0, 7, 11, 16]), (41, [0, 7, 9, 14])],
]
def swish(dur=0.3):
    n = int(dur * SR); x = np.random.default_rng(5).standard_normal(n)
    t = np.linspace(0, 1, n); out = np.zeros(n)
    seg = 6
    for k in range(seg):
        a, b = int(k * n / seg), int((k + 1) * n / seg)
        fc = 500 + 2600 * (k / seg)
        out[a:b] = bpf(x, fc * .7, fc * 1.3)[a:b]
    return out * np.sin(np.pi * t) ** 2 * 0.5
def tick():
    n = int(.012 * SR); x = np.random.default_rng(9).standard_normal(n) * np.exp(-np.arange(n) / (.002 * SR))
    return hpf(x, 1800)
def chime():
    out = np.zeros(int(1.6 * SR))
    for k, f in enumerate((1318.5, 1975.5)):
        n = int(1.4 * SR); t = np.arange(n) / SR
        s = (np.sin(2 * np.pi * f * t) + 0.18 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)) * np.exp(-t * 3.2) * np.minimum(1, t / .004)
        i = int(k * .1 * SR); out[i:i + n] += s[:len(out) - i] * 0.5
    return out
def thump():
    n = int(.6 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (46 + 40 * np.exp(-t * 14)) * t) * np.exp(-t * 6)
def render_music(sched, out_path, seed=7, key=0, bpm=84):
    total = sched["total"]; n = int((total + 2.5) * SR); m = np.zeros((2, n)); rng = np.random.default_rng(seed)
    beat = 60 / bpm; bar = 4 * beat; prog = PROG[key % len(PROG)]
    nb = int(np.ceil(total / bar)) + 1
    for b in range(nb):
        root, offs = prog[b % 4]; t0 = b * bar
        put(m, t0, pad([midi(root + o) for o in offs[:3]], bar + 0.4), 1.0)
        put(m, t0, epiano(midi(root - 12), bar * .9, .8), .6)
        order = [0, 1, 2, 3, 2, 1, 2, 3] if b % 2 == 0 else [0, 2, 1, 3, 2, 3, 1, 2]
        for k, idx in enumerate(order):
            vel = (0.55 + 0.25 * rng.random()) * (1.0 if k % 2 == 0 else .78)
            put(m, t0 + k * beat / 2, epiano(midi(root + 12 + offs[idx]), 1.3, vel), .5, pan=(rng.random() - .5) * .5)
    # events
    ev = np.zeros((2, n))
    put(ev, sched["T"][0]["S"] + 0.02, thump(), 0.35)
    for i, T in enumerate(sched["T"]):
        if i > 0: put(ev, T["S"] - 0.05, swish(), 0.16)
        for tt in T.get("ticks", []): put(ev, tt, tick(), 0.05 + 0.02 * rng.random())
        if T.get("chime") is not None: put(ev, T["chime"], chime(), 0.16)
    m = reverb(m, 0.24); m = m / (np.abs(m).max() + 1e-9) * 0.5
    out = m.copy()
    np.save(out_path + ".ev.npy", ev)
    import soundfile as sf
    sf.write(out_path, m.T, SR); return ev
