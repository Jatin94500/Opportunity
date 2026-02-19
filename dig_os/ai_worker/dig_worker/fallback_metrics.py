from __future__ import annotations


def update_metrics(
    loss: float,
    accuracy: float,
    epoch: int,
    total_epochs: int,
    difficulty: float,
) -> tuple[float, float]:
    progress = max(0.0, min(1.0, epoch / max(1, total_epochs)))
    target_loss = 0.02 + (difficulty * 0.05)
    decay = max(0.001, (loss - target_loss) * (0.14 + (progress * 0.13)))
    next_loss = max(target_loss, loss - decay)
    next_accuracy = min(0.995, accuracy + (1.0 - accuracy) * (0.15 + progress * 0.18))
    return next_loss, next_accuracy


def reward_from_metrics(bounty_dig: float, accuracy: float, eco_multiplier: float) -> float:
    return max(0.0, bounty_dig * accuracy * eco_multiplier)

