"""Deterministic repeated-repetition variance analysis for Phase 2 receipts."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Iterable, Mapping, Optional

from research.phase_1.arms import ARMS, COMPONENT_SCREEN_ARMS


PROTOCOL = "phase-2-controlled-ablation-variance-v1"
COMPONENT_EFFECTS_PROTOCOL = "phase-2-component-effects-v1"
DEFAULT_NEUTRAL_ARM = "neutral_control"
DEFAULT_TREATMENT_ARM = "subtractive_rubric"
_GROUP_FIELDS = ("task_id", "model", "reasoning_effort", "arm")
_COMPARISON_FIELDS = ("task_id", "model", "reasoning_effort")
_TOKEN_FIELDS = ("input_tokens", "output_tokens", "total_tokens")
_COMPONENT_FACTORS = ("T", "D", "B")
_COMPONENT_SCREEN_ARM_SET = frozenset(COMPONENT_SCREEN_ARMS)


def _sample_sd(values: list[float]) -> Optional[float]:
    return stdev(values) if len(values) >= 2 else None


def _numeric_summary(values: list[float]) -> dict:
    return {
        "values": values,
        "count": len(values),
        "mean": mean(values) if values else None,
        "sample_sd": _sample_sd(values),
    }


def _require_mapping(value, description: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise ValueError(f"{description} must be a mapping")
    return value


def _receipt_group_key(receipt: Mapping) -> tuple[str, str, str, str]:
    cell = _require_mapping(receipt.get("cell"), "receipt.cell")
    missing = [field for field in _GROUP_FIELDS if field not in cell]
    if missing:
        raise ValueError(f"receipt.cell missing fields: {missing}")
    return tuple(cell[field] for field in _GROUP_FIELDS)


def _status(actual: Mapping) -> str:
    return actual.get("adapter_status", "missing")


def _behavior_pass(record: Mapping) -> bool:
    tests = _require_mapping(record.get("tests"), "receipt.record.tests")
    if "passed" not in tests:
        raise ValueError("receipt.record.tests missing passed")
    return bool(tests["passed"])


def _completed_summary(records: list[Mapping]) -> dict:
    repetitions = [record["cell"]["repetition"] for record in records]
    raw_net_values = [record["record"]["diff"]["raw_net"] for record in records]
    behavior_passes = [_behavior_pass(record["record"]) for record in records]
    token_stats = {}
    for field in _TOKEN_FIELDS:
        values = [
            record["actual"].get(field)
            for record in records
            if record["actual"].get(field) is not None
        ]
        token_stats[field] = _numeric_summary(values)
    return {
        "completed_repetition_ids": repetitions,
        "raw_net_values": raw_net_values,
        "raw_net_mean": mean(raw_net_values),
        "raw_net_sample_sd": _sample_sd(raw_net_values),
        "raw_net_min": min(raw_net_values),
        "raw_net_max": max(raw_net_values),
        "behavior_pass_count": sum(behavior_passes),
        "behavior_failure_count": len(behavior_passes) - sum(behavior_passes),
        "token_stats": token_stats,
    }


def _validate_completed_receipt(receipt: Mapping) -> None:
    record = _require_mapping(receipt["record"], "receipt.record")
    actual = _require_mapping(receipt["actual"], "receipt.actual")
    diff = _require_mapping(record.get("diff"), "receipt.record.diff")
    if "raw_net" not in diff:
        raise ValueError("receipt.record.diff missing raw_net")
    if not isinstance(receipt["cell"].get("repetition"), int):
        raise ValueError("receipt.cell.repetition must be an integer")
    if not isinstance(diff["raw_net"], (int, float)) or isinstance(diff["raw_net"], bool):
        raise ValueError("receipt.record.diff.raw_net must be numeric")
    _behavior_pass(record)
    for field in _TOKEN_FIELDS:
        value = actual.get(field)
        if value is not None and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            raise ValueError(f"receipt.actual.{field} must be numeric or null")


def _pair_comparison(
    key: tuple[str, str, str, str],
    neutral: list[Mapping],
    treatment: list[Mapping],
    *,
    treatment_arm: str,
    neutral_arm: str = DEFAULT_NEUTRAL_ARM,
) -> dict:
    task_id, model, reasoning_effort, _ = key
    neutral_ids = {record["cell"]["repetition"] for record in neutral}
    treatment_ids = {record["cell"]["repetition"] for record in treatment}
    comparison = {
        "task_id": task_id,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "neutral_arm": neutral_arm,
        "treatment_arm": treatment_arm,
        "neutral_repetition_ids": sorted(neutral_ids),
        "treatment_repetition_ids": sorted(treatment_ids),
    }
    # Historical r5 field names remain for the classic subtractive contrast.
    if treatment_arm == DEFAULT_TREATMENT_ARM:
        comparison["subtractive_repetition_ids"] = sorted(treatment_ids)
    if not neutral_ids or neutral_ids != treatment_ids:
        if not neutral_ids or not treatment_ids:
            reason = "one or both arms have no completed repetitions"
        else:
            reason = (
                "completed repetition ID sets differ between neutral and "
                f"{treatment_arm} arms"
            )
            if treatment_arm == DEFAULT_TREATMENT_ARM:
                reason = "completed repetition ID sets differ between neutral and subtractive arms"
        comparison.update({"status": "unmatched", "reason": reason})
        return comparison

    neutral_by_id = {record["cell"]["repetition"]: record for record in neutral}
    treatment_by_id = {record["cell"]["repetition"]: record for record in treatment}
    paired = []
    for repetition in sorted(neutral_ids):
        neutral_record = neutral_by_id[repetition]
        treatment_record = treatment_by_id[repetition]
        neutral_passed = _behavior_pass(neutral_record["record"])
        treatment_passed = _behavior_pass(treatment_record["record"])
        pair = {
            "repetition": repetition,
            "raw_net_delta": (
                treatment_record["record"]["diff"]["raw_net"]
                - neutral_record["record"]["diff"]["raw_net"]
            ),
            "neutral_behavior_pass": neutral_passed,
            "treatment_behavior_pass": treatment_passed,
        }
        if treatment_arm == DEFAULT_TREATMENT_ARM:
            pair["subtractive_behavior_pass"] = treatment_passed
        paired.append(pair)
    deltas = [pair["raw_net_delta"] for pair in paired]
    comparison.update({
        "status": "matched",
        "repetitions": paired,
        "raw_net_deltas": deltas,
        "raw_net_delta_mean": mean(deltas),
        "raw_net_delta_sample_sd": _sample_sd(deltas),
        "both_behavior_pass_count": sum(
            pair["neutral_behavior_pass"] and pair["treatment_behavior_pass"]
            for pair in paired
        ),
        "neutral_only_behavior_pass_count": sum(
            pair["neutral_behavior_pass"] and not pair["treatment_behavior_pass"]
            for pair in paired
        ),
        "treatment_only_behavior_pass_count": sum(
            not pair["neutral_behavior_pass"] and pair["treatment_behavior_pass"]
            for pair in paired
        ),
    })
    if treatment_arm == DEFAULT_TREATMENT_ARM:
        comparison["subtractive_only_behavior_pass_count"] = comparison[
            "treatment_only_behavior_pass_count"
        ]
    return comparison


def _factor_arms(factor: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if factor not in _COMPONENT_FACTORS:
        raise ValueError(f"unknown component factor: {factor}")
    on_arms = tuple(
        name for name in COMPONENT_SCREEN_ARMS if factor in ARMS[name].components
    )
    off_arms = tuple(
        name for name in COMPONENT_SCREEN_ARMS if factor not in ARMS[name].components
    )
    return on_arms, off_arms


def _collect_component_screen_receipts(records: Iterable[Mapping]) -> list[Mapping]:
    """Fail-closed ingest for a complete atomic component screen."""
    completed: list[Mapping] = []
    seen_repetitions = set()
    for receipt in records:
        receipt = _require_mapping(receipt, "receipt")
        for field in ("cell", "actual", "record"):
            _require_mapping(receipt.get(field), f"receipt.{field}")
        key = _receipt_group_key(receipt)
        status = _status(receipt["actual"])
        if status != "completed":
            raise ValueError(
                "component effects require completed receipts; "
                f"got adapter_status={status!r} for {key}"
            )
        _validate_completed_receipt(receipt)
        repetition = receipt["cell"]["repetition"]
        duplicate_key = (*key, repetition)
        if duplicate_key in seen_repetitions:
            raise ValueError(f"duplicate completed repetition ID: {duplicate_key}")
        seen_repetitions.add(duplicate_key)
        completed.append(receipt)

    if not completed:
        raise ValueError("component effects require at least one completed receipt")

    arms_present = {receipt["cell"]["arm"] for receipt in completed}
    if arms_present != _COMPONENT_SCREEN_ARM_SET:
        missing = sorted(_COMPONENT_SCREEN_ARM_SET - arms_present)
        extra = sorted(arms_present - _COMPONENT_SCREEN_ARM_SET)
        raise ValueError(
            "component effects require exact coverage of COMPONENT_SCREEN_ARMS; "
            f"missing={missing}, extra={extra}"
        )
    return completed


def _factor_effect_for_group(
    key: tuple[str, str, str],
    arms: Mapping[str, list[Mapping]],
    factor: str,
) -> dict:
    task_id, model, reasoning_effort = key
    on_arms, off_arms = _factor_arms(factor)
    repetition_sets = [
        {receipt["cell"]["repetition"] for receipt in arms[arm_name]}
        for arm_name in COMPONENT_SCREEN_ARMS
    ]
    shared_repetitions = set.intersection(*repetition_sets) if repetition_sets else set()
    if not shared_repetitions or any(
        repetitions != shared_repetitions for repetitions in repetition_sets
    ):
        raise ValueError(
            "component effects require matched unique repetition IDs across all "
            f"COMPONENT_SCREEN_ARMS for {key}"
        )

    by_arm_rep = {
        arm_name: {
            receipt["cell"]["repetition"]: receipt for receipt in arms[arm_name]
        }
        for arm_name in COMPONENT_SCREEN_ARMS
    }
    deltas = []
    on_behavior_pass_count = 0
    off_behavior_pass_count = 0
    for repetition in sorted(shared_repetitions):
        on_values = []
        off_values = []
        for arm_name in on_arms:
            receipt = by_arm_rep[arm_name][repetition]
            on_values.append(receipt["record"]["diff"]["raw_net"])
            on_behavior_pass_count += int(_behavior_pass(receipt["record"]))
        for arm_name in off_arms:
            receipt = by_arm_rep[arm_name][repetition]
            off_values.append(receipt["record"]["diff"]["raw_net"])
            off_behavior_pass_count += int(_behavior_pass(receipt["record"]))
        deltas.append(mean(on_values) - mean(off_values))

    return {
        "task_id": task_id,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "factor": factor,
        "on_arms": list(on_arms),
        "off_arms": list(off_arms),
        "raw_net_deltas": deltas,
        "raw_net_delta_mean": mean(deltas),
        "raw_net_delta_sample_sd": _sample_sd(deltas),
        "on_behavior_pass_count": on_behavior_pass_count,
        "off_behavior_pass_count": off_behavior_pass_count,
    }


def analyze_component_effects(records: Iterable[Mapping]) -> dict:
    """Report T/D/B on-minus-off raw_net effects for a complete component screen.

    Fail-closed: every receipt must be completed with numeric raw_net, the arm
    set must be exactly COMPONENT_SCREEN_ARMS, and repetition IDs must be unique
    and matched across those arms within each task/model/effort group.
    Factor membership comes from ARMS component metadata.
    """
    completed = _collect_component_screen_receipts(records)
    arms_by_group: dict[tuple[str, str, str], dict[str, list[Mapping]]] = defaultdict(
        dict
    )
    for receipt in completed:
        cell = receipt["cell"]
        group_key = tuple(cell[field] for field in _COMPARISON_FIELDS)
        arm = cell["arm"]
        arms_by_group[group_key].setdefault(arm, []).append(receipt)

    effects = []
    for key in sorted(arms_by_group):
        arms = arms_by_group[key]
        present = set(arms)
        if present != _COMPONENT_SCREEN_ARM_SET:
            missing = sorted(_COMPONENT_SCREEN_ARM_SET - present)
            raise ValueError(
                "component effects require exact COMPONENT_SCREEN_ARMS coverage "
                f"for {key}; missing={missing}"
            )
        for factor in _COMPONENT_FACTORS:
            effects.append(_factor_effect_for_group(key, arms, factor))
    return {
        "protocol": COMPONENT_EFFECTS_PROTOCOL,
        "effects": effects,
    }


def analyze_variance_records(
    records: Iterable[Mapping],
    *,
    neutral_arm: str = DEFAULT_NEUTRAL_ARM,
) -> dict:
    """Analyze completed receipts while retaining non-completed status counts."""
    grouped: dict[tuple[str, str, str, str], dict[str, list[Mapping]]] = defaultdict(
        lambda: defaultdict(list)
    )
    seen_repetitions = set()
    status_counts = defaultdict(int)
    completed_receipts: list[Mapping] = []
    for receipt in records:
        receipt = _require_mapping(receipt, "receipt")
        for field in ("cell", "actual", "record"):
            _require_mapping(receipt.get(field), f"receipt.{field}")
        key = _receipt_group_key(receipt)
        actual = receipt["actual"]
        status = _status(actual)
        status_counts[status] += 1
        if status != "completed":
            grouped[key][status].append(receipt)
            continue
        _validate_completed_receipt(receipt)
        repetition = receipt["cell"]["repetition"]
        duplicate_key = (*key, repetition)
        if duplicate_key in seen_repetitions:
            raise ValueError(f"duplicate completed repetition ID: {duplicate_key}")
        seen_repetitions.add(duplicate_key)
        grouped[key]["completed"].append(receipt)
        completed_receipts.append(receipt)

    groups = []
    for key in sorted(grouped):
        task_id, model, reasoning_effort, arm = key
        completed = sorted(
            grouped[key].get("completed", []),
            key=lambda receipt: receipt["cell"]["repetition"],
        )
        group = dict(zip(_GROUP_FIELDS, key))
        group.update({
            "status_counts": {
                status: len(receipts)
                for status, receipts in sorted(grouped[key].items())
            },
            "completed_count": len(completed),
        })
        if completed:
            group.update(_completed_summary(completed))
        else:
            group.update({
                "completed_repetition_ids": [],
                "raw_net_values": [],
                "raw_net_mean": None,
                "raw_net_sample_sd": None,
                "raw_net_min": None,
                "raw_net_max": None,
                "behavior_pass_count": 0,
                "behavior_failure_count": 0,
                "token_stats": {
                    field: _numeric_summary([]) for field in _TOKEN_FIELDS
                },
            })
        groups.append(group)

    arms_by_comparison: dict[tuple[str, str, str], dict[str, list[Mapping]]] = defaultdict(dict)
    for group_key, arms in grouped.items():
        comparison_key = group_key[:3]
        arm = group_key[3]
        arms_by_comparison[comparison_key][arm] = arms.get("completed", [])

    comparisons = []
    for key, arms in sorted(arms_by_comparison.items()):
        treatment_arms = sorted(arm for arm in arms if arm != neutral_arm)
        # Classic two-arm reports still emit a subtractive slot when only
        # neutral (or only subtractive) receipts are present.
        if not treatment_arms:
            treatment_arms = [DEFAULT_TREATMENT_ARM]
        for treatment_arm in treatment_arms:
            comparisons.append(
                _pair_comparison(
                    (*key, neutral_arm),
                    arms.get(neutral_arm, []),
                    arms.get(treatment_arm, []),
                    treatment_arm=treatment_arm,
                    neutral_arm=neutral_arm,
                )
            )
    result = {
        "protocol": PROTOCOL,
        "groups": groups,
        "paired_comparisons": comparisons,
        "status_counts": {
            status: status_counts[status] for status in sorted(status_counts)
        },
    }
    completed_arms = {receipt["cell"]["arm"] for receipt in completed_receipts}
    if completed_arms == _COMPONENT_SCREEN_ARM_SET:
        # Fail-closed when the completed arm set is exactly COMPONENT_SCREEN_ARMS.
        # Historical two-arm inputs never enter this branch.
        result["component_effects"] = analyze_component_effects(completed_receipts)
    return result



def load_result_files(paths: Iterable[str]) -> list[Mapping]:
    """Load receipt objects or receipt lists from UTF-8 JSON files."""
    receipts = []
    for path in paths:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(payload, Mapping):
            receipts.append(payload)
        elif isinstance(payload, list):
            receipts.extend(payload)
        else:
            raise ValueError(f"result file must contain an object or list: {path}")
    return receipts


def analyze_result_files(paths: Iterable[str]) -> dict:
    return analyze_variance_records(load_result_files(paths))
