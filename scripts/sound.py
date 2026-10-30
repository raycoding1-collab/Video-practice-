#!/usr/bin/env python3
"""Synthesise a soundtrack (beat-synced music bed + sound effects) from a cue list.

Everything is generated with numpy, so it is free and unlimited.

Usage: python3 scripts/sound.py cues.json out.wav

cues.json:
  {"duration": 10, "bpm": 120, "music": [0, 8],
   "cues": [{"t": 0, "sfx": "hit"}, {"t": 2, "sfx": "whoosh", "len": 0.35}, ...]}

Effects: hit, thud, drop, pop, tick, swish, glitch, whoosh, riser.
whoosh and riser *end* at t, so a cue at a cut leads into it.
"""
import json
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(7)


def ts(dur):
    return np.arange(int(dur * SR)) / SR


def noise(dur):
    return rng.standard_normal((int(dur * SR), 2))


def filt(x, kind, freq, order=2):
    sos = signal.butter(order, freq, kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def stereo(x):
    return np.stack([x, x], 1) if x.ndim == 1 else x


def place(buf, x, t):
    x, i = stereo(x), int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n]


def chirp(f_end, f_start, dur, tau):
    """Sine whose pitch glides from f_start to f_end with time constant tau."""
    t = ts(dur)
    f = f_end + (f_start - f_end) * np.exp(-t / tau)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def swept_noise(dur, f0, f1, width=0.5):
    """Noise with a resonant band sweeping from f0 to f1 (spectral mask)."""
    n = noise(dur)
    f, tt, z = signal.stft(n.T, fs=SR, nperseg=1024)
    fc = f0 * (f1 / f0) ** np.clip(tt / dur, 0, 1)
    mask = np.exp(-0.5 * ((np.log(f[:, None] + 1) - np.log(fc[None, :])) / width) ** 2)
    _, y = signal.istft(z * mask, fs=SR, nperseg=1024)
    y = y.T[:len(n)]
    return y / (np.abs(y).max() + 1e-9)


# ---------------------------------------------------------------- instruments

def kick():
    t = ts(0.45)
    body = chirp(42, 150, 0.45, 0.025) * np.exp(-t / 0.13)
    click = filt(noise(0.45)[:, 0], "highpass", 2000) * np.exp(-t / 0.002) * 0.25
    return np.tanh(1.6 * (body + click)) * 0.8


def hat():
    t = ts(0.06)
    return filt(noise(0.06), "highpass", 7000) * np.exp(-t / 0.012)[:, None] * 0.12


def clap():
    out = np.zeros((int(0.25 * SR), 2))
    for k, off in enumerate((0, 0.011, 0.022)):
        t = ts(0.2)
        burst = filt(noise(0.2), "bandpass", [900, 2600]) * np.exp(-t / (0.012 if k < 2 else 0.07))[:, None]
        place(out, burst, off)
    return out * 0.35


def bass(f, dur):
    t = ts(dur)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / 0.005) * np.exp(-t / (dur * 0.6))
    return np.tanh(2.2 * x * env) * 0.3


def pad(dur, chord=(110, 164.8, 220, 261.6, 329.6)):
    t = ts(dur)
    out = np.zeros((len(t), 2))
    for f in chord:
        for ch, det in ((0, 0.35), (1, -0.35)):
            out[:, ch] += sum(np.sin(2 * np.pi * (f + det) * k * t) / k for k in range(1, 7))
    out = filt(out, "lowpass", 1100)
    env = np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.8)
    return out / np.abs(out).max() * env[:, None] * 0.09


# ---------------------------------------------------------------- effects

def hit(**_):
    t = ts(1.2)
    boom = chirp(32, 95, 1.2, 0.08) * np.exp(-t / 0.32)
    crack = filt(noise(1.2), "lowpass", 3500) * np.exp(-t / 0.05)[:, None] * 0.5
    out = stereo(boom) + crack
    place(out, clap(), 0)
    return np.tanh(1.4 * out) * 0.9


def thud(**_):
    t = ts(0.45)
    return stereo(kick()) * 0.9 + filt(noise(0.45), "lowpass", 1500) * np.exp(-t / 0.03)[:, None] * 0.3


def drop(**_):
    t = ts(3.0)
    sub = chirp(28, 75, 3.0, 0.25) * np.exp(-t / 0.9)
    out = stereo(sub)
    place(out, hit() * 0.7, 0)
    return np.tanh(1.3 * out) * 0.95


def pop(**_):
    t = ts(0.09)
    return stereo(chirp(480, 1300, 0.09, 0.02) * np.exp(-t / 0.035)) * 0.3


def tick(**_):
    t = ts(0.03)
    return filt(noise(0.03), "highpass", 3000) * np.exp(-t / 0.003)[:, None] * 0.35


def swish(dur=0.3, **_):
    t = ts(dur)
    return swept_noise(dur, 3500, 700) * np.sin(np.pi * t / dur)[:, None] * 0.3


def glitch(dur=0.32, **_):
    out = np.zeros((int(dur * SR), 2))
    t0 = 0.0
    while t0 < dur - 0.04:
        seg = rng.uniform(0.012, 0.04)
        t = ts(seg)
        if rng.random() < 0.5:
            x = stereo(np.sign(np.sin(2 * np.pi * rng.uniform(150, 2200) * t)))
        else:  # sample-and-hold "bitcrushed" noise
            x = np.repeat(noise(seg / 12), 12, axis=0)[: len(t)]
        place(out, x * rng.uniform(0.15, 0.35), t0)
        t0 += seg + rng.uniform(0, 0.02)
    return out


def whoosh(dur=0.35, **_):
    t = ts(dur)
    env = (t / dur) ** 1.6 * np.minimum(1, (dur - t) / 0.015)
    return swept_noise(dur, 350, 5500) * env[:, None] * 0.45


def riser(dur=1.5, **_):
    t = ts(dur)
    env = (t / dur) ** 2 * np.minimum(1, (dur - t) / 0.01)
    tone = np.sin(2 * np.pi * np.cumsum(150 + 1250 * (t / dur) ** 2) / SR)
    return (swept_noise(dur, 200, 9000) * 0.35 + stereo(tone) * 0.15) * env[:, None]


SFX = {f.__name__: f for f in (hit, thud, drop, pop, tick, swish, glitch, whoosh, riser)}
LEADS_IN = {"whoosh", "riser"}  # these end at their cue time
DUCKERS = {"hit", "thud", "drop"}


def reverb(x, secs=1.1):
    t = ts(secs)
    ir = filt(noise(secs), "lowpass", 5000) * np.exp(-t / 0.22)[:, None]
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)


def main(cue_file, out_file):
    spec = json.load(open(cue_file))
    n = int(spec["duration"] * SR)
    music, sfx = np.zeros((n, 2)), np.zeros((n, 2))

    if spec.get("music"):
        start, end = spec["music"]
        beat = 60 / spec.get("bpm", 120)
        roots = (55, 55, 43.65, 49)  # A, A, F, G
        for b in range(int(round((end - start) / beat))):
            tb = start + b * beat
            root = roots[(b // 4) % len(roots)]
            place(music, kick(), tb)
            place(music, hat(), tb + beat / 2)
            if b % 2:
                place(music, clap(), tb)
            place(music, bass(root, beat * 0.45), tb)
            place(music, bass(root * (2 if b % 4 == 3 else 1), beat * 0.4), tb + beat / 2)
        place(music, pad(end - start + 0.6), start)
        i = int(end * SR)  # hard stop at the end of the music, with a tiny fade
        music[i:] = 0
        music[max(0, i - 240):i] *= np.linspace(1, 0, min(240, i))[:, None]

    duck = np.ones(n)
    for cue in spec["cues"]:
        kind, t = cue["sfx"], cue["t"]
        x = SFX[kind](**({"dur": cue["len"]} if "len" in cue else {}))
        place(sfx, x, t - len(x) / SR if kind in LEADS_IN else t)
        if kind in DUCKERS:  # sidechain: dip the music under impacts
            i = int(t * SR)
            rec = np.linspace(0.3, 1, int(0.3 * SR))
            seg = duck[i:i + len(rec)]
            duck[i:i + len(rec)] = np.minimum(seg, rec[: len(seg)])

    mix = music * duck[:, None] + sfx + reverb(sfx) * 0.22
    mix /= np.abs(mix).max() + 1e-9
    mix = np.tanh(1.6 * mix) / np.tanh(1.6) * 0.9
    wavfile.write(out_file, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
