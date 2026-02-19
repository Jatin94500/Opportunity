# DIG OS (Decentralized Intelligence Grid)

DIG OS is a sovereign desktop shell stack that pairs:

- `rust_daemon/`: hardware telemetry, workload policy, thermal protection, and control API
- `ui_shell/`: native Python (PySide6) "Nebula Glass" desktop shell experience
- `ai_worker/`: Python + Cython useful-compute worker with checkpointing and mission scheduling
- `install_script.sh`: base provisioning script for Arch Linux systems

This repository is a production-oriented scaffold, not a full Linux distro image. It is designed so each layer can run independently during development and integrate into a custom Arch-based distribution pipeline.

## Quick Start (Development)

1. Start daemon:
   - `cd dig_os/rust_daemon`
   - `cargo run`
2. Build Cython module and start worker:
   - `cd dig_os/ai_worker`
   - `python -m pip install -r requirements.txt`
   - `python setup.py build_ext --inplace`
   - `python scripts/run_worker.py`
3. Start UI shell:
   - `cd dig_os/ui_shell`
   - `python -m pip install -r requirements.txt`
   - `python main.py`

## System Design

- UI responsiveness strategy: reserve resources for shell via cgroups v2
- Thermal strategy: if GPU junction temp exceeds threshold, throttle worker allocations
- Mission strategy: priority queue with high-value preemption and epoch checkpoint restore
- UX language: Nebula Glass (deep blur, neon accents, full-screen overlays)
