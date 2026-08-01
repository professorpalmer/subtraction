"""Deterministic summaries of Phase 2 result artifacts."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping


def _sum_reported(values):
    values = [value for value in values if value is not None]
    return sum(values) if values else None


def aggregate_results(results: Iterable[Mapping]) -> dict:
    groups = defaultdict(list)
    for result in results:
        cell = result["cell"]
        groups[(cell["model"], cell["arm"])].append(result)
    summaries = []
    for (model, arm), records in sorted(groups.items()):
        completed_records = [
            record for record in records
            if record.get("actual", {}).get("adapter_status") == "completed"
        ]
        records_by_pass = [record["record"] for record in completed_records]
        raw_loc = [record["diff"]["raw_net"] for record in records_by_pass]
        summaries.append({
            "model": model,
            "arm": arm,
            "run_count": len(records),
            "completed_count": len(completed_records),
            "adapter_failure_count": sum(
                record.get("actual", {}).get("adapter_status") != "completed"
                for record in records
            ),
            "passed_tests": sum(record["tests"]["passed"] for record in records_by_pass),
            "failure_count": sum(bool(record["failure_reasons"]) for record in records_by_pass),
            "raw_loc_total": sum(raw_loc),
            "raw_loc_mean": sum(raw_loc) / len(raw_loc) if raw_loc else None,
            "reported_input_tokens": _sum_reported(
                record["actual"].get("input_tokens") for record in completed_records
            ),
            "reported_output_tokens": _sum_reported(
                record["actual"].get("output_tokens") for record in completed_records
            ),
            "reported_total_tokens": _sum_reported(
                record["actual"].get("total_tokens") for record in completed_records
            ),
            "runs_with_input_tokens": sum(
                record["actual"].get("input_tokens") is not None
                for record in completed_records
            ),
            "runs_with_output_tokens": sum(
                record["actual"].get("output_tokens") is not None
                for record in completed_records
            ),
            "runs_with_total_tokens": sum(
                record["actual"].get("total_tokens") is not None
                for record in completed_records
            ),
        })
    return {"protocol": "phase-2-controlled-ablation-v1", "groups": summaries}


def aggregate_result_files(paths: Iterable[str]) -> dict:
    import json
    from pathlib import Path
    return aggregate_results(json.loads(Path(path).read_text()) for path in paths)
