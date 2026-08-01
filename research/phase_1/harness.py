"""Dry-run harness and adapter-neutral result data model."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

from .arms import ARM_NAMES, ARMS, prompt_for
from .fixtures import FixtureTask, build_fixture_corpus
from .metrics import DiffMetrics, measure_diff

OFFLINE_FIXTURE_SOURCE = "offline_fixture"


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


@dataclass(frozen=True)
class TestResult:
    passed: bool
    tests_run: int
    failure_reason: Optional[str] = None


@dataclass(frozen=True)
class RunRecord:
    model: Optional[str]
    reasoning_effort: Optional[str]
    execution_source: str
    task_id: str
    task_type: str
    expected_sign: str
    expected_class: str
    arm: str
    prompt: str
    turns: int
    tool_calls: int
    token_usage: TokenUsage
    diff: DiffMetrics
    tests: TestResult
    failure_reasons: tuple[str, ...]
    dry_run: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _test_source(task: FixtureTask, source: str) -> TestResult:
    passed = task.is_source_valid(source)
    return TestResult(passed, 1, None if passed else "behavior oracle failed")


def _failure_reasons(task: FixtureTask, arm: str, diff: DiffMetrics, tests: TestResult) -> tuple[str, ...]:
    failures: list[str] = []
    if task.expected_sign == "positive" and diff.raw_net <= 0:
        failures.append("expected_positive_diff")
    elif task.expected_sign == "nonpositive" and diff.raw_net > 0:
        failures.append("expected_nonpositive_diff")
    elif task.expected_sign == "negative" and diff.raw_net >= 0:
        failures.append("expected_negative_diff")
    elif task.expected_sign == "semantic_zero" and diff.structural_symbols_net != 0:
        failures.append("expected_semantic_zero_diff")
    if task.expected_class == "additive" and diff.raw_added <= diff.raw_removed:
        failures.append("expected_additive_patch")
    elif task.expected_class == "subtractive" and diff.raw_removed <= diff.raw_added:
        failures.append("expected_subtractive_patch")
    elif task.expected_class == "raw_churn" and not diff.likely_move_or_copy:
        failures.append("expected_raw_churn_control")
    if ARMS[arm].requires_delete and task.task_type in {"refactor", "cleanup"} and diff.raw_removed == 0:
        failures.append("delete_first_gate_violation")
    if not tests.passed:
        failures.append(tests.failure_reason or "tests failed")
    return tuple(failures)


def measure_candidate_patch(
    task: FixtureTask,
    arm: str,
    candidate_source: str,
    *,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    execution_source: str,
    turns: int,
    tool_calls: int,
    token_usage: Optional[TokenUsage] = None,
    dry_run: bool = False,
) -> RunRecord:
    prompt = prompt_for(arm, task.task_type, task.instruction)
    diff = measure_diff(task.before, candidate_source)
    tests = _test_source(task, candidate_source)
    return RunRecord(
        model=model,
        reasoning_effort=reasoning_effort,
        execution_source=execution_source,
        task_id=task.task_id,
        task_type=task.task_type,
        expected_sign=task.expected_sign,
        expected_class=task.expected_class,
        arm=arm,
        prompt=prompt,
        turns=turns,
        tool_calls=tool_calls,
        token_usage=token_usage or TokenUsage(),
        diff=diff,
        tests=tests,
        failure_reasons=_failure_reasons(task, arm, diff, tests),
        dry_run=dry_run,
    )


def run_task(
    task: FixtureTask,
    arm: str,
) -> RunRecord:
    """Measure the hand-authored transformation as offline fixture evidence."""
    return measure_candidate_patch(
        task,
        arm,
        task.after,
        execution_source=OFFLINE_FIXTURE_SOURCE,
        turns=1,
        tool_calls=0,
        token_usage=TokenUsage(),
        dry_run=True,
    )


def run_dry_run(
    output_path: Optional[Union[str, Path]] = None,
    arms: Iterable[str] = ARM_NAMES,
) -> list[RunRecord]:
    records = [run_task(task, arm) for task in build_fixture_corpus() for arm in arms]
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([record.to_dict() for record in records], indent=2, sort_keys=True) + "\n")
    return records


def aggregate_token_usage(records: Iterable[RunRecord]) -> dict:
    records = list(records)
    input_values = [r.token_usage.input_tokens for r in records if r.token_usage.input_tokens is not None]
    output_values = [r.token_usage.output_tokens for r in records if r.token_usage.output_tokens is not None]
    return {
        "runs": len(records),
        "reported_input_tokens": sum(input_values) if input_values else None,
        "reported_output_tokens": sum(output_values) if output_values else None,
        "runs_with_input_tokens": len(input_values),
        "runs_with_output_tokens": len(output_values),
    }


def classify_patch(before: str, after: str) -> tuple[str, ...]:
    """Flag common metric gaming without declaring semantic failure."""
    flags = list(measure_diff(before, after).gaming_flags)
    if before.count("\n") > after.count("\n") and before.count("#") > after.count("#"):
        flags.append("comment_deletion_candidate")
    if "assert" in before and "assert" not in after:
        flags.append("test_assertion_removed")
    return tuple(sorted(set(flags)))
