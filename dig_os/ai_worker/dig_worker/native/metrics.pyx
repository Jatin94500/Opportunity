# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

cpdef tuple update_metrics(
    double loss,
    double accuracy,
    int epoch,
    int total_epochs,
    double difficulty
):
    cdef double progress = epoch / (total_epochs if total_epochs > 0 else 1.0)
    cdef double target_loss = 0.02 + (difficulty * 0.05)
    cdef double decay = (loss - target_loss) * (0.16 + progress * 0.14)
    if decay < 0.001:
        decay = 0.001
    loss = loss - decay
    if loss < target_loss:
        loss = target_loss

    accuracy = accuracy + (1.0 - accuracy) * (0.18 + progress * 0.17)
    if accuracy > 0.995:
        accuracy = 0.995

    return (loss, accuracy)


cpdef double reward_from_metrics(double bounty_dig, double accuracy, double eco_multiplier):
    cdef double reward = bounty_dig * accuracy * eco_multiplier
    if reward < 0:
        reward = 0
    return reward

