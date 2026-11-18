#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepSeek 大肥鱼 · 宣传片生成器.

4096×2560 @ 60fps。时间轴与配乐见 timeline.py / pet_music.py。
画面全部用 PyQt5 QPainter 现画；宠物帧从上游 640×360 WebM 现抽（带 alpha），
抽不到时退回包内的动画 WebP。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from functools import lru_cache

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import PyQt5  # noqa: E402

os.environ.setdefault(
    "QT_QPA_PLATFORM_PLUGIN_PATH",
    os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins", "platforms"),
)

from PyQt5.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PyQt5.QtGui import (  # noqa: E402
    QColor, QFont, QFontDatabase, QFontMetricsF, QGuiApplication, QImage,
    QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF,
    QRadialGradient,
)

from PIL import Image  # noqa: E402

import timeline as T  # noqa: E402

# 逻辑画布（输出 2×）
LW, LH = 2048, 1280
W, H = 4096, 2560
FPS = 60

ANIM_DIR = os.path.join(ROOT, "package", "contents", "ui", "assets", "anim")
FRAMES_ROOT = "/tmp/pet_promo_frames"
NEW_SRC = os.path.join(ROOT, "reference", "dsh-pet-indesktop", "assets",
                       "characters", "shenshen", "videos")
OLD_SRC = os.path.join(ROOT, "reference", "dsh-pet-src", "dsh-pet", "assets", "webm")

# ---------------- 配色 ----------------
BG0 = "#9be7ff"
BG1 = "#c9d4ff"
BG2 = "#ffd9ec"
INK = "#0b1b33"
MUTED = "#465a78"
DIM = "#64748b"
LINE = "#cbd5e1"
BLUE = "#0284c7"
BLUE_D = "#38bdf8"
PINK = "#db2777"
GREEN = "#059669"
YELLOW = "#f59e0b"
PURPLE = "#7c3aed"


def col(hexstr: str, alpha: float = 1.0) -> QColor:
    c = QColor(hexstr)
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    return c


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smooth(v):
    v = clamp(v)
    return v * v * (3 - 2 * v)


def ease_out(v):
    v = clamp(v)
    return 1 - (1 - v) ** 3


def seg(u, a, b):
    if b <= a:
        return 1.0 if u >= b else 0.0
    return clamp((u - a) / (b - a))


# ---------------- 字体 ----------------
FAM = {}


def _families():
    global FAM
    if not FAM:
        fams = set(QFontDatabase().families())
        for role, choices in {
            "sans": ["HarmonyOS Sans SC", "Microsoft YaHei", "Noto Sans CJK SC", "Droid Sans Fallback"],
            "serif": ["SimSun", "宋体", "Noto Serif CJK SC"],
            "mono": ["DejaVu Sans Mono", "Noto Sans Mono"],
        }.items():
            FAM[role] = next((c for c in choices if c in fams), choices[-1])
    return FAM


@lru_cache(maxsize=256)
def font(px: int, bold: bool = False, role: str = "sans", italic: bool = False) -> QFont:
    f = QFont(_families()[role])
    f.setPixelSize(max(1, int(px)))
    f.setWeight(QFont.Bold if bold else QFont.Normal)
    f.setItalic(italic)
    f.setHintingPreference(QFont.PreferNoHinting)
    return f


def _rounded_path(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def text(p: QPainter, s: str, rect: QRectF, px: float, color: str,
         bold: bool = False, align=Qt.AlignLeft | Qt.AlignVCenter,
         alpha: float = 1.0, role: str = "sans", italic: bool = False) -> None:
    if alpha <= 0.002:
        return
    p.setFont(font(int(px), bold, role, italic))
    p.setPen(col(color, alpha))
    p.drawText(rect, int(align), s)


def text_w(s: str, px: float, bold: bool = False, role: str = "sans") -> float:
    return QFontMetricsF(font(int(px), bold, role)).horizontalAdvance(s)


# ---------------- 通用绘制 ----------------


def rrect(p: QPainter, rect: QRectF, r: float, fill: str | None,
          border: str | None = None, bw: float = 1.0, alpha: float = 1.0,
          shadow: float = 0.0) -> None:
    if shadow > 0:
        for i, a in ((18, 0.06), (10, 0.10), (4, 0.16)):
            p.setPen(Qt.NoPen)
            p.setBrush(col("#000000", a * alpha * shadow))
            p.drawRoundedRect(rect.adjusted(-i, -i + 6, i, i + 10), r + i, r + i)
    p.setPen(QPen(col(border, alpha), bw) if border else Qt.NoPen)
    p.setBrush(col(fill, alpha) if fill else Qt.NoBrush)
    p.drawRoundedRect(rect, r, r)


def glow(p: QPainter, cx: float, cy: float, radius: float, color: str,
         alpha: float) -> None:
    g = QRadialGradient(QPointF(cx, cy), radius)
    g.setColorAt(0.0, col(color, alpha))
    g.setColorAt(0.55, col(color, alpha * 0.35))
    g.setColorAt(1.0, col(color, 0.0))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(QPointF(cx, cy), radius, radius)


def background(p: QPainter, u: float, variant: int = 0) -> None:
    g = QLinearGradient(0, 0, LW, LH)
    g.setColorAt(0.0, QColor(BG0))
    g.setColorAt(0.55, QColor(BG1))
    g.setColorAt(1.0, QColor(BG2))
    p.fillRect(0, 0, LW, LH, g)
    glow(p, LW * 0.72, LH * 0.28, LW * 0.46, "#bae6fd", 0.36)
    glow(p, LW * 0.20, LH * 0.82, LW * 0.30, "#ddd6fe", 0.22)
    if variant:
        glow(p, LW * 0.50, LH * 0.48, LW * 0.32, "#a5f3fc", 0.14)
    p.setPen(QPen(col(INK, 0.025), 1.0))
    step = 96
    for x in range(0, LW + 1, step):
        p.drawLine(x, 0, x, LH)
    for y in range(0, LH + 1, step):
        p.drawLine(0, y, LW, y)
    colors = ["#7dd3fc", "#c4b5fd", "#f9a8d4", "#a7f3d0"]
    for i, (fx, fy, rr, aa) in enumerate([
        (0.16, 0.24, 90, 0.06), (0.84, 0.72, 130, 0.05),
        (0.62, 0.12, 50, 0.08), (0.40, 0.90, 70, 0.04),
    ]):
        x = LW * fx + math.sin(u * 0.25 + i) * 18
        y = LH * fy + math.cos(u * 0.20 + i) * 14
        p.setPen(Qt.NoPen)
        p.setBrush(col(colors[i % 4], aa * 1.7))
        p.drawEllipse(QPointF(x, y), rr, rr)


def footer(p: QPainter, u: float, alpha: float = 0.55) -> None:
    p.setPen(Qt.NoPen)
    p.setBrush(col(BLUE, 0.7 * alpha))
    p.drawEllipse(QPointF(112, 1228), 4, 4)
    text(p, "DeepSeek 大肥鱼 · KDE Plasma 6", QRectF(126, 1210, 700, 36),
         17, MUTED, alpha=alpha)


# ---------------- 宠物帧 ----------------


def _find_source(name: str) -> str | None:
    for dp, _ds, fs in os.walk(NEW_SRC):
        if name + ".webm" in fs:
            return os.path.join(dp, name + ".webm")
    p = os.path.join(OLD_SRC, name + ".webm")
    return p if os.path.exists(p) else None


def prepare_frames(names) -> None:
    os.makedirs(FRAMES_ROOT, exist_ok=True)
    for name in names:
        outdir = os.path.join(FRAMES_ROOT, name)
        if os.path.isdir(outdir) and len([f for f in os.listdir(outdir) if f.endswith(".png")]) > 20:
            continue
        src = _find_source(name)
        if not src:
            print("  [warn] no source for", name, "- will fall back to WebP")
            continue
        os.makedirs(outdir, exist_ok=True)
        print("  extract", name)
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-c:v", "libvpx-vp9", "-i", src,
            "-vf", "fps=20,format=rgba,lut=c3='if(lt(val,2),0,val)'",
            "-pix_fmt", "rgba",
            os.path.join(outdir, "%03d.png"),
        ], check=True)


@lru_cache(maxsize=5)
def frames(name: str):
    outdir = os.path.join(FRAMES_ROOT, name)
    paths = sorted(
        os.path.join(outdir, f) for f in os.listdir(outdir)
        if f.endswith(".png")
    ) if os.path.isdir(outdir) else []
    if paths:
        return [QImage(p).convertToFormat(QImage.Format_RGBA8888) for p in paths]
    # 退回包内 WebP
    path = os.path.join(ANIM_DIR, name + ".webp")
    im = Image.open(path)
    out = []
    for i in range(im.n_frames):
        im.seek(i)
        rgba = im.convert("RGBA")
        out.append(QImage(rgba.tobytes(), rgba.width, rgba.height,
                          QImage.Format_RGBA8888).copy())
    return out


def pet(p: QPainter, rect: QRectF, name: str, t: float, start: float = 0.0,
        alpha: float = 1.0, squash: float = 1.0, rot: float = 0.0) -> None:
    fs = frames(name)
    if not fs:
        return
    idx = int(max(0.0, t - start) * 20) % len(fs)
    img = fs[idx]
    p.save()
    p.setOpacity(alpha)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    c = rect.center()
    p.translate(c)
    p.rotate(rot)
    p.translate(-c)
    p.translate(c.x(), rect.bottom())
    p.scale(1.0, squash)
    p.translate(-c.x(), -rect.bottom())
    p.drawImage(rect, img)
    p.restore()


def squash_at(u: float, t0: float, depth: float = 0.72) -> float:
    if u < t0:
        return 1.0
    v = (u - t0) / 0.24
    if v >= 1:
        return 1.0
    if v < 0.45:
        return 1 - (1 - depth) * (v / 0.45) ** 2
    q = (v - 0.45) / 0.55
    c1 = 1.70158
    f = 1 + (c1 + 1) * (q - 1) ** 3 + c1 * (q - 1) ** 2
    return depth + (1 - depth) * max(f, 0)


# ---------------- 小件 ----------------


def cursor(p: QPainter, x: float, y: float, alpha: float = 1.0,
           scale: float = 1.0, ring: float = 0.0) -> None:
    p.save()
    p.setOpacity(alpha)
    p.translate(x, y)
    p.scale(scale, scale)
    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(0, 34)
    path.lineTo(9, 25)
    path.lineTo(16, 42)
    path.lineTo(23, 39)
    path.lineTo(16, 22)
    path.lineTo(28, 22)
    path.closeSubpath()
    p.setPen(QPen(col("#020617", 0.9), 2.0))
    p.setBrush(col("#f8fafc"))
    p.drawPath(path)
    if ring > 0:
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(col(BLUE, 0.8 * (1 - ring)), 3))
        p.drawEllipse(QPointF(2, 2), 10 + 34 * ring, 10 + 34 * ring)
    p.restore()


def bubble(p: QPainter, cx: float, bottom: float, msg: str, alpha: float,
           scale: float = 1.0) -> None:
    if alpha <= 0.002:
        return
    f = font(24, False, "sans")
    fm = QFontMetricsF(f)
    maxw = 540
    br = fm.boundingRect(QRectF(0, 0, maxw, 1000), int(Qt.TextWordWrap), msg)
    w = min(maxw, max(150, br.width() + 52))
    h = br.height() + 38
    rect = QRectF(cx - w / 2, bottom - h - 14, w, h)
    p.save()
    p.setOpacity(alpha)
    p.translate(cx, bottom - 14)
    p.scale(scale, scale)
    p.translate(-cx, -(bottom - 14))
    for i, a in ((12, 0.08), (6, 0.13)):
        p.setPen(Qt.NoPen)
        p.setBrush(col("#000000", a))
        p.drawRoundedRect(rect.adjusted(-i, -i, i, i + 6), 18 + i, 18 + i)
    p.setPen(QPen(col(YELLOW, 0.62), 1.4))
    p.setBrush(col("#fff8dc"))
    p.drawRoundedRect(rect, 18, 18)
    tail = QPolygonF([QPointF(cx - 13, rect.bottom() - 2),
                      QPointF(cx + 13, rect.bottom() - 2),
                      QPointF(cx - 1, rect.bottom() + 16)])
    p.setPen(Qt.NoPen)
    p.setBrush(col("#fff8dc"))
    p.drawPolygon(tail)
    p.setFont(f)
    p.setPen(col(INK))
    p.drawText(QRectF(rect.x() + 26, rect.y() + 19, rect.width() - 52,
                      rect.height() - 38), int(Qt.TextWordWrap | Qt.AlignHCenter | Qt.AlignVCenter), msg)
    p.restore()


def badge(p: QPainter, x: float, y: float, label: str, alpha: float,
          accent: str = BLUE) -> None:
    if alpha <= 0.002:
        return
    f = font(19, True, "sans")
    w = QFontMetricsF(f).horizontalAdvance(label) + 52
    rect = QRectF(x, y, w, 40)
    p.save()
    p.setOpacity(alpha)
    p.setPen(QPen(col(accent, 0.55), 1.2))
    p.setBrush(col(accent, 0.12))
    p.drawRoundedRect(rect, 20, 20)
    p.setPen(Qt.NoPen)
    p.setBrush(col(accent, 0.9))
    p.drawEllipse(QPointF(x + 20, y + 20), 4, 4)
    p.setFont(f)
    p.setPen(col(INK))
    p.drawText(QRectF(x + 32, y, w - 44, 40), int(Qt.AlignLeft | Qt.AlignVCenter), label)
    p.restore()


def bullet(p: QPainter, x: float, y: float, label: str, alpha: float) -> None:
    if alpha <= 0.002:
        return
    p.save()
    p.setOpacity(alpha)
    p.setPen(Qt.NoPen)
    p.setBrush(col(BLUE, 0.9))
    p.drawEllipse(QPointF(x, y + 15), 5, 5)
    text(p, label, QRectF(x + 22, y, 800, 38), 27, INK)
    p.restore()


# ---------------- 桌面/窗口 ----------------


TOP_LINES = [
    [("import", "#7c3aed"), (" QtQuick", "#2563eb")],
    [("import", "#7c3aed"), (" org.kde.plasma.plasmoid", "#2563eb")],
    [],
    [("PlasmoidItem", "#7c3aed"), (" {", "#334155")],
    [("    Plasmoid.backgroundHints", "#7c3aed"), (": ", "#334155"), ('"NoBackground"', "#059669")],
    [],
    [("    fullRepresentation", "#7c3aed"), (": ", "#334155"), ("Item", "#7c3aed"), (" {", "#334155")],
    [("        ", "#334155"), ("Pet", "#7c3aed"), (" {", "#334155")],
    [("            petSize", "#7c3aed"), (": ", "#334155"), ("420", "#dc2626")],
    [("            allowRoam", "#7c3aed"), (": ", "#334155"), ("false", "#dc2626")],
    [("            walkSpeed", "#7c3aed"), (": ", "#334155"), ("2.5", "#dc2626")],
    [("            ", "#334155"), ("// 108 段动画，全部本地", "#64748b")],
    [("        }", "#334155")],
    [("    }", "#334155")],
    [("}", "#334155")],
]

def desktop_window(p: QPainter, rect: QRectF, u: float, dim: float = 0.0) -> None:
    rrect(p, rect, 16, "#ffffff", LINE, 1.2, 1.0, 0.8)
    title = QRectF(rect.x(), rect.y(), rect.width(), 44)
    p.setPen(Qt.NoPen)
    p.setBrush(col("#e0f2fe"))
    p.drawRoundedRect(title, 16, 16)
    p.drawRect(QRectF(title.x(), title.bottom() - 16, title.width(), 16))
    for i, c in enumerate(["#fb7185", "#fbbf24", "#34d399"]):
        p.setBrush(col(c, 0.9))
        p.drawEllipse(QPointF(rect.x() + 24 + i * 22, rect.y() + 22), 6, 6)
    text(p, "main.qml — DeepSeek 大肥鱼", QRectF(rect.x() + 100, rect.y(), 700, 44),
         18, "#334155")
    side = QRectF(rect.x(), rect.y() + 44, 190, rect.height() - 44)
    p.setPen(Qt.NoPen)
    p.setBrush(col("#f8fafc"))
    p.drawRect(side)
    files = ["main.qml", "Pet.qml", "LayerPetWindow.qml", "AnimCatalog.js", "MoveData.js"]
    for i, name in enumerate(files):
        if i == 0:
            p.setBrush(col(BLUE, 0.13))
            p.drawRoundedRect(QRectF(side.x() + 10, side.y() + 16 + i * 38,
                                     side.width() - 20, 32), 6, 6)
        text(p, name, QRectF(side.x() + 24, side.y() + 16 + i * 38,
                             side.width() - 32, 32), 15,
             "#1e293b" if i == 0 else MUTED)
    x0 = side.right() + 28
    y0 = rect.y() + 72
    for i, line in enumerate(TOP_LINES):
        xx = x0
        for s, c in line:
            p.setFont(font(17, False, "mono"))
            p.setPen(col(c))
            p.drawText(QPointF(xx, y0 + i * 31), s)
            xx += QFontMetricsF(font(17, False, "mono")).horizontalAdvance(s)
    if int(u * 2) % 2 == 0:
        p.setPen(QPen(col(BLUE, 0.8), 2))
        p.drawLine(QPointF(x0 + 300, y0 + 14 * 31 - 18),
                   QPointF(x0 + 300, y0 + 14 * 31 + 6))
    p.setPen(Qt.NoPen)
    p.setBrush(col("#f1f5f9"))
    p.drawRect(QRectF(rect.x(), rect.bottom() - 26, rect.width(), 26))
    text(p, "QML · UTF-8 · 108 animations", QRectF(rect.x() + 20, rect.bottom() - 26,
                                                   700, 26), 14, MUTED)
    if dim > 0:
        p.setPen(Qt.NoPen)
        p.setBrush(col("#ffffff", dim))
        p.drawRoundedRect(rect, 16, 16)


def topbar(p: QPainter) -> None:
    p.setPen(Qt.NoPen)
    p.setBrush(col("#ffffff", 0.82))
    p.drawRect(QRectF(0, 0, LW, 52))
    p.setPen(QPen(col(INK, 0.10), 1))
    p.drawLine(0, 52, LW, 52)
    p.setPen(Qt.NoPen)
    p.setBrush(col(BLUE, 0.9))
    p.drawEllipse(QPointF(48, 26), 7, 7)
    text(p, "DeepSeek 大肥鱼", QRectF(66, 0, 500, 52), 18, INK)
    text(p, "00:47", QRectF(LW - 200, 0, 100, 52), 18, MUTED,
         align=Qt.AlignRight | Qt.AlignVCenter)
    for i, c in enumerate(["#0ea5e9", "#ec4899", "#10b981"]):
        p.setBrush(col(c, 0.8))
        p.drawEllipse(QPointF(LW - 80 + i * 22, 26), 5, 5)


# ---------------- 场景 ----------------


def scene_intro(p: QPainter, u: float) -> None:
    background(p, u)
    a = smooth(u / 0.9)
    logo = QPixmap(os.path.join(HERE, "assets", "logo.png"))
    if not logo.isNull():
        p.save()
        p.setOpacity(a)
        p.setClipPath(_rounded_path(QRectF(112, 170, 100, 100), 22))
        p.drawPixmap(QRectF(112, 170, 100, 100), logo, QRectF(logo.rect()))
        p.restore()
        p.setPen(QPen(col("#ffffff", 0.18 * a), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(112, 170, 100, 100), 22, 22)
    text(p, "DeepSeek 大肥鱼", QRectF(110, 340, 1300, 150), 112, INK, True, alpha=a)
    text(p, "KDE Plasma 6 桌面宠物", QRectF(116, 505, 1000, 60), 40, "#1d4ed8", alpha=smooth((u - 0.3) / 0.8))
    p.setPen(QPen(col(BLUE, 0.5), 2))
    p.drawLine(QPointF(118, 588), QPointF(118 + 760 * ease_out(u / 1.2), 588))
    text(p, "108 段透明动画 · Layer Shell 置顶 · 全本地运行",
         QRectF(118, 620, 1200, 44), 25, MUTED, alpha=smooth((u - 0.6) / 0.8))
    # 宠物
    px = 1160 + 80 * (1 - ease_out(u / 1.1))
    rect = QRectF(px, 545, 720, 405)
    glow(p, rect.center().x(), rect.center().y(), 330, BLUE_D, 0.20 * a)
    if u < 1.3:
        pet(p, rect, "待机呼吸休闲", u, alpha=a)
    else:
        pet(p, rect, "点击回应-元气挥手", u, start=1.3, alpha=a)
    bubble(p, rect.center().x() - 40, rect.y() + 100, "主人，你来啦～",
           smooth((u - 2.6) / 0.5), 0.94 + 0.06 * ease_out(seg(u, 2.6, 3.1)))
    text(p, "v1.1.2", QRectF(112, 1120, 300, 40), 18, DIM, alpha=0.8)


def scene_desktop(p: QPainter, u: float) -> None:
    background(p, u + 5)
    topbar(p)
    win = QRectF(160, 150, 1220, 880)
    desktop_window(p, win, u)
    # 宠物
    prect = QRectF(1120, 690, 760, 428)
    click_t = 3.0
    glow(p, prect.center().x(), prect.center().y(), 300, BLUE_D, 0.16)
    if u >= click_t:
        pet(p, prect, "点击回应-元气挥手", u, start=click_t,
            squash=squash_at(u, click_t, 0.78))
    else:
        pet(p, prect, "待机呼吸休闲", u)
    # 光标
    cs = seg(u, 2.0, 2.95)
    if cs > 0:
        sx, sy = 760, 560
        tx, ty = prect.center().x() - 30, prect.center().y() + 130
        cx = sx + (tx - sx) * ease_out(cs)
        cy = sy + (ty - sy) * ease_out(cs)
        ring = seg(u, click_t, click_t + 0.4)
        cursor(p, cx, cy, 0.95, 1.25, ring if u >= click_t else 0.0)
    bubble(p, prect.center().x() - 30, prect.y() + 100,
           "主人，已经凌晨 12 点了～", smooth((u - 3.35) / 0.5),
           0.94 + 0.06 * ease_out(seg(u, 3.35, 3.9)))
    badge(p, 1440, 92, "LAYER SHELL · 始终置顶", smooth((u - 1.0) / 0.6))
    text(p, "点一下，它会回应你", QRectF(180, 1080, 900, 50), 26, MUTED,
         alpha=smooth((u - 4.2) / 0.5))
    footer(p, u)


def card(p: QPainter, rect: QRectF, index: int, label: str, name: str,
         u: float, alpha: float) -> None:
    p.save()
    p.setOpacity(alpha)
    glow(p, rect.center().x(), rect.center().y(), 260, BLUE_D, 0.13)
    rrect(p, rect, 18, "#ffffff", LINE, 1.1, 1.0, 0.5)
    text(p, "%02d" % (index + 1), QRectF(rect.x() + 24, rect.y() + 18, 80, 34),
         16, BLUE, True, alpha=0.8)
    prect = QRectF(rect.center().x() - 260, rect.y() + 48, 520, 292)
    p.save()
    p.setClipRect(rect.adjusted(1, 1, -1, -1))
    pet(p, prect, name, u, start=0)
    p.restore()
    text(p, label, QRectF(rect.x(), rect.bottom() - 64, rect.width(), 44),
         24, INK, True, Qt.AlignHCenter | Qt.AlignVCenter)
    p.restore()


def scene_anims(p: QPainter, u: float) -> None:
    background(p, u + 13, 1)
    text(p, "108 段透明动画，随机不重样", QRectF(100, 96, 1500, 90), 62, INK, True)
    text(p, "待机 · 点击回应 · 玩耍 · 吃东西 · 节日 · 睡觉",
         QRectF(104, 196, 1500, 46), 27, "#1d4ed8")
    items = [
        ("待机", "待机呼吸休闲"),
        ("点击回应", "点击回应-元气挥手"),
        ("玩耍", "原地专心玩魔方"),
        ("睡觉", "睡觉-循环"),
    ]
    for i, (label, name) in enumerate(items):
        a = smooth((u - 0.15 - i * 0.12) / 0.55)
        x = 92 + i * 468
        rect = QRectF(x, 300 - 24 * (1 - a), 440, 470)
        card(p, rect, i, label, name, u + i * 0.4, a)
    text(p, "右键菜单可点播全部动画", QRectF(100, 840, 900, 50), 26, MUTED,
         alpha=smooth((u - 1.2) / 0.6))
    footer(p, u)


# 拖拽抛掷关键帧：t, 画布 x, y, rot
THROW_KEYS = [
    (0.0, 1280, 760, 0),
    (1.0, 1280, 760, 0),
    (2.0, 1180, 640, -4),
    (2.9, 860, 330, -8),
    (3.5, 820, 310, -10),
    (4.3, 1500, 300, 10),
    (4.8, 1680, 320, 14),
    (5.4, 1430, 560, -6),
    (6.2, 1290, 760, 0),
    (10.0, 1290, 760, 0),
]


def throw_pos(u: float):
    keys = THROW_KEYS
    for i in range(len(keys) - 1):
        t0, x0, y0, r0 = keys[i]
        t1, x1, y1, r1 = keys[i + 1]
        if t0 <= u <= t1:
            q = ease_out(seg(u, t0, t1)) if u < 3.5 else smooth(seg(u, t0, t1))
            return x0 + (x1 - x0) * q, y0 + (y1 - y0) * q, r0 + (r1 - r0) * q
    return keys[-1][1], keys[-1][2], keys[-1][3]


def scene_throw(p: QPainter, u: float) -> None:
    background(p, u + 24)
    topbar(p)
    win = QRectF(120, 230, 1180, 820)
    desktop_window(p, win, u, dim=0.35)
    text(p, "拖拽 · 甩抛 · 反弹", QRectF(120, 100, 1200, 70), 52, INK, True)
    text(p, "有物理，也有手感", QRectF(124, 172, 900, 40), 24, "#1d4ed8")
    x, y, rot = throw_pos(u)
    prect = QRectF(x - 310, y - 175, 620, 349)
    # 轨迹
    path = QPainterPath()
    pts = [QPointF(k[1], k[2]) for k in THROW_KEYS[1:9]]
    path.moveTo(pts[0])
    for i in range(1, len(pts)):
        path.lineTo(pts[i])
    pen = QPen(col(BLUE, 0.35), 2)
    pen.setStyle(Qt.DashLine)
    pen.setDashPattern([8, 10])
    pen.setDashOffset(-u * 18)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    # 宠物
    dragging = 1.0 <= u < 3.5
    if dragging:
        pet(p, prect, "被鼠标拖拽悬空反馈", u, start=1.0, rot=rot)
    else:
        pet(p, prect, "点击回应-元气挥手", u, start=6.3, rot=rot,
            squash=squash_at(u, 6.2, 0.74))
    # 光标
    if dragging:
        cursor(p, prect.center().x() + 40, prect.center().y() + 90, 0.95, 1.25,
               seg(u, 1.0, 1.4))
    # 落地尘环
    if 6.2 <= u < 7.0:
        q = seg(u, 6.2, 7.0)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(col(BLUE, 0.5 * (1 - q)), 3))
        p.drawEllipse(QPointF(prect.center().x(), prect.bottom() - 20),
                      60 + 220 * q, 18 + 70 * q)
    # 标注
    badge(p, 980, 520, "拖拽", smooth((u - 1.6) / 0.4))
    badge(p, 1230, 380, "甩抛", smooth((u - 3.9) / 0.4))
    badge(p, 1600, 420, "反弹", smooth((u - 4.7) / 0.4))
    badge(p, 1350, 820, "Q 弹", smooth((u - 6.3) / 0.4))
    footer(p, u)


# ---------------- 程序化右键菜单 ----------------


MENU_CATS = ["小动作", "玩耍", "吃什么", "时节", "文字", "走动", "点击回应"]
MENU_ACTS = [
    "悠闲哼歌", "超大伸懒腰", "原地敲击桌面互动", "原地重力下蹲压缩",
    "哈欠连天", "原地小憩沉眠", "女仆屈膝礼仪", "被吓一跳",
    "小幅度原地360度旋转展示", "偷吃零食被抓住", "用鲸鱼尾巴拍打地面",
    "打瞌睡被惊醒", "照镜子", "整体换装试色",
]
MENU_BTNS = ["待机", "转身", "回原位", "睡觉", "报时", "设置"]


def menu_panel(p: QPainter, rect: QRectF, alpha: float) -> None:
    p.save()
    p.setOpacity(alpha)
    rrect(p, rect, 16, "#ffffff", LINE, 1.2, 1.0, 0.7)
    lx = rect.x() + 18
    ly = rect.y() + 22
    for i, name in enumerate(MENU_CATS):
        r = QRectF(lx, ly + i * 58, 196, 48)
        if i == 0:
            p.setPen(Qt.NoPen)
            p.setBrush(col(BLUE, 0.14))
            p.drawRoundedRect(r, 8, 8)
        text(p, name, QRectF(lx + 16, r.y(), 180, 48), 22,
             INK if i == 0 else MUTED, i == 0)
    p.setPen(QPen(col(INK, 0.12), 1))
    p.drawLine(QPointF(rect.x() + 238, rect.y() + 18),
               QPointF(rect.x() + 238, rect.bottom() - 90))
    ax = rect.x() + 262
    ay = rect.y() + 22
    for i, name in enumerate(MENU_ACTS):
        r = QRectF(ax, ay + i * 46, rect.width() - 300, 40)
        if i == 8:
            p.setPen(Qt.NoPen)
            p.setBrush(col("#dbeafe"))
            p.drawRoundedRect(r, 7, 7)
        text(p, name, QRectF(ax + 14, r.y(), r.width() - 20, 40), 21,
             INK if i == 8 else "#334155", i == 8)
    p.setPen(Qt.NoPen)
    p.setBrush(col(INK, 0.12))
    p.drawRoundedRect(QRectF(rect.right() - 18, rect.y() + 24, 5, rect.height() - 160), 2.5, 2.5)
    p.setBrush(col(INK, 0.32))
    p.drawRoundedRect(QRectF(rect.right() - 18, rect.y() + 120, 5, 120), 2.5, 2.5)
    by = rect.bottom() - 78
    p.setPen(QPen(col(INK, 0.12), 1))
    p.drawLine(QPointF(rect.x() + 14, by), QPointF(rect.right() - 14, by))
    bw = (rect.width() - 36) / len(MENU_BTNS)
    for i, name in enumerate(MENU_BTNS):
        r = QRectF(rect.x() + 18 + i * bw, by + 12, bw - 8, 50)
        p.setPen(QPen(col(INK, 0.18), 1))
        p.setBrush(col("#f8fafc"))
        p.drawRoundedRect(r, 8, 8)
        text(p, name, r, 20, INK, align=Qt.AlignCenter)
    p.restore()


def scene_menu(p: QPainter, u: float) -> None:
    background(p, u + 33)
    text(p, "右键，换一个动作", QRectF(100, 110, 1200, 90), 62, INK, True)
    text(p, "全部动画都在本地播放", QRectF(104, 208, 900, 42), 26, "#1d4ed8")
    a = smooth((u - 0.2) / 0.6)
    panel = QRectF(1080 - 50 * (1 - a), 230, 820, 860)
    menu_panel(p, panel, a)
    for i, label in enumerate([
        "按分类点播 108 段动画",
        "待机 · 玩耍 · 吃东西 · 时节",
        "走动 · 报时 · 睡觉 · 回原位",
        "整点报时气泡",
        "CPU / 内存占用反应",
    ]):
        bullet(p, 132, 360 + i * 68, label, smooth((u - 0.4 - i * 0.10) / 0.5))
    prect = QRectF(110, 820, 620, 349)
    pet(p, prect, "待机呼吸休闲", u)
    cursor(p, panel.x() + 360, panel.y() + 330, 0.9, 1.15, 0.0)
    footer(p, u)


def scene_outro(p: QPainter, u: float) -> None:
    background(p, u + 41, 1)
    text(p, "把大肥鱼带回家", QRectF(100, 120, 1500, 100), 76, INK, True)
    text(p, "KDE Plasma 6 · Wayland Layer Shell · MIT",
         QRectF(104, 228, 1200, 46), 28, "#1d4ed8")
    # 终端卡片
    card = QRectF(100, 340, 1120, 226)
    rrect(p, card, 14, "#ffffff", LINE, 1.2, 1.0, 0.6)
    p.setPen(Qt.NoPen)
    p.setBrush(col("#e0f2fe"))
    p.drawRoundedRect(QRectF(card.x(), card.y(), card.width(), 34), 14, 14)
    p.drawRect(QRectF(card.x(), card.y() + 18, card.width(), 16))
    text(p, "konsole", QRectF(card.x() + 18, card.y(), 300, 34), 14, MUTED)
    text(p, "$", QRectF(card.x() + 26, card.y() + 52, 30, 40), 24, GREEN, role="mono")
    text(p, "kpackagetool6 -t Plasma/Applet -i deepseek大肥鱼.plasmoid",
         QRectF(card.x() + 56, card.y() + 52, card.width() - 80, 40), 23,
         INK, role="mono")
    text(p, "# 或：右键桌面 → 添加组件 → 从文件安装组件",
         QRectF(card.x() + 26, card.y() + 112, card.width() - 50, 38), 18, DIM,
         role="mono")
    text(p, "github.com/iamlinxuhan/plasmoid-deepseek-pet",
         QRectF(102, 632, 1200, 44), 30, BLUE, True)
    text(p, "Release v1.1.2 · deepseek大肥鱼.plasmoid",
         QRectF(104, 686, 900, 34), 19, MUTED)
    # 宠物
    prect = QRectF(1300, 570, 680, 382)
    glow(p, prect.center().x(), prect.center().y(), 320, BLUE_D, 0.18)
    pet(p, prect, "点击回应-元气挥手", u, start=0.4)
    bubble(p, prect.center().x() - 60, prect.y() + 100, "记得常来看我呀～",
           smooth((u - 1.0) / 0.5), 0.94 + 0.06 * ease_out(seg(u, 1.0, 1.5)))
    text(p, "108 段动画 · 无 DSH / Node / Python / 模型 API · 全部本地运行",
         QRectF(102, 1090, 1600, 42), 22, MUTED)
    text(p, "Artwork: PC2005-cloud/dsh-pet · Behavior: MerZlin/dsh-pet-indesktop · Layer Shell: KDE",
         QRectF(102, 1142, 1700, 32), 16, DIM)


# ---------------- 时间轴 ----------------


def scene_index(t: float):
    j = 0
    for i in range(len(T.SCENES)):
        if t >= T.START[i]:
            j = i
    if j > 0 and t < T.START[j - 1] + T.SCENES[j - 1][1]:
        return j - 1, j
    return j, -1


def render_scene(img: QImage, fn, u: float) -> None:
    p = QPainter(img)
    p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing |
                     QPainter.SmoothPixmapTransform)
    p.scale(img.width() / LW, img.height() / LH)
    fn(p, u)
    p.end()


def render_frame(img: QImage, t: float) -> None:
    a, b = scene_index(t)
    ua = t - T.START[a]
    render_scene(_buf_a(img.width(), img.height()), SCENES[a], ua)
    if b >= 0:
        ub = t - T.START[b]
        render_scene(_buf_b(img.width(), img.height()), SCENES[b], ub)
        q = smooth((t - T.START[b]) / T.TR)
        p = QPainter(img)
        p.drawImage(0, 0, _BA)
        p.setOpacity(q)
        p.drawImage(0, 0, _BB)
        p.end()
    else:
        p = QPainter(img)
        p.drawImage(0, 0, _BA)
        p.end()
    # 淡入淡出 + 进度（浅色片不压暗角）
    p = QPainter(img)
    fade = 1.0
    if t < 0.9:
        fade = t / 0.9
    if t > T.DUR - 1.1:
        fade = (T.DUR - t) / 1.1
    if fade < 1.0:
        p.fillRect(0, 0, img.width(), img.height(),
                   QColor(255, 255, 255, int(255 * (1 - smooth(fade)))))
    p.setPen(Qt.NoPen)
    p.setBrush(col(BLUE, 0.55))
    p.drawRect(QRectF(0, img.height() - 6, img.width() * clamp(t / T.DUR), 6))
    p.end()


_BA = _BB = None


def _buf_a(w: int, h: int) -> QImage:
    global _BA, _BB
    if _BA is None or _BA.width() != w or _BA.height() != h:
        _BA = QImage(w, h, QImage.Format_RGB888)
        _BB = QImage(w, h, QImage.Format_RGB888)
    return _BA


def _buf_b(w: int, h: int) -> QImage:
    _buf_a(w, h)
    return _BB


SCENES = [scene_intro, scene_desktop, scene_anims, scene_throw,
          scene_menu, scene_outro]
assert len(SCENES) == len(T.SCENES)


def write_cues(path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(T.cues(), fh, ensure_ascii=False, indent=1)


def build_video(out_path: str, audio: str | None, t0: float = 0.0,
                t1: float | None = None, w: int = W, h: int = H,
                fps: int = FPS) -> None:
    t1 = T.DUR if t1 is None else t1
    n = int(round((t1 - t0) * fps))
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (w, h),
           "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-i", audio]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "256k", "-shortest"]
    cmd += ["-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    img = QImage(w, h, QImage.Format_RGB888)
    stride = w * 3
    for i in range(n):
        t = t0 + i / fps
        render_frame(img, t)
        proc.stdin.write(img.constBits().asstring(stride * h))
        if i % 150 == 0:
            print("  frame %d/%d  t=%5.1fs" % (i, n, t), flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", help="comma separated times")
    ap.add_argument("--preview-dir", default="/tmp/pet_promo_preview")
    ap.add_argument("--preview-size", default="2048x1280")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--range")
    ap.add_argument("--out", default=os.path.join(HERE, "deepseek-pet-promo-4k60.mp4"))
    args = ap.parse_args()

    app = QGuiApplication(sys.argv[:1])  # noqa: F841
    print("准备宠物帧…")
    prepare_frames([
        "待机呼吸休闲", "点击回应-元气挥手", "原地专心玩魔方",
        "睡觉-循环", "被鼠标拖拽悬空反馈",
    ])

    if args.preview:
        os.makedirs(args.preview_dir, exist_ok=True)
        pw, ph = (int(x) for x in args.preview_size.lower().split("x"))
        for s in args.preview.split(","):
            t = float(s)
            img = QImage(pw, ph, QImage.Format_RGB888)
            render_frame(img, t)
            path = os.path.join(args.preview_dir, "t%05.1f.png" % t)
            img.save(path)
            print(path)
        return 0

    if args.render:
        cues = "/tmp/pet_promo_cues.json"
        write_cues(cues)
        audio = None
        if not args.no_audio and not args.range:
            audio = "/tmp/pet_promo_audio.wav"
            import pet_music
            print("合成配乐…")
            pet_music.build(cues, audio)
        print("渲染视频…")
        if args.range:
            a, b = (float(x) for x in args.range.split(","))
            build_video(args.out, None, a, b)
        else:
            build_video(args.out, audio)
        print("完成：" + args.out)
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
