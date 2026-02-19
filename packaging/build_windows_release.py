from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"
RELEASE_DIR = ROOT / "release"
PAYLOAD_DIR = RELEASE_DIR / "payload"
PAYLOAD_ZIP = RELEASE_DIR / "nurochain_payload.zip"


def _run(command: list[str]) -> None:
    print(">", " ".join(command))
    subprocess.run(command, cwd=str(ROOT), check=True)


def _run_pyinstaller(args: list[str]) -> None:
    _run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", *args])


def _copy_required_assets() -> None:
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)

    binaries = {
        "OpportunityOS.exe": DIST_DIR / "OpportunityOS.exe",
        "NeuroChain.exe": DIST_DIR / "NeuroChain.exe",
        "Qubo.exe": DIST_DIR / "Qubo.exe",
    }
    for target_name, source_path in binaries.items():
        if not source_path.exists():
            raise FileNotFoundError(f"Expected build output not found: {source_path}")
        shutil.copy2(source_path, PAYLOAD_DIR / target_name)

    shutil.copytree(ROOT / "dig_os" / "ui_shell" / "assets", PAYLOAD_DIR / "assets", dirs_exist_ok=True)
    shutil.copytree(ROOT / "datasets", PAYLOAD_DIR / "datasets", dirs_exist_ok=True)
    shutil.copytree(ROOT / "fonts", PAYLOAD_DIR / "fonts", dirs_exist_ok=True)

    image_file = ROOT / "image.png"
    if image_file.exists():
        shutil.copy2(image_file, PAYLOAD_DIR / "image.png")

    for wallpaper in ROOT.glob("wp877*"):
        shutil.copy2(wallpaper, PAYLOAD_DIR / wallpaper.name)

    runtime_dir = PAYLOAD_DIR / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    wallet_state = ROOT / "runtime" / "opportunity_wallet_state.json"
    if wallet_state.exists():
        shutil.copy2(wallet_state, runtime_dir / wallet_state.name)
    else:
        (runtime_dir / "opportunity_wallet_state.json").write_text(
            json.dumps(
                {
                    "wallet_balance": 0.0,
                    "pending_balance": 0.0,
                    "total_profit": 0.0,
                    "blocks_mined": 0,
                    "source": "install-default",
                    "updated_at": "1970-01-01T00:00:00Z",
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )


def _zip_payload() -> None:
    if PAYLOAD_ZIP.exists():
        PAYLOAD_ZIP.unlink()
    with zipfile.ZipFile(PAYLOAD_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in PAYLOAD_DIR.rglob("*"):
            if path.is_dir():
                continue
            archive.write(path, path.relative_to(PAYLOAD_DIR))


def _prepare_release_dir() -> None:
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)


def build_all() -> None:
    _prepare_release_dir()

    _run_pyinstaller(
        [
            "--onefile",
            "--windowed",
            "--name",
            "OpportunityOS",
            "--paths",
            str(ROOT / "dig_os" / "ui_shell"),
            "--hidden-import",
            "PySide6.QtWebEngineWidgets",
            "--hidden-import",
            "PySide6.QtWebEngineCore",
            "--exclude-module",
            "PyQt5",
            "--exclude-module",
            "PyQt6",
            str(ROOT / "dig_os" / "ui_shell" / "main.py"),
        ]
    )
    _run_pyinstaller(
        [
            "--onefile",
            "--windowed",
            "--name",
            "NeuroChain",
            "--exclude-module",
            "PyQt5",
            "--exclude-module",
            "PySide6",
            str(ROOT / "neurochain_demo.py"),
        ]
    )
    _run_pyinstaller(
        [
            "--onefile",
            "--windowed",
            "--name",
            "Qubo",
            "--paths",
            str(ROOT / "qubofinalprotype" / "qubofinalprotype" / "qubofinalprotype"),
            "--hidden-import",
            "matplotlib.backends.backend_qtagg",
            "--hidden-import",
            "matplotlib.backends.backend_qt5agg",
            "--exclude-module",
            "PyQt6",
            "--exclude-module",
            "PySide6",
            str(ROOT / "qubofinalprotype" / "qubofinalprotype" / "qubofinalprotype" / "run_gui.py"),
        ]
    )

    _copy_required_assets()
    _zip_payload()

    _run_pyinstaller(
        [
            "--onefile",
            "--name",
            "NuroChainSetup",
            "--add-data",
            f"{PAYLOAD_ZIP};.",
            str(ROOT / "packaging" / "windows_installer.py"),
        ]
    )

    setup_exe = DIST_DIR / "NuroChainSetup.exe"
    if not setup_exe.exists():
        raise FileNotFoundError(f"Installer output not found: {setup_exe}")
    shutil.copy2(setup_exe, RELEASE_DIR / "NuroChainSetup.exe")

    readme = RELEASE_DIR / "README.txt"
    readme.write_text(
        "NuroChain Opportunity OS - Windows Installer\n"
        "1. Share NuroChainSetup.exe.\n"
        "2. Run NuroChainSetup.exe on target machine.\n"
        "3. Default install path: %LOCALAPPDATA%\\NuroChain\n"
        "4. Desktop and Start Menu shortcuts are created automatically.\n"
        "5. Launch app via OpportunityOS.exe or 'Launch Opportunity OS.bat'.\n",
        encoding="utf-8",
    )

    print("\nBuild complete.")
    print(f"Installer: {RELEASE_DIR / 'NuroChainSetup.exe'}")


if __name__ == "__main__":
    try:
        build_all()
    except subprocess.CalledProcessError as exc:
        print(f"Build command failed with exit code {exc.returncode}")
        raise SystemExit(exc.returncode) from exc
