"""Launch-video music + SFX, fully synthesised (no samples)."""
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
BPM = 120
BEAT = 60 / BPM
rng = np.random.default_rng(7)
N = 0
PROGS = [
    [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])],   # Am F C G (launch)
    [(48, [55, 60, 64]), (43, [55, 59, 62]), (45, [57, 60, 64]), (41, [53, 57, 60])],   # C G Am F
    [(41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62]), (45, [57, 60, 64])],   # F C G Am
]

def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)

def add(buf_l, buf_r, start, sig, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    seg = sig[: j - i] * gain
    gl = np.cos((pan + 1) * np.pi / 4)
    gr = np.sin((pan + 1) * np.pi / 4)
    buf_l[i:j] += seg * gl
    buf_r[i:j] += seg * gr

def env_ad(n, a, d, curve=3.0):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-t / max(d, 1e-4) * curve / 3)
    return e

def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)

def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)

def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), f2 / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


# ---------- drum / fx voices
def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 8)
    click = hp(rng.standard_normal(n), 3000) * np.exp(-t * 300) * 0.15
    return (s + click) * 1.0

def clap():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 1200, 5500)
    e = np.exp(-t * 22) + 0.6 * np.exp(-(t - 0.012).clip(0) * 30) * (t > 0.012)
    return x * e * 0.5

def hat(open_=False):
    n = int((0.22 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 7000)
    return x * np.exp(-t * (14 if open_ else 70)) * 0.22

def boom(dur=1.8):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 38 + 90 * np.exp(-t * 6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 2.2)
    noise = lp(rng.standard_normal(n), 900) * np.exp(-t * 5) * 0.6
    return (s + noise) * 1.1

def whoosh(dur=0.9, up=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    # sweep via time-varying one-pole approximated by block filtering
    out = np.zeros(n)
    blk = 512
    for i in range(0, n, blk):
        p = i / n
        fc = (300 + 7000 * (p if up else 1 - p) ** 2)
        seg = x[i : i + blk]
        b, a = signal.butter(2, min(fc, 18000) / (SR / 2), "low")
        out[i : i + blk] = signal.lfilter(b, a, seg)
    e = np.sin(np.pi * np.minimum(t / dur, 1.0)) ** 2
    return out * e * 0.5

def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    blk = 1024
    for i in range(0, n, blk):
        pp = i / n
        fc = 400 + 9000 * pp ** 2
        b, a = signal.butter(2, min(fc, 18000) / (SR / 2), "low")
        out[i : i + blk] = signal.lfilter(b, a, noise[i : i + blk])
    # tonal sweep
    f = 200 * (2 ** (3.2 * p))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return (out * 0.6 + tone) * (p ** 1.6)

def pluck(freq, dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(4 * np.pi * freq * t) + 0.3 * signal.sawtooth(2 * np.pi * freq * t))
    cut = 600 + 3500 * np.exp(-t * 14)
    # crude per-sample cutoff using blockwise filter
    out = np.zeros(n)
    blk = 256
    for i in range(0, n, blk):
        fc = float(cut[min(i, n - 1)])
        b, a = signal.butter(2, min(fc, 15000) / (SR / 2), "low")
        out[i : i + blk] = signal.lfilter(b, a, s[i : i + blk])
    return out * np.exp(-t * 9) * 0.35

def pad(freqs, dur, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for det in (-0.07, 0.0, 0.07):
            fr = f * 2 ** (det / 12)
            s += signal.sawtooth(2 * np.pi * fr * t + rng.random() * 6.28) * 0.12
    s = lp(s, 900 + 2500 * bright, 2)
    a = min(1.2, dur / 2)
    e = np.minimum(t / a, 1.0) * np.minimum((dur - t) / 0.6, 1.0).clip(0)
    return s * e

def bass(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t)
    s = lp(s, 400)
    e = np.minimum(t / 0.01, 1.0) * np.minimum((dur - t) / 0.05, 1.0).clip(0)
    return s * e * 0.55


def render_music(sched, out_path, seed=7, key=0):
    global rng, N
    S = sched["S"]; TOTAL = sched["total"]; CWX = [c["t"] for c in sched["cw"]]
    r_i = sched["reveal"]; m_i = sched["morning"]; c_i = sched["cta"]
    DUR = TOTAL + 0.05
    N = int(SR * DUR)
    rng = np.random.default_rng(seed)
    L = np.zeros(N); R = np.zeros(N)
    PROG = [(r + key, [x + key for x in tri]) for r, tri in PROGS[seed % len(PROGS)]]

    def bar_at(t): return int(t // 2.0)
    S_REV = S[r_i]; S_FEAT = S[r_i + 1]; S_MOR = S[m_i]; S_CTA = S[c_i]
    S_PRE = S[m_i - 1]
    CUTS = [1.0] + S[1:]
    for b in range(int(DUR // 2) + 1):
        root, tri = PROG[b % 4]
        st = b * 2.0
        if st >= DUR: break
        freqs = [midi(n) for n in tri] + [midi(root + 12)]
        bright = 2.2 if S_MOR <= st < S_CTA else 1.0
        pd = pad(freqs, 2.1, bright)
        gain = 0.55
        if st < 1.0: gain = 0.3
        if st >= S_CTA: gain = 0.7
        add(L, R, st, pd, pan=-0.2, gain=gain)
        add(L, R, st + 0.01, pd * 0.9, pan=0.2, gain=gain)
    for b in range(int(DUR // 2) + 1):
        st = b * 2.0
        if st < 1.0 or st >= S_CTA: continue
        root, _ = PROG[b % 4]
        f = midi(root)
        for i, off in enumerate([0, 0.5, 1.0, 1.5]):
            if S_MOR <= st < S_CTA and i % 2: continue
            add(L, R, st + off, bass(f if i != 3 else f * 1.5, 0.45), gain=0.9)
    t = 1.0; beat_i = 0
    while t < S_CTA:
        in_morning = S_MOR <= t < S_CTA
        if not in_morning:
            add(L, R, t, kick(), gain=0.9)
            if t >= S[1]: add(L, R, t + BEAT / 2, hat(), pan=0.3, gain=0.8)
            if beat_i % 2 == 1 and t >= S_REV: add(L, R, t, clap(), gain=0.7)
            if beat_i % 4 == 3 and t >= S_FEAT: add(L, R, t + BEAT / 2, hat(True), pan=-0.3, gain=0.8)
        else:
            if beat_i % 2 == 0: add(L, R, t, kick(), gain=0.5)
            add(L, R, t + BEAT / 2, hat(), pan=0.3, gain=0.4)
        t += BEAT; beat_i += 1
    t = S_FEAT; step = BEAT / 4; k = 0
    while t < S_MOR:
        root, tri = PROG[bar_at(t) % 4]
        notes = [tri[0] + 12, tri[1] + 12, tri[2] + 12, tri[1] + 12]
        n = notes[k % 4] + (12 if (k // 8) % 2 else 0)
        amp = 0.55 if t < S_PRE else 0.4
        add(L, R, t, pluck(midi(n)), pan=-0.4 + 0.8 * ((k % 8) / 7), gain=amp)
        t += step; k += 1
    t = S_MOR; k = 0
    while t < S_CTA:
        root, tri = PROG[bar_at(t) % 4]
        n = [tri[2] + 24, tri[1] + 24, tri[0] + 24, tri[1] + 24][k % 4]
        add(L, R, t, pluck(midi(n), 0.6), pan=0.2, gain=0.4)
        t += BEAT; k += 1
    for c in CUTS:
        big = abs(c - S_REV) < 1e-6 or abs(c - S_CTA) < 1e-6
        add(L, R, c, boom(), gain=0.85 if big else 0.55)
        add(L, R, c - 0.45, whoosh(0.45, up=True), gain=0.5)
    for c in CWX:
        add(L, R, c - 0.12, whoosh(0.3, up=True), gain=0.6)
        add(L, R, c, boom(0.6), gain=0.4)
    add(L, R, S_REV - 2.5, riser(2.5), gain=0.8)
    add(L, R, S_CTA - 3.0, riser(3.0), gain=0.8)
    add(L, R, 0.0, riser(1.0), gain=0.4)
    fin = pad([midi(57 + key), midi(60 + key), midi(64 + key), midi(69 + key), midi(72 + key)], 6.5, 2.5)
    add(L, R, S_CTA, fin, pan=-0.2, gain=0.9)
    add(L, R, S_CTA, fin, pan=0.2, gain=0.9)
    for i, n in enumerate([81, 84, 88, 93]):
        add(L, R, S_CTA + 0.2 + i * 0.25, pluck(midi(n + key), 1.2), pan=-0.3 + 0.2 * i, gain=0.5)
    fi = int((TOTAL - 1.2) * SR)
    mask = np.ones(N); mask[fi:] = np.linspace(1, 0, N - fi) ** 1.5
    L *= mask; R *= mask
    fi2 = int(0.4 * SR)
    L[:fi2] *= np.linspace(0, 1, fi2); R[:fi2] *= np.linspace(0, 1, fi2)
    def delay(x, ms, fb, mix):
        d = int(SR * ms / 1000); y = x.copy()
        for kk in range(1, 5): y[kk * d:] += x[: N - kk * d] * (fb ** kk) * mix
        return y
    L = delay(L, 375, 0.45, 0.35); R = delay(R, 500, 0.45, 0.35)
    stereo = np.tanh(np.stack([L, R], axis=1) * 0.9)
    stereo = stereo / np.max(np.abs(stereo)) * 0.70
    wavfile.write(out_path, SR, (stereo * 32767).astype(np.int16))
    return stereo
