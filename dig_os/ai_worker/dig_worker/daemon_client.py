from __future__ import annotations

import time
from typing import Any

import requests

from .models import Mission


class WorkerDaemonClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def get_missions(self) -> list[Mission]:
        try:
            response = self.session.get(f"{self.base_url}/api/v1/missions", timeout=0.8)
            response.raise_for_status()
            payload = response.json()
            return [Mission.from_api(item) for item in payload]
        except Exception:
            return self._fallback_missions()

    def set_mode(self, mode: str) -> None:
        try:
            self.session.post(
                f"{self.base_url}/api/v1/mode",
                json={"mode": mode},
                timeout=0.8,
            ).raise_for_status()
        except Exception:
            return

    def _fallback_missions(self) -> list[Mission]:
        t = int(time.time())
        priorities = [100, 55, 20]
        drift = [0, (t // 15) % 5, (t // 20) % 4]
        return [
            Mission(
                id="med-pancreas-001",
                title="Pancreatic Cancer Detection",
                bounty_dig=500,
                dataset_gb=4.2,
                eta_minutes=12,
                priority=priorities[0] + drift[0],
                domain="medical",
            ),
            Mission(
                id="space-exoplanet-004",
                title="Exoplanet Atmosphere Analysis",
                bounty_dig=120,
                dataset_gb=2.1,
                eta_minutes=7,
                priority=priorities[1] + drift[1],
                domain="space",
            ),
            Mission(
                id="render-cyberpunk-2099",
                title="Render Cyberpunk 2099 Frame",
                bounty_dig=50,
                dataset_gb=1.4,
                eta_minutes=4,
                priority=priorities[2] + drift[2],
                domain="render",
            ),
        ]

