"""Deterministic, usage-first analysis of Phase 2 result receipts."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


TOKEN_FIELDS = ("input_tokens", "output_tokens", "total_tokens")
ARMS = ("neutral_control", "subtractive_rubric")
DEFAULT_NEUTRAL_ARM = ARMS[0]
DEFAULT_TREATMENT_ARM = ARMS[1]
CURRENT_PROTOCOL = "phase-2-controlled-ablation-v1"
LEGACY_PROTOCOL = "phase-2-controlled-ablation-v0"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid JSON artifact: {path}") from exc


def _is_receipt_record(record: Any) -> bool:
    return (
        isinstance(record, dict)
        and isinstance(record.get("cell"), Mapping)
        and isinstance(record.get("actual"), Mapping)
    )


def _records_from_document(document: Any, path: Path) -> List[dict]:
    if isinstance(document, list):
        records = document
    elif isinstance(document, dict) and isinstance(document.get("results"), list):
        records = document["results"]
    elif isinstance(document, dict):
        if not _is_receipt_record(document):
            raise ValueError(
                f"result artifact must contain Phase 2 receipt records with "
                f"object-shaped cell and actual fields: {path}"
            )
        records = [document]
    else:
        raise ValueError(f"result artifact must contain an object or list: {path}")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError(f"result artifact contains a non-object record: {path}")
    for record in records:
        if not _is_receipt_record(record):
            raise ValueError(
                f"result artifact contains a non-receipt record without "
                f"object-shaped cell and actual fields: {path}"
            )
    return records


def load_result_files(paths: Iterable[str]) -> List[dict]:
    """Load object or list-shaped Phase 2 JSON artifacts in path order."""
    loaded: List[dict] = []
    for path_string in paths:
        path = Path(path_string)
        for record in _records_from_document(_read_json(path), path):
            loaded.append(record)
    return loaded


def _is_explicit_legacy_schema(record: Mapping[str, Any]) -> bool:
    """Allow missing status only for the explicitly pre-status protocol."""
    return record.get("protocol") == LEGACY_PROTOCOL or record.get(
        "adapter_status_schema"
    ) == "pre-adapter-status"


def _status_for(record: Mapping[str, Any]) -> Tuple[Optional[str], bool]:
    actual = record.get("actual", {})
    if not isinstance(actual, Mapping):
        raise ValueError("result record actual field must be an object")
    if "adapter_status" in actual:
        status = actual["adapter_status"]
        return status, status == "completed"
    return None, _is_explicit_legacy_schema(record)


def _numeric_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"token value must be numeric or null: {value!r}")
    return value


def _sum(values: Iterable[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    return sum(present) if present else None


def _mean(values: Iterable[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    return sum(present) / len(present) if present else None


def _cost(tokens: Optional[float], rate: Optional[float]) -> Optional[float]:
    if tokens is None or rate is None:
        return None
    return tokens * rate / 1_000_000


def _rates_for_model(
    pricing: Optional[Mapping[str, Any]], model: str
) -> Optional[Dict[str, float]]:
    if pricing is None or model not in pricing:
        return None
    raw_rates = pricing[model]
    if isinstance(raw_rates, (int, float)) and not isinstance(raw_rates, bool):
        # A lone scalar does not define independent input/output/total field rates.
        return {}
    if not isinstance(raw_rates, Mapping):
        raise ValueError(f"pricing for {model} must be a number or object")
    rates: Dict[str, float] = {}
    aliases = {"input_tokens": "input", "output_tokens": "output", "total_tokens": "total"}
    for field, alias in aliases.items():
        rate = raw_rates.get(alias, raw_rates.get(field))
        if rate is not None:
            if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate < 0:
                raise ValueError(f"pricing rate for {model}/{alias} must be nonnegative")
            rates[field] = rate
    return rates


def _token_summary(records: Sequence[Mapping[str, Any]], pricing: Optional[Mapping[str, Any]]) -> dict:
    model = records[0]["cell"]["model"]
    rates = _rates_for_model(pricing, model)
    summary: Dict[str, Any] = {"run_count": len(records)}
    for field in TOKEN_FIELDS:
        values = [
            _numeric_or_none(record.get("actual", {}).get(field))
            for record in records
        ]
        summary[f"reported_{field}"] = _sum(values)
        summary[f"mean_{field}"] = _mean(values)
        summary[f"runs_with_{field}"] = sum(value is not None for value in values)
        summary[f"{field}_cost"] = _cost(
            summary[f"reported_{field}"],
            None if rates is None else rates.get(field),
        )
    return summary


def _comparison_value(
    neutral: Mapping[str, Any],
    treatment: Mapping[str, Any],
    field: str,
    *,
    treatment_arm: str = DEFAULT_TREATMENT_ARM,
) -> dict:
    neutral_value = neutral.get(f"reported_{field}")
    treatment_value = treatment.get(f"reported_{field}")
    neutral_mean = neutral.get(f"mean_{field}")
    treatment_mean = treatment.get(f"mean_{field}")
    delta = (
        None
        if neutral_value is None or treatment_value is None
        else treatment_value - neutral_value
    )
    relative = None if delta is None or neutral_value == 0 else delta / neutral_value
    result = {
        "neutral": neutral_value,
        "treatment": treatment_value,
        "neutral_total": neutral_value,
        "treatment_total": treatment_value,
        "neutral_mean": neutral_mean,
        "treatment_mean": treatment_mean,
        "delta_treatment_minus_neutral": delta,
        "relative_change": relative,
    }
    # Preserve historical subtractive_* keys for the classic r5 contrast.
    if treatment_arm == DEFAULT_TREATMENT_ARM:
        result.update({
            "subtractive": treatment_value,
            "subtractive_total": treatment_value,
            "subtractive_mean": treatment_mean,
            "delta_subtractive_minus_neutral": delta,
        })
    return result


GroupKey = Tuple[str, str, Optional[str], str]


def _cell_group_key(cell: Mapping[str, Any]) -> GroupKey:
    effort = cell.get("reasoning_effort")
    return (
        str(cell["task_id"]),
        str(cell["model"]),
        None if effort is None else str(effort),
        str(cell["arm"]),
    )


def _comparison_identity(key: GroupKey) -> Tuple[str, str, Optional[str]]:
    task_id, model, effort, _ = key
    return task_id, model, effort


def _repetition_ids(records: Sequence[Mapping[str, Any]]) -> Optional[List[int]]:
    ids: List[int] = []
    for record in records:
        cell = record.get("cell", {})
        if not isinstance(cell, Mapping) or "repetition" not in cell:
            return None
        repetition = cell["repetition"]
        if isinstance(repetition, bool) or not isinstance(repetition, int) or repetition < 1:
            raise ValueError("repetition must be a positive integer")
        ids.append(repetition)
    return sorted(ids)


def _unmatched_reason(
    neutral_records: Sequence[Mapping[str, Any]],
    treatment_records: Sequence[Mapping[str, Any]],
    neutral: Mapping[str, Any],
    treatment: Mapping[str, Any],
) -> Optional[str]:
    if neutral["run_count"] != treatment["run_count"]:
        return "unequal repetition counts"
    neutral_ids = _repetition_ids(neutral_records)
    treatment_ids = _repetition_ids(treatment_records)
    if neutral_ids is not None or treatment_ids is not None:
        if neutral_ids is None or treatment_ids is None:
            return "incomplete repetition ids"
        if neutral_ids != treatment_ids:
            return "misaligned repetition ids"
    for field in TOKEN_FIELDS:
        neutral_coverage = neutral[f"runs_with_{field}"]
        treatment_coverage = treatment[f"runs_with_{field}"]
        if neutral_coverage != treatment_coverage:
            return f"unequal token coverage for {field}"
    return None


def _compare_groups(
    groups: Mapping[GroupKey, dict],
    grouped_records: Mapping[GroupKey, List[Mapping[str, Any]]],
    *,
    neutral_arm: str = DEFAULT_NEUTRAL_ARM,
    treatment_arms: Optional[Sequence[str]] = None,
) -> List[dict]:
    identities = sorted({_comparison_identity(key) for key in groups})
    present_arms = {key[3] for key in groups}
    if treatment_arms is None:
        discovered = sorted(arm for arm in present_arms if arm != neutral_arm)
        selected_treatments: Sequence[str] = discovered or (DEFAULT_TREATMENT_ARM,)
    else:
        selected_treatments = tuple(treatment_arms)
    comparisons = []
    for task_id, model, effort in identities:
        neutral_key = (task_id, model, effort, neutral_arm)
        neutral = groups.get(neutral_key)
        for treatment_arm in selected_treatments:
            treatment_key = (task_id, model, effort, treatment_arm)
            treatment = groups.get(treatment_key)
            item: Dict[str, Any] = {
                "task_id": task_id,
                "model": model,
                "neutral_arm": neutral_arm,
                "treatment_arm": treatment_arm,
            }
            if effort is not None:
                item["reasoning_effort"] = effort
            if neutral is None or treatment is None:
                item.update({"status": "unmatched", "reason": "missing arm"})
                comparisons.append(item)
                continue
            reason = _unmatched_reason(
                grouped_records[neutral_key],
                grouped_records[treatment_key],
                neutral,
                treatment,
            )
            if reason is not None:
                update: Dict[str, Any] = {"status": "unmatched", "reason": reason}
                if reason == "unequal repetition counts":
                    update["neutral_run_count"] = neutral["run_count"]
                    update["treatment_run_count"] = treatment["run_count"]
                    if treatment_arm == DEFAULT_TREATMENT_ARM:
                        update["subtractive_run_count"] = treatment["run_count"]
                comparisons.append({**item, **update})
                continue
            item["status"] = "matched"
            item["repetition_count"] = neutral["run_count"]
            item["tokens"] = {
                field: _comparison_value(
                    neutral, treatment, field, treatment_arm=treatment_arm,
                )
                for field in TOKEN_FIELDS
            }
            comparisons.append(item)
    return comparisons


def analyze_records(
    records: Iterable[Mapping[str, Any]],
    pricing: Optional[Mapping[str, Any]] = None,
    *,
    neutral_arm: str = DEFAULT_NEUTRAL_ARM,
    treatment_arms: Optional[Sequence[str]] = None,
) -> dict:
    """Analyze completed adapter receipts without synthesizing token fields."""
    included: List[Mapping[str, Any]] = []
    excluded_statuses: Dict[str, int] = defaultdict(int)
    for record in records:
        status, include = _status_for(record)
        if include:
            included.append(record)
        else:
            excluded_statuses["missing" if status is None else str(status)] += 1

    grouped: Dict[GroupKey, List[Mapping[str, Any]]] = defaultdict(list)
    for record in included:
        cell = record.get("cell", {})
        if not isinstance(cell, Mapping):
            raise ValueError("result record cell field must be an object")
        try:
            key = _cell_group_key(cell)
        except KeyError as exc:
            raise ValueError("result record cell lacks task_id, model, or arm") from exc
        grouped[key].append(record)

    summaries = []
    summary_map: Dict[GroupKey, dict] = {}
    for key in sorted(grouped):
        task_id, model, effort, arm = key
        summary = {
            "task_id": task_id,
            "model": model,
            "arm": arm,
            **_token_summary(grouped[key], pricing),
        }
        if effort is not None:
            summary["reasoning_effort"] = effort
        summaries.append(summary)
        summary_map[key] = summary

    return {
        "protocol": "phase-3-token-cost-analysis-v1",
        "input_record_count": len(included) + sum(excluded_statuses.values()),
        "included_completed_record_count": len(included),
        "excluded_record_count": sum(excluded_statuses.values()),
        "excluded_by_adapter_status": dict(sorted(excluded_statuses.items())),
        "pricing_supplied": pricing is not None,
        "summaries": summaries,
        "matched_arm_comparisons": _compare_groups(
            summary_map,
            grouped,
            neutral_arm=neutral_arm,
            treatment_arms=treatment_arms,
        ),
    }


def analyze_files(
    paths: Iterable[str], pricing: Optional[Mapping[str, Any]] = None
) -> dict:
    return analyze_records(load_result_files(paths), pricing)


def calculate_context_savings(
    baseline_input_tokens_per_turn: float,
    reduction_fraction: float,
    future_turn_count: int,
    price_per_million_input_tokens: Optional[float] = None,
) -> dict:
    """Calculate a labeled hypothetical future-context scenario."""
    if (
        isinstance(baseline_input_tokens_per_turn, bool)
        or not isinstance(baseline_input_tokens_per_turn, (int, float))
        or baseline_input_tokens_per_turn < 0
    ):
        raise ValueError("baseline input tokens per turn must be nonnegative")
    if (
        isinstance(reduction_fraction, bool)
        or not isinstance(reduction_fraction, (int, float))
        or reduction_fraction < 0
        or reduction_fraction >= 1
    ):
        raise ValueError("reduction fraction must be in [0, 1)")
    if isinstance(future_turn_count, bool) or not isinstance(future_turn_count, int) or future_turn_count < 1:
        raise ValueError("future turn count must be a positive integer")
    if price_per_million_input_tokens is not None and (
        isinstance(price_per_million_input_tokens, bool)
        or not isinstance(price_per_million_input_tokens, (int, float))
        or price_per_million_input_tokens < 0
    ):
        raise ValueError("input token price must be nonnegative")
    baseline = baseline_input_tokens_per_turn * future_turn_count
    leaner = baseline * (1 - reduction_fraction)
    saved = baseline - leaner
    return {
        "scenario": "hypothetical_multi_turn_context_savings",
        "observed_data": False,
        "assumptions": {
            "baseline_input_tokens_per_turn": baseline_input_tokens_per_turn,
            "reduction_fraction": reduction_fraction,
            "future_turn_count": future_turn_count,
        },
        "baseline_input_tokens": baseline,
        "leaner_input_tokens": leaner,
        "saved_input_tokens": saved,
        "saved_input_cost": _cost(saved, price_per_million_input_tokens),
    }
