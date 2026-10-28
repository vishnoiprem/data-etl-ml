import time


def simulate(check, *, polls: int, interval: float, mode: str):
    """Simulate a sensor waiting for a condition to become true.

    Args:
        check: A callable returning True once the condition holds.
        polls: The maximum number of attempts.
        interval: Seconds between polls.
        mode: ``"poke"`` or ``"reschedule"``.

    Returns:
        A ``(polls_used, slot_held_fraction)`` tuple.
    """
    slot_held = 0.0
    for attempt in range(1, polls + 1):
        if mode == "poke":
            slot_held += 1.0          # the worker is occupied this whole period
        if check():
            return attempt, slot_held
        if mode == "reschedule":
            pass                       # no slot held while waiting
        time.sleep(interval)
    return polls, slot_held


ready_after = 5
state = {"polls": 0}


def condition():
    state["polls"] += 1
    return state["polls"] >= ready_after


poke_polls, poke_slots = simulate(condition, polls=10, interval=0.01, mode="poke")
print(f"poke      : {poke_polls} polls, worker slots consumed: {poke_slots:.0f}")

state["polls"] = 0
resched_polls, resched_slots = simulate(condition, polls=10, interval=0.01, mode="reschedule")
print(f"reschedule: {resched_polls} polls, worker slots consumed: {resched_slots:.0f}")

print()
print(f"same polls: {poke_polls == resched_polls}")
print(f"slots saved by reschedule: {poke_slots - resched_slots:.0f}")
print()
print("A 'poke' sensor holds a worker slot for every poll it makes.")
print("That is why long waits use 'reschedule' (or deferrable=True).")
