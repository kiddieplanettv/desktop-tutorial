"""Synthesize the whole soundtrack (no vocals): background music + sound effects.

Reads build/<segment>_events.json written by the Blender scripts and writes
build/soundtrack.wav, aligned frame-accurately with the rendered video.
Pure numpy, no samples or external audio.
"""
import json, os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
SR = 44100
FPS = 24
ORDER = ["k_intro", "k_ep1", "k_ep2", "k_ep3", "k_ep4", "k_game", "k_finale"]
rng = np.random.default_rng(7)

# ----------------------------------------------------------------------------- primitives

def t_(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, a=0.005, r=0.1, sustain=1.0):
    e = np.ones(n) * sustain
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, sustain, na)
    if nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def expdec(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def osc(freq, dur, kind="sine", phase=0.0):
    t = t_(dur)
    f = np.broadcast_to(np.asarray(freq, dtype=float), t.shape) if np.ndim(freq) else np.full(t.shape, float(freq))
    ph = 2 * np.pi * np.cumsum(f) / SR + phase
    if kind == "sine":
        return np.sin(ph)
    if kind == "square":
        return np.tanh(4 * np.sin(ph))
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    if kind == "tri":
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1.0) - 1) - 1
    raise ValueError(kind)


def bandnoise(dur, lo, hi):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def glide(f0, f1, dur, curve=1.0):
    t = np.linspace(0, 1, int(dur * SR)) ** curve
    return f0 * (f1 / f0) ** t


def cat(*xs):
    return np.concatenate(xs)


def silence(d):
    return np.zeros(int(d * SR))


def note_hz(n):  # midi
    return 440.0 * 2 ** ((n - 69) / 12)

# ----------------------------------------------------------------------------- sound effects

def beep(f, d, kind="square", vol=1.0):
    return osc(f, d, kind) * env(int(d * SR), 0.003, 0.02) * vol


def sfx_alarm(dur=4.0, **_):
    unit = cat(beep(1320, 0.11), silence(0.06), beep(1320, 0.11), silence(0.06), beep(1320, 0.11), silence(0.35))
    reps = int(np.ceil(dur / (len(unit) / SR)))
    return np.tile(unit, reps)[: int(dur * SR)] * 0.45


def sfx_door(dur=1.2, **_):
    n = int(dur * SR)
    x = bandnoise(dur, 80, 900) * 0.5 + osc(55 + 10 * np.sin(np.linspace(0, 30, n)), dur, "saw") * 0.15
    clatter = (np.sin(np.linspace(0, dur * 2 * np.pi * 14, n)) > 0.7) * bandnoise(dur, 1500, 4000) * 0.15
    return (x + clatter) * env(n, 0.05, 0.2) * 0.5


def sfx_wake(**_):
    d = 0.35
    return osc(glide(380, 980, d, 0.6), d, "sine") * env(int(d * SR), 0.01, 0.12) * 0.6


def sfx_siren_police(dur=3.0, **_):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 950 + 380 * np.sin(2 * np.pi * t / 0.7)
    x = osc(f, dur, "sine") * 0.7 + osc(f * 2, dur, "sine") * 0.15
    return x * env(n, 0.08, 0.25) * 0.35


def sfx_siren_ambulance(dur=3.0, **_):
    unit = cat(osc(960, 0.42, "tri"), osc(770, 0.42, "tri"))
    n = int(dur * SR)
    x = np.tile(unit, int(np.ceil(n / len(unit))))[:n]
    return x * env(n, 0.03, 0.2) * 0.35


def bell(f=880, d=1.0):
    n = int(d * SR)
    parts = [(1.0, 1.0, 0.9), (2.76, 0.5, 0.5), (5.4, 0.25, 0.25), (8.9, 0.12, 0.15)]
    x = sum(a * np.sin(2 * np.pi * f * r * t_(d)) * expdec(n, tau * d) for r, a, tau in parts)
    return x / 1.8


def sfx_siren_fire(dur=3.0, **_):
    n = int(dur * SR)
    out = np.zeros(n)
    step = int(0.3 * SR)
    for i in range(0, n, step):
        b = bell(1150 if (i // step) % 2 == 0 else 1050, 0.5)
        out[i:i + len(b)] += b[: n - i]
    horn = osc(220, dur, "saw") * 0.06 * env(n, 0.1, 0.3)
    return (out * 0.45 + lowpass(horn, 900)) * env(n, 0.01, 0.15)


def sfx_siren_tow(dur=3.0, **_):
    unit = cat(beep(620, 0.09), silence(0.07), beep(620, 0.09), silence(0.4))
    n = int(dur * SR)
    return np.tile(unit, int(np.ceil(n / len(unit))))[:n] * 0.38


def sfx_heli(dur=3.0, vol=1.0, **_):
    n = int(dur * SR)
    t = np.arange(n) / SR
    thump = (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t)) ** 6
    x = lowpass(bandnoise(dur, 40, 1200), 500) * thump * 1.2 + osc(48, dur, "sine") * 0.15
    if dur > 5:
        vol *= 0.5
    return x * env(n, 0.6, 0.6) * 0.32 * vol


def sfx_honk(**_):
    h = (osc(415, 0.22, "square") + osc(520, 0.22, "square")) * 0.5
    h = lowpass(h, 2500) * env(len(h), 0.005, 0.04)
    return cat(h, silence(0.08), h) * 0.4


def sfx_sad(**_):
    out = []
    for i, (a, b) in enumerate([(392, 370), (370, 349), (349, 330), (330, 300)]):
        d = 0.42 if i < 3 else 0.8
        f = glide(a, b, d)
        if i == 3:
            f = f * (1 + 0.025 * np.sin(2 * np.pi * 6 * t_(d)))
        x = lowpass(osc(f, d, "saw"), 1200) * env(int(d * SR), 0.02, 0.08)
        out.append(x)
    return cat(*out) * 0.35


def woof(p=1.0):
    d = 0.16
    f = glide(560 * p, 300 * p, d, 0.7)
    x = lowpass(osc(f, d, "saw") + 0.4 * bandnoise(d, 300, 2500), 1800)
    return x * env(int(d * SR), 0.005, 0.06)


def sfx_bark(**_):
    return cat(woof(1.1), silence(0.1), woof(1.2)) * 0.45


def sfx_boing(vol=1.0, **_):
    d = 0.32
    t = t_(d)
    f = glide(180, 520, d, 0.5) * (1 + 0.12 * np.sin(2 * np.pi * 18 * t) * np.exp(-t * 6))
    return osc(f, d, "sine") * env(int(d * SR), 0.003, 0.12) * 0.45 * vol


def arp(notes, step=0.09, d=0.5, kind="sine", vol=0.35):
    total = step * (len(notes) - 1) + d
    out = np.zeros(int(total * SR) + 1)
    for i, m in enumerate(notes):
        x = (osc(note_hz(m), d, kind) + 0.3 * osc(note_hz(m) * 2, d, "sine")) * expdec(int(d * SR), d / 3)
        s = int(i * step * SR)
        out[s:s + len(x)] += x
    return out * vol


def sfx_love(**_):
    return arp([72, 76, 79, 84, 88], step=0.08, d=0.6, vol=0.3)


def sfx_tada(**_):
    d1, d2 = 0.12, 0.9
    out = []
    for m, d in [(67, d1), (67, d1), (72, d2)]:
        ch = sum(lowpass(osc(note_hz(m + k), d, "saw"), 3000) for k in (0, 4, 7)) / 3
        out.append(ch * env(int(d * SR), 0.01, 0.2))
        out.append(silence(0.02))
    return cat(*out) * 0.32


def sfx_yay(vol=1.0, **_):
    a = sfx_tada() * 0.8
    b = np.pad(arp([84, 88, 91, 96], step=0.07, d=0.4, vol=0.25), (int(0.25 * SR), 0))
    out = np.zeros(max(len(a), len(b)))
    out[: len(a)] += a
    out[: len(b)] += b
    return out * vol


def sfx_confetti(vol=1.0, **_):
    pop = bandnoise(0.06, 200, 6000) * expdec(int(0.06 * SR), 0.015) * 0.6
    tw = np.zeros(int(1.0 * SR))
    for i in range(14):
        f = rng.uniform(2500, 6000)
        d = 0.12
        s = int(rng.uniform(0.05, 0.8) * SR)
        x = osc(f, d) * expdec(int(d * SR), 0.03) * 0.15
        tw[s:s + len(x)] += x
    return cat(pop, tw) * vol


def sfx_balloon(**_):
    d = 0.5
    f = glide(500, 900, d) * (1 + 0.05 * np.sin(2 * np.pi * 9 * t_(d)))
    return lowpass(osc(f, d, "saw"), 2000) * env(int(d * SR), 0.02, 0.15) * 0.18


def sfx_whoosh(vol=1.0, **_):
    d = 0.6
    n = int(d * SR)
    x = bandnoise(d, 300, 5000)
    sweep = np.sin(np.linspace(0, np.pi, n)) ** 2
    return lowpass(x * sweep, 2500) * 0.35 * vol


def sfx_pop(vol=1.0, pitch=1.0, **_):
    d = 0.09
    return osc(glide(900 * pitch, 300 * pitch, d), d) * expdec(int(d * SR), 0.03) * 0.5 * vol


def sfx_thud(**_):
    d = 0.25
    return osc(glide(140, 50, d), d) * expdec(int(d * SR), 0.06) * 0.6


def sfx_open(**_):
    return cat(bandnoise(0.03, 1000, 6000) * 0.3, lowpass(osc(glide(300, 500, 0.25), 0.25, "saw"), 1500) * env(int(0.25 * SR), 0.01, 0.1) * 0.12)


def sfx_magic(**_):
    out = np.zeros(int(1.2 * SR))
    for i in range(12):
        m = 84 + [0, 2, 4, 7, 9, 12][i % 6] + 12 * (i // 6)
        x = osc(note_hz(m), 0.3) * expdec(int(0.3 * SR), 0.08) * 0.18
        s = int(i * 0.06 * SR)
        out[s:s + len(x)] += x
    return out


def sfx_sparkle(**_):
    return sfx_magic() * 0.8


def sfx_giggle(**_):
    out = []
    for i, f in enumerate([1000, 1150, 1050, 1200, 1100]):
        d = 0.07
        out += [osc(f * (1 + 0.04 * np.sin(2 * np.pi * 30 * t_(d))), d) * env(int(d * SR), 0.005, 0.03) * 0.25, silence(0.05)]
    return cat(*out)


def sfx_crackle(dur=3.0, **_):
    n = int(dur * SR)
    x = lowpass(bandnoise(dur, 100, 2000), 600) * 0.12
    clicks = np.zeros(n)
    idx = rng.integers(0, n, int(dur * 25))
    clicks[idx] = rng.uniform(0.3, 1.0, len(idx))
    clicks = np.convolve(clicks, np.exp(-np.arange(200) / 30) * np.sin(np.arange(200) * 1.3), mode="same")
    return (x + clicks * 0.15) * env(n, 0.3, 0.4) * 0.6


def sfx_water(dur=3.0, **_):
    n = int(dur * SR)
    x = bandnoise(dur, 1500, 9000) * (0.8 + 0.2 * np.sin(np.linspace(0, dur * 40, n)))
    return x * env(n, 0.1, 0.3) * 0.18


def sfx_fizz(**_):
    d = 1.2
    return bandnoise(d, 2000, 10000) * expdec(int(d * SR), 0.35) * 0.25


def motor(dur, base=110, vol=0.12):
    n = int(dur * SR)
    f = base * (1 + 0.08 * np.sin(np.linspace(0, dur * 20, n)))
    x = lowpass(osc(f, dur, "saw") + 0.3 * osc(f * 1.5, dur, "square"), 900)
    return x * env(n, 0.08, 0.15) * vol


def sfx_ladder(dur=3.0, **_):
    return motor(dur, 120, 0.16)


def sfx_crane(dur=3.0, **_):
    return motor(dur, 95, 0.16)


def sfx_winch(dur=2.0, **_):
    return motor(dur, 160, 0.12)


def meow(p=1.0, d=0.55, sad=False):
    t = t_(d)
    shape = np.sin(np.pi * np.linspace(0, 1, len(t)))
    f = (520 + 260 * shape) * p
    if sad:
        f = (500 + 180 * np.sin(np.pi * np.linspace(0, 0.7, len(t)))) * p * np.linspace(1, 0.82, len(t))
    x = osc(f, d, "saw")
    x = lowpass(x, 1800 + 1200 * shape.mean()) * env(len(t), 0.03, 0.15)
    return x * 0.3


def sfx_meow_sad(**_):
    return meow(0.9, 0.8, sad=True)


def sfx_meow(**_):
    return meow(1.0, 0.5)


def sfx_meow_happy(**_):
    return cat(meow(1.2, 0.3), silence(0.05), meow(1.3, 0.35))


def sfx_slide(dur=3.0, **_):
    return osc(glide(1400, 500, dur), dur, "sine") * env(int(dur * SR), 0.05, 0.2) * 0.22


def sfx_sputter(**_):
    out = []
    for i in range(6):
        d = rng.uniform(0.06, 0.12)
        out += [lowpass(bandnoise(d, 60, 800), 300) * expdec(int(d * SR), 0.03) * 0.7, silence(rng.uniform(0.05, 0.25))]
    return cat(*out)


def sfx_clank(**_):
    return bell(420, 0.5) * 0.4 + bandnoise(0.5, 2000, 7000) * expdec(int(0.5 * SR), 0.03) * 0.2


def sfx_ratchet(dur=1.5, **_):
    n = int(dur * SR)
    out = np.zeros(n)
    for i in range(0, n, int(SR / 16)):
        c = bandnoise(0.015, 2000, 8000) * expdec(int(0.015 * SR), 0.004)
        out[i:i + len(c)] += c[: n - i] * 0.3
    return out


def sfx_beep_happy(**_):
    return cat(beep(880, 0.12, "square", 0.3), silence(0.06), beep(1175, 0.18, "square", 0.3))


def sfx_question(**_):
    d = 0.5
    return osc(glide(300, 750, d, 2.0), d, "sine") * env(int(d * SR), 0.01, 0.1) * 0.4


def baa(p=1.0, d=0.7, sad=False):
    t = t_(d)
    f = 330 * p * (1 + 0.06 * np.sin(2 * np.pi * 7 * t))
    if sad:
        f = f * np.linspace(1.0, 0.8, len(t))
    x = lowpass(osc(f, d, "saw"), 1400) + 0.3 * lowpass(osc(f * 3, d, "saw"), 3000)
    return x * env(len(t), 0.04, 0.2) * 0.25


def sfx_baa_sad(**_):
    return baa(0.9, 1.0, sad=True)


def sfx_baa(**_):
    return baa(1.1, 0.6)


def sfx_birds(dur=10.0, **_):
    n = int(dur * SR)
    out = np.zeros(n)
    t = 0.3
    while t < dur - 1:
        f0 = rng.uniform(2600, 4200)
        for k in range(rng.integers(2, 5)):
            d = rng.uniform(0.05, 0.12)
            f = glide(f0 * rng.uniform(0.95, 1.1), f0 * rng.uniform(1.1, 1.4), d)
            x = osc(f, d) * env(int(d * SR), 0.005, 0.03) * 0.05
            s = int((t + k * 0.13) * SR)
            out[s:s + len(x)] += x[: n - s]
        t += rng.uniform(1.0, 3.0)
    return out


def sfx_kick(vol=1.0, **_):
    d = 0.12
    return (osc(glide(180, 70, d), d) * expdec(int(d * SR), 0.03) + bandnoise(d, 300, 3000) * expdec(int(d * SR), 0.01) * 0.3) * 0.6 * vol


def pizz(m, d=0.18, vol=0.25):
    f = note_hz(m)
    x = lowpass(osc(f, d, "saw"), 1800) * expdec(int(d * SR), 0.05)
    return x * vol


def sfx_sneak(dur=8.0, **_):
    notes = [57, None, 60, None, 64, 63, 62, None, 57, None, 60, None, 59, 58, 57, None]
    step = 0.2
    n = int(dur * SR)
    out = np.zeros(n)
    i = 0
    t = 0.0
    while t < dur - 0.3:
        m = notes[i % len(notes)]
        if m is not None:
            x = pizz(m)
            s = int(t * SR)
            out[s:s + len(x)] += x[: n - s]
        t += step
        i += 1
    return out


def sfx_sneak_short(**_):
    return sfx_sneak(1.6)


def sfx_tiptoe(dur=4.0, **_):
    return sfx_sneak(dur) * 0.7


def sfx_oops(**_):
    d = 0.45
    return (osc(glide(700, 380, d, 0.8), d, "tri") * env(int(d * SR), 0.01, 0.15)) * 0.35


def sfx_splash(**_):
    d = 0.7
    return bandnoise(d, 400, 7000) * expdec(int(d * SR), 0.15) * 0.45


def sfx_slip(**_):
    d = 0.5
    return osc(glide(1500, 300, d, 0.6), d, "sine") * env(int(d * SR), 0.01, 0.1) * 0.25


def sfx_climb(dur=4.0, **_):
    n = int(dur * SR)
    out = np.zeros(n)
    for i in range(0, n, int(0.22 * SR)):
        c = bandnoise(0.06, 800, 4000) * expdec(int(0.06 * SR), 0.02) * 0.18
        out[i:i + len(c)] += c[: n - i]
    return out


def ooh(f0, f1, d):
    t = t_(d)
    f = glide(f0, f1, d) * (1 + 0.03 * np.sin(2 * np.pi * 8 * t))
    x = lowpass(osc(f, d, "saw"), 1600) + 0.5 * lowpass(osc(f * 2, d, "tri"), 2500)
    return x * env(len(t), 0.02, 0.06) * 0.22


def sfx_monkey(**_):
    return cat(ooh(420, 620, 0.18), silence(0.04), ooh(520, 820, 0.16), silence(0.04), ooh(620, 980, 0.2))


def sfx_monkey_scared(**_):
    return cat(*[cat(ooh(900, 1200, 0.1), silence(0.03)) for _ in range(5)])


def sfx_monkey_happy(**_):
    return cat(ooh(500, 900, 0.15), silence(0.03), ooh(600, 1100, 0.15), silence(0.03), ooh(700, 1300, 0.25))


def sfx_ding(pitch=1.0, **_):
    return bell(1320 * pitch, 0.8) * 0.35


def sfx_truck(dur=5.0, **_):
    n = int(dur * SR)
    x = lowpass(osc(55 * (1 + 0.05 * np.sin(np.linspace(0, dur * 9, n))), dur, "saw"), 400) * 0.18
    return x * env(n, 0.4, 0.6)


def sfx_beep_reverse(dur=1.5, **_):
    unit = cat(beep(1050, 0.25, "sine", 0.35), silence(0.25))
    n = int(dur * SR)
    return np.tile(unit, int(np.ceil(n / len(unit))))[:n]


def sfx_truck_beep(dur=2.0, **_):
    return sfx_beep_reverse(dur) * 0.9 + sfx_truck(dur) * 0.6


def sfx_brake(**_):
    d = 0.6
    return bandnoise(d, 2500, 4500) * env(int(d * SR), 0.02, 0.2) * 0.2


def sfx_baa_mama(**_):
    return baa(0.75, 0.9)


def sfx_whistle(**_):
    d = 0.5
    t = t_(d)
    f = 2900 * (1 + 0.04 * np.sign(np.sin(2 * np.pi * 28 * t)))
    return cat(osc(f[: int(0.18 * SR)], 0.18) * env(int(0.18 * SR), 0.005, 0.02), silence(0.06), osc(f, d) * env(len(t), 0.005, 0.05)) * 0.22


SFX = {k[4:]: v for k, v in globals().items() if k.startswith("sfx_")}

# ----------------------------------------------------------------------------- music

def drum_kick():
    d = 0.25
    return osc(glide(150, 45, d, 0.4), d) * expdec(int(d * SR), 0.08)


def drum_hat():
    d = 0.05
    return bandnoise(d, 6000, 14000) * expdec(int(d * SR), 0.012)


def drum_clap():
    d = 0.15
    return bandnoise(d, 800, 5000) * expdec(int(d * SR), 0.04)


def marimba(m, d=0.35):
    f = note_hz(m)
    n = int(d * SR)
    x = np.sin(2 * np.pi * f * t_(d)) + 0.35 * np.sin(2 * np.pi * f * 4 * t_(d)) * expdec(n, 0.02)
    return x * expdec(n, 0.12) * env(n, 0.002, 0.03)


def pluck_bass(m, d=0.4):
    f = note_hz(m)
    n = int(d * SR)
    x = lowpass(osc(f, d, "tri") + 0.3 * osc(f, d, "saw"), 600)
    return x * expdec(n, 0.25) * env(n, 0.003, 0.05)


def pad(ms, d):
    n = int(d * SR)
    x = sum(osc(note_hz(m), d, "tri") * 0.5 + osc(note_hz(m) * 1.003, d, "sine") * 0.5 for m in ms) / len(ms)
    return lowpass(x, 1500) * env(n, 0.3, 0.4)


def add(out, s, x):
    if s >= len(out):
        return
    m = min(len(x), len(out) - s)
    out[s:s + m] += x[:m]


def music(total_sec, bpm=112):
    beat = 60 / bpm
    bar = 4 * beat
    out = np.zeros(int(total_sec * SR) + SR)
    # C - G - Am - F, then C - F - G - C
    prog = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69]),
            (48, [60, 64, 67]), (41, [60, 65, 69]), (43, [59, 62, 67]), (48, [60, 64, 67])]
    phrases = [
        [72, None, 76, 79, 76, None, 74, 72],
        [74, None, 71, 74, 79, None, 77, 74],
        [76, 76, 72, None, 69, 72, 76, None],
        [77, None, 76, 74, 72, None, 69, None],
        [72, 74, 76, 79, 81, None, 79, 76],
        [77, 76, 74, None, 72, None, 74, None],
        [79, None, 77, 76, 74, 72, 71, 74],
        [72, None, 67, None, 72, None, None, None],
    ]
    nbars = int(total_sec / bar) + 1
    for b in range(nbars):
        t0 = b * bar
        root, chord = prog[b % 8]
        s = int(t0 * SR)
        p = pad([c - 12 for c in chord], bar) * 0.10
        add(out, s, p)
        for k in range(4):
            bs = int((t0 + k * beat) * SR)
            x = pluck_bass(root if k % 2 == 0 else root + 7, beat * 0.95) * 0.32
            add(out, bs, x)
            kk = drum_kick() * (0.35 if k % 2 == 0 else 0.2)
            add(out, bs, kk)
            if k % 2 == 1:
                c = drum_clap() * 0.12
                add(out, bs, c)
            for h in range(2):
                hs = int((t0 + k * beat + h * beat / 2) * SR)
                hh = drum_hat() * (0.08 if h == 0 else 0.05)
                add(out, hs, hh)
        mel = phrases[(b // 1) % 8] if (b // 8) % 2 == 0 else phrases[(b + 4) % 8]
        for i, m in enumerate(mel):
            if m is None:
                continue
            ms = int((t0 + i * beat / 2) * SR)
            x = marimba(m + (12 if (b // 16) % 2 else 0) * 0, beat * 0.9) * 0.16
            add(out, ms, x)
    return out[: int(total_sec * SR)]

# ----------------------------------------------------------------------------- mix

def main():
    order = sys.argv[1].split(",") if len(sys.argv) > 1 else ORDER
    out_name = sys.argv[2] if len(sys.argv) > 2 else "soundtrack.wav"
    segs = []
    off = 0
    for name in order:
        with open(os.path.join(BUILD, name + "_events.json")) as fh:
            d = json.load(fh)
        segs.append((name, off, d))
        off += d["frames"]
    total_frames = off
    total = total_frames / FPS
    n = int(total * SR)
    fx = np.zeros(n)
    duck = np.ones(n)
    count = 0
    for name, off, d in segs:
        for ev in d["events"]:
            fn = SFX.get(ev["name"])
            if fn is None:
                print("missing sfx", ev["name"])
                continue
            kw = {k: v for k, v in ev.items() if k not in ("frame", "name")}
            x = fn(**kw)
            s = int((off + ev["frame"]) / FPS * SR)
            if s >= n:
                continue
            fx[s:s + len(x)] += x[: n - s]
            count += 1
            if ev["name"] in ("sad", "baa_sad", "meow_sad"):
                a, b = s, min(n, s + int(3.5 * SR))
                duck[a:b] = np.minimum(duck[a:b], 0.45)
    # smooth ducking curve
    k = int(0.3 * SR)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    mus = music(total) * duck
    mix = mus * 0.9 + fx
    # game segment: soften music while the sounds are being guessed
    peak = np.abs(mix).max()
    mix = np.tanh(mix / max(peak, 1e-9) * 1.4) * 0.85
    # fades
    fi, fo = int(0.5 * SR), int(1.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    mix[-fo:] *= np.linspace(1, 0, fo)
    stereo = np.stack([mix, mix], axis=1)
    pcm = (stereo * 32767).astype(np.int16)
    path = os.path.join(BUILD, out_name)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {path}: {total:.1f}s, {count} sound effects")


if __name__ == "__main__":
    main()
