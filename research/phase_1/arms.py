"""Frozen prompt/process arms and task-type routing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Arm:
    name: str
    prompt: str
    allowed_task_types: frozenset[str]
    requires_delete: bool = False


_ALL = frozenset({"feature", "refactor", "cleanup", "measurement_control"})
_NON_FEATURE = frozenset({"refactor", "cleanup", "measurement_control"})
_DIRECTION_NEUTRAL = frozenset({"neutral_control", "concise_control"})

ARMS = {
    "neutral_control": Arm("neutral_control", "Implement the task and keep tests green.", _ALL),
    "concise_control": Arm("concise_control", "Make the smallest clear change that completes the task; keep tests green.", _ALL),
    "subtractive_rubric": Arm(
        "subtractive_rubric",
        "For refactor or cleanup work, add no capability: inventory references, identify safe deletions, preserve behavior, and run tests. Feature work remains sign-matched.",
        _ALL,
    ),
    "delete_first_gate": Arm(
        "delete_first_gate",
        "For refactor or cleanup work, first inventory callers and make a safe deletion before adding code; no safe deletion is an acceptable result. Feature work is exempt.",
        _ALL,
        True,
    ),
    "semantic_net_loc_budget": Arm(
        "semantic_net_loc_budget",
        "Match the task type. Prefer structural symbol net <= 0 for refactors and cleanup, but never delete tests, API behavior, or comments merely to hit a number; explain exceptions and run tests.",
        _ALL,
    ),
    "post_hoc_cleanup_comparator": Arm(
        "post_hoc_cleanup_comparator",
        "Implement the task neutrally, then perform one separate cleanup pass that preserves required behavior and tests.",
        _ALL,
    ),
}

ARM_NAMES = tuple(ARMS)


def choose_arm(arm_name: str, task_type: str) -> Arm:
    """Validate that an arm exists and is explicitly compatible with a task."""
    if arm_name not in ARMS:
        raise ValueError(f"unknown arm: {arm_name}")
    if task_type not in ARMS[arm_name].allowed_task_types:
        raise ValueError(f"arm {arm_name} is not compatible with {task_type}")
    return ARMS[arm_name]


def prompt_for(arm_name: str, task_type: str, instruction: str) -> str:
    arm = choose_arm(arm_name, task_type)
    if task_type == "feature":
        routing = "Feature task: additions are allowed when required."
    elif arm_name in _DIRECTION_NEUTRAL:
        routing = f"Task type: {task_type}. Follow the stated task without a prescribed diff direction."
    elif task_type in _NON_FEATURE:
        routing = "Maintenance task: do not force additions; prove semantic deletions."
    else:
        routing = f"Task type: {task_type}. Preserve behavior and keep tests green."
    return f"{routing}\n{arm.prompt}\nTask: {instruction}"
