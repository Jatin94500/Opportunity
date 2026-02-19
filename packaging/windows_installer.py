from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

APP_NAME = "NuroChain Opportunity OS"
PAYLOAD_FILE = "nurochain_payload.zip"
SHORTCUT_FOLDER_NAME = "NuroChain Opportunity OS"


def _default_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "NuroChain"
    return Path.home() / "NuroChain"


def _default_desktop_dir() -> Path:
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        return Path(user_profile) / "Desktop"
    return Path.home() / "Desktop"


def _default_start_menu_programs_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def _payload_candidates() -> list[Path]:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / PAYLOAD_FILE)
        candidates.append(Path(sys.executable).resolve().parent / PAYLOAD_FILE)
    candidates.append(Path(__file__).resolve().with_name(PAYLOAD_FILE))
    return candidates


def _resolve_payload_path() -> Path:
    for candidate in _payload_candidates():
        if candidate.exists():
            return candidate
    searched = "\n".join(str(path) for path in _payload_candidates())
    raise FileNotFoundError(f"Unable to locate installer payload.\nChecked:\n{searched}")


def _copy_tree_contents(source: Path, destination: Path) -> None:
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def _ensure_runtime_defaults(install_dir: Path) -> None:
    runtime_dir = install_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    wallet_state = runtime_dir / "opportunity_wallet_state.json"
    if wallet_state.exists():
        return
    wallet_state.write_text(
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


def _write_launcher(install_dir: Path) -> None:
    launcher = install_dir / "Launch Opportunity OS.bat"
    launcher.write_text(
        "@echo off\r\n"
        "cd /d \"%~dp0\"\r\n"
        "start \"\" \"OpportunityOS.exe\"\r\n",
        encoding="utf-8",
    )


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _create_windows_shortcut(link_path: Path, target_path: Path, working_dir: Path) -> bool:
    icon_value = f"{target_path},0"
    script = (
        "$ErrorActionPreference='Stop';"
        "$shell=New-Object -ComObject WScript.Shell;"
        f"$shortcut=$shell.CreateShortcut({_ps_quote(str(link_path))});"
        f"$shortcut.TargetPath={_ps_quote(str(target_path))};"
        f"$shortcut.WorkingDirectory={_ps_quote(str(working_dir))};"
        f"$shortcut.IconLocation={_ps_quote(icon_value)};"
        "$shortcut.Save();"
    )
    for shell_executable in ("powershell", "pwsh"):
        try:
            subprocess.run(
                [
                    shell_executable,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            continue
    return False


def _write_batch_shortcut(path: Path, target_path: Path, working_dir: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "@echo off\r\n"
        f"cd /d \"{working_dir}\"\r\n"
        f"start \"\" \"{target_path}\"\r\n",
        encoding="utf-8",
    )


def _create_shortcuts(
    install_dir: Path,
    desktop_dir: Path | None = None,
    start_menu_dir: Path | None = None,
) -> list[Path]:
    created: list[Path] = []
    desktop_root = (desktop_dir or _default_desktop_dir()).resolve()
    start_menu_root = (start_menu_dir or _default_start_menu_programs_dir()).resolve()
    start_menu_folder = start_menu_root / SHORTCUT_FOLDER_NAME

    app_entries = (
        ("Opportunity OS", install_dir / "OpportunityOS.exe"),
        ("NeuroChain", install_dir / "NeuroChain.exe"),
        ("Qubo", install_dir / "Qubo.exe"),
    )

    desktop_root.mkdir(parents=True, exist_ok=True)
    main_target = install_dir / "OpportunityOS.exe"
    if main_target.exists():
        desktop_link = desktop_root / f"{SHORTCUT_FOLDER_NAME}.lnk"
        if _create_windows_shortcut(desktop_link, main_target, install_dir):
            created.append(desktop_link)
        else:
            desktop_bat = desktop_root / f"{SHORTCUT_FOLDER_NAME}.bat"
            _write_batch_shortcut(desktop_bat, main_target, install_dir)
            created.append(desktop_bat)

    start_menu_folder.mkdir(parents=True, exist_ok=True)
    for label, target in app_entries:
        if not target.exists():
            continue
        link_path = start_menu_folder / f"{label}.lnk"
        if _create_windows_shortcut(link_path, target, install_dir):
            created.append(link_path)
            continue
        bat_path = start_menu_folder / f"{label}.bat"
        _write_batch_shortcut(bat_path, target, install_dir)
        created.append(bat_path)
    return created


def install(payload_zip: Path, install_dir: Path) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nurochain_setup_") as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(payload_zip, "r") as archive:
            archive.extractall(temp_root)
        _copy_tree_contents(temp_root, install_dir)

    _ensure_runtime_defaults(install_dir)
    _write_launcher(install_dir)


def _launch_app(install_dir: Path) -> None:
    executable = install_dir / "OpportunityOS.exe"
    if not executable.exists():
        return
    kwargs: dict[str, object] = {"cwd": str(install_dir)}
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen([str(executable)], **kwargs)  # noqa: S603


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} installer")
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=_default_install_dir(),
        help="Installation target directory",
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Do not launch OpportunityOS.exe after installation",
    )
    parser.add_argument(
        "--no-shortcuts",
        action="store_true",
        help="Skip Desktop and Start Menu shortcut creation",
    )
    parser.add_argument(
        "--desktop-dir",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--start-menu-dir",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    install_dir = args.install_dir.resolve()
    print(f"{APP_NAME} setup")
    print(f"Target directory: {install_dir}")
    try:
        payload_path = _resolve_payload_path()
        print(f"Payload: {payload_path}")
        install(payload_path, install_dir)
    except Exception as exc:
        print(f"Installation failed: {exc}")
        return 1

    print("Installation complete.")
    print(f"Main app: {install_dir / 'OpportunityOS.exe'}")
    print(f"NeuroChain app: {install_dir / 'NeuroChain.exe'}")
    print(f"Qubo app: {install_dir / 'Qubo.exe'}")
    if not args.no_shortcuts:
        try:
            shortcuts = _create_shortcuts(
                install_dir,
                desktop_dir=args.desktop_dir,
                start_menu_dir=args.start_menu_dir,
            )
            if shortcuts:
                print("Shortcuts created:")
                for shortcut in shortcuts:
                    print(f"- {shortcut}")
        except Exception as exc:
            print(f"Shortcut creation warning: {exc}")
    if not args.no_launch:
        _launch_app(install_dir)
        print("Opportunity OS launched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
