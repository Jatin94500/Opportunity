from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

_BOOTSTRAP_ENV = "NUROCHAIN_UI_VENV_BOOTSTRAPPED"


def _project_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _venv_python_path() -> Path:
    root = _project_root_dir()
    if sys.platform.startswith("win"):
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def _missing_runtime_modules() -> list[str]:
    required = ("PySide6", "algosdk")
    return [name for name in required if importlib.util.find_spec(name) is None]


def _ensure_runtime_python() -> None:
    if getattr(sys, "frozen", False):
        return
    if os.environ.get(_BOOTSTRAP_ENV) == "1":
        return
    if not _missing_runtime_modules():
        return

    candidate = _venv_python_path()
    if not candidate.exists():
        return
    if Path(sys.executable).resolve() == candidate.resolve():
        return

    os.environ[_BOOTSTRAP_ENV] = "1"
    args = [str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]]
    try:
        os.execv(args[0], args)
    except OSError:
        return


_ensure_runtime_python()

from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from dig_shell.app import OpportunityShellWindow
from dig_shell.theme import build_stylesheet


def _runtime_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _bundle_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
    return Path(__file__).resolve().parent


def _resolve_asset(*parts: str) -> Path:
    relative = Path(*parts)
    for base in (_runtime_root_dir(), _bundle_base_dir()):
        candidate = base / relative
        if candidate.exists():
            return candidate
    return _runtime_root_dir() / relative


def _bootstrap_ui_font(app: QApplication) -> QFont:
    default_font = QFont("Inter", 11)
    font_path = _resolve_asset("assets", "fonts", "Inter-Variable.ttf")
    if not font_path.exists():
        return default_font

    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id < 0:
        return default_font

    families = QFontDatabase.applicationFontFamilies(font_id)
    if families:
        default_font = QFont(families[0], 11)
    default_font.setWeight(QFont.Weight.Normal)
    return default_font


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Opportunity OS Shell")
    app.setStyleSheet(build_stylesheet())
    app.setFont(_bootstrap_ui_font(app))

    logo = _resolve_asset("assets", "icons", "logo-o.png")
    if logo.exists():
        app.setWindowIcon(QIcon(str(logo)))

    window = OpportunityShellWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
