from __future__ import annotations

from datetime import datetime
import importlib.util
import time
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QStyle,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .models import TelemetrySnapshot

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView  # type: ignore[attr-defined]

    WEB_ENGINE_AVAILABLE = True
except Exception:
    WEB_ENGINE_AVAILABLE = False
    QWebEngineView = None  # type: ignore[assignment]

_ASSET_ICON_FILES = {
    "terminal": "terminal.png",
    "bin": "bin.png",
    "logo": "logo-o.png",
    "browser": "browser.png",
    "settings": "settings.png",
    "jupyter": "jupyter.svg",
    "qubo": "qubo.png",
}


def _runtime_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def _ui_shell_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return _runtime_root_dir()
    return Path(__file__).resolve().parents[1]


_UI_SHELL_DIR = _ui_shell_base_dir()
_ICON_DIR = _UI_SHELL_DIR / "assets" / "icons"


def find_wallpaper_path() -> Path | None:
    root_dir = _runtime_root_dir()
    matches = sorted(root_dir.glob("wp877*"))
    if matches:
        return matches[0]
    return None


def _asset_icon(key: str) -> QIcon:
    filename = _ASSET_ICON_FILES.get(key)
    if not filename:
        return QIcon()
    path = _ICON_DIR / filename
    if not path.exists():
        return QIcon()
    return QIcon(str(path))


def _enable_tabular_numbers(font: QFont) -> None:
    # Enable OpenType tabular figures when available in the active font.
    try:
        for tag in font.featureTags():
            value = tag.toString()
            tag_text = value.decode("ascii", "ignore") if isinstance(value, (bytes, bytearray)) else str(value)
            if tag_text == "tnum":
                font.setFeature(tag, 1)
                break
    except Exception:
        return


def make_ui_font(
    size: int = 11,
    weight: QFont.Weight = QFont.Weight.Normal,
    monospace: bool = False,
    tabular: bool = False,
) -> QFont:
    family = "JetBrains Mono" if monospace else "Inter"
    font = QFont(family, size)
    font.setWeight(weight)
    if tabular:
        _enable_tabular_numbers(font)
    return font


def apply_ui_font(
    widget: QWidget,
    size: int = 11,
    weight: QFont.Weight = QFont.Weight.Normal,
    monospace: bool = False,
    tabular: bool = False,
) -> None:
    widget.setFont(make_ui_font(size=size, weight=weight, monospace=monospace, tabular=tabular))


class PanelWindow(QFrame):
    def __init__(self, title: str, icon: QIcon, content: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panelWindow")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("panelHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(14, 14))
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        for symbol, callback in (
            ("\u2212", self._minimize_panel),
            ("\u25A1", self._restore_panel),
            ("\u00D7", self.hide),
        ):
            button = QPushButton(symbol)
            button.setObjectName("windowControl")
            button.setFixedSize(18, 18)
            button.clicked.connect(callback)
            header_layout.addWidget(button)
        root.addWidget(header)

        self._body = QFrame()
        self._body.setObjectName("panelBody")
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(content)
        root.addWidget(self._body, 1)
        self._is_collapsed = False

    def _minimize_panel(self) -> None:
        if self._is_collapsed:
            return
        self._is_collapsed = True
        self._body.hide()
        self.setMaximumHeight(34)

    def _restore_panel(self) -> None:
        if not self._is_collapsed:
            self.show()
            return
        self._is_collapsed = False
        self.setMaximumHeight(16777215)
        self._body.show()

class LineChart(QWidget):
    def __init__(self, title: str, line_color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title = title
        self.line_color = QColor(line_color)
        self.values: list[float] = [0.0] * 60
        self.setMinimumHeight(128)

    def push(self, value: float) -> None:
        self.values.append(value)
        self.values = self.values[-90:]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(40, 45, 56, 230))

        painter.setPen(QPen(QColor(92, 104, 123), 1.0))
        for i in range(1, 5):
            y = int((self.height() / 5) * i)
            painter.drawLine(0, y, self.width(), y)

        painter.setPen(QPen(QColor(216, 222, 233), 1.0))
        painter.drawText(8, 16, self.title)

        if len(self.values) < 2:
            return

        low = min(self.values)
        high = max(self.values)
        scale = high - low if high > low else 1.0

        path = QPainterPath()
        for index, value in enumerate(self.values):
            x = (index / (len(self.values) - 1)) * (self.width() - 16) + 8
            normalized = (value - low) / scale
            y = (1.0 - normalized) * (self.height() - 34) + 22
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.setPen(QPen(self.line_color, 2.0))
        painter.drawPath(path)


class CandlestickChart(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title = title
        self._candles: list[tuple[float, float, float, float]] = []
        self._bucket_open = 0.0
        self._bucket_high = 0.0
        self._bucket_low = 0.0
        self._bucket_ticks = 0
        self._bucket_size = 4
        self.setMinimumHeight(118)

    def push_price(self, price: float) -> None:
        if self._bucket_ticks == 0:
            self._bucket_open = price
            self._bucket_high = price
            self._bucket_low = price
        else:
            self._bucket_high = max(self._bucket_high, price)
            self._bucket_low = min(self._bucket_low, price)
        self._bucket_ticks += 1

        if self._bucket_ticks >= self._bucket_size:
            candle = (self._bucket_open, self._bucket_high, self._bucket_low, price)
            self._candles.append(candle)
            self._candles = self._candles[-50:]
            self._bucket_ticks = 0
            self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(40, 45, 56, 230))

        painter.setPen(QPen(QColor(92, 104, 123), 1.0))
        for i in range(1, 5):
            y = int((self.height() / 5) * i)
            painter.drawLine(0, y, self.width(), y)

        painter.setPen(QPen(QColor(216, 222, 233), 1.0))
        painter.drawText(8, 16, self.title)

        if not self._candles:
            return

        lows = [c[2] for c in self._candles]
        highs = [c[1] for c in self._candles]
        low = min(lows)
        high = max(highs)
        scale = high - low if high > low else 1.0

        candle_area_top = 22
        candle_area_height = self.height() - 30
        candle_w = max(4.0, (self.width() - 20) / max(1, len(self._candles)))

        def price_to_y(value: float) -> float:
            normalized = (value - low) / scale
            return (1.0 - normalized) * candle_area_height + candle_area_top

        for idx, (open_v, high_v, low_v, close_v) in enumerate(self._candles):
            x_center = 10 + idx * candle_w + candle_w / 2.0
            wick_top = price_to_y(high_v)
            wick_bottom = price_to_y(low_v)
            open_y = price_to_y(open_v)
            close_y = price_to_y(close_v)

            is_up = close_v >= open_v
            color = QColor("#A3BE8C" if is_up else "#BF616A")
            painter.setPen(QPen(color, 1.2))
            painter.drawLine(int(x_center), int(wick_top), int(x_center), int(wick_bottom))

            body_top = min(open_y, close_y)
            body_bottom = max(open_y, close_y)
            body_h = max(2.0, body_bottom - body_top)
            body_w = max(2.5, candle_w * 0.55)
            x = x_center - body_w / 2.0
            painter.fillRect(int(x), int(body_top), int(body_w), int(body_h), color)


@dataclass
class WalletSnapshot:
    balance: float
    pending: float
    pnl_per_hour: float
    delta_percent: float


class MiningDashboardPanel(QFrame):
    mode_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._shares_accepted = 1240
        self._shares_rejected = 12
        self._fan_percent = 48

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel("Mining Dashboard")
        title.setObjectName("sectionTitle")
        apply_ui_font(title, size=13, weight=QFont.Weight.DemiBold)
        root.addWidget(title)

        stats = QGridLayout()
        root.addLayout(stats)

        self.gpu_temp = QLabel("GPU: --C")
        self.gpu_load = QLabel("Load: --%")
        self.hashrate = QLabel("Hashrate: -- MH/s")
        self.profit = QLabel("P/L: -- ALGO/hr")
        self.power = QLabel("Power: -- W")
        self.vram = QLabel("VRAM: -- GB")
        self.accuracy = QLabel("Accuracy: --%")

        for index, widget in enumerate(
            (self.gpu_temp, self.gpu_load, self.hashrate, self.profit, self.power, self.vram, self.accuracy)
        ):
            tile = QFrame()
            tile.setObjectName("metricTile")
            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(10, 8, 10, 8)
            widget.setObjectName("metricLabel")
            apply_ui_font(widget, size=11, weight=QFont.Weight.Bold, tabular=True)
            tile_layout.addWidget(widget)
            stats.addWidget(tile, index // 3, index % 3)

        self.hashrate_chart = LineChart("Hashrate (MH/s)", "#88C0D0")
        self.temp_chart = LineChart("GPU Temperature (C)", "#D08770")
        root.addWidget(self.hashrate_chart)
        root.addWidget(self.temp_chart)

        footer = QHBoxLayout()
        self.pool_status = QLabel("Pool: connected | Latency: -- ms")
        self.shares = QLabel("Shares A/R: 0 / 0")
        apply_ui_font(self.pool_status, size=11, weight=QFont.Weight.Medium, tabular=True)
        apply_ui_font(self.shares, size=11, weight=QFont.Weight.Medium, tabular=True)
        footer.addWidget(self.pool_status)
        footer.addStretch(1)
        footer.addWidget(self.shares)
        root.addLayout(footer)

        actions = QHBoxLayout()
        for label, mode in (
            ("Performance Lock", "gaming"),
            ("Balanced", "balanced"),
            ("Sleep Mining", "sleep"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, value=mode: self.mode_requested.emit(value))
            actions.addWidget(button)
        actions.addStretch(1)
        root.addLayout(actions)

    def update_telemetry(
        self,
        telemetry: TelemetrySnapshot,
        mining_active: bool = False,
        accuracy: float = 0.0,
        pnl_per_hour: float = 0.0,
    ) -> None:
        hashrate = telemetry.gpu_load_percent * 0.92
        power = 110 + telemetry.gpu_load_percent * 1.8
        vram = 2.0 + telemetry.gpu_load_percent * 0.08

        self.gpu_temp.setText(f"GPU: {telemetry.gpu_temp_c:.1f} C")
        self.gpu_load.setText(f"Load: {telemetry.gpu_load_percent:.1f}%")
        self.hashrate.setText(f"Hashrate: {hashrate:.1f} MH/s")
        sign = "+" if pnl_per_hour >= 0 else ""
        self.profit.setText(f"P/L: {sign}{pnl_per_hour:.2f} ALGO/hr")
        self.power.setText(f"Power: {power:.0f} W")
        self.vram.setText(f"VRAM: {vram:.1f} GB")
        self.accuracy.setText(f"Accuracy: {accuracy * 100.0:.2f}%")

        self._fan_percent = min(92, max(30, int(30 + telemetry.gpu_load_percent * 0.6)))
        self._shares_accepted += int(telemetry.gpu_load_percent / 45.0)
        self._shares_rejected += 1 if telemetry.gpu_temp_c > 82 else 0
        state = "active" if mining_active else "idle"
        self.pool_status.setText(
            f"Pool: connected | Latency: {telemetry.net_latency_ms:.1f} ms | Fan: {self._fan_percent}% | Miner: {state}"
        )
        self.shares.setText(f"Shares A/R: {self._shares_accepted} / {self._shares_rejected}")

        self.hashrate_chart.push(hashrate)
        self.temp_chart.push(telemetry.gpu_temp_c)


class BalanceStripWidget(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("balanceStrip")
        self._value = 0.0
        self._pending = 0.0
        self._last_value = 0.0
        self._last_delta = 0.0

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(6)

        top = QHBoxLayout()
        title = QLabel("Wallet Balance")
        title.setObjectName("minorText")
        apply_ui_font(title, size=11, weight=QFont.Weight.Medium)
        top.addWidget(title)
        top.addStretch(1)

        self.delta = QLabel("0.00%")
        self.delta.setObjectName("balanceDelta")
        apply_ui_font(self.delta, size=11, weight=QFont.Weight.Bold, tabular=True)
        top.addWidget(self.delta)
        root.addLayout(top)

        self.value = QLabel("0.00 ALGO")
        self.value.setObjectName("balanceValue")
        apply_ui_font(self.value, size=20, weight=QFont.Weight.Bold, tabular=True)
        root.addWidget(self.value)

        stats = QHBoxLayout()
        self.pending = QLabel("Pending: 0.00 ALGO")
        self.per_hour = QLabel("0.00 ALGO / hr")
        self.pending.setObjectName("minorText")
        self.per_hour.setObjectName("minorText")
        apply_ui_font(self.pending, size=11, weight=QFont.Weight.Medium, tabular=True)
        apply_ui_font(self.per_hour, size=11, weight=QFont.Weight.Medium, tabular=True)
        stats.addWidget(self.pending)
        stats.addStretch(1)
        stats.addWidget(self.per_hour)
        root.addLayout(stats)

        self.candles = CandlestickChart("Wallet P/L (candles)")
        root.addWidget(self.candles)

        bars = QHBoxLayout()
        bars.setSpacing(4)
        self._bars: list[QFrame] = []
        for _ in range(10):
            bar = QFrame()
            bar.setObjectName("balanceBar")
            bar.setFixedSize(14, 3)
            bars.addWidget(bar)
            self._bars.append(bar)
        bars.addStretch(1)
        root.addLayout(bars)

    @property
    def snapshot(self) -> WalletSnapshot:
        delta_pct = 0.0 if abs(self._last_value) <= 1e-9 else (self._last_delta / abs(self._last_value)) * 100.0
        return WalletSnapshot(
            balance=self._value,
            pending=self._pending,
            pnl_per_hour=self._last_delta * 3600.0,
            delta_percent=delta_pct,
        )

    def update_telemetry(
        self,
        telemetry: TelemetrySnapshot,
        mining_active: bool,
        accuracy: float,
        external_balance: float | None = None,
        external_pending: float | None = None,
    ) -> WalletSnapshot:
        self._last_value = self._value
        self._last_delta = 0.0

        if external_balance is not None:
            next_balance = float(external_balance)
            self._last_delta = next_balance - self._value
            self._value = next_balance
            if external_pending is not None:
                self._pending = float(external_pending)
            elif self._last_delta > 0:
                self._pending += self._last_delta * 0.28
            elif self._last_delta < 0:
                self._pending = max(0.0, self._pending + self._last_delta * 0.12)
        elif mining_active:
            load_factor = max(0.35, min(1.25, telemetry.gpu_load_percent / 78.0))
            thermal_penalty = 0.7 if telemetry.gpu_temp_c > 85 else 1.0
            accuracy_edge = accuracy - 0.86
            self._last_delta = accuracy_edge * load_factor * thermal_penalty * 0.85
            self._value = max(0.0, self._value + self._last_delta)
            if self._last_delta > 0:
                self._pending += self._last_delta * 0.45
            else:
                self._pending = max(0.0, self._pending + self._last_delta * 0.15)
        else:
            self._pending = max(0.0, self._pending - 0.01)

        pnl_per_hour = self._last_delta * 3600.0
        delta_pct = 0.0 if abs(self._last_value) <= 1e-9 else (self._last_delta / abs(self._last_value)) * 100.0

        sign = "+" if delta_pct >= 0 else ""
        sign_hr = "+" if pnl_per_hour >= 0 else ""
        self.value.setText(f"{self._value:,.2f} ALGO")
        self.delta.setText(f"{sign}{delta_pct:.3f}%")
        self.pending.setText(f"Pending: {self._pending:.2f} ALGO")
        self.per_hour.setText(f"{sign_hr}{pnl_per_hour:.2f} ALGO / hr")

        if delta_pct < 0:
            self.delta.setStyleSheet(
                "color: #BF616A; background-color: rgba(191,97,106,30); border: 1px solid rgba(191,97,106,100); border-radius: 9999px; padding: 2px 8px; font-size: 10px; font-weight: 700;"
            )
        else:
            self.delta.setStyleSheet("")

        active = min(10, max(0, int(telemetry.gpu_load_percent / 10))) if mining_active else 0
        for idx, bar in enumerate(self._bars):
            if idx < active:
                bar.setStyleSheet("background-color: #88C0D0; border-radius: 1px;")
            else:
                bar.setStyleSheet("background-color: rgba(136,192,208,50); border-radius: 1px;")

        self.candles.push_price(self._value)
        return self.snapshot


class TerminalPanel(QFrame):
    command_issued = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        self.output = QPlainTextEdit()
        self.output.setObjectName("terminalOutput")
        self.output.setReadOnly(True)
        self.output.setFont(QFont("JetBrains Mono", 10))
        self.output.appendPlainText("neuro@node:~$ cowsay 'Compute with purpose.'")
        self.output.appendPlainText(" _________________________________")
        self.output.appendPlainText("< Living on Earth may be expensive >")
        self.output.appendPlainText(" ---------------------------------")
        self.output.appendPlainText("neuro@node:~$ neofetch")
        self.output.appendPlainText("OS: Opportunity OS")
        self.output.appendPlainText("Kernel: tuned low-latency profile")
        self.output.appendPlainText("Shell: Opportunity Desktop")
        self.output.appendPlainText("Theme: Nordic")
        self.output.appendPlainText("")
        self.output.appendPlainText("Commands: start-miner | stop-miner | switch-coin | check-gpu | wallet-balance | system-status")
        root.addWidget(self.output, 1)

        row = QHBoxLayout()
        prompt = QLabel("dig@node:~$")
        prompt.setObjectName("terminalPrompt")
        row.addWidget(prompt)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type mining command and press Enter...")
        self.input.returnPressed.connect(self._submit)
        row.addWidget(self.input, 1)
        root.addLayout(row)

    def write_line(self, line: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output.appendPlainText(f"[{timestamp}] {line}")

    def _submit(self) -> None:
        command = self.input.text().strip()
        if not command:
            return
        self.output.appendPlainText(f"dig@node:~$ {command}")
        self.command_issued.emit(command)
        self.input.clear()


class FileManagerPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("fileSidebar")
        self.sidebar.setFixedWidth(170)
        for section in ("My Computer", "Home", "Desktop", "Documents", "Music", "Images", "Mining"):
            self.sidebar.addItem(section)
        self.sidebar.currentTextChanged.connect(self._populate_grid)
        root.addWidget(self.sidebar)

        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        menu_row = QHBoxLayout()
        menu_row.setContentsMargins(2, 0, 2, 0)
        for label in ("File", "Edit", "View", "Go", "Bookmarks", "Help"):
            menu = QLabel(label)
            menu.setObjectName("minorText")
            menu_row.addWidget(menu)
        menu_row.addStretch(1)
        right_layout.addLayout(menu_row)

        path_row = QFrame()
        path_row.setObjectName("pathRow")
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(8, 4, 8, 4)
        self.path_label = QLabel("/home/dig")
        self.path_label.setObjectName("panelTitle")
        path_layout.addWidget(self.path_label)
        path_layout.addStretch(1)
        right_layout.addWidget(path_row)

        self.grid_host = QFrame()
        self.grid_layout = QGridLayout(self.grid_host)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(10)
        right_layout.addWidget(self.grid_host, 1)

        self.footer = QLabel("9 items, Free space: 466.5 GB")
        self.footer.setObjectName("minorText")
        right_layout.addWidget(self.footer)

        root.addWidget(right_panel, 1)
        self.sidebar.setCurrentRow(0)

    def _populate_grid(self, section: str) -> None:
        self.path_label.setText(f"/home/dig/{section.lower().replace(' ', '_')}")
        folders = {
            "My Computer": ("Documenti", "Git", "Immagini", "Modelli", "Musica", "Pubblici", "Scaricati", "Scrivania", "Video"),
            "Home": ("Desktop", "Downloads", "Mining", "Wallet", "Config", "Logs", "Models", "Data", "Backups"),
            "Desktop": ("Computer", "Home", "Trash"),
            "Documents": ("Contracts", "Wallet Notes", "Roadmap", "Benchmarks"),
            "Music": ("Ambient", "Focus", "System Sounds"),
            "Images": ("Wallpapers", "Charts", "Render"),
            "Mining": ("current_job.ckpt", "profit_history.csv", "pool.conf", "latency-cache.db"),
        }
        items = folders.get(section, ("Empty",))

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for idx, label in enumerate(items):
            btn = QToolButton()
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            icon = themed_icon(("folder-symbolic",), QStyle.StandardPixmap.SP_DirIcon, self)
            btn.setIcon(icon)
            btn.setIconSize(QSize(30, 30))
            btn.setText(label)
            btn.setObjectName("fileGridItem")
            self.grid_layout.addWidget(btn, idx // 5, idx % 5)

        self.footer.setText(f"{len(items)} items, Free space: 466.5 GB")


class BrowserDialog(QDialog):
    def __init__(self, title: str = "Opportunity Browser", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1040, 720)
        self.setWindowIcon(themed_icon(("asset:browser", "firefox", "web-browser"), QStyle.StandardPixmap.SP_BrowserReload, self))

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        chrome = QFrame()
        chrome.setObjectName("browserChrome")
        chrome_layout = QVBoxLayout(chrome)
        chrome_layout.setContentsMargins(8, 8, 8, 8)
        chrome_layout.setSpacing(6)

        tab_row = QHBoxLayout()
        tab_row.setContentsMargins(0, 0, 0, 0)
        tab_chip = QFrame()
        tab_chip.setObjectName("browserTabChip")
        chip_layout = QHBoxLayout(tab_chip)
        chip_layout.setContentsMargins(10, 4, 10, 4)
        chip_layout.setSpacing(6)
        tab_icon = QLabel()
        tab_icon.setPixmap(themed_icon(("asset:browser",), QStyle.StandardPixmap.SP_BrowserReload, self).pixmap(14, 14))
        chip_layout.addWidget(tab_icon)
        chip_layout.addWidget(QLabel("New Tab"))
        tab_row.addWidget(tab_chip)
        tab_row.addStretch(1)
        chrome_layout.addLayout(tab_row)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(6)
        self.back_btn = QToolButton()
        self.back_btn.setObjectName("browserNavButton")
        self.back_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.fwd_btn = QToolButton()
        self.fwd_btn.setObjectName("browserNavButton")
        self.fwd_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self.reload_btn = QToolButton()
        self.reload_btn.setObjectName("browserNavButton")
        self.reload_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.home_btn = QToolButton()
        self.home_btn.setObjectName("browserNavButton")
        self.home_btn.setIcon(themed_icon(("asset:logo",), QStyle.StandardPixmap.SP_DirHomeIcon, self))

        address = QFrame()
        address.setObjectName("browserAddressBar")
        address_layout = QHBoxLayout(address)
        address_layout.setContentsMargins(8, 4, 8, 4)
        address_layout.setSpacing(6)
        lock_label = QLabel()
        lock_label.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton).pixmap(12, 12))
        address_layout.addWidget(lock_label)
        self.url_input = QLineEdit("https://www.google.com")
        self.url_input.setObjectName("browserUrlInput")
        self.url_input.returnPressed.connect(self._go_to_input)
        address_layout.addWidget(self.url_input, 1)
        self.open_external_btn = QToolButton()
        self.open_external_btn.setObjectName("browserOpenButton")
        self.open_external_btn.setText("Open")
        self.open_external_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.open_external_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.open_external_btn.clicked.connect(self._open_external)
        controls.addWidget(self.back_btn)
        controls.addWidget(self.fwd_btn)
        controls.addWidget(self.reload_btn)
        controls.addWidget(self.home_btn)
        controls.addWidget(address, 1)
        controls.addWidget(self.open_external_btn)
        chrome_layout.addLayout(controls)
        root.addWidget(chrome)

        self.status = QLabel("")
        self.status.setObjectName("browserStatus")
        root.addWidget(self.status)

        self._current_url = "https://www.google.com"
        self.web: QWebEngineView | None = None
        self.fallback_text: QLabel | None = None

        self.back_btn.clicked.connect(self._go_back)
        self.fwd_btn.clicked.connect(self._go_forward)
        self.reload_btn.clicked.connect(self._reload)
        self.home_btn.clicked.connect(lambda: self.open_url("https://www.google.com"))

        if WEB_ENGINE_AVAILABLE and QWebEngineView is not None:
            self.web = QWebEngineView()
            self.web.urlChanged.connect(lambda qurl: self.url_input.setText(qurl.toString()))
            self.web.loadStarted.connect(lambda: self.status.setText("Loading..."))
            self.web.loadFinished.connect(self._on_load_finished)
            root.addWidget(self.web, 1)
            self.open_url(self._current_url)
        else:
            self.fallback_text = QLabel(
                "Embedded web view is unavailable in this runtime.\nUse 'Open External' to open pages in your system browser."
            )
            self.fallback_text.setWordWrap(True)
            self.fallback_text.setObjectName("minorText")
            root.addWidget(self.fallback_text, 1)
            self.back_btn.setEnabled(False)
            self.fwd_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)
            self.home_btn.setEnabled(False)
            self.status.setText("Qt WebEngine unavailable")

    def open_url(self, url: str) -> None:
        target = QUrl.fromUserInput(url)
        self._current_url = target.toString()
        self.url_input.setText(self._current_url)
        if self.web is not None:
            self.status.setText(f"Loading: {self._current_url}")
            self.web.setUrl(target)
            return
        self._open_external_url(target)

    def _go_to_input(self) -> None:
        self.open_url(self.url_input.text().strip())

    def _go_back(self) -> None:
        if self.web is not None:
            self.web.back()

    def _go_forward(self) -> None:
        if self.web is not None:
            self.web.forward()

    def _reload(self) -> None:
        if self.web is not None:
            self.web.reload()
            return
        self._open_external_url(QUrl.fromUserInput(self.url_input.text().strip()))

    def _open_external(self) -> None:
        self._open_external_url(QUrl.fromUserInput(self.url_input.text().strip()))

    def _open_external_url(self, target: QUrl) -> None:
        ok = QDesktopServices.openUrl(target)
        if ok:
            self.status.setText(f"Opened in system browser: {target.toString()}")
        else:
            self.status.setText("Failed to open external browser")

    def _on_load_finished(self, ok: bool) -> None:
        if ok:
            self.status.setText("Loaded")
            return
        self.status.setText("Embedded load failed. Opening in system browser...")
        self._open_external_url(QUrl.fromUserInput(self.url_input.text().strip()))


class JupyterServerManager:
    def __init__(self) -> None:
        self.process: subprocess.Popen[str] | None = None
        self.port: int | None = None
        self.notebook_dir = Path.home() / "OpportunityOS" / "notebooks"
        self.notebook_dir.mkdir(parents=True, exist_ok=True)

    def ensure_started(self) -> str:
        if self.process is not None and self.process.poll() is None and self.port is not None:
            if self._wait_for_port(self.port, 0.4):
                return self.base_url

        if importlib.util.find_spec("notebook") is None:
            raise RuntimeError("Notebook package is not installed. Install 'notebook' to run an embedded server.")

        self.shutdown()
        self.port = self._next_free_port(8888, 8920)
        if self.port is None:
            raise RuntimeError("No free local port found for Jupyter")

        args = [
            sys.executable,
            "-m",
            "notebook",
            "--no-browser",
            "--ip=127.0.0.1",
            f"--port={self.port}",
            "--NotebookApp.token=",
            "--NotebookApp.password=",
            f"--notebook-dir={self.notebook_dir}",
        ]

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            text=True,
        )

        if not self._wait_for_port(self.port, 15.0):
            self.shutdown()
            raise RuntimeError("Jupyter failed to start")
        return self.base_url

    @property
    def base_url(self) -> str:
        port = self.port if self.port is not None else 8888
        return f"http://127.0.0.1:{port}/tree"

    def shutdown(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2.5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    @staticmethod
    def _next_free_port(start: int, end: int) -> int | None:
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.2)
                if sock.connect_ex(("127.0.0.1", port)) != 0:
                    return port
        return None

    @staticmethod
    def _wait_for_port(port: int, timeout: float) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.2)
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    return True
            time.sleep(0.2)
        return False


class JupyterNotebookDialog(BrowserDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Opportunity Notebook", parent)
        self.setWindowIcon(themed_icon(("asset:jupyter",), QStyle.StandardPixmap.SP_FileDialogInfoView, self))
        self.server = JupyterServerManager()
        self.url_input.setText("about:blank")
        self.status.setText("Jupyter server not started")
        self.start_btn = QPushButton("Start Jupyter")
        self.stop_btn = QPushButton("Stop Jupyter")
        self.start_btn.clicked.connect(self._start_and_open)
        self.stop_btn.clicked.connect(self.shutdown_server)
        controls = QFrame()
        controls.setObjectName("jupyterControls")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch(1)
        self.layout().addWidget(controls)  # type: ignore[union-attr]

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._start_and_open()

    def _start_and_open(self) -> None:
        try:
            url = self.server.ensure_started()
            self.open_url(url)
            self.status.setText(f"Jupyter running at {url}")
        except Exception as exc:
            self.status.setText(f"Jupyter start failed: {exc}")

    def shutdown_server(self) -> None:
        self.server.shutdown()
        self.status.setText("Jupyter stopped")


class SettingsPanel(QFrame):
    mode_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self.tabs.addTab(self._system_tab(), "System")
        self.tabs.addTab(self._mining_tab(), "Mining")
        self.tabs.addTab(self._gpu_tab(), "GPU")
        self.tabs.addTab(self._network_tab(), "Network")
        self.tabs.addTab(self._security_tab(), "Security")
        self.tabs.addTab(self._wallet_tab(), "Wallet")
        self.tabs.addTab(self._updates_tab(), "Updates")
        self.tabs.addTab(self._advanced_tab(), "Advanced")

    def _system_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow("Performance profile", self._combo(("Balanced", "Performance Lock", "Eco")))
        form.addRow("Theme", self._combo(("Nordic Dark", "Adwaita Dark", "Opportunity Dark")))
        form.addRow("Workspace behavior", self._combo(("Static workspaces", "Dynamic workspaces")))
        return page

    def _mining_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow("Default pool", QLineEdit("stratum+tcp://pool.dig.net:4444"))
        form.addRow("Backup pool", QLineEdit("stratum+tcp://backup.dig.net:4444"))
        form.addRow("Coin selection", self._combo(("ALGO", "ERG", "RVN", "AUTO")))
        form.addRow("Auto-profit mode", QCheckBox("Enable dynamic coin switching"))
        benchmark = QPushButton("Run benchmark")
        benchmark.clicked.connect(lambda: self.mode_requested.emit("gaming"))
        form.addRow("Benchmark", benchmark)
        return page

    def _gpu_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow("Core clock offset", self._slider(-300, 300, 80))
        form.addRow("Memory clock offset", self._slider(-1000, 1500, 320))
        form.addRow("Power limit (%)", self._slider(40, 120, 85))
        form.addRow("Fan target (%)", self._slider(20, 100, 62))
        return page

    def _network_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow("Primary interface", self._combo(("eth0", "wlan0", "auto")))
        form.addRow("Failover", QCheckBox("Enable backup route"))
        form.addRow("Cluster API", QLineEdit("https://cluster.dig.net/api"))
        return page

    def _security_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow("Wallet encryption", QCheckBox("TPM-backed vault enabled"))
        form.addRow("SSH", QCheckBox("Allow hardened SSH"))
        form.addRow("Firewall", QCheckBox("Enable nftables ruleset"))
        form.addRow("Secure boot status", QLabel("Verified"))
        return page

    def _wallet_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow("Wallet address", QLineEdit("dig1q9x8...m4k2"))
        form.addRow("Auto-payout threshold", QLineEdit("250 ALGO"))
        form.addRow("2FA withdrawals", QCheckBox("Require OTP"))
        return page

    def _updates_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow("Channel", self._combo(("Stable", "LTS", "Testing")))
        form.addRow("Btrfs snapshots", QCheckBox("Create pre-update snapshot"))
        form.addRow("Auto rollback", QCheckBox("Rollback on failed boot"))
        return page

    def _advanced_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.addRow("cgroups v2 UI reservation", QLineEdit("CPU 5% | GPU 5%"))
        form.addRow("Thermal throttle", QLineEdit("85C => reduce workload by 20%"))
        form.addRow("Cluster mode", QCheckBox("Enable remote node manager"))
        return page

    @staticmethod
    def _combo(values: tuple[str, ...]) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        return combo

    @staticmethod
    def _slider(minimum: int, maximum: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(value)
        return slider


class SettingsDialog(QDialog):
    mode_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Opportunity Settings")
        self.resize(940, 600)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Control Grid")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        root.addLayout(header)

        self.panel = SettingsPanel()
        self.panel.mode_requested.connect(self.mode_requested.emit)
        root.addWidget(self.panel, 1)


def themed_icon(names: tuple[str, ...], fallback: QStyle.StandardPixmap, widget: QWidget) -> QIcon:
    for name in names:
        if name.startswith("asset:"):
            icon = _asset_icon(name.split(":", 1)[1])
            if not icon.isNull():
                return icon
            continue
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
    return widget.style().standardIcon(fallback)

