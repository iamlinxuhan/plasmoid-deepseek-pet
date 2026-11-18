#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大肥鱼宣传封面（亮色版）：16:9 / 16:10 / 4:3 / 3:4 / 9:16 / 1:1。

参考 GomokuAI 与 ncmctl-GUI 的 cover 脚本：每个平台比例单独排版。
浅蓝 → 薰衣草 → 粉的渐变、白色玻璃卡片、黄色高亮、彩色贴纸；
宠物本体保留原画深蓝色，在亮底上更跳。
"""

from __future__ import annotations

import math
import os
import sys

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
    QBrush, QColor, QFontMetricsF, QGuiApplication, QImage, QLinearGradient,
    QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QRadialGradient,
)

import film_pet as F  # noqa: E402

OUT = os.path.join(ROOT, "store", "covers")

SKY1 = "#9be7ff"
SKY2 = "#c9d4ff"
SKY3 = "#ffd9ec"
INK = "#0b1b33"
MUTED = "#465a78"
W = "#ffffff"
CYAN = "#0ea5e9"
PINK = "#ec4899"
YELLOW = "#f59e0b"
MINT = "#10b981"
PURPLE = "#8b5cf6"


def bg(p: QPainter, w: int, h: int) -> None:
    g = QLinearGradient(0, 0, w, h)
    g.setColorAt(0.0, QColor(SKY1))
    g.setColorAt(0.52, QColor(SKY2))
    g.setColorAt(1.0, QColor(SKY3))
    p.fillRect(0, 0, w, h, g)
    # 大块柔光
    for cx, cy, rr, c, a in [
        (0.16, 0.18, 0.28, "#ffffff", 0.55),
        (0.88, 0.20, 0.24, "#e0f2fe", 0.55),
        (0.78, 0.86, 0.30, "#fce7f3", 0.55),
        (0.12, 0.80, 0.22, "#ede9fe", 0.45),
    ]:
        rg = QRadialGradient(QPointF(w * cx, h * cy), max(w, h) * rr)
        rg.setColorAt(0.0, QColor(c))
        rg.setColorAt(0.55, QColor(c))
        rg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(rg)
        p.drawEllipse(QPointF(w * cx, h * cy), max(w, h) * rr, max(w, h) * rr)
    # 淡网格
    p.setPen(QPen(QColor(11, 27, 51, 18), max(1.0, w / 1600)))
    step = max(60, int(w / 16))
    for x in range(0, w + 1, step):
        p.drawLine(x, 0, x, h)
    for y in range(0, h + 1, step):
        p.drawLine(0, y, w, y)
    # 彩色纸屑
    rng = [(0.08, 0.12, 9, PINK), (0.92, 0.10, 8, YELLOW), (0.05, 0.62, 7, CYAN),
           (0.95, 0.55, 11, PINK), (0.12, 0.93, 9, PURPLE), (0.90, 0.92, 8, MINT),
           (0.30, 0.06, 6, YELLOW), (0.70, 0.04, 7, CYAN), (0.52, 0.97, 7, PINK),
           (0.82, 0.42, 5, YELLOW)]
    for fx, fy, rr, c in rng:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(w * fx, h * fy), rr * w / 1920, rr * w / 1920)


def card(p: QPainter, rect: QRectF, r: float, fill=QColor(255, 255, 255, 236),
         border=QColor(255, 255, 255, 255), shadow: float = 0.18) -> None:
    for i, a in ((18, 0.06), (10, 0.09), (4, 0.13)):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(11, 27, 51, int(255 * a * shadow)))
        p.drawRoundedRect(rect.adjusted(-i, -i + 8, i, i + 12), r + i, r + i)
    p.setPen(QPen(border, max(1.0, rect.width() / 700)))
    p.setBrush(fill)
    p.drawRoundedRect(rect, r, r)


def pill(p: QPainter, x: float, y: float, label: str, px: float,
         accent: str = CYAN, alpha: float = 1.0) -> float:
    f = F.font(int(px), True, "sans")
    w = QFontMetricsF(f).horizontalAdvance(label) + px * 2.5
    h = px * 2.0
    r = QRectF(x, y, w, h)
    p.setPen(QPen(QColor(accent), max(1.0, px / 12)))
    p.setBrush(QColor(255, 255, 255, int(240 * alpha)))
    p.drawRoundedRect(r, h / 2, h / 2)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(accent))
    p.drawEllipse(QPointF(x + px * 0.9, y + h / 2), px * 0.22, px * 0.22)
    F.text(p, label, QRectF(x + px * 1.5, y, w - px * 1.6, h), px, INK, True)
    return w


def chips(p: QPainter, x: float, y: float, labels, px: float, gap: float,
          maxw: float) -> float:
    cx = x
    row_h = px * 2.6
    for label in labels:
        w = QFontMetricsF(F.font(int(px), True, "sans")).horizontalAdvance(label) + px * 2.5
        if cx > x and cx + w > x + maxw:
            cx = x
            y += row_h
        pill(p, cx, y, label, px)
        cx += w + gap
    return y + row_h


def grad_text(p: QPainter, s: str, rect: QRectF, px: float, font_role: str = "sans",
              align=Qt.AlignLeft | Qt.AlignVCenter) -> None:
    f = F.font(int(px), True, font_role)
    p.setFont(f)
    g = QLinearGradient(rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
    g.setColorAt(0.0, QColor("#2563eb"))
    g.setColorAt(0.55, QColor("#7c3aed"))
    g.setColorAt(1.0, QColor("#db2777"))
    p.setPen(QPen(QBrush(g), 1))
    p.drawText(rect, int(align), s)


def highlight(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(253, 224, 71, 220))
    p.drawRoundedRect(QRectF(x, y, w, h), h * 0.22, h * 0.22)


def bubble(p: QPainter, cx: float, bottom: float, msg: str, px: float,
           alpha: float = 1.0) -> None:
    f = F.font(int(px), True, "sans")
    fm = QFontMetricsF(f)
    maxw = px * 22
    br = fm.boundingRect(QRectF(0, 0, maxw, 1000), int(Qt.TextWordWrap), msg)
    w = min(maxw, max(px * 6.0, br.width() + px * 2.2))
    h = br.height() + px * 1.7
    rect = QRectF(cx - w / 2, bottom - h, w, h)
    p.save()
    p.setOpacity(alpha)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(11, 27, 51, 34))
    p.drawRoundedRect(rect.adjusted(-4, -4 + 7, 4, 4 + 9), h * 0.28, h * 0.28)
    p.setPen(QPen(QColor(YELLOW), max(1.4, px / 9)))
    p.setBrush(QColor("#fff8dc"))
    p.drawRoundedRect(rect, h * 0.28, h * 0.28)
    tail = QPolygonF([QPointF(cx - px * 0.55, rect.bottom() - 2),
                      QPointF(cx + px * 0.55, rect.bottom() - 2),
                      QPointF(cx - 1, rect.bottom() + px * 0.75)])
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#fff8dc"))
    p.drawPolygon(tail)
    p.setPen(QPen(QColor(YELLOW), max(1.4, px / 9)))
    p.drawLine(tail[0], tail[2])
    p.drawLine(tail[1], tail[2])
    p.setFont(f)
    p.setPen(QColor(INK))
    p.drawText(QRectF(rect.x() + px * 1.1, rect.y() + px * 0.8, rect.width() - px * 2.2,
                      rect.height() - px * 1.6),
               int(Qt.TextWordWrap | Qt.AlignHCenter | Qt.AlignVCenter), msg)
    p.restore()


def sticker_108(p: QPainter, cx: float, cy: float, r: float) -> None:
    p.setPen(QPen(QColor("#ffffff"), r * 0.10))
    p.setBrush(QColor(YELLOW))
    p.drawEllipse(QPointF(cx, cy), r, r)
    F.text(p, "108", QRectF(cx - r, cy - r * 0.55, r * 2, r * 0.85),
           r * 0.80, "#ffffff", True, Qt.AlignCenter)
    F.text(p, "段动画", QRectF(cx - r, cy + r * 0.22, r * 2, r * 0.5),
           r * 0.30, "#ffffff", True, Qt.AlignCenter)


def layer_pill(p: QPainter, x: float, y: float, px: float) -> None:
    w = QFontMetricsF(F.font(int(px), True, "sans")).horizontalAdvance("LAYER SHELL · 始终置顶") + px * 3.4
    r = QRectF(x, y, w, px * 2.0)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 235))
    p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
    p.setBrush(QColor(CYAN))
    p.drawEllipse(QPointF(x + px, y + px), px * 0.30, px * 0.30)
    F.text(p, "LAYER SHELL · 始终置顶", QRectF(x + px * 1.7, y, w - px * 1.8, r.height()),
           px, "#075985", True)


def mini_menu(p: QPainter, rect: QRectF, s: float) -> None:
    card(p, rect, 18 * s, QColor(255, 255, 255, 245), QColor(255, 255, 255, 255), 0.16)
    pad = rect.width() * 0.055
    F.text(p, "右键换动作", QRectF(rect.x() + pad, rect.y() + pad * 0.7,
                                   rect.width() - pad * 2, 26 * s), 21 * s, INK, True)
    F.text(p, "108 段动画 · 全本地", QRectF(rect.x() + pad, rect.y() + pad * 0.7 + 24 * s,
                                            rect.width() - pad * 2, 18 * s),
           12 * s, MUTED)
    rows = [("小动作", CYAN), ("玩耍", PINK), ("吃什么", YELLOW), ("走动", MINT)]
    y = rect.y() + pad * 0.7 + 48 * s
    rh = (rect.height() - (y - rect.y()) - pad) / 4
    for name, c in rows:
        rr = QRectF(rect.x() + pad, y, rect.width() - pad * 2, rh - 5 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c).lighter(185))
        p.drawRoundedRect(rr, 8 * s, 8 * s)
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(rr.x() + rh * 0.42, rr.center().y()), rh * 0.14, rh * 0.14)
        F.text(p, name, QRectF(rr.x() + rh * 0.75, rr.y(), rr.width() - rh, rr.height()),
               13 * s, INK, True)
        y += rh


def fish_card(p: QPainter, rect: QRectF, s: float, bubble_px: float) -> None:
    card(p, rect, 26 * s, QColor(255, 255, 255, 248), QColor(255, 255, 255, 255), 0.22)
    # 卡片内部做成一块浅色桌面，而不是一整片白
    inner = QPainterPath()
    inner.addRoundedRect(rect.adjusted(2, 2, -2, -2), 25 * s, 25 * s)
    p.save()
    p.setClipPath(inner)
    g = QLinearGradient(rect.topLeft(), rect.bottomRight())
    g.setColorAt(0.0, QColor("#e0f6ff"))
    g.setColorAt(0.55, QColor("#eef2ff"))
    g.setColorAt(1.0, QColor("#ffe4f3"))
    p.fillRect(rect, g)
    p.setPen(QPen(QColor(11, 27, 51, 16), max(1.0, s)))
    st = max(40, int(rect.width() / 14))
    for x in range(int(rect.x()), int(rect.right()) + 1, st):
        p.drawLine(x, int(rect.y()), x, int(rect.bottom()))
    for y in range(int(rect.y()), int(rect.bottom()) + 1, st):
        p.drawLine(int(rect.x()), y, int(rect.right()), y)
    p.restore()

    # 代码窗口：让卡片上半部分有内容，也交代 Layer Shell / QML
    win = QRectF(rect.x() + rect.width() * 0.055, rect.y() + rect.height() * 0.115,
                 rect.width() * 0.70, rect.height() * 0.37)
    for i, a in ((12, 0.10), (6, 0.14)):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(11, 27, 51, int(255 * a)))
        p.drawRoundedRect(win.adjusted(-i, -i + 8, i, i + 10), 16 * s + i, 16 * s + i)
    p.setPen(QPen(QColor("#334155"), 1.2 * s))
    p.setBrush(QColor("#0f172a"))
    p.drawRoundedRect(win, 14 * s, 14 * s)
    head = QRectF(win.x(), win.y(), win.width(), win.height() * 0.11)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#111c30"))
    p.drawRoundedRect(head, 14 * s, 14 * s)
    p.drawRect(QRectF(head.x(), head.bottom() - 14 * s, head.width(), 14 * s))
    for i, c in enumerate(["#fb7185", "#fbbf24", "#34d399"]):
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(head.x() + head.height() * 0.55 + i * head.height() * 0.42,
                              head.center().y()), head.height() * 0.15, head.height() * 0.15)
    F.text(p, "main.qml — DeepSeek 大肥鱼",
           QRectF(head.x() + head.height() * 2.0, head.y(), head.width() * 0.7, head.height()),
           9.5 * s, "#94a3b8", role="mono")
    code_colors = ["#93c5fd", "#c084fc", "#fbbf24", "#86efac", "#93c5fd", "#f472b6", "#e2e8f0"]
    y = head.bottom() + 12 * s
    for i in range(7):
        x = win.x() + 18 * s
        p.setBrush(QColor(code_colors[i]))
        p.setOpacity(0.9)
        p.drawRoundedRect(QRectF(x, y, (win.width() * (0.18 + 0.06 * (i % 3))),
                                 5 * s), 2.5 * s, 2.5 * s)
        p.setBrush(QColor(code_colors[(i + 2) % len(code_colors)]))
        p.drawRoundedRect(QRectF(x + win.width() * 0.28, y,
                                 win.width() * (0.12 + 0.05 * (i % 2)), 5 * s),
                          2.5 * s, 2.5 * s)
        p.setBrush(QColor(code_colors[(i + 4) % len(code_colors)]))
        p.drawRoundedRect(QRectF(x + win.width() * 0.52, y,
                                 win.width() * (0.10 + 0.06 * ((i + 1) % 3)), 5 * s),
                          2.5 * s, 2.5 * s)
        y += 16 * s
    p.setOpacity(1)

    # 桌面底栏
    task = QRectF(rect.x() + rect.width() * 0.055, rect.bottom() - rect.height() * 0.072,
                  rect.width() * 0.89, rect.height() * 0.048)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 225))
    p.drawRoundedRect(task, task.height() / 2, task.height() / 2)
    for i, c in enumerate([CYAN, PINK, YELLOW, MINT, PURPLE]):
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(task.x() + task.height() * 0.55 + i * task.height() * 0.62,
                              task.center().y()), task.height() * 0.15, task.height() * 0.15)
    F.text(p, "00:47", QRectF(task.right() - 70 * s, task.y(), 50 * s, task.height()),
           9 * s, "#334155", True)

    # 鱼：尽量放大，压在窗口和底栏前面
    fish_w = rect.width() * 0.94
    fish_h = fish_w * 9 / 16
    frect = QRectF(rect.center().x() - fish_w / 2 + rect.width() * 0.05,
                   rect.bottom() - fish_h - rect.height() * 0.065,
                   fish_w, fish_h)
    F.glow(p, frect.center().x(), frect.center().y(), fish_w * 0.55, "#7dd3fc", 0.32)
    F.pet(p, frect, "点击回应-元气挥手", 1.6)
    bubble(p, frect.center().x() - fish_w * 0.03, frect.y() + fish_h * 0.22,
           "主人，已经凌晨 12 点了～", bubble_px)
    sticker_108(p, rect.right() - 78 * s, rect.y() + rect.height() * 0.18, 55 * s)

def title_card(p: QPainter, rect: QRectF, s: float, compact: bool = False) -> None:
    # 不铺大白卡：只在文字后面放一层柔光，让标题直接落在渐变背景上。
    F.glow(p, rect.x() + rect.width() * 0.46, rect.y() + rect.height() * 0.40,
           max(rect.width(), rect.height()) * 0.92, "#ffffff", 0.52)
    pad = rect.width() * 0.07
    left = rect.x() + pad
    y = rect.y() + pad * 0.7
    grad_text(p, "DeepSeek", QRectF(left, y, rect.width() - pad * 2, 92 * s),
              92 * s, "sans")
    F.text(p, "大肥鱼", QRectF(left, y + 92 * s, rect.width() - pad * 2, 100 * s),
           92 * s, INK, True)
    # 黄色高亮垫在大肥鱼后面
    tw = QFontMetricsF(F.font(int(92 * s), True, "sans")).horizontalAdvance("大肥鱼")
    highlight(p, left - 6 * s, y + 92 * s + 20 * s, tw + 12 * s, 70 * s)
    # 重画文字盖在 highlight 上
    F.text(p, "大肥鱼", QRectF(left, y + 92 * s, rect.width() - pad * 2, 100 * s),
           92 * s, INK, True)
    F.text(p, "KDE Plasma 6 桌面宠物", QRectF(left + 2 * s, y + 200 * s,
                                               rect.width() - pad * 2, 36 * s),
           25 * s, "#1d4ed8", True)
    p.setPen(QPen(QColor(CYAN), 2 * s))
    p.drawLine(QPointF(left, y + 246 * s), QPointF(left + 190 * s, y + 246 * s))
    F.text(p, "108 段透明动画 · 点击 / 拖拽 / 甩抛", QRectF(left, y + 262 * s,
                                                            rect.width() - pad * 2, 28 * s),
           15 * s, MUTED)
    F.text(p, "Layer Shell 置顶 · 整点报时 · CPU/内存反应", QRectF(left, y + 292 * s,
                                                                   rect.width() - pad * 2, 28 * s),
           15 * s, MUTED)
    if not compact:
        chips(p, left, y + 340 * s,
              ["全本地运行", "无需 DSH / Node / Python", "MIT 开源"], 12 * s, 8 * s,
              rect.width() - pad * 2)


def footer(p: QPainter, w: int, h: int, s: float) -> None:
    F.text(p, "github.com/iamlinxuhan/plasmoid-deepseek-pet",
           QRectF(w * 0.045, h - 52 * s, w * 0.65, 30 * s), 15 * s, "#334155")
    F.text(p, "v1.1.2 · MIT", QRectF(w - 200 * s, h - 52 * s, 160 * s, 30 * s),
           15 * s, "#334155", align=Qt.AlignRight | Qt.AlignVCenter)


def cover(w: int, h: int, portrait: bool = False, square: bool = False) -> QImage:
    img = QImage(w, h, QImage.Format_RGB888)
    p = QPainter(img)
    p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing |
                     QPainter.SmoothPixmapTransform)
    bg(p, w, h)
    s = w / 1920 if not portrait else w / 1080

    if square:
        tcard = QRectF(w * 0.055, h * 0.06, w * 0.52, h * 0.35)
        title_card(p, tcard, s * 0.80)
        fcard = QRectF(w * 0.49, h * 0.30, w * 0.46, h * 0.62)
        fish_card(p, fcard, s * 0.78, 18 * s * 0.78)
        mini_menu(p, QRectF(w * 0.055, h * 0.52, w * 0.40, h * 0.32), s * 0.75)
        chips(p, w * 0.055, h * 0.88, ["108 段动画", "全本地", "MIT"], 12 * s * 0.8,
              8 * s, w * 0.50)
        footer(p, w, h, s * 0.8)
    elif portrait:
        tcard = QRectF(w * 0.06, h * 0.045, w * 0.88, h * 0.235 if h > 1600 else h * 0.285)
        title_card(p, tcard, s * 1.05, compact=True)
        chips(p, w * 0.075, tcard.bottom() + h * 0.014,
              ["108 段透明动画", "全本地", "无需 API"], 13 * s * 1.05, 8 * s, w * 0.86)
        fcard = QRectF(w * 0.07, h * 0.355 if h > 1600 else h * 0.395,
                       w * 0.86, h * 0.425 if h > 1600 else h * 0.385)
        fish_card(p, fcard, s * 1.05, 20 * s * 1.05)
        mini_menu(p, QRectF(w * 0.07, h * 0.815, w * 0.54, h * 0.135), s * 1.0)
        chips(p, w * 0.65, h * 0.825, ["MIT 开源", "v1.1.2"], 12 * s, 8 * s, w * 0.30)
        footer(p, w, h, s * 0.9)
    else:
        tcard = QRectF(w * 0.055, h * 0.115, w * 0.365, h * 0.455)
        title_card(p, tcard, s)
        fcard = QRectF(w * 0.455, h * 0.075, w * 0.50, h * 0.80)
        fish_card(p, fcard, s, 20 * s)
        mini_menu(p, QRectF(w * 0.055, h * 0.625, w * 0.355, h * 0.215), s * 0.92)
        footer(p, w, h, s)

    p.end()
    return img


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    app = QGuiApplication(sys.argv[:1])  # noqa: F841
    F.prepare_frames(["点击回应-元气挥手"])
    jobs = [
        ("deepseek-pet-cover-16x9.png", 1920, 1080, False, False),
        ("deepseek-pet-cover-16x10.png", 1920, 1200, False, False),
        ("deepseek-pet-cover-4x3.png", 1440, 1080, False, False),
        ("deepseek-pet-cover-3x4.png", 1080, 1440, True, False),
        ("deepseek-pet-cover-9x16.png", 1080, 1920, True, False),
        ("deepseek-pet-cover-1x1.png", 1080, 1080, False, True),
    ]
    for name, w, h, portrait, square in jobs:
        img = cover(w, h, portrait, square)
        path = os.path.join(OUT, name)
        img.save(path)
        print("%s  %dx%d" % (path, w, h))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
