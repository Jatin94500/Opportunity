from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QThread, Signal

from core.wallet import AlgorandWallet


class WalletSyncThread(QThread):
    balance_updated = Signal(float)
    address_loaded = Signal(str)
    sync_error = Signal(str)
    sync_tick = Signal(bool, str)

    def __init__(self, poll_interval_sec: int = 10, parent=None) -> None:
        super().__init__(parent)
        self.poll_interval_sec = max(2, int(poll_interval_sec))
        self.wallet: AlgorandWallet | None = None

    def run(self) -> None:
        try:
            self.wallet = AlgorandWallet()
        except Exception as exc:
            self.sync_error.emit(f"Algorand wallet init failed: {exc}")
            return

        if self.wallet.address:
            self.address_loaded.emit(self.wallet.address)

        while not self.isInterruptionRequested():
            try:
                live_balance = self.wallet.get_balance()
                if self.wallet.last_error:
                    self.sync_error.emit(f"Algorand balance sync failed: {self.wallet.last_error}")
                    self.sync_tick.emit(False, datetime.now().strftime("%H:%M:%S"))
                else:
                    self.balance_updated.emit(live_balance)
                    self.sync_tick.emit(True, datetime.now().strftime("%H:%M:%S"))
            except Exception as exc:
                self.sync_error.emit(f"Algorand balance sync failed: {exc}")
                self.sync_tick.emit(False, datetime.now().strftime("%H:%M:%S"))

            for _ in range(self.poll_interval_sec * 10):
                if self.isInterruptionRequested():
                    return
                self.msleep(100)
