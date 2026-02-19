# DIG Rust Daemon

Rust control-plane daemon for DIG OS.

## Responsibilities

- Expose telemetry API (`/api/v1/telemetry`)
- Expose runtime controls (`/api/v1/mode`)
- Publish mission catalog (`/api/v1/missions`)
- Enforce thermal throttle policy
- Apply cgroups v2 resource reservations (Linux)

## Run

```bash
cd dig_os/rust_daemon
cargo run
```

## Environment Variables

- `DIG_DAEMON_ADDR` (default `127.0.0.1:7788`)
- `DIG_POLL_INTERVAL_MS` (default `1000`)
- `DIG_THERMAL_LIMIT_C` (default `85`)
- `DIG_UI_RESERVED_CPU_PERCENT` (default `5`)
- `DIG_UI_RESERVED_GPU_PERCENT` (default `5`)

