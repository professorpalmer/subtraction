"""Frozen prompt/process arms and task-type routing.

Intervention language is factored into three atomic components that compose:

- T: task-type / no-new-capability language
- D: delete-first / reference-proof language
- B: semantic net-LOC / budget language

The component screen uses the genuine 2³ cross of atomic T/D/B fragments,
including `task_type_delete_first_net_loc_budget` as the T+D+B cell.
`subtractive_rubric` remains the backward-compatible historical composite
(optional bridge/legacy comparator) and is not part of that screen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class Arm:
    name: str
    prompt: str
    allowed_task_types: frozenset[str]
    requires_delete: bool = False
    components: frozenset[str] = frozenset()


_ALL = frozenset({"feature", "refactor", "cleanup", "measurement_control"})
_NON_FEATURE = frozenset({"refactor", "cleanup", "measurement_control"})
_DIRECTION_NEUTRAL = frozenset({"neutral_control", "concise_control"})

# Atomic intervention fragments. Pure T/B must not inherit D wording.
COMPONENT_T = (
    "For refactor or cleanup work, add no new capability and match the task type; "
    "feature work remains sign-matched."
)
COMPONENT_D = (
    "For refactor or cleanup work, first inventory callers and references, then make "
    "a safe deletion before adding code; prove semantic deletions; no safe deletion "
    "is an acceptable result. Feature work is exempt."
)
COMPONENT_B = (
    "Prefer structural symbol net <= 0 for refactors and cleanup, but never delete "
    "tests, API behavior, or comments merely to hit a number; explain exceptions and "
    "run tests."
)

_COMPONENT_TEXT = {
    "T": COMPONENT_T,
    "D": COMPONENT_D,
    "B": COMPONENT_B,
}


def compose_components(components: Iterable[str]) -> str:
    """Join atomic T/D/B fragments in canonical order."""
    selected = set(components)
    ordered = [name for name in ("T", "D", "B") if name in selected]
    unknown = sorted(selected - {"T", "D", "B"})
    if unknown:
        raise ValueError(f"unknown intervention components: {unknown}")
    if not ordered:
        raise ValueError("at least one intervention component is required")
    return " ".join(_COMPONENT_TEXT[name] for name in ordered)


def _component_arm(
    name: str,
    components: Iterable[str],
    *,
    prompt: Optional[str] = None,
    requires_delete: Optional[bool] = None,
) -> Arm:
    ordered = frozenset(components)
    text = prompt if prompt is not None else compose_components(ordered)
    delete = ("D" in ordered) if requires_delete is None else requires_delete
    return Arm(name, text, _ALL, delete, ordered)


ARMS = {
    "neutral_control": Arm(
        "neutral_control",
        "Implement the task and keep tests green.",
        _ALL,
        components=frozenset(),
    ),
    "concise_control": Arm(
        "concise_control",
        "Make the smallest clear change that completes the task; keep tests green.",
        _ALL,
        components=frozenset(),
    ),
    # Eight-component screen arms (T × D × B) plus legacy extras below.
    "task_type_gate": _component_arm("task_type_gate", ("T",)),
    "delete_first_gate": _component_arm("delete_first_gate", ("D",)),
    "semantic_net_loc_budget": _component_arm("semantic_net_loc_budget", ("B",)),
    "task_type_delete_first": _component_arm("task_type_delete_first", ("T", "D")),
    "task_type_net_loc_budget": _component_arm("task_type_net_loc_budget", ("T", "B")),
    "delete_first_net_loc_budget": _component_arm(
        "delete_first_net_loc_budget", ("D", "B"),
    ),
    # Atomic T+D+B cell for the component screen (distinct from legacy composite).
    "task_type_delete_first_net_loc_budget": _component_arm(
        "task_type_delete_first_net_loc_budget", ("T", "D", "B"),
    ),
    # Backward-compatible historical composite; optional bridge/legacy comparator.
    # Excluded from COMPONENT_SCREEN_ARMS so the 120-cell screen stays atomic.
    "subtractive_rubric": _component_arm(
        "subtractive_rubric",
        ("T", "D", "B"),
        prompt=(
            "For refactor or cleanup work, add no capability: inventory references, "
            "identify safe deletions, preserve behavior, and run tests. "
            "Feature work remains sign-matched."
        ),
        requires_delete=False,
    ),
    "post_hoc_cleanup_comparator": Arm(
        "post_hoc_cleanup_comparator",
        "Implement the task neutrally, then perform one separate cleanup pass that "
        "preserves required behavior and tests.",
        _ALL,
        components=frozenset(),
    ),
}

# Explicit 2^3 component screen used by the next-wave ablation protocol.
COMPONENT_SCREEN_ARMS = (
    "neutral_control",
    "task_type_gate",
    "delete_first_gate",
    "semantic_net_loc_budget",
    "task_type_delete_first",
    "task_type_net_loc_budget",
    "delete_first_net_loc_budget",
    "task_type_delete_first_net_loc_budget",
)

ARM_NAMES = tuple(ARMS)


def choose_arm(arm_name: str, task_type: str) -> Arm:
    """Validate that an arm exists and is explicitly compatible with a task."""
    if arm_name not in ARMS:
        raise ValueError(f"unknown arm: {arm_name}")
    if task_type not in ARMS[arm_name].allowed_task_types:
        raise ValueError(f"arm {arm_name} is not compatible with {task_type}")
    return ARMS[arm_name]


def _routing_for(arm: Arm, task_type: str) -> str:
    if task_type == "feature":
        return "Feature task: additions are allowed when required."
    if arm.name in _DIRECTION_NEUTRAL or not arm.components:
        return (
            f"Task type: {task_type}. Follow the stated task without a prescribed "
            "diff direction."
        )
    # Exact historical two-arm routing for the legacy composite only.
    if arm.name == "subtractive_rubric" and task_type in _NON_FEATURE:
        return "Maintenance task: do not force additions; prove semantic deletions."
    # Atomic component-screen arms share one base; T/D/B text is the factor.
    return f"Task type: {task_type}. Preserve behavior and keep tests green."


def prompt_for(arm_name: str, task_type: str, instruction: str) -> str:
    arm = choose_arm(arm_name, task_type)
    return f"{_routing_for(arm, task_type)}\n{arm.prompt}\nTask: {instruction}"
