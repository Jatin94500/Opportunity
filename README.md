# NuroChain Opportunity OS

NuroChain Opportunity OS is a desktop shell + AI compute demo stack that combines:

- `Opportunity OS` desktop shell (PySide6) as the main experience.
- `NeuroChain` (PyQt6) as an in-OS app for useful-compute simulation and wallet updates.
- `Qubo` as an additional app entry.
- Windows packaging scripts for one-file app builds and installer generation.

## Main Components

- `dig_os/ui_shell/main.py`: main Opportunity OS launcher.
- `dig_os/ui_shell/dig_shell/`: UI shell screens, widgets, daemon client, app launcher logic.
- `dig_os/ui_shell/core/wallet.py`: Algorand TestNet wallet sync (`algod` via Algonode endpoint).
- `neurochain_demo.py`: standalone NeuroChain app.
- `qubofinalprotype/qubofinalprotype/qubofinalprotype/run_gui.py`: Qubo app entry.
- `packaging/build_windows_release.py`: builds `OpportunityOS.exe`, `NeuroChain.exe`, `Qubo.exe`, and installer.
- `packaging/windows_installer.py`: installer runtime logic and shortcut creation.

## Key Runtime Files

- `runtime/opportunity_wallet_state.json`: shared wallet/metrics state between UI shell and apps.
- `data/keystore.json`: local Algorand wallet keystore created on first run.
- `datasets/`: datasets used by NeuroChain tasks.

## Prerequisites

- Windows 10/11
- Python 3.11+ (3.13 works in this repo)
- Git + Git LFS

## Setup

1. Clone repository:

```bat
git clone https://github.com/Jatin94500/Opportunity.git
cd Opportunity
```

2. Enable Git LFS and fetch large files:

```bat
git lfs install
git lfs pull
```

3. Create and activate virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate
```

4. Install UI shell dependencies:

```bat
pip install -r dig_os\ui_shell\requirements.txt
```

5. Install NeuroChain dependencies:

```bat
pip install numpy pandas scikit-learn PyQt6 pyqtgraph qtawesome
```

6. Optional (Qubo runtime dependencies if needed):

```bat
pip install pyqt5 matplotlib
```

## Run

Run main Opportunity OS:

```bat
.venv\Scripts\python.exe dig_os\ui_shell\main.py
```

Run NeuroChain directly:

```bat
.venv\Scripts\python.exe neurochain_demo.py
```

## Build Windows Release

Build apps and installer:

```bat
.venv\Scripts\python.exe packaging\build_windows_release.py
```

Expected outputs:

- `dist/OpportunityOS.exe`
- `dist/NeuroChain.exe`
- `dist/Qubo.exe`
- `release/NuroChainSetup.exe`

## Algorand Notes

- Default endpoint is Algonode TestNet in `dig_os/ui_shell/core/wallet.py`.
- Override endpoint with `NUROCHAIN_ALGOD_ADDRESS`.
- Override token with `NUROCHAIN_ALGOD_TOKEN`.
- Wallet sync status is shown in the OS top panel and written into `runtime/opportunity_wallet_state.json`.

## Daemon Telemetry Notes

- UI shell tries `http://127.0.0.1:7788` for live telemetry.
- If unavailable, shell automatically falls back to mock telemetry so UI still runs.

## Troubleshooting

- If app launches but UI does not appear, check `Alt+Tab` and ensure no hidden instance is running.
- If `algosdk` import fails, run with the project venv interpreter (`.venv\Scripts\python.exe`).
- If clone is missing large binaries, run `git lfs pull`.
- If packaging fails, verify `PyInstaller` is installed in `.venv`.
