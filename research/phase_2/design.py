"""Explicit, deterministic factorial design for Phase 2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

from research.phase_1.arms import COMPONENT_SCREEN_ARMS, choose_arm
from research.phase_1.fixtures import FixtureTask, build_fixture_corpus

DEFAULT_ARMS = ("neutral_control", "subtractive_rubric")
DEFAULT_MODEL_EFFORTS = (
    ("gpt-5.6-luna", "maximum"),
    ("grok-4.5", "high"),
    ("composer-2.5", "default"),
)
DEFAULT_MODEL_EFFORT_BY_MODEL = {model: effort for model, effort in DEFAULT_MODEL_EFFORTS}
ABLATION_SCREEN_TASK_IDS = ("refactor-shared-strip",)


@dataclass(frozen=True)
class DesignCell:
    task_id: str
    task_class: str
    model: str
    reasoning_effort: str
    arm: str
    repetition: int
    cell_id: str

    @classmethod
    def create(
        cls, task_id: str, task_class: str, model: str,
        reasoning_effort: str, arm: str, repetition: int,
    ) -> "DesignCell":
        values = (task_id, task_class, model, reasoning_effort, arm, repetition)
        digest = hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()[:12]
        return cls(task_id, task_class, model, reasoning_effort, arm, repetition, f"cell-{digest}")

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize_arms(arms: Optional[Iterable[str]]) -> tuple[str, ...]:
    from research.phase_1.arms import ARMS as ARM_REGISTRY

    selected = tuple(DEFAULT_ARMS if arms is None else arms)
    if not selected:
        raise ValueError("arms must contain at least one arm")
    if len(set(selected)) != len(selected):
        raise ValueError("arms must be unique")
    unknown = [arm for arm in selected if arm not in ARM_REGISTRY]
    if unknown:
        raise ValueError(f"unknown arms: {unknown}")
    return selected


class FactorialDesign:
    """A validated set of task × model/effort × arm × repetition cells."""

    def __init__(
        self,
        cells: Iterable[DesignCell],
        tasks: Optional[Iterable[FixtureTask]] = None,
        supported_models: Optional[Iterable[str]] = None,
        protocol: str = "phase-2-controlled-ablation-v1",
    ) -> None:
        self.cells = tuple(cells)
        self.tasks = tuple(tasks or build_fixture_corpus())
        self.supported_models = frozenset(supported_models or {model for model, _ in DEFAULT_MODEL_EFFORTS})
        self.protocol = protocol
        self.validate()

    def validate(self) -> None:
        if not self.cells:
            raise ValueError("factorial design must contain at least one cell")
        task_map = {task.task_id: task for task in self.tasks}
        if len(task_map) != len(self.tasks):
            raise ValueError("fixture corpus contains duplicate task IDs")
        seen = set()
        for cell in self.cells:
            if cell.repetition < 1:
                raise ValueError("repetition must be positive")
            if cell.task_id not in task_map:
                raise ValueError(f"unknown task: {cell.task_id}")
            task = task_map[cell.task_id]
            if cell.task_class != task.task_type:
                raise ValueError(f"task class mismatch for {cell.task_id}")
            if cell.model not in self.supported_models:
                raise ValueError(f"unsupported model: {cell.model}")
            if not cell.model or not cell.reasoning_effort:
                raise ValueError("model and reasoning_effort must be explicit")
            expected_effort = DEFAULT_MODEL_EFFORT_BY_MODEL.get(cell.model)
            if expected_effort is not None and cell.reasoning_effort != expected_effort:
                raise ValueError(
                    f"unsupported model/effort pairing: {cell.model}/{cell.reasoning_effort}"
                )
            choose_arm(cell.arm, cell.task_class)
            key = (cell.task_id, cell.model, cell.reasoning_effort, cell.arm, cell.repetition)
            if key in seen:
                raise ValueError(f"duplicate design cell: {key}")
            seen.add(key)
            expected_id = DesignCell.create(
                cell.task_id, cell.task_class, cell.model, cell.reasoning_effort,
                cell.arm, cell.repetition,
            ).cell_id
            if cell.cell_id != expected_id:
                raise ValueError(f"non-deterministic cell ID: {cell.cell_id}")
        model_efforts = {(cell.model, cell.reasoning_effort) for cell in self.cells}
        arms = {cell.arm for cell in self.cells}
        repetitions = {cell.repetition for cell in self.cells}
        expected = {
            (task.task_id, model, effort, arm, repetition)
            for task in self.tasks
            for model, effort in model_efforts
            for arm in arms
            for repetition in repetitions
        }
        actual = {
            (cell.task_id, cell.model, cell.reasoning_effort, cell.arm, cell.repetition)
            for cell in self.cells
        }
        if actual != expected:
            missing = sorted(expected - actual)
            raise ValueError(f"incomplete factorial design; missing cells: {missing[:3]}")

    def to_dict(self) -> dict:
        arms = []
        seen_arms = set()
        for cell in self.cells:
            if cell.arm not in seen_arms:
                arms.append(cell.arm)
                seen_arms.add(cell.arm)
        return {
            "protocol": self.protocol,
            "tasks": [
                {"task_id": task.task_id, "task_class": task.task_type, "instruction": task.instruction}
                for task in self.tasks
            ],
            "arms": arms,
            "supported_models": sorted(self.supported_models),
            "cells": [cell.to_dict() for cell in self.cells],
        }

    def write_manifest(self, path: Union[str, Path]) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def build_default_design(
    repetitions: int = 10,
    task_ids: Optional[Iterable[str]] = None,
    arms: Optional[Iterable[str]] = None,
) -> FactorialDesign:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    selected_arms = _normalize_arms(arms)
    fixture_tasks = build_fixture_corpus()
    if task_ids is not None:
        requested_task_ids = set(task_ids)
        available_task_ids = {task.task_id for task in fixture_tasks}
        unknown_task_ids = sorted(requested_task_ids - available_task_ids)
        if unknown_task_ids:
            raise ValueError(f"unknown task IDs: {unknown_task_ids}")
        fixture_tasks = tuple(
            task for task in fixture_tasks if task.task_id in requested_task_ids
        )
        if not fixture_tasks:
            raise ValueError("task_ids must contain at least one known task")
    cells = []
    for task in fixture_tasks:
        for model, effort in DEFAULT_MODEL_EFFORTS:
            for arm in selected_arms:
                for repetition in range(1, repetitions + 1):
                    cells.append(DesignCell.create(
                        task.task_id, task.task_type, model, effort, arm, repetition,
                    ))
    return FactorialDesign(cells, tasks=fixture_tasks)


def build_ablation_screen_design(repetitions: int = 5) -> FactorialDesign:
    """8-arm component screen on refactor-shared-strip × 3 models × R repetitions."""
    design = build_default_design(
        repetitions=repetitions,
        task_ids=ABLATION_SCREEN_TASK_IDS,
        arms=COMPONENT_SCREEN_ARMS,
    )
    return FactorialDesign(
        design.cells,
        tasks=design.tasks,
        supported_models=design.supported_models,
        protocol="phase-2-component-ablation-v1",
    )
