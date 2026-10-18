"""The two auto-hiding bars that float over the video (monochrome, YouTube-style).

Top bar:    only a three-dot menu button, top right. Everything else lives in that menu.
Bottom bar: thin seek bar on top, then
            [play/pause] [prev] [next] [volume] [time]  ......  [loop] [audio] [queue] [subtitles] [settings] [fullscreen]
Every control except play/pause can be shown or hidden in Preferences > Bars, and the size and
background opacity of both bars can be changed there too.
"""
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from . import theme
from .icons import icon
from .util import fmt_time
from .widgets import IconButton, OverlayWindow, SeekBar

BASE_PILL = 24          # pill size in pixels at 100 percent bar size
BAR_ICON_KEYS = ("prev", "next", "volume", "time", "loop", "audio", "queue", "subs", "settings", "fullscreen")
# narrowest stage width (px) at which each control is still shown, so a small window never overflows
BAR_MIN_WIDTH = {"fullscreen": 260, "volume": 300, "settings": 380, "subs": 360, "time": 420,
                 "prev": 480, "next": 480, "loop": 520, "audio": 540, "queue": 560}
PILL_BG = "rgba(22,22,22,0.72)"
PILL_HOVER = "rgba(70,70,70,0.80)"


def set_pill_size(btn: IconButton, size: int) -> None:
    """(Re)size a pill button and its icon."""
    isz = max(10, round(size * 0.58))
    btn.setFixedSize(size, size)
    btn._size = isz
    btn.setIconSize(QSize(isz, isz))
    btn.setStyleSheet(f"QToolButton {{ background: {PILL_BG}; border-radius: {size // 2}px; padding: 0; }}"
                      f"QToolButton:hover {{ background: {PILL_HOVER}; }}"
                      f"QToolButton:checked {{ background: {PILL_HOVER}; }}")
    btn.refresh()


def pill(btn: IconButton, size: int = BASE_PILL) -> IconButton:
    """Round dark pill behind a white icon, as on YouTube."""
    set_pill_size(btn, size)
    return btn


class VolumeControl(QWidget):
    """Speaker pill. Hover it and a thin line with a white dot slides out."""
    volume_changed = Signal(int)
    mute_clicked = Signal()

    MAX = 125
    BOX = 24
    SLIDER = 56
    ICON = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self.value, self.muted = 80, False
        self._t = 0.0           # 0 collapsed .. 1 expanded
        self._target = 0.0
        self._drag = False
        self.setFixedSize(self.BOX, self.BOX)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._step)

    def set_scale(self, box: int):
        """Resize for a different bar size (collapses the slider)."""
        self.BOX = box
        self.SLIDER = round(box * 2.3)
        self.ICON = max(10, round(box * 0.58))
        self._t = self._target = 0.0
        self._timer.stop()
        self.setFixedSize(self.BOX, self.BOX)
        self.update()

    # -- state
    def set_value(self, v, muted=None):
        self.value = max(0, min(self.MAX, int(v)))
        if muted is not None:
            self.muted = muted
        self.setToolTip(f"Volume {self.value}%")
        self.update()

    def _slider_rect(self):
        x0 = self.BOX - 4
        return x0 + 8, self.width() - 16          # (left, width) of the line

    def _set_from_x(self, x):
        left, w = self._slider_rect()
        v = round(max(0.0, min(1.0, (x - left) / max(1, w))) * self.MAX)
        if abs(v - 100) <= 3:
            v = 100
        self.set_value(v, False)
        self.volume_changed.emit(self.value)

    # -- expand / collapse
    def _go(self, target):
        self._target = target
        if not self._timer.isActive():
            self._timer.start()

    def _step(self):
        d = self._target - self._t
        if abs(d) < 0.04:
            self._t = self._target
            self._timer.stop()
        else:
            self._t += d * 0.35
        self.setFixedWidth(int(self.BOX + (self.SLIDER + 6) * self._t))
        self.update()

    def enterEvent(self, e):
        self._go(1.0)

    def leaveEvent(self, e):
        if not self._drag:
            self._go(0.0)

    # -- mouse
    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if e.position().x() < self.BOX - 4:
            self.mute_clicked.emit()
        elif self._t > 0.5:
            self._drag = True
            self._set_from_x(e.position().x())

    def mouseMoveEvent(self, e):
        if self._drag:
            self._set_from_x(e.position().x())

    def mouseReleaseEvent(self, e):
        self._drag = False
        if not self.underMouse():
            self._go(0.0)

    def wheelEvent(self, e):
        self.set_value(self.value + (5 if e.angleDelta().y() > 0 else -5), False)
        self.volume_changed.emit(self.value)

    # -- paint
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(22, 22, 22, 184))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        name = "volume_mute" if (self.muted or self.value == 0) else "volume"
        pm = icon(name, "#FFFFFF", self.ICON).pixmap(QSize(self.ICON, self.ICON))
        p.drawPixmap(int((self.BOX - self.ICON) / 2), int((self.height() - self.ICON) / 2), pm)
        if self._t > 0.55:
            left, w = self._slider_rect()
            cy = self.height() / 2
            frac = 0.0 if self.muted else self.value / self.MAX
            p.setPen(QPen(QColor(255, 255, 255, 90), 2.5, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(left, cy), QPointF(left + w, cy))
            p.setPen(QPen(QColor("#FFFFFF"), 2.5, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(left, cy), QPointF(left + w * frac, cy))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(QPointF(left + w * frac, cy), max(3, self.BOX / 6), max(3, self.BOX / 6))
        p.end()


class TopBar(OverlayWindow):
    """Just a three-dot button. The window is full width but only the button takes clicks."""
    menu_clicked = Signal()

    HEIGHT = 38          # defaults; the real values are hpx and btn_area (they follow the bar size setting)
    BTN_AREA = 46

    def __init__(self, owner):
        super().__init__(owner, gradient="none")
        self.hpx, self.btn_area = self.HEIGHT, self.BTN_AREA
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(0, 7, 10, 7)
        self._lay.addStretch(1)
        self.btn_menu = pill(IconButton("more_v", "Menu", size=14), BASE_PILL)
        self.btn_menu.clicked.connect(self.menu_clicked)
        self._lay.addWidget(self.btn_menu)
        # Kept so the rest of the app can still call them; they are never shown.
        self.btn_library = IconButton("sidebar_left", "", checkable=True, parent=self)
        self.btn_pip = IconButton("pip", "", checkable=True, parent=self)
        self.folder_chip = QPushButton("", self)
        self.title = QLabel("", self)
        for w in (self.btn_library, self.btn_pip, self.folder_chip, self.title):
            w.hide()
        self.apply_metrics(100)

    def apply_metrics(self, scale_pct: int):
        s = max(18, round(BASE_PILL * scale_pct / 100))
        set_pill_size(self.btn_menu, s)
        m = max(4, round(s * 0.28))
        self._lay.setContentsMargins(0, m, 10, m)
        self.hpx = s + 2 * m
        self.btn_area = s + 22

    def paintEvent(self, e):       # nothing behind the button
        pass

    def set_title(self, text: str):
        pass

    def set_folder(self, name: str):
        self.folder_chip.setText(name or "")

    def set_fullscreen(self, on: bool):
        pass


class BottomBar(OverlayWindow):
    play_clicked = Signal()
    subs_clicked = Signal()
    sidebar_clicked = Signal()
    mute_clicked = Signal()
    fullscreen_clicked = Signal()
    resume_clicked = Signal()
    prev_clicked = Signal()
    next_clicked = Signal()
    audio_clicked = Signal()
    queue_clicked = Signal()
    loop_clicked = Signal()
    speed_clicked = Signal()

    HEIGHT = 45          # default; the real value is hpx (it follows the bar size setting)

    def __init__(self, owner):
        super().__init__(owner, gradient="up")
        self.hpx = self.HEIGHT
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(14, 2, 14, 5)
        self._outer.setSpacing(2)
        self.seek = SeekBar()
        self._outer.addWidget(self.seek)

        self._row = QHBoxLayout()
        self._row.setSpacing(5)
        self.btn_play = pill(IconButton("play", "Play / pause (Space)", size=14), BASE_PILL)
        self.btn_play.clicked.connect(self.play_clicked)
        self.btn_prev = pill(IconButton("prev", "Previous (P)", size=14), BASE_PILL)
        self.btn_next = pill(IconButton("next", "Next (N)", size=14), BASE_PILL)
        self.btn_prev.clicked.connect(self.prev_clicked)
        self.btn_next.clicked.connect(self.next_clicked)
        self.cone = VolumeControl()            # name kept: window.py talks to bottom.cone
        self.cone.mute_clicked.connect(self.mute_clicked)
        self.time = QPushButton("0:00 / 0:00")
        self.time.setFlat(True)
        self.time.setFocusPolicy(Qt.NoFocus)
        self.time.setCursor(Qt.PointingHandCursor)
        self.time.setToolTip("Click to show remaining time")
        self.time.clicked.connect(self._toggle_remaining)
        self.show_remaining = False
        # "Continue from 12:34" button, shown for a few seconds when a file has a saved position
        self.resume = QPushButton("")
        self.resume.setFlat(True)
        self.resume.setFocusPolicy(Qt.NoFocus)
        self.resume.setCursor(Qt.PointingHandCursor)
        self.resume.clicked.connect(self.resume_clicked)
        self.resume.hide()

        self.btn_loop = pill(IconButton("repeat", "Repeat: off (click to change)", size=14, checkable=True), BASE_PILL)
        self.btn_audio = pill(IconButton("audio", "Audio track (B)", size=14), BASE_PILL)
        self.btn_queue = pill(IconButton("queue", "Queue (Ctrl+Q)", size=14, checkable=True), BASE_PILL)
        self.btn_subs = pill(IconButton("subtitles", "Subtitles (V)", size=14), BASE_PILL)
        self.btn_tune = pill(IconButton("settings", "Settings (Ctrl+T)", size=14, checkable=True), BASE_PILL)
        self.btn_full = pill(IconButton("fullscreen", "Fullscreen (F)", size=14), BASE_PILL)
        self.btn_loop.clicked.connect(self.loop_clicked)
        self.btn_audio.clicked.connect(self.audio_clicked)
        self.btn_queue.clicked.connect(self.queue_clicked)
        self.btn_subs.clicked.connect(self.subs_clicked)
        self.btn_tune.clicked.connect(self.sidebar_clicked)
        self.btn_full.clicked.connect(self.fullscreen_clicked)

        for w in (self.btn_play, self.btn_prev, self.btn_next, self.cone, self.time, self.resume):
            self._row.addWidget(w)
        self._row.addStretch(1)
        for w in (self.btn_loop, self.btn_audio, self.btn_queue, self.btn_subs, self.btn_tune, self.btn_full):
            self._row.addWidget(w)
        self._outer.addLayout(self._row)

        self._ctl = {"prev": self.btn_prev, "next": self.btn_next, "volume": self.cone, "time": self.time,
                     "loop": self.btn_loop, "audio": self.btn_audio, "queue": self.btn_queue,
                     "subs": self.btn_subs, "settings": self.btn_tune, "fullscreen": self.btn_full}
        self._wanted = {k: k in ("volume", "time", "loop", "subs", "settings", "fullscreen") for k in BAR_ICON_KEYS}
        self._pills = [self.btn_play, self.btn_prev, self.btn_next, self.btn_loop, self.btn_audio,
                       self.btn_queue, self.btn_subs, self.btn_tune, self.btn_full]

        # Kept so window.py can still call them; never shown.
        self.btn_mute = IconButton("volume", "", parent=self)
        self.speed = QPushButton("1x", self)
        for w in (self.btn_mute, self.speed):
            w.hide()
        self._pos = self._len = 0
        self._width = 10_000
        self.apply_metrics(100, 85)

    # ---------------------------------------------------------------- size, opacity, which controls
    def apply_metrics(self, scale_pct: int, opacity_pct: int):
        s = max(18, round(BASE_PILL * scale_pct / 100))
        for b in self._pills:
            set_pill_size(b, s)
        self.cone.set_scale(s)
        fs = max(9, round(s * 0.46))
        for w in (self.time, self.resume):
            w.setFixedHeight(s)
        self.time.setStyleSheet(f"QPushButton {{ background: {PILL_BG}; border: none; border-radius: {s // 2}px;"
                                f" color: #FFFFFF; font-size: {fs}px; font-weight: 600; padding: 0 {round(s * 0.45)}px; }}"
                                f"QPushButton:hover {{ background: {PILL_HOVER}; }}")
        self.resume.setStyleSheet(f"QPushButton {{ background: {PILL_BG}; border: none; border-radius: {s // 2}px;"
                                  f" color: #FFFFFF; font-size: {fs}px; font-weight: 600; padding: 0 {round(s * 0.45)}px; }}"
                                  f"QPushButton:hover {{ background: {PILL_HOVER}; }}")
        seek_h = max(10, round(12 * scale_pct / 100))
        self.seek.setFixedHeight(seek_h)
        top, bottom = max(1, round(s * 0.08)), max(3, round(s * 0.2))
        self._outer.setContentsMargins(14, top, 14, bottom)
        self.hpx = seek_h + self._outer.spacing() + s + top + bottom
        self.alpha = int(255 * max(0, min(100, opacity_pct)) / 100)
        self.update()

    def set_wanted(self, flags: dict):
        for k in BAR_ICON_KEYS:
            if k in flags:
                self._wanted[k] = bool(flags[k])
        self.refresh_visibility(self._width)

    def refresh_visibility(self, width: int):
        """Show each control only if the user wants it and the window is wide enough."""
        self._width = width
        for k, w in self._ctl.items():
            w.setVisible(self._wanted.get(k, False) and width >= BAR_MIN_WIDTH[k])

    # window.py used to ask for a glow on neon themes; the monochrome build has none
    def apply_glow(self):
        pass

    def set_playing(self, playing: bool):
        self.btn_play.set_icon("pause" if playing else "play")

    def set_fullscreen(self, on: bool):
        self.btn_full.set_icon("exit_fullscreen" if on else "fullscreen")
        self.btn_full.setToolTip("Leave fullscreen (F)" if on else "Fullscreen (F)")

    def set_repeat_state(self, mode: str):
        self.btn_loop.set_icon("repeat_one" if mode == "one" else "repeat")
        self.btn_loop.setChecked(mode != "off")
        label = {"off": "off", "all": "the whole queue", "one": "this file"}.get(mode, "off")
        self.btn_loop.setToolTip(f"Repeat: {label} (click to change)")

    def set_time(self, pos: int, length: int):
        self._pos, self._len = pos, length
        force_h = length >= 3_600_000
        if self.show_remaining and length:
            left = f"-{fmt_time(max(0, length - pos), force_h)}"
            self.time.setText(f"{left} / {fmt_time(length, force_h)}")
        else:
            self.time.setText(f"{fmt_time(pos, force_h)} / {fmt_time(length, force_h)}")
        self.seek.set_length(length)
        self.seek.set_position(pos)

    def _toggle_remaining(self):
        self.show_remaining = not self.show_remaining
        self.time.setToolTip("Click to show elapsed time" if self.show_remaining else "Click to show remaining time")
        self.set_time(self._pos, self._len)

    def set_speed(self, rate: float):
        self.speed.setText(f"{rate:g}x")

    def set_volume(self, v: int, muted: bool):
        self.cone.set_value(v, muted)
