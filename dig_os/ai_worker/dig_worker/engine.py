from __future__ import annotations

from datetime import datetime
import time

from .fallback_metrics import reward_from_metrics, update_metrics
from .models import Mission, MissionState

try:
    from .native.metrics import reward_from_metrics as native_reward_from_metrics
    from .native.metrics import update_metrics as native_update_metrics
except Exception:  # pragma: no cover
    native_reward_from_metrics = None
    native_update_metrics = None


class TrainingEngine:
    def __init__(self) -> None:
        self.use_native = native_update_metrics is not None and native_reward_from_metrics is not None

    def run_epoch(self, mission: Mission, state: MissionState, eco_multiplier: float) -> tuple[MissionState, float]:
        state.epoch += 1
        state.last_updated = datetime.utcnow()
        difficulty = self._difficulty_for_domain(mission.domain)

        if self.use_native:
            loss, accuracy = native_update_metrics(
                state.loss,
                state.accuracy,
                state.epoch,
                state.total_epochs,
                difficulty,
            )
        else:
            loss, accuracy = update_metrics(
                state.loss,
                state.accuracy,
                state.epoch,
                state.total_epochs,
                difficulty,
            )
        state.loss = float(loss)
        state.accuracy = float(accuracy)

        if self.use_native:
            reward = float(native_reward_from_metrics(mission.bounty_dig, state.accuracy, eco_multiplier))
        else:
            reward = float(reward_from_metrics(mission.bounty_dig, state.accuracy, eco_multiplier))

        # Simulate batch processing time; higher priority gets shorter scheduling delay.
        delay = max(0.15, 0.65 - (mission.priority / 220.0))
        time.sleep(delay)
        return state, reward

    @staticmethod
    def _difficulty_for_domain(domain: str) -> float:
        if domain == "medical":
            return 0.9
        if domain == "space":
            return 0.65
        if domain == "render":
            return 0.35
        return 0.5

