#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo ./install_script.sh"
  exit 1
fi

echo "[DIG OS] Installing base dependencies..."
pacman -Syu --noconfirm
pacman -S --noconfirm \
  base-devel \
  git \
  curl \
  wget \
  python \
  python-pip \
  python-virtualenv \
  qt6-base \
  qt6-svg \
  rustup \
  clang \
  cmake \
  pkgconf \
  jq \
  iptables-nft \
  flatpak

echo "[DIG OS] Bootstrapping Rust toolchain..."
if ! command -v cargo >/dev/null 2>&1; then
  rustup default stable
fi

echo "[DIG OS] Enabling cgroups v2 recommendation..."
echo "Ensure kernel cmdline includes: systemd.unified_cgroup_hierarchy=1"

echo "[DIG OS] Optional GPU stack install..."
echo "NVIDIA: pacman -S --noconfirm nvidia nvidia-utils cuda"
echo "AMD ROCm: pacman -S --noconfirm rocm-opencl-runtime rocminfo"

echo "[DIG OS] Installing UI and worker dependencies..."
pushd "$(dirname "$0")/ui_shell" >/dev/null
python -m pip install -r requirements.txt
popd >/dev/null

pushd "$(dirname "$0")/ai_worker" >/dev/null
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python setup.py build_ext --inplace
popd >/dev/null

echo "[DIG OS] Completed. Start services with:"
echo "  1) cd dig_os/rust_daemon && cargo run"
echo "  2) cd dig_os/ai_worker && python scripts/run_worker.py"
echo "  3) cd dig_os/ui_shell && python main.py"
