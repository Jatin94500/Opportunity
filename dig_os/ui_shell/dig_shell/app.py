from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from .daemon_client import DaemonClient
from .screens import BootScreen, DesktopScreen, LockScreen


class OpportunityShellWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Opportunity OS")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self._allow_close = False
        self.daemon = DaemonClient()

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.boot = BootScreen()
        self.lock = LockScreen()
        self.desktop = DesktopScreen(self.daemon)
        self.desktop.power_off_requested.connect(self._power_off)
        self.desktop.close_requested.connect(self._power_off)
        self.desktop.minimize_requested.connect(self.showMinimized)

        self.stack.addWidget(self.boot)
        self.stack.addWidget(self.lock)
        self.stack.addWidget(self.desktop)
        self.stack.setCurrentWidget(self.boot)

        self.boot.boot_complete.connect(self._show_lock)
        self.lock.unlocked.connect(self._show_desktop)

        self.lock_refresh = QTimer(self)
        self.lock_refresh.setInterval(2000)
        self.lock_refresh.timeout.connect(self._update_lock_earnings)
        self.lock_refresh.start()

        self.resize(1440, 900)

    def _show_lock(self) -> None:
        self.stack.setCurrentWidget(self.lock)

    def _show_desktop(self) -> None:
        self.desktop.reset_home()
        self.stack.setCurrentWidget(self.desktop)
        self.desktop.setFocus()
        self.desktop.refresh()

    def _update_lock_earnings(self) -> None:
        telemetry = self.daemon.get_telemetry()
        slept_earnings = max(50.0, telemetry.impact_score * 5.5)
        self.lock.set_sleep_earnings(slept_earnings)

    def _power_off(self) -> None:
        self.desktop.shutdown()
        self._allow_close = True
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._allow_close:
            event.accept()
            return
        event.ignore()


# Backward-compatible alias for existing imports.
NeurochainShellWindow = OpportunityShellWindow
