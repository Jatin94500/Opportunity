from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import time

from .models import Mission


@dataclass(order=True)
class QueueEntry:
    sort_index: tuple[int, float] = field(init=False, repr=False)
    priority: int
    inserted_at: float
    mission: Mission = field(compare=False)

    def __post_init__(self) -> None:
        # max-heap behavior using min-heap primitive
        self.sort_index = (-self.priority, self.inserted_at)


class PriorityMissionQueue:
    def __init__(self) -> None:
        self._heap: list[QueueEntry] = []
        self._known: set[str] = set()

    def push_many(self, missions: list[Mission]) -> None:
        now = time.time()
        for mission in missions:
            if mission.id in self._known:
                continue
            self._known.add(mission.id)
            heapq.heappush(
                self._heap,
                QueueEntry(priority=mission.priority, inserted_at=now, mission=mission),
            )

    def pop_next(self) -> Mission | None:
        if not self._heap:
            return None
        entry = heapq.heappop(self._heap)
        self._known.discard(entry.mission.id)
        return entry.mission

    def peek_best(self) -> Mission | None:
        if not self._heap:
            return None
        return self._heap[0].mission

    def requeue(self, mission: Mission) -> None:
        if mission.id in self._known:
            return
        self._known.add(mission.id)
        heapq.heappush(
            self._heap,
            QueueEntry(priority=mission.priority, inserted_at=time.time(), mission=mission),
        )

    def should_preempt(self, current: Mission, delta: int) -> bool:
        best = self.peek_best()
        if best is None:
            return False
        return best.priority >= current.priority + delta

