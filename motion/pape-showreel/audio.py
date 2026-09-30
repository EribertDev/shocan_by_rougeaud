"""Bande-son synthétisée du showreel PAPE (120 BPM, 20 s), calée sur les temps de index.html.

    python3 audio.py  ->  soundtrack.wav
"""
import wave
import numpy as np

SR = 44100
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
L = np.zeros(N)
R = np.zeros(N)
BEAT = 0.5


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * gain * (1 - max(0, pan))
    R[i:i + len(sig)] += sig * gain * (1 + min(0, pan))


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def lowpass(x, cutoff):
    """Passe-bas à un pôle ; cutoff peut être un tableau (filtre qui s'ouvre)."""
    cutoff = np.broadcast_to(cutoff, x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def kick(gain=1.0):
    n = int(.45 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / .035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .001, .16) * gain


def hat(dur=.05):
    n = int(dur * SR); x = rng.standard_normal(n)
    x = x - lowpass(x, 7000)
    return x * env(n, .0005, dur / 3)


def clap():
    n = int(.25 * SR); x = rng.standard_normal(n)
    x = lowpass(x, 3500) - lowpass(x, 900)
    e = env(n, .001, .07)
    for d in (.0, .011, .022):
        e[int(d * SR):] += env(n - int(d * SR), .0005, .008) * .6
    return x * e * 2.2


def blip(freq, dur=.12, gain=.3):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * t) * env(n, .001, dur / 4) * gain


def whoosh(dur=.45, up=True):
    n = int(dur * SR); x = rng.standard_normal(n)
    k = np.linspace(0, 1, n)
    cut = 300 + 7000 * (k ** 2 if up else (1 - k) ** 2)
    shape = np.sin(np.pi * np.clip(k if up else 1 - k, 0, 1) ** (2.2 if up else .5)) ** 1.5
    return lowpass(x, cut) * shape * .9


def impact():
    n = int(1.6 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / .08)) / SR) * env(n, .001, .5)
    crack = lowpass(rng.standard_normal(n), 2500) * env(n, .001, .06)
    return boom * 1.1 + crack * .8


def riser(dur):
    n = int(dur * SR); k = np.linspace(0, 1, n)
    noise = lowpass(rng.standard_normal(n), 200 + 9000 * k ** 3) * k ** 2
    tone = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (k * 3)) / SR) * k ** 3 * .25
    return noise * .8 + tone


def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    f = freq * (1 + detune)
    return 2 * ((t * f) % 1) - 1


def note(freq, dur, cutoff=600, gain=.3, a=.01, d=None):
    n = int(dur * SR)
    x = (saw(freq, n) + saw(freq, n, .006) + saw(freq, n, -.006)) / 3
    x = lowpass(x, cutoff)
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.minimum(1, (dur - t) / .05)
    if d:
        e *= np.exp(-t / d)
    return x * e * gain


# ---------- progression : Am – F – C – G (une mesure = 2 s) ----------
ROOTS = [55.0, 43.65, 65.41, 49.0]
CHORDS = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]

# nappes (tout le long, sauf la fin)
for bar in range(10):
    t0 = bar * 2.0
    if t0 >= 19.5:
        break
    ch = CHORDS[bar % 4]
    dur = min(2.0, 19.6 - t0)
    for j, f in enumerate(ch):
        add(note(f, dur, cutoff=900 if t0 >= 5 else 500, gain=.05, a=.4), t0, pan=(j - 1) * .5)

# basse pulsée en croches (à partir de 2 s)
for bar in range(1, 10):
    t0 = bar * 2.0
    for s in range(8):
        t = t0 + s * .25
        if t >= 19.25 or 16.0 <= t < 16.5:
            continue
        add(note(ROOTS[bar % 4], .22, cutoff=380, gain=.35, a=.004, d=.12), t)

# kick
for b in range(int(DUR / BEAT)):
    t = b * BEAT
    if 2.0 <= t < 16.0 or 16.5 <= t < 19.5:
        add(kick(), t, .95)
add(kick(.6), 0.05)

# clap sur les temps 2 et 4, hats
for b in range(int(DUR / BEAT)):
    t = b * BEAT
    if 5.0 <= t < 16.0 and b % 2 == 1:
        add(clap(), t, .5)
    if 16.5 <= t < 19.5 and b % 2 == 1:
        add(clap(), t, .5)
for s in range(int(DUR / .125)):
    t = s * .125
    if 5.0 <= t < 16.0 or 16.5 <= t < 19.4:
        add(hat(.04 if s % 2 else .07), t, .18 if s % 2 else .28, pan=.3 if s % 2 else -.3)
    elif 2.0 <= t < 5.0 and s % 4 == 2:
        add(hat(.08), t, .3)

# intro : riser + « pop » du point
add(riser(1.0), 0.6, .5)
add(blip(880, .3, .35), 0.07)
add(blip(1320, .2, .2), 1.05)

# lettres PAPE et soulignement
for i in range(4):
    add(blip([440, 554, 659, 880][i], .15, .28), 2.33 + i * .11, pan=(i - 1.5) * .3)

# machine à écrire (38 caractères/s pendant le sous-titre)
for i in range(52):
    add(hat(.015), 3.05 + i / 38, .22, pan=(i % 5 - 2) * .15)

# whooshes aux transitions
for t in (1.55, 4.55, 5.65, 6.55, 7.45, 11.85, 16.05, 19.15):
    add(whoosh(.45), t, .55, pan=.2)
add(whoosh(.5, up=False), 8.25, .4)

# impacts
for t in (2.33, 5.0, 12.5, 16.5):
    add(impact(), t, .55)
add(impact(), 15.45, .7)

# cartes services et nœuds de la frise
for i in range(4):
    add(blip(660 + i * 110, .1, .22), 8.7 + i * .14, pan=(i - 1.5) * .4)


def ease_io(k):
    return 4 * k ** 3 if k < .5 else 1 - (-2 * k + 2) ** 3 / 2


for i in range(5):
    target = i / 4
    for s in range(281):
        tt = 12.6 + s * .01
        if ease_io(min(1, (tt - 12.6) / 2.8)) >= target - 1e-3:
            add(blip([523, 587, 659, 784, 1047][i], .25, .25), tt, pan=(i - 2) * .35)
            break

# montée vers la signature
add(riser(2.0), 14.05, .45)

# clic sur le bouton + fin
add(blip(1800, .03, .5), 18.6)
add(blip(900, .08, .3), 18.62)
add(impact(), 19.5, .45)

# ---------- réverbération légère + master ----------
ir_n = int(1.2 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR / .35)
ir /= np.sqrt(np.sum(ir ** 2)) * 6


def reverb(x):
    m = len(x) + ir_n
    size = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]


L2 = L + reverb(L) * .5
R2 = R + reverb(np.roll(R, 400)) * .5
mix = np.stack([L2, R2], 1)
mix = np.tanh(mix * 1.3) / np.tanh(1.3)  # saturation douce / limiteur
fade = np.ones(N)
fade[-int(.35 * SR):] = np.linspace(1, 0, int(.35 * SR))
mix *= fade[:, None]
mix = mix / np.max(np.abs(mix)) * .92

with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('soundtrack.wav written')
