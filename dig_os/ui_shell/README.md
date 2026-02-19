# Opportunity OS UI Shell (Python)

Native desktop shell built with **PySide6** (Qt for Python).

## Features in this scaffold

- Linux-style boot and login screens (top bar + password card)
- Top bar with Activities, workspace switching, time, mining tray stats, and shell controls
- Start-menu launcher with themed app icons (`Files`, `Terminal`, `Browser`, `Nurochain`, `Qubo`, `Jupyter`, `Settings`)
- Start-only bottom dock for cleaner layout
- Linux-style panel windows for Terminal, File Manager, and Mining Dashboard
- Desktop `Wallet Balance Strip` widget with live ALGO balance and profit/hr
- Mining telemetry panel with hashrate/temp charts, power/VRAM/profit estimates
- System logs routed to Terminal panels (not shown as a separate desktop log panel)
- Terminal commands: `start-miner`, `stop-miner`, `switch-coin`, `check-gpu`, `wallet-balance`, `system-status`
- File manager with Linux-like sidebar + permissions columns
- Settings dialog sections: `System`, `Mining`, `GPU`, `Network`, `Security`, `Wallet`, `Updates`, `Advanced`
- Jupyter notebook dialog app for mining session inspection
- Daemon integration with fallback mocks (`http://127.0.0.1:7788`)

## Run

```bash
cd dig_os/ui_shell
python -m pip install -r requirements.txt
python main.py
```
