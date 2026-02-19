from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
import time

from .checkpoint import CheckpointStore
from .config import WorkerConfig
from .daemon_client import WorkerDaemonClient
from .engine import TrainingEngine
from .models import Mission, MissionState
from .scheduler import PriorityMissionQueue


class WorkerRuntime:
    def __init__(self, config: WorkerConfig) -> None:
        self.config = config
        self.client = WorkerDaemonClient(config.daemon_url)
        self.scheduler = PriorityMissionQueue()
        self.checkpoints = CheckpointStore(config.checkpoints_dir)
        self.engine = TrainingEngine()
        self.current_mission: Mission | None = None
        self.current_state: MissionState | None = None
        self.total_rewards: float = 0.0
        self.total_xp: int = 0
        self.last_mission_refresh = 0.0

    def run_forever(self) -> None:
        if self.config.verbose:
            print("[DIG-WORKER] Starting runtime")
            print(f"[DIG-WORKER] Daemon: {self.config.daemon_url}")
            print(f"[DIG-WORKER] Checkpoints: {self.config.checkpoints_dir.resolve()}")

        while True:
            now = time.time()
            if now - self.last_mission_refresh >= self.config.mission_refresh_seconds:
                self._refresh_missions()
                self.last_mission_refresh = now

            self._maybe_start_next_mission()
            self._run_current_epoch()
            time.sleep(self.config.poll_interval_seconds)

    def _refresh_missions(self) -> None:
        missions = self.client.get_missions()
        self.scheduler.push_many(missions)
        if self.config.verbose:
            print(f"[DIG-WORKER] Mission catalog refresh -> {len(missions)} entries")

        if self.current_mission and self.scheduler.should_preempt(
            self.current_mission,
            delta=self.config.preempt_delta_priority,
        ):
            if self.config.verbose:
                best = self.scheduler.peek_best()
                best_title = best.title if best else "Unknown"
                print(
                    f"[DIG-WORKER] Preempting {self.current_mission.title} "
                    f"for higher-value mission {best_title}"
                )
            self.scheduler.requeue(self.current_mission)
            self.current_mission = None
            self.current_state = None

    def _maybe_start_next_mission(self) -> None:
        if self.current_mission is not None:
            return

        mission = self.scheduler.pop_next()
        if mission is None:
            if self.config.verbose:
                print("[DIG-WORKER] No mission available. Idle cycle.")
            return

        checkpoint = self.checkpoints.latest(mission.id)
        if checkpoint:
            state_payload = checkpoint.get("state", {})
            state = MissionState(
                mission_id=mission.id,
                epoch=int(state_payload.get("epoch", 0)),
                total_epochs=mission.total_epochs,
                accuracy=float(state_payload.get("accuracy", 0.10)),
                loss=float(state_payload.get("loss", 1.0)),
                started_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
            )
            if self.config.verbose:
                print(
                    f"[DIG-WORKER] Restored checkpoint for {mission.title} at "
                    f"epoch {state.epoch}/{state.total_epochs}"
                )
        else:
            state = MissionState(
                mission_id=mission.id,
                total_epochs=mission.total_epochs,
            )
            if self.config.verbose:
                print(
                    f"[DIG-WORKER] Starting mission: {mission.title} | "
                    f"Priority {mission.priority} | Epochs {state.total_epochs}"
                )

        self.current_mission = mission
        self.current_state = state

    def _run_current_epoch(self) -> None:
        if self.current_mission is None or self.current_state is None:
            return

        eco_multiplier = self._eco_multiplier()
        mission = self.current_mission
        state = self.current_state

        updated_state, reward = self.engine.run_epoch(mission, state, eco_multiplier)
        self.current_state = updated_state
        self.total_rewards += reward / updated_state.total_epochs
        self.total_xp += max(1, int(updated_state.accuracy * 5))

        extra = {
            "reward_estimate": reward,
            "eco_multiplier": eco_multiplier,
            "mission": asdict(mission),
        }
        self.checkpoints.save(mission.id, updated_state, extra=extra)

        if self.config.verbose:
            print(
                f"[DIG-WORKER] {mission.title} | "
                f"Epoch {updated_state.epoch}/{updated_state.total_epochs} | "
                f"acc={updated_state.accuracy:.4f} loss={updated_state.loss:.4f}"
            )

        if updated_state.completed():
            payout = reward
            self.total_rewards += payout
            self.total_xp += int(payout / 2)
            if self.config.verbose:
                print(
                    f"[DIG-WORKER] VERIFIED {mission.title} | "
                    f"Reward +{payout:.2f} DIG | "
                    f"Session DIG={self.total_rewards:.2f} XP={self.total_xp}"
                )
            self._write_session_receipt(mission, updated_state, payout)
            self.current_mission = None
            self.current_state = None

    def _eco_multiplier(self) -> float:
        hour = datetime.now().hour
        if hour >= 22 or hour < 6:
            self.client.set_mode("sleep")
            return 1.15
        self.client.set_mode("balanced")
        return 0.92

    def _write_session_receipt(self, mission: Mission, state: MissionState, payout: float) -> None:
        receipt = {
            "mission_id": mission.id,
            "mission_title": mission.title,
            "finished_at": datetime.utcnow().isoformat() + "Z",
            "accuracy": round(state.accuracy, 6),
            "loss": round(state.loss, 6),
            "payout_dig": round(payout, 3),
            "session_total_rewards_dig": round(self.total_rewards, 3),
            "session_total_xp": self.total_xp,
        }
        out_file = self.config.checkpoints_dir / f"receipt-{mission.id}.json"
        out_file.write_text(json.dumps(receipt, indent=2), encoding="utf-8")


def run() -> None:
    config = WorkerConfig()
    runtime = WorkerRuntime(config)
    runtime.run_forever()

