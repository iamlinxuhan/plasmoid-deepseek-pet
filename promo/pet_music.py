#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给大肥鱼宣传片现谱一段 49.5 秒的原创背景音乐。

参考 ncmctl-GUI/promo_v2_music.py 的合成方式：Am–F–C–G、电钢铺底、分解和弦、
软底鼓、侧链呼吸、卷积混响与低通扫频；这里另外写了一条五声音阶主旋律，
并按场景（桌面 / 动画 / 拖拽 / 菜单 / 片尾）改变配器密度。

不引用任何现成歌曲。输出 48kHz 立体声 WAV。
"""

from __future__ import annotations

import json
import math
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
PEAK = 0.90
CLICK = Path(__file__).resolve().parent.parent / "package/contents/ui/assets/sound/click-duck.wav"

NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "Fs": 6,
         "G": 7, "Gs": 8, "A": 9, "As": 10, "B": 11}


def note(name: str) -> float:
    octave = int(name[-1])
    return 440.0 * (2 ** ((NAMES[name[:-1]] - 9) / 12 + (octave - 4)))


def midi_hz(n: float) -> float:
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


CHORDS = [
    ("A2", ["A3", "C4", "E4"]),
    ("F2", ["F3", "A3", "C4"]),
    ("C3", ["C3", "E3", "G3"]),
    ("G2", ["G3", "B3", "D4"]),
]


def adsr(n: int, attack=0.01, decay=0.12, sustain=0.55, release=0.35) -> np.ndarray:
    env = np.ones(n)
    a = min(max(1, int(attack * SR)), n)
    d = min(max(1, int(decay * SR)), n - a)
    r = min(max(1, int(release * SR)), n - a - d)
    if a:
        env[:a] = np.linspace(0, 1, a)
    if d:
        env[a:a + d] = np.linspace(1, sustain, d)
    if n - a - d - r > 0:
        env[a + d:n - r] = sustain
    if r:
        env[n - r:] = np.linspace(sustain, 0, r)
    return env


def tone(freq: float, seconds: float, amp: float,
         harmonics=(1.0, 0.35, 0.15)) -> np.ndarray:
    n = max(1, int(seconds * SR))
    t = np.arange(n) / SR
    data = np.zeros(n)
    for index, weight in enumerate(harmonics, start=1):
        data += weight * np.sin(2 * np.pi * freq * index * t)
    return (amp * data * adsr(n)).astype(np.float32)


def lead_note(freq: float, seconds: float, amp: float) -> np.ndarray:
    n = max(1, int(seconds * SR))
    t = np.arange(n) / SR
    vib = 1.0 + 0.0032 * np.sin(2 * np.pi * 5.1 * t) * np.minimum(1.0, t / 0.35)
    ph = 2 * np.pi * np.cumsum(freq * vib) / SR
    sig = np.sin(ph) + 0.13 * np.sin(2 * ph) + 0.04 * np.sin(3 * ph)
    env = np.minimum(1.0, t / 0.055) * np.minimum(1.0, (seconds - t) / 0.16)
    return (amp * sig * np.maximum(env, 0.0)).astype(np.float32)


def bell(freq: float, seconds: float, amp: float) -> np.ndarray:
    n = max(1, int(seconds * SR))
    t = np.arange(n) / SR
    sig = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.6)
           + 0.35 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t * 4.5))
    return (amp * sig * np.minimum(1.0, t / 0.004)).astype(np.float32)


def kick(amp: float) -> np.ndarray:
    n = int(0.17 * SR)
    t = np.arange(n) / SR
    f = 92.0 * np.exp(-t * 26.0) + 42.0
    return (amp * np.sin(2 * np.pi * f * t) * np.exp(-t * 22.0)).astype(np.float32)


def whoosh(seconds: float, amp: float, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n).astype(np.float32)
    # 一阶低通，截止频率从 300Hz 扫到 4kHz
    alpha = np.linspace(0.01, 0.35, n)
    out = np.empty(n, dtype=np.float32)
    prev = 0.0
    for i in range(n):
        prev += alpha[i] * (noise[i] - prev)
        out[i] = prev
    env = np.sin(np.pi * np.clip(t / seconds, 0, 1)) ** 1.5
    return (amp * out * env).astype(np.float32)


def mix(buf: np.ndarray, sound: np.ndarray, start: float) -> None:
    i = int(start * SR)
    if i < 0:
        sound = sound[-i:]
        i = 0
    if i >= len(buf):
        return
    end = min(len(buf), i + len(sound))
    buf[i:end] += sound[:end - i]


def lowpass_sweep(signal: np.ndarray, cutoff_at) -> np.ndarray:
    block = 8192
    step = block // 2
    window = np.hanning(block)
    freqs = np.fft.rfftfreq(block, 1 / SR)
    out = np.zeros_like(signal)
    norm = np.zeros_like(signal)
    for start in range(0, len(signal), step):
        seg = signal[start:start + block]
        if len(seg) == 0:
            break
        if len(seg) < block:
            seg = np.pad(seg, (0, block - len(seg)))
        cutoff = cutoff_at((start + block / 2) / SR)
        mask = 1.0 / (1.0 + (freqs / max(1.0, cutoff)) ** 4)
        spec = np.fft.rfft(seg * window)
        filtered = np.fft.irfft(spec * mask, n=block)
        end = min(len(out), start + block)
        out[start:end] += filtered[:end - start] * window[:end - start]
        norm[start:end] += (window * window)[:end - start]
    return out / np.maximum(norm, 1e-3)


def reverb(signal: np.ndarray,
           taps=((0.031, 0.30), (0.047, 0.22), (0.071, 0.16),
                 (0.113, 0.11), (0.179, 0.07))) -> np.ndarray:
    wet = signal.copy()
    for delay, gain in taps:
        d = int(delay * SR)
        if 0 < d < len(signal):
            wet[d:] += signal[:-d] * gain
    return wet


def sidechain_env(times, total: int, depth: float = 0.30) -> np.ndarray:
    env = np.ones(total, dtype=np.float32)
    length = int(0.34 * SR)
    for start in times:
        i = int(start * SR)
        if i >= total:
            continue
        end = min(total, i + length)
        n = end - i
        curve = 1 - depth * np.exp(-np.arange(n) / (SR * 0.12))
        attack = min(n, int(0.012 * SR))
        if attack > 0:
            curve[:attack] = np.linspace(1, 1 - depth, attack)
        env[i:end] = np.minimum(env[i:end], curve)
    return env


def highpass(signal: np.ndarray, cutoff: float = 30.0) -> np.ndarray:
    rc = 1.0 / (2 * np.pi * cutoff)
    dt = 1.0 / SR
    alpha = rc / (rc + dt)
    out = np.empty_like(signal)
    prev_in = 0.0
    prev_out = 0.0
    for i, x in enumerate(signal):
        y = alpha * (prev_out + x - prev_in)
        out[i] = y
        prev_in = x
        prev_out = y
    return out


def load_click() -> np.ndarray | None:
    if not CLICK.exists():
        return None
    with wave.open(str(CLICK), "rb") as handle:
        ch = handle.getnchannels()
        sr = handle.getframerate()
        raw = handle.readframes(handle.getnframes())
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        data = data.reshape(-1, 2).mean(axis=1)
    if sr != SR and len(data) > 1:
        target = int(len(data) * SR / sr)
        data = np.interp(np.linspace(0, len(data) - 1, target),
                         np.arange(len(data)), data).astype(np.float32)
    return data


# 五声音阶主旋律：4 小节一句（A 小调），在桌面/动画/拖拽段落出现。
MOTIF = [
    (0.0, 76, 1.0), (1.0, 74, 1.0), (2.0, 72, 2.0), (4.0, 69, 2.6),
    (7.5, 72, 0.6),
    (8.0, 74, 1.0), (9.0, 76, 1.0), (10.0, 79, 2.0), (12.0, 76, 1.6),
    (14.0, 74, 0.8), (15.0, 72, 0.8),
]


def build(cues_path: str, out_path: str) -> None:
    cues = json.loads(Path(cues_path).read_text(encoding="utf-8"))
    dur = float(cues["dur"])
    bpm = float(cues.get("bpm", 92))
    beat = 60.0 / bpm
    bar = beat * 4
    total = int(SR * dur)
    rng = np.random.default_rng(7)

    starts = {s["name"]: float(s["start"]) for s in cues.get("scenes", [])}
    trans = [float(x) for x in cues.get("trans", [])]
    s_desk = starts.get("desktop", 4.3)
    s_anim = starts.get("anims", 12.6)
    s_throw = starts.get("throw", 22.9)
    s_menu = starts.get("menu", 32.2)
    s_out = starts.get("outro", 40.5)

    def section_at(t: float) -> str:
        if t < s_desk:
            return "intro"
        if t < s_anim:
            return "desktop"
        if t < s_throw:
            return "anims"
        if t < s_menu:
            return "throw"
        if t < s_out:
            return "menu"
        return "outro"

    bass_l = np.zeros(total, dtype=np.float32)
    bass_r = np.zeros(total, dtype=np.float32)
    pad_l = np.zeros(total, dtype=np.float32)
    pad_r = np.zeros(total, dtype=np.float32)
    arp_l = np.zeros(total, dtype=np.float32)
    arp_r = np.zeros(total, dtype=np.float32)
    lead_l = np.zeros(total, dtype=np.float32)
    lead_r = np.zeros(total, dtype=np.float32)
    kick_l = np.zeros(total, dtype=np.float32)
    kick_r = np.zeros(total, dtype=np.float32)
    perc_l = np.zeros(total, dtype=np.float32)
    perc_r = np.zeros(total, dtype=np.float32)
    kick_times = []

    gains = {
        "intro": dict(pad=0.055, bass=0.0, arp=0.030, kick=0.0, lead=0.0, perc=0.0),
        "desktop": dict(pad=0.038, bass=0.105, arp=0.045, kick=0.16, lead=0.090, perc=0.0),
        "anims": dict(pad=0.046, bass=0.120, arp=0.055, kick=0.19, lead=0.115, perc=0.020),
        "throw": dict(pad=0.040, bass=0.130, arp=0.060, kick=0.20, lead=0.125, perc=0.024),
        "menu": dict(pad=0.042, bass=0.070, arp=0.034, kick=0.0, lead=0.040, perc=0.0),
        "outro": dict(pad=0.055, bass=0.0, arp=0.026, kick=0.0, lead=0.0, perc=0.0),
    }

    bars = int(dur / bar) + 1
    for b in range(bars):
        t0 = b * bar
        sec = section_at(t0)
        g = gains[sec]
        root_name, chord = CHORDS[b % 4]
        root = note(root_name)
        if sec == "intro" and b < 2:
            g = dict(g, pad=0.045, arp=0.018)
        # 拖拽场景开头半小节抽掉鼓，制造“被抓起”的停顿
        drop = sec == "throw" and t0 <= s_throw + 0.8
        # 低音
        if g["bass"] > 0:
            bass = tone(root, beat * 1.6, g["bass"], (1.0, 0.2))
            mix(bass_l, bass, t0)
            mix(bass_r, bass, t0)
        # 铺底
        for index, name in enumerate(chord):
            pad = tone(note(name), bar * 0.95, g["pad"],
                       (1.0, 0.4, 0.2, 0.08))
            jitter = rng.uniform(-0.004, 0.004)
            mix(pad_l, pad * (0.9 if index else 1.0), t0 + jitter)
            mix(pad_r, pad * (1.0 if index else 0.9), t0 + jitter)
        # 分解和弦
        for step in range(8):
            name = chord[step % len(chord)]
            freq = note(name)
            arp = tone(freq, beat * 0.45, g["arp"] * rng.uniform(0.9, 1.1),
                       (1.0, 0.25, 0.1))
            start = t0 + step * beat / 2 + rng.uniform(-0.006, 0.006)
            pan = 0.65 + 0.35 * (step % 2)
            mix(arp_l, arp * pan, start)
            mix(arp_r, arp * (1.35 - pan), start)
        # 鼓
        if g["kick"] > 0 and not drop:
            for beat_i in range(4):
                start = t0 + beat_i * beat
                k = kick(g["kick"])
                mix(kick_l, k, start)
                mix(kick_r, k, start)
                kick_times.append(start)
        # 轻沙锤
        if g["perc"] > 0:
            for step in range(8):
                if step == 5:
                    continue
                n = int(0.05 * SR)
                noise = (rng.normal(0, 1, n) *
                         np.exp(-np.arange(n) / SR * 90)).astype(np.float32)
                start = t0 + step * beat / 2
                mix(perc_l, noise * g["perc"] * 1.0, start)
                mix(perc_r, noise * g["perc"] * 0.8, start)
        # 主旋律：桌面进入，菜单退成稀疏，片尾收住
        if g["lead"] > 0 and b >= int(s_desk / bar):
            amp = g["lead"]
            if sec == "menu":
                amp *= 0.7
            if sec == "throw" and t0 > s_throw + 5.0:
                amp *= 0.75
            for pos, midi, length in MOTIF:
                start = t0 + pos * beat
                if start >= dur:
                    continue
                if sec == "menu" and pos not in (0.0, 4.0, 8.0, 12.0):
                    continue
                ln = lead_note(midi_hz(midi), length * beat * 1.02, amp)
                mix(lead_l, ln, start)
                mix(lead_r, ln * 0.92, start)

    # 片尾长和弦
    tail = max(0.0, dur - bar * 2.0)
    for name in ["A3", "C4", "E4"]:
        pad = tone(note(name), dur - tail, 0.045, (1.0, 0.3, 0.1))
        mix(pad_l, pad, tail)
        mix(pad_r, pad, tail)
    mix(lead_l, bell(midi_hz(81), 3.2, 0.06), tail + 0.2)
    mix(lead_r, bell(midi_hz(81), 3.2, 0.06), tail + 0.2)

    # 转场铃
    for i, t in enumerate(trans):
        mix(lead_l, bell(midi_hz(76 if i % 2 == 0 else 81), 1.8, 0.035), max(0.0, t - 0.1))
        mix(lead_r, bell(midi_hz(76 if i % 2 == 0 else 81), 1.8, 0.030), max(0.0, t - 0.1))

    # 点击音效（桌宠自己的 click-duck.wav）
    click = load_click()
    if click is not None:
        click_start = s_desk + 3.0
        mix(lead_l, click * 0.32, click_start)
        mix(lead_r, click * 0.32, click_start)

    # 甩出 whoosh + 落地低频
    wh = whoosh(0.55, 0.10, 21)
    mix(perc_l, wh, s_throw + 3.5)
    mix(perc_r, wh * 0.8, s_throw + 3.5)
    land = kick(0.20)
    mix(kick_l, land, s_throw + 6.2)
    mix(kick_r, land, s_throw + 6.2)

    # 琶音低通扫频：桌面偏暗，动画/拖拽打开，菜单收回来
    def cutoff(t: float) -> float:
        if t < s_desk:
            return 700 + 1800 * (t / max(0.1, s_desk))
        if t < s_anim:
            return 4200
        if t < s_menu:
            return 7600
        if t < s_out:
            return 4600
        return 3200

    arp_l = lowpass_sweep(arp_l, cutoff)
    arp_r = lowpass_sweep(arp_r, cutoff)

    dry = (pad_l + pad_r + arp_l + arp_r) * 0.5
    wet = reverb(dry) * 0.42
    env = sidechain_env(kick_times, total, 0.28)
    left = kick_l + (bass_l + pad_l + arp_l) * env + lead_l * 1.0 + perc_l * 0.8 + wet * 0.5
    right = kick_r + (bass_r + pad_r + arp_r) * env + lead_r * 1.0 + perc_r * 0.8 + wet * 0.5

    left = highpass(left)
    right = highpass(right)

    # 淡入淡出
    fade_in = int(1.2 * SR)
    fade_out = int(2.8 * SR)
    for channel in (left, right):
        channel[:fade_in] *= np.linspace(0, 1, fade_in) ** 1.2
        channel[-fade_out:] *= np.linspace(1, 0, fade_out) ** 1.2

    left = np.tanh(left * 1.2) / 1.2
    right = np.tanh(right * 1.2) / 1.2
    peak = max(float(np.max(np.abs(left))), float(np.max(np.abs(right))), 1e-9)
    left = (left / peak * PEAK * 32767).astype(np.int16)
    right = (right / peak * PEAK * 32767).astype(np.int16)
    stereo = np.stack([left, right], axis=1).reshape(-1)
    with wave.open(out_path, "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(stereo.tobytes())
    rms = float(np.sqrt(np.mean((left.astype(np.float32) / 32767.0) ** 2)))
    print("music %.2fs · %d bars · RMS %.1f dBFS -> %s"
          % (dur, bars, 20 * math.log10(max(rms, 1e-9)), out_path))


def main() -> int:
    cues = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pet_promo_cues.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/pet_promo_audio.wav"
    build(cues, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
