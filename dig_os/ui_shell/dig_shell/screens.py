from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path
import subprocess
import sys
import time

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QConicalGradient, QFont, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .daemon_client import DaemonClient
from .widgets import (
    BalanceStripWidget,
    BrowserDialog,
    FileManagerPanel,
    JupyterNotebookDialog,
    MiningDashboardPanel,
    PanelWindow,
    SettingsDialog,
    TerminalPanel,
    apply_ui_font,
    find_wallpaper_path,
    themed_icon,
)

try:
    from ui.threads import WalletSyncThread
except Exception:
    WalletSyncThread = None  # type: ignore[assignment]


def _clock_text(now: datetime) -> str:
    days = ("lun", "mar", "mer", "gio", "ven", "sab", "dom")
    months = ("gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic")
    return f"{days[now.weekday()]} {now.day:02d} {months[now.month - 1]} {now:%H:%M}"


def _runtime_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def _detached_process_kwargs(cwd: Path) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "cwd": str(cwd),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    else:
        kwargs["start_new_session"] = True
    return kwargs


def _paint_wallpaper_fill(
    painter: QPainter,
    pixmap: QPixmap,
    target_size: QSize,
    cache: dict[str, object] | None = None,
) -> bool:
    if pixmap.isNull() or target_size.width() <= 0 or target_size.height() <= 0:
        return False
    scaled: QPixmap
    if cache is not None:
        cached_size = cache.get("size")
        cached_scaled = cache.get("scaled")
        if isinstance(cached_size, QSize) and cached_size == target_size and isinstance(cached_scaled, QPixmap):
            scaled = cached_scaled
        else:
            scaled = pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            cache["size"] = QSize(target_size)
            cache["scaled"] = scaled
    else:
        scaled = pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
    source_x = max(0, (scaled.width() - target_size.width()) // 2)
    source_y = max(0, (scaled.height() - target_size.height()) // 2)
    painter.drawPixmap(
        0,
        0,
        scaled,
        source_x,
        source_y,
        target_size.width(),
        target_size.height(),
    )
    return True


class BootScreen(QWidget):
    boot_complete = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._progress = 0
        self._phase = 0.0
        wallpaper = find_wallpaper_path()
        self._wallpaper = QPixmap(str(wallpaper)) if wallpaper is not None else QPixmap()
        self._wallpaper_cache: dict[str, object] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(10)
        root.addStretch(1)

        icon_label = QLabel()
        icon = themed_icon(("asset:logo", "applications-system-symbolic"), QStyle.StandardPixmap.SP_ComputerIcon, self)
        icon_label.setPixmap(icon.pixmap(70, 70))
        root.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.title = QLabel("Opportunity OS")
        self.title.setObjectName("bootTitle")
        root.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.status = QLabel("Initializing core services... 0%")
        self.status.setObjectName("bootText")
        root.addWidget(self.status, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

        self.timer = QTimer(self)
        self.timer.setInterval(28)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _tick(self) -> None:
        self._phase += 0.10
        self._progress += 1
        self.status.setText(f"Initializing core services... {self._progress}%")
        if self._progress >= 100:
            self.timer.stop()
            self.boot_complete.emit()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painted = _paint_wallpaper_fill(painter, self._wallpaper, self.size(), self._wallpaper_cache)
        if not painted:
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor("#2A2139"))
            gradient.setColorAt(0.5, QColor("#A13D87"))
            gradient.setColorAt(1.0, QColor("#2D2C7F"))
            painter.fillRect(self.rect(), gradient)

        overlay = QLinearGradient(0, 0, 0, self.height())
        overlay.setColorAt(0.0, QColor(14, 10, 28, 185))
        overlay.setColorAt(1.0, QColor(14, 10, 28, 220))
        painter.fillRect(self.rect(), overlay)

        center = QPointF(self.width() / 2.0, self.height() * 0.61)
        radius = 62.0
        ring_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2.0, radius * 2.0)

        track_pen = QPen(QColor(255, 255, 255, 55), 10.0)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(ring_rect)

        spin_gradient = QConicalGradient(center, -90.0 - (self._phase * 120.0))
        spin_gradient.setColorAt(0.0, QColor("#FFFFFF"))
        spin_gradient.setColorAt(0.42, QColor("#FFC3E2"))
        spin_gradient.setColorAt(1.0, QColor("#6D9CFF"))
        progress_pen = QPen(QBrush(spin_gradient), 10.0)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        span = int(-(self._progress / 100.0) * 360.0 * 16.0)
        painter.drawArc(ring_rect, 90 * 16, span)

        pulse_alpha = max(60, min(180, int(120 + 60 * math.sin(self._phase * 3.0))))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, pulse_alpha))
        painter.drawEllipse(center, 5.5, 5.5)


class LockScreen(QWidget):
    unlocked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sleep_earnings = 450.0
        wallpaper = find_wallpaper_path()
        self._wallpaper = QPixmap(str(wallpaper)) if wallpaper is not None else QPixmap()
        self._wallpaper_cache: dict[str, object] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(64, 42, 64, 52)
        root.setSpacing(12)

        top = QFrame()
        top.setObjectName("topBar")
        top.setFixedHeight(28)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(8, 1, 8, 1)
        top_layout.addWidget(QLabel("Activities"))
        top_layout.addStretch(1)
        self.clock = QLabel("")
        self.clock.setObjectName("topCenterStatus")
        top_layout.addWidget(self.clock)
        top_layout.addStretch(1)
        top_layout.addWidget(QLabel("it"))
        root.addWidget(top)

        root.addStretch(1)
        card = QFrame()
        card.setObjectName("lockCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(8)

        avatar = QLabel()
        avatar_icon = themed_icon(("asset:logo", "avatar-default-symbolic"), QStyle.StandardPixmap.SP_DirHomeIcon, self)
        avatar.setPixmap(avatar_icon.pixmap(52, 52))
        avatar.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(avatar)

        title = QLabel("Opportunity OS")
        title.setObjectName("sectionTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(title)

        user = QLabel("User: commander")
        user.setObjectName("minorText")
        user.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(user)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self.unlocked.emit)
        card_layout.addWidget(self.password)

        self.earnings = QLabel("Earnings while locked: 450 ALGO")
        self.earnings.setObjectName("minorText")
        card_layout.addWidget(self.earnings)

        login = QPushButton("Sign In")
        login.clicked.connect(self.unlocked.emit)
        card_layout.addWidget(login)
        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

        self.time_timer = QTimer(self)
        self.time_timer.setInterval(1000)
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start()
        self._update_time()

    def set_sleep_earnings(self, amount: float) -> None:
        self._sleep_earnings = amount
        self.earnings.setText(f"Earnings while locked: {amount:.0f} ALGO")

    def _update_time(self) -> None:
        self.clock.setText(_clock_text(datetime.now()))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painted = _paint_wallpaper_fill(painter, self._wallpaper, self.size(), self._wallpaper_cache)
        if not painted:
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor("#2A2139"))
            gradient.setColorAt(0.56, QColor("#BC4E9D"))
            gradient.setColorAt(1.0, QColor("#2D2C7F"))
            painter.fillRect(self.rect(), gradient)

        overlay = QLinearGradient(0, 0, 0, self.height())
        overlay.setColorAt(0.0, QColor(24, 16, 38, 165))
        overlay.setColorAt(1.0, QColor(15, 12, 33, 230))
        painter.fillRect(self.rect(), overlay)


class DesktopScreen(QWidget):
    power_off_requested = Signal()
    minimize_requested = Signal()
    close_requested = Signal()

    def __init__(self, daemon: DaemonClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.daemon = daemon
        self.telemetry = self.daemon.get_telemetry()
        self.missions = self.daemon.get_missions()
        self.mining_active = False
        self.training_accuracy = 0.0
        self.dashboard_panels: list[MiningDashboardPanel] = []
        self.terminal_panels: list[TerminalPanel] = []
        self.files_window: PanelWindow | None = None
        self.terminal_window: PanelWindow | None = None
        self.mining_window: PanelWindow | None = None
        self.monitor_window: PanelWindow | None = None
        self.start_button: QToolButton | None = None
        self._nurochain_process: subprocess.Popen[str] | None = None
        self._last_nurochain_launch = 0.0
        self._qubo_process: subprocess.Popen[str] | None = None
        self._last_qubo_launch = 0.0
        self._gpu_tray_state = "normal"
        self._wallet_sync_path = _runtime_root_dir() / "runtime" / "opportunity_wallet_state.json"
        self._wallet_sync_marker: tuple[int, int] | None = None
        self._external_wallet_balance: float | None = None
        self._external_wallet_pending: float | None = None
        self._algorand_balance: float | None = None
        self._algorand_address: str | None = None
        self._algorand_last_sync_ok: bool = False
        self._algorand_last_sync_time: str = "--:--:--"
        self._algorand_sync_thread: WalletSyncThread | None = None
        self.lbl_algo_address: QLabel | None = None
        self.lbl_algo_balance: QLabel | None = None
        self.lbl_algo_status: QLabel | None = None
        wallpaper = find_wallpaper_path()
        self._wallpaper = QPixmap(str(wallpaper)) if wallpaper is not None else QPixmap()
        self._wallpaper_cache: dict[str, object] = {}

        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.mode_requested.connect(self._apply_mode)
        self.browser_dialog = BrowserDialog(parent=self)
        self.jupyter_dialog = JupyterNotebookDialog(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 14)
        root.setSpacing(0)
        root.addWidget(self._build_top_bar())

        center = QHBoxLayout()
        center.setContentsMargins(16, 10, 16, 8)
        center.setSpacing(10)
        center.addWidget(self._build_workspaces(), 1)
        root.addLayout(center, 1)

        root.addWidget(self._build_bottom_dock(), 0, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)

        self._start_blockchain_sync()

        self.poller = QTimer(self)
        self.poller.setInterval(1000)
        self.poller.timeout.connect(self.refresh)
        self.poller.start()
        self.refresh()

    def _build_top_bar(self) -> QFrame:
        top = QFrame()
        top.setObjectName("topBar")
        top.setFixedHeight(28)
        layout = QHBoxLayout(top)
        layout.setContentsMargins(8, 1, 8, 1)
        layout.setSpacing(7)

        activities = QPushButton("Activities")
        activities.setObjectName("flatTopButton")
        activities.clicked.connect(lambda: self._log("Activities opened"))
        layout.addWidget(activities)

        self.workspace_buttons: list[QPushButton] = []
        for idx in (1, 2, 3):
            btn = QPushButton(str(idx))
            btn.setObjectName("workspaceButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked=False, i=idx: self._switch_workspace(i - 1))
            self.workspace_buttons.append(btn)
            layout.addWidget(btn)
        self.workspace_buttons[0].setChecked(True)

        layout.addStretch(1)
        self.clock_label = QLabel("-- --- --:--")
        self.clock_label.setObjectName("topCenterStatus")
        apply_ui_font(self.clock_label, size=11, weight=QFont.Weight.DemiBold, tabular=True)
        layout.addWidget(self.clock_label)
        layout.addStretch(1)

        self.tray_hash = QLabel("-- MH/s")
        self.tray_hash.setObjectName("trayLabel")
        self.tray_net = QLabel("net --ms")
        self.tray_net.setObjectName("trayLabel")
        self.tray_gpu = QLabel("gpu --C")
        self.tray_gpu.setObjectName("trayLabel")
        self.tray_wallet = QLabel("ALGO --")
        self.tray_wallet.setObjectName("trayLabel")
        for label in (self.tray_hash, self.tray_net, self.tray_gpu, self.tray_wallet):
            apply_ui_font(label, size=11, weight=QFont.Weight.Medium, tabular=True)
        layout.addWidget(self.tray_hash)
        layout.addWidget(self.tray_net)
        layout.addWidget(self.tray_gpu)
        layout.addWidget(self.tray_wallet)

        shell_minimize = QToolButton()
        shell_minimize.setObjectName("shellControl")
        shell_minimize.setText("−")
        shell_minimize.setToolTip("Minimize")
        shell_minimize.clicked.connect(self.minimize_requested.emit)
        layout.addWidget(shell_minimize)

        shell_close = QToolButton()
        shell_close.setObjectName("shellControlClose")
        shell_close.setText("×")
        shell_close.setToolTip("Close")
        shell_close.clicked.connect(self.close_requested.emit)
        layout.addWidget(shell_close)

        return top

    def _build_desktop_shortcuts(self) -> QFrame:
        container = QFrame()
        container.setObjectName("desktopShortcuts")
        container.setFixedWidth(1)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        return container

    def _build_workspaces(self) -> QStackedWidget:
        self.workspace_stack = QStackedWidget()
        self.workspace_stack.addWidget(self._workspace_one())
        self.workspace_stack.addWidget(self._workspace_two())
        self.workspace_stack.addWidget(self._workspace_three())
        return self.workspace_stack

    def _workspace_one(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 2, 0)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 14, 0)
        top_row.addStretch(1)
        self.algorand_panel = self._build_algorand_panel()
        top_row.addWidget(self.algorand_panel)
        self.balance_strip = BalanceStripWidget()
        self.balance_strip.setFixedWidth(382)
        top_row.addWidget(self.balance_strip)
        layout.addLayout(top_row)

        home_hint = QLabel("Opportunity home is ready. Open apps from Start.")
        home_hint.setObjectName("minorText")
        layout.addWidget(home_hint, alignment=Qt.AlignmentFlag.AlignHCenter)

        files = FileManagerPanel()
        self.files_window = PanelWindow(
            "Home",
            themed_icon(("system-file-manager-symbolic",), QStyle.StandardPixmap.SP_DirIcon, self),
            files,
        )
        self.files_window.hide()
        layout.addWidget(self.files_window, 1)
        return page

    def _build_algorand_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("algorandWalletPanel")
        panel.setFixedSize(310, 108)
        panel.setStyleSheet(
            "QFrame#algorandWalletPanel {"
            "background: rgba(20, 20, 30, 0.82);"
            "border: 1px solid rgba(0, 240, 255, 170);"
            "border-radius: 15px;"
            "}"
        )

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 10, 14, 10)
        panel_layout.setSpacing(3)

        title = QLabel("Algorand TestNet")
        title.setStyleSheet("color: #7D8094;")
        apply_ui_font(title, size=11, weight=QFont.Weight.Medium)
        panel_layout.addWidget(title)

        self.lbl_algo_address = QLabel("Wallet: Syncing...")
        self.lbl_algo_address.setStyleSheet("color: #7D8094;")
        apply_ui_font(self.lbl_algo_address, size=10, weight=QFont.Weight.Medium, tabular=True)
        panel_layout.addWidget(self.lbl_algo_address)

        self.lbl_algo_balance = QLabel("0.000 ALGO")
        self.lbl_algo_balance.setStyleSheet("color: #00F0FF;")
        apply_ui_font(self.lbl_algo_balance, size=20, weight=QFont.Weight.Bold, tabular=True)
        panel_layout.addWidget(self.lbl_algo_balance)

        self.lbl_algo_status = QLabel("Sync: waiting")
        self.lbl_algo_status.setStyleSheet("color: #7D8094;")
        apply_ui_font(self.lbl_algo_status, size=9, weight=QFont.Weight.Medium, tabular=True)
        panel_layout.addWidget(self.lbl_algo_status)
        return panel

    def _start_blockchain_sync(self) -> None:
        if WalletSyncThread is None:
            if self.lbl_algo_address is not None:
                self.lbl_algo_address.setText("Wallet: SDK unavailable")
            if self.lbl_algo_status is not None:
                self.lbl_algo_status.setText("Sync: unavailable")
            return
        if self._algorand_sync_thread is not None and self._algorand_sync_thread.isRunning():
            return

        thread = WalletSyncThread(poll_interval_sec=4, parent=self)
        thread.address_loaded.connect(self._on_algorand_address_loaded)
        thread.balance_updated.connect(self._on_algorand_balance_updated)
        thread.sync_error.connect(self._on_algorand_sync_error)
        thread.sync_tick.connect(self._on_algorand_sync_tick)
        thread.start()
        self._algorand_sync_thread = thread

    def _on_algorand_address_loaded(self, address: str) -> None:
        self._algorand_address = address
        short_addr = f"{address[:6]}...{address[-4:]}" if len(address) > 12 else address
        if self.lbl_algo_address is not None:
            self.lbl_algo_address.setText(f"Wallet: {short_addr}")
        self._log(f"Algorand wallet loaded: {short_addr}")

    def _on_algorand_balance_updated(self, balance: float) -> None:
        self._algorand_balance = float(balance)
        self._external_wallet_balance = float(balance)
        self._external_wallet_pending = 0.0
        if self.lbl_algo_balance is not None:
            self.lbl_algo_balance.setText(f"{balance:.3f} ALGO")
        snapshot = self.balance_strip.update_telemetry(
            self.telemetry,
            mining_active=self.mining_active,
            accuracy=self.training_accuracy,
            external_balance=float(balance),
            external_pending=0.0,
        )
        self.tray_wallet.setText(f"ALGO {snapshot.balance:.2f}")
        for panel in self.dashboard_panels:
            panel.update_telemetry(
                self.telemetry,
                mining_active=self.mining_active,
                accuracy=self.training_accuracy,
                pnl_per_hour=snapshot.pnl_per_hour,
            )
        self._write_algorand_wallet_state(float(balance))

    def _on_algorand_sync_error(self, message: str) -> None:
        self._log(message)

    def _on_algorand_sync_tick(self, ok: bool, timestamp: str) -> None:
        self._algorand_last_sync_ok = bool(ok)
        self._algorand_last_sync_time = timestamp
        self.tray_wallet.setToolTip(f"Algorand sync: {'live' if ok else 'retrying'} at {timestamp}")
        if self.lbl_algo_status is None:
            return
        if ok:
            self.lbl_algo_status.setText(f"Sync: live {timestamp}")
            self.lbl_algo_status.setStyleSheet("color: #7D8094;")
        else:
            self.lbl_algo_status.setText(f"Sync: retrying {timestamp}")
            self.lbl_algo_status.setStyleSheet("color: #F2BE77;")

    def _write_algorand_wallet_state(self, balance: float) -> None:
        payload: dict[str, object] = {}
        try:
            sync_dir = self._wallet_sync_path.parent
            sync_dir.mkdir(parents=True, exist_ok=True)
            if self._wallet_sync_path.exists():
                try:
                    existing = json.loads(self._wallet_sync_path.read_text(encoding="utf-8"))
                    if isinstance(existing, dict):
                        payload.update(existing)
                except Exception:
                    payload = {}

            payload.update(
                {
                    "wallet_balance": round(float(balance), 6),
                    "pending_balance": 0.0,
                    "source": "algorand-testnet",
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                }
            )
            payload.setdefault("total_profit", 0.0)
            payload.setdefault("blocks_mined", 0)
            tmp_path = sync_dir / ".opportunity_wallet_state.tmp"
            tmp_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
            tmp_path.replace(self._wallet_sync_path)
        except Exception:
            return

    def _workspace_two(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        split = QSplitter(Qt.Orientation.Horizontal)
        dashboard = MiningDashboardPanel()
        dashboard.mode_requested.connect(self._apply_mode)
        self.dashboard_panels.append(dashboard)
        self.mining_window = PanelWindow(
            "Mining Dashboard",
            themed_icon(("utilities-system-monitor-symbolic",), QStyle.StandardPixmap.SP_ComputerIcon, self),
            dashboard,
        )
        self.mining_window.hide()
        split.addWidget(self.mining_window)

        terminal = TerminalPanel()
        terminal.command_issued.connect(self._handle_terminal_command)
        self.terminal_panels.append(terminal)
        self.terminal_window = PanelWindow(
            "Terminal",
            themed_icon(("utilities-terminal-symbolic",), QStyle.StandardPixmap.SP_TitleBarNormalButton, self),
            terminal,
        )
        self.terminal_window.hide()
        split.addWidget(self.terminal_window)
        split.setSizes((600, 500))
        layout.addWidget(split, 1)
        return page

    def _workspace_three(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        dashboard = MiningDashboardPanel()
        dashboard.mode_requested.connect(self._apply_mode)
        self.dashboard_panels.append(dashboard)
        self.monitor_window = PanelWindow(
            "Monitoring",
            themed_icon(("utilities-system-monitor-symbolic",), QStyle.StandardPixmap.SP_ComputerIcon, self),
            dashboard,
        )
        self.monitor_window.hide()
        layout.addWidget(self.monitor_window, 1)
        return page

    def _build_bottom_dock(self) -> QFrame:
        dock = QFrame()
        dock.setObjectName("bottomDock")
        dock.setFixedHeight(46)

        layout = QHBoxLayout(dock)
        layout.setContentsMargins(8, 1, 8, 1)
        layout.setSpacing(4)

        def _dock_button(
            tooltip: str,
            icon_names: tuple[str, ...],
            fallback: QStyle.StandardPixmap,
            callback,
        ) -> QToolButton:
            button = QToolButton()
            button.setObjectName("dockButton")
            button.setIcon(themed_icon(icon_names, fallback, self))
            button.setIconSize(QSize(22, 22))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            return button

        layout.addStretch(1)
        layout.addWidget(
            _dock_button(
                "Files",
                ("system-file-manager-symbolic",),
                QStyle.StandardPixmap.SP_DirIcon,
                self._open_files,
            )
        )
        layout.addWidget(
            _dock_button(
                "Terminal",
                ("asset:terminal", "utilities-terminal-symbolic"),
                QStyle.StandardPixmap.SP_TitleBarNormalButton,
                self._open_terminal,
            )
        )

        self.start_button = QToolButton()
        self.start_button.setIcon(themed_icon(("asset:logo",), QStyle.StandardPixmap.SP_ComputerIcon, self))
        self.start_button.setIconSize(QSize(24, 24))
        self.start_button.setObjectName("startButton")
        self.start_button.setToolTip("Opportunity OS")
        self.start_button.clicked.connect(self._show_app_menu)
        layout.addWidget(self.start_button)

        layout.addWidget(
            _dock_button(
                "Browser",
                ("asset:browser", "firefox"),
                QStyle.StandardPixmap.SP_BrowserReload,
                self._open_browser,
            )
        )
        layout.addWidget(
            _dock_button(
                "Settings",
                ("asset:settings", "preferences-system-symbolic"),
                QStyle.StandardPixmap.SP_FileDialogDetailedView,
                self._open_settings,
            )
        )
        layout.addStretch(1)
        return dock

    def _show_app_menu(self) -> None:
        menu = QMenu(self)
        menu.setObjectName("startMenu")
        menu.setMinimumWidth(280)

        title_action = QAction(themed_icon(("asset:logo",), QStyle.StandardPixmap.SP_ComputerIcon, self), "Opportunity OS", menu)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()

        entries = (
            ("Files", ("system-file-manager-symbolic",), QStyle.StandardPixmap.SP_DirIcon, self._open_files),
            ("Terminal", ("asset:terminal", "utilities-terminal-symbolic"), QStyle.StandardPixmap.SP_TitleBarNormalButton, self._open_terminal),
            ("Browser", ("asset:browser", "firefox"), QStyle.StandardPixmap.SP_BrowserReload, self._open_browser),
            ("Nurochain", ("asset:logo",), QStyle.StandardPixmap.SP_ComputerIcon, self._open_nurochain),
            ("Qubo", ("asset:qubo", "applications-engineering-symbolic"), QStyle.StandardPixmap.SP_ComputerIcon, self._open_qubo),
            ("Jupyter Notebook", ("asset:jupyter",), QStyle.StandardPixmap.SP_FileDialogInfoView, self._open_jupyter),
            ("Settings", ("asset:settings", "preferences-system-symbolic"), QStyle.StandardPixmap.SP_FileDialogDetailedView, self._open_settings),
            ("Mining Dashboard", ("utilities-system-monitor-symbolic",), QStyle.StandardPixmap.SP_ComputerIcon, self._open_mining_dashboard),
            ("Trash", ("asset:bin", "user-trash-symbolic"), QStyle.StandardPixmap.SP_TrashIcon, lambda: self._log("Trash opened")),
        )
        for label, icon_names, fallback, callback in entries:
            action = QAction(themed_icon(icon_names, fallback, self), label, menu)
            action.triggered.connect(callback)
            menu.addAction(action)

        menu.addSeparator()
        shutdown = QAction(
            themed_icon(("system-shutdown-symbolic",), QStyle.StandardPixmap.SP_TitleBarCloseButton, self),
            "Power Off",
            menu,
        )
        shutdown.triggered.connect(self.power_off_requested.emit)
        menu.addAction(shutdown)

        if self.start_button is None:
            menu.exec(self.mapToGlobal(QPoint(20, self.height() - 20)))
            return
        anchor = self.start_button.mapToGlobal(self.start_button.rect().topLeft())
        menu_height = menu.sizeHint().height()
        menu.exec(QPoint(anchor.x(), max(0, anchor.y() - menu_height - 8)))

    def _open_settings(self) -> None:
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()
        self._log("Settings opened")

    def _open_files(self) -> None:
        self._switch_workspace(0)
        if self.files_window is not None:
            self.files_window.show()
        self._log("Files opened")

    def _open_terminal(self) -> None:
        self._switch_workspace(1)
        if self.terminal_window is not None:
            self.terminal_window.show()
        self._log("Terminal opened")

    def _open_mining_dashboard(self) -> None:
        self._switch_workspace(1)
        if self.mining_window is not None:
            self.mining_window.show()
        self._log("Mining dashboard opened")

    def _open_browser(self) -> None:
        self.browser_dialog.show()
        self.browser_dialog.raise_()
        self.browser_dialog.activateWindow()
        self._log("Browser opened")

    def _open_jupyter(self) -> None:
        self.jupyter_dialog.show()
        self.jupyter_dialog.raise_()
        self.jupyter_dialog.activateWindow()
        self._log("Jupyter Notebook opened")

    def _open_nurochain(self) -> None:
        now = time.monotonic()
        if now - self._last_nurochain_launch < 1.2:
            self._log("Nurochain launch throttled")
            return

        if self._nurochain_process is not None and self._nurochain_process.poll() is None:
            self._log("Nurochain is already running")
            return

        root_dir = _runtime_root_dir()
        if getattr(sys, "frozen", False):
            exe_candidates = (
                root_dir / "NeuroChain.exe",
                root_dir / "neurochain_demo.exe",
                root_dir / "NeuroChain" / "NeuroChain.exe",
            )
            for candidate in exe_candidates:
                if not candidate.exists():
                    continue
                try:
                    self._nurochain_process = subprocess.Popen([str(candidate)], **_detached_process_kwargs(root_dir))  # noqa: S603
                    self._last_nurochain_launch = now
                    self._log("Nurochain launched")
                    return
                except Exception as exc:
                    self._log(f"Failed to launch Nurochain executable: {exc}")
                    return
            self._log("Nurochain executable not found in installation")
            return

        demo_script = root_dir / "neurochain_demo.py"
        if not demo_script.exists():
            self._log(f"Nurochain not found: {demo_script}")
            return

        venv_scripts = root_dir / ".venv" / "Scripts"
        venv_python = venv_scripts / "python.exe"
        venv_pythonw = venv_scripts / "pythonw.exe"

        if sys.platform.startswith("win"):
            system_python = Path(sys.executable)
            system_pythonw = system_python.with_name("pythonw.exe")
            if venv_pythonw.exists():
                python_executable = str(venv_pythonw)
            elif venv_python.exists():
                python_executable = str(venv_python)
            elif system_pythonw.exists():
                python_executable = str(system_pythonw)
            else:
                python_executable = str(system_python)
        else:
            python_executable = str(venv_python if venv_python.exists() else Path(sys.executable))

        try:
            self._nurochain_process = subprocess.Popen([python_executable, str(demo_script)], **_detached_process_kwargs(root_dir))  # noqa: S603
            self._last_nurochain_launch = now
            self._log("Nurochain launched")
        except Exception as exc:
            self._log(f"Failed to launch Nurochain: {exc}")

    def _open_qubo(self) -> None:
        now = time.monotonic()
        if now - self._last_qubo_launch < 1.2:
            self._log("Qubo launch throttled")
            return

        if self._qubo_process is not None and self._qubo_process.poll() is None:
            self._log("Qubo is already running")
            return

        root_dir = _runtime_root_dir()
        if getattr(sys, "frozen", False):
            exe_candidates = (
                root_dir / "Qubo.exe",
                root_dir / "Qubo" / "Qubo.exe",
            )
            for candidate in exe_candidates:
                if not candidate.exists():
                    continue
                try:
                    self._qubo_process = subprocess.Popen([str(candidate)], **_detached_process_kwargs(root_dir))  # noqa: S603
                    self._last_qubo_launch = now
                    self._log("Qubo launched")
                    return
                except Exception as exc:
                    self._log(f"Failed to launch Qubo executable: {exc}")
                    return
            self._log("Qubo executable not found in installation")
            return

        qubo_root = root_dir / "qubofinalprotype" / "qubofinalprotype" / "qubofinalprotype"
        qubo_script = qubo_root / "run_gui.py"
        if not qubo_script.exists():
            self._log(f"Qubo not found: {qubo_script}")
            return

        app_venv_scripts = qubo_root / ".venv" / "Scripts"
        app_venv_python = app_venv_scripts / "python.exe"
        app_venv_pythonw = app_venv_scripts / "pythonw.exe"

        root_venv_scripts = root_dir / ".venv" / "Scripts"
        root_venv_python = root_venv_scripts / "python.exe"
        root_venv_pythonw = root_venv_scripts / "pythonw.exe"

        system_python = Path(sys.executable)
        system_pythonw = system_python.with_name("pythonw.exe")

        def _probe_python(executable: Path) -> bool:
            if not executable.exists():
                return False
            probe_executable = executable
            if sys.platform.startswith("win") and executable.name.lower() == "pythonw.exe":
                paired = executable.with_name("python.exe")
                if paired.exists():
                    probe_executable = paired
            try:
                probe = subprocess.run(
                    [str(probe_executable), "-c", "import PyQt5"],
                    cwd=str(qubo_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=6,
                )
                return probe.returncode == 0
            except Exception:
                return False

        if sys.platform.startswith("win"):
            candidates = (
                app_venv_pythonw,
                app_venv_python,
                root_venv_pythonw,
                root_venv_python,
                system_pythonw,
                system_python,
            )
        else:
            candidates = (
                app_venv_python,
                root_venv_python,
                system_python,
            )

        python_executable = None
        for candidate in candidates:
            if _probe_python(candidate):
                python_executable = str(candidate)
                break

        if python_executable is None:
            self._log("No compatible Python found for Qubo (PyQt5 missing or invalid interpreter)")
            return

        try:
            self._qubo_process = subprocess.Popen([python_executable, str(qubo_script)], **_detached_process_kwargs(qubo_root))  # noqa: S603
            self._last_qubo_launch = now
            self._log("Qubo launched")
        except Exception as exc:
            self._log(f"Failed to launch Qubo: {exc}")

    def _switch_workspace(self, index: int) -> None:
        self.workspace_stack.setCurrentIndex(index)
        for pos, button in enumerate(self.workspace_buttons):
            button.setChecked(pos == index)
        self._log(f"Switched to workspace {index + 1}")

    def _apply_mode(self, mode: str) -> None:
        self.daemon.set_mode(mode)  # type: ignore[arg-type]
        self.mining_active = mode in {"autopilot", "gaming", "sleep"}
        self._log(f"Mode changed to {mode.upper()}")

    def _handle_terminal_command(self, command: str) -> None:
        cmd = command.strip().lower()
        if cmd == "start-miner":
            self._apply_mode("autopilot")
            self._open_mining_dashboard()
            self._log("Miner started in auto-pilot")
        elif cmd == "stop-miner":
            self._apply_mode("balanced")
            self._log("Miner stopped; balanced mode active")
        elif cmd == "switch-coin":
            self._log("Switched to most profitable coin")
        elif cmd == "check-gpu":
            self._log(f"GPU {self.telemetry.gpu_temp_c:.1f}C | load {self.telemetry.gpu_load_percent:.1f}%")
        elif cmd == "wallet-balance":
            snap = self.balance_strip.snapshot
            self._log(f"Balance {snap.balance:.2f} ALGO | Pending {snap.pending:.2f}")
        elif cmd == "system-status":
            self._log(
                f"CPU {self.telemetry.cpu_temp_c:.1f}C | GPU {self.telemetry.gpu_temp_c:.1f}C | "
                f"NET {self.telemetry.net_latency_ms:.1f}ms"
            )
        else:
            self._log("Unknown command")

    def _log(self, message: str) -> None:
        for terminal in self.terminal_panels:
            terminal.write_line(message)

    def _read_external_wallet_state(self) -> tuple[float | None, float | None]:
        try:
            stat = self._wallet_sync_path.stat()
        except OSError:
            return self._external_wallet_balance, self._external_wallet_pending

        marker = (int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000))), int(stat.st_size))
        if marker == self._wallet_sync_marker:
            return self._external_wallet_balance, self._external_wallet_pending

        try:
            payload = json.loads(self._wallet_sync_path.read_text(encoding="utf-8"))
        except Exception:
            return self._external_wallet_balance, self._external_wallet_pending

        balance = payload.get("wallet_balance")
        pending = payload.get("pending_balance")

        if isinstance(balance, (int, float)):
            self._external_wallet_balance = float(balance)
        if isinstance(pending, (int, float)):
            self._external_wallet_pending = float(pending)

        self._wallet_sync_marker = marker
        return self._external_wallet_balance, self._external_wallet_pending

    def refresh(self) -> None:
        self.telemetry = self.daemon.get_telemetry()
        self.missions = self.daemon.get_missions()
        self.training_accuracy = self._estimate_accuracy(self.telemetry)

        hashrate = self.telemetry.gpu_load_percent * 0.92
        self.clock_label.setText(_clock_text(datetime.now()))
        self.tray_hash.setText(f"{hashrate:.1f} MH/s")
        self.tray_net.setText(f"net {self.telemetry.net_latency_ms:.0f}ms")
        self.tray_gpu.setText(f"gpu {self.telemetry.gpu_temp_c:.0f}C")
        if self.telemetry.gpu_temp_c >= 85:
            state = "hot"
        elif self.telemetry.gpu_temp_c >= 78:
            state = "warm"
        else:
            state = "normal"

        if state != self._gpu_tray_state:
            self._gpu_tray_state = state
            if state == "hot":
                self.tray_gpu.setStyleSheet("color: #F9858E;")
            elif state == "warm":
                self.tray_gpu.setStyleSheet("color: #F2BE77;")
            else:
                self.tray_gpu.setStyleSheet("color: #A7E0B0;")

        external_balance, external_pending = self._read_external_wallet_state()
        if self._algorand_balance is not None:
            external_balance = self._algorand_balance
            external_pending = 0.0

        snapshot = self.balance_strip.update_telemetry(
            self.telemetry,
            mining_active=self.mining_active,
            accuracy=self.training_accuracy,
            external_balance=external_balance,
            external_pending=external_pending,
        )
        self.tray_wallet.setText(f"ALGO {snapshot.balance:.2f}")
        for panel in self.dashboard_panels:
            panel.update_telemetry(
                self.telemetry,
                mining_active=self.mining_active,
                accuracy=self.training_accuracy,
                pnl_per_hour=snapshot.pnl_per_hour,
            )

    def _estimate_accuracy(self, telemetry) -> float:
        raw = (
            0.62
            + (telemetry.gpu_load_percent / 100.0) * 0.34
            - max(0.0, telemetry.net_latency_ms - 45.0) * 0.0014
            - max(0.0, telemetry.gpu_temp_c - 82.0) * 0.002
        )
        raw = max(0.40, min(0.995, raw))
        if self.training_accuracy <= 0:
            return raw
        return (self.training_accuracy * 0.78) + (raw * 0.22)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_1:
                self._switch_workspace(0)
                return
            if event.key() == Qt.Key.Key_2:
                self._switch_workspace(1)
                return
            if event.key() == Qt.Key.Key_3:
                self._switch_workspace(2)
                return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = QMenu(self)
        open_start = QAction("Open Applications", self)
        open_start.triggered.connect(self._show_app_menu)
        open_files = QAction("Open Files", self)
        open_files.triggered.connect(self._open_files)
        open_terminal = QAction("Open Terminal", self)
        open_terminal.triggered.connect(self._open_terminal)
        open_browser = QAction("Open Browser", self)
        open_browser.triggered.connect(self._open_browser)
        open_nurochain = QAction("Open Nurochain", self)
        open_nurochain.triggered.connect(self._open_nurochain)
        open_qubo = QAction("Open Qubo", self)
        open_qubo.triggered.connect(self._open_qubo)
        open_settings = QAction("Open Settings", self)
        open_settings.triggered.connect(self._open_settings)
        open_jupyter = QAction("Open Jupyter Notebook", self)
        open_jupyter.triggered.connect(self._open_jupyter)
        perf_lock = QAction("Enable Performance Lock", self)
        perf_lock.triggered.connect(lambda: self._apply_mode("gaming"))

        menu.addAction(open_start)
        menu.addSeparator()
        menu.addAction(open_files)
        menu.addAction(open_terminal)
        menu.addAction(open_browser)
        menu.addAction(open_nurochain)
        menu.addAction(open_qubo)
        menu.addAction(open_jupyter)
        menu.addAction(open_settings)
        menu.addSeparator()
        menu.addAction(perf_lock)
        menu.exec(event.globalPos())

    def shutdown(self) -> None:
        self.jupyter_dialog.shutdown_server()
        if self._algorand_sync_thread is not None and self._algorand_sync_thread.isRunning():
            self._algorand_sync_thread.requestInterruption()
            self._algorand_sync_thread.wait(2500)
        self._algorand_sync_thread = None

    def reset_home(self) -> None:
        for window in (self.files_window, self.terminal_window, self.mining_window, self.monitor_window):
            if window is not None:
                window.hide()
        self._switch_workspace(0)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painted = _paint_wallpaper_fill(painter, self._wallpaper, self.size(), self._wallpaper_cache)
        if not painted:
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor("#2A2139"))
            gradient.setColorAt(0.35, QColor("#A13D87"))
            gradient.setColorAt(0.62, QColor("#E05B86"))
            gradient.setColorAt(1.0, QColor("#2D2C7F"))
            painter.fillRect(self.rect(), gradient)

        overlay = QLinearGradient(0, 0, 0, self.height())
        overlay.setColorAt(0.0, QColor(23, 18, 36, 75))
        overlay.setColorAt(0.55, QColor(16, 14, 31, 120))
        overlay.setColorAt(1.0, QColor(11, 10, 26, 185))
        painter.fillRect(self.rect(), overlay)
