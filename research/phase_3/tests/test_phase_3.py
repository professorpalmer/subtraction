from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from research.phase_3.analysis import (
    analyze_files,
    analyze_records,
    calculate_context_savings,
    load_result_files,
    _records_from_document,
)


def result(task_id="task", model="model", arm="neutral_control", repetition=1,
           input_tokens=100, output_tokens=10, total_tokens=None,
           status="completed", protocol="phase-2-controlled-ablation-v1",
           reasoning_effort=None):
    actual = {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }
    if status is not None:
        actual["adapter_status"] = status
    cell = {
        "task_id": task_id,
        "model": model,
        "arm": arm,
        "repetition": repetition,
    }
    if reasoning_effort is not None:
        cell["reasoning_effort"] = reasoning_effort
    return {
        "protocol": protocol,
        "cell": cell,
        "actual": actual,
    }


class PhaseThreeTests(unittest.TestCase):
    def test_list_file_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.json"
            path.write_text(json.dumps([result(), result(repetition=2)]))
            self.assertEqual(len(load_result_files([str(path)])), 2)

    def test_status_exclusion_requires_explicit_legacy_schema(self):
        records = [
            result(input_tokens=10, status="completed"),
            result(input_tokens=20, status="failed"),
            result(input_tokens=30, status=None),
            result(input_tokens=40, status=None, protocol="phase-2-controlled-ablation-v0"),
        ]
        analysis = analyze_records(records)
        self.assertEqual(analysis["included_completed_record_count"], 2)
        self.assertEqual(analysis["excluded_record_count"], 2)
        self.assertEqual(analysis["excluded_by_adapter_status"], {"failed": 1, "missing": 1})
        self.assertEqual(analysis["summaries"][0]["reported_input_tokens"], 50)

    def test_matched_arm_token_deltas_and_means(self):
        records = [
            result(arm="neutral_control", input_tokens=100, output_tokens=10, total_tokens=110),
            result(arm="subtractive_rubric", input_tokens=80, output_tokens=12, total_tokens=92),
        ]
        comparison = analyze_records(records)["matched_arm_comparisons"][0]
        self.assertEqual(comparison["status"], "matched")
        self.assertEqual(comparison["tokens"]["input_tokens"]["delta_subtractive_minus_neutral"], -20)
        self.assertEqual(comparison["tokens"]["total_tokens"]["neutral_mean"], 110)
        self.assertAlmostEqual(comparison["tokens"]["total_tokens"]["relative_change"], -18 / 110)

    def test_unequal_and_missing_conditions_are_not_compared(self):
        records = [
            result(task_id="unequal", arm="neutral_control"),
            result(task_id="unequal", arm="neutral_control", repetition=2),
            result(task_id="unequal", arm="subtractive_rubric"),
            result(task_id="missing", arm="neutral_control"),
        ]
        comparisons = analyze_records(records)["matched_arm_comparisons"]
        self.assertEqual(comparisons[0]["status"], "unmatched")
        self.assertEqual(comparisons[0]["reason"], "missing arm")
        self.assertEqual(comparisons[1]["reason"], "unequal repetition counts")

    def test_pricing_and_missing_cost_behavior(self):
        records = [
            result(model="priced", input_tokens=100, output_tokens=10, total_tokens=None),
            result(model="unpriced", input_tokens=100, output_tokens=None, total_tokens=100),
        ]
        analysis = analyze_records(records, {"priced": {"input": 2, "output": 4}})
        priced, unpriced = analysis["summaries"]
        self.assertEqual(priced["input_tokens_cost"], 0.0002)
        self.assertIsNone(priced["total_tokens_cost"])
        self.assertIsNone(unpriced["input_tokens_cost"])
        self.assertIsNone(unpriced["total_tokens_cost"])

    def test_scenario_arithmetic_and_validation(self):
        scenario = calculate_context_savings(100, 0.25, 4, 2)
        self.assertFalse(scenario["observed_data"])
        self.assertEqual(scenario["baseline_input_tokens"], 400)
        self.assertEqual(scenario["leaner_input_tokens"], 300)
        self.assertEqual(scenario["saved_input_tokens"], 100)
        self.assertEqual(scenario["saved_input_cost"], 0.0002)
        for arguments in ((100, -0.1, 4), (100, 1, 4), (100, 0.2, 0)):
            with self.assertRaises(ValueError):
                calculate_context_savings(*arguments)

    def test_analysis_is_deterministic(self):
        first = analyze_records([
            result(model="z", arm="neutral_control"),
            result(model="a", arm="neutral_control"),
        ])
        second = analyze_records([
            result(model="a", arm="neutral_control"),
            result(model="z", arm="neutral_control"),
        ])
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_cli_analyze_and_scenario_smoke_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "inputs.json"
            analysis_output = root / "analysis.json"
            scenario_output = root / "scenario.json"
            inputs.write_text(json.dumps([result()]))
            subprocess.run(
                [sys.executable, "-m", "research.phase_3.cli", "analyze",
                 str(inputs), "--output", str(analysis_output)],
                check=True,
            )
            subprocess.run(
                [sys.executable, "-m", "research.phase_3.cli", "scenario",
                 "--baseline-input-tokens-per-turn", "100",
                 "--reduction-fraction", "0.2", "--future-turn-count", "5",
                 "--output", str(scenario_output)],
                check=True,
            )
            self.assertEqual(json.loads(analysis_output.read_text())["included_completed_record_count"], 1)
            self.assertEqual(json.loads(scenario_output.read_text())["saved_input_tokens"], 100)

    def test_summary_artifact_is_rejected(self):
        summary = {"protocol": "phase-2-controlled-ablation-v1", "groups": []}
        with self.assertRaises(ValueError) as context:
            _records_from_document(summary, Path("summary.json"))
        self.assertIn("receipt records", str(context.exception))

    def test_unequal_token_coverage_blocks_comparison(self):
        records = [
            result(arm="neutral_control", input_tokens=100, output_tokens=10, total_tokens=110),
            result(arm="subtractive_rubric", input_tokens=80, output_tokens=None, total_tokens=None),
        ]
        comparison = analyze_records(records)["matched_arm_comparisons"][0]
        self.assertEqual(comparison["status"], "unmatched")
        self.assertEqual(comparison["reason"], "unequal token coverage for output_tokens")
        self.assertNotIn("tokens", comparison)

    def test_misaligned_repetition_ids_block_comparison(self):
        records = [
            result(arm="neutral_control", repetition=1),
            result(arm="neutral_control", repetition=2),
            result(arm="subtractive_rubric", repetition=1),
            result(arm="subtractive_rubric", repetition=3),
        ]
        comparison = analyze_records(records)["matched_arm_comparisons"][0]
        self.assertEqual(comparison["status"], "unmatched")
        self.assertEqual(comparison["reason"], "misaligned repetition ids")
        self.assertNotIn("tokens", comparison)

    def test_scalar_pricing_does_not_apply_to_all_fields(self):
        records = [result(model="priced", input_tokens=100, output_tokens=10, total_tokens=110)]
        analysis = analyze_records(records, {"priced": 2})
        summary = analysis["summaries"][0]
        self.assertIsNone(summary["input_tokens_cost"])
        self.assertIsNone(summary["output_tokens_cost"])
        self.assertIsNone(summary["total_tokens_cost"])

    def test_object_pricing_prices_input_and_output_independently(self):
        records = [
            result(model="priced", input_tokens=100, output_tokens=10, total_tokens=110),
        ]
        analysis = analyze_records(records, {"priced": {"input": 2, "output": 4}})
        summary = analysis["summaries"][0]
        self.assertEqual(summary["input_tokens_cost"], 0.0002)
        self.assertEqual(summary["output_tokens_cost"], 0.00004)
        self.assertIsNone(summary["total_tokens_cost"])

    def test_reasoning_effort_separates_groups_and_comparisons(self):
        records = [
            result(arm="neutral_control", reasoning_effort="high", input_tokens=100),
            result(arm="subtractive_rubric", reasoning_effort="high", input_tokens=80),
            result(arm="neutral_control", reasoning_effort="default", input_tokens=50),
            result(arm="subtractive_rubric", reasoning_effort="default", input_tokens=40),
        ]
        analysis = analyze_records(records)
        efforts = {summary["reasoning_effort"] for summary in analysis["summaries"]}
        self.assertEqual(efforts, {"high", "default"})
        comparisons = analysis["matched_arm_comparisons"]
        self.assertEqual(len(comparisons), 2)
        by_effort = {item["reasoning_effort"]: item for item in comparisons}
        self.assertEqual(by_effort["high"]["status"], "matched")
        self.assertEqual(
            by_effort["high"]["tokens"]["input_tokens"]["delta_subtractive_minus_neutral"],
            -20,
        )
        self.assertEqual(by_effort["default"]["status"], "matched")
        self.assertEqual(
            by_effort["default"]["tokens"]["input_tokens"]["delta_subtractive_minus_neutral"],
            -10,
        )

    def test_multi_arm_comparisons_vs_neutral(self):
        records = [
            result(arm="neutral_control", input_tokens=100, output_tokens=10, total_tokens=110),
            result(arm="task_type_gate", input_tokens=90, output_tokens=10, total_tokens=100),
            result(arm="subtractive_rubric", input_tokens=80, output_tokens=10, total_tokens=90),
        ]
        comparisons = {
            item["treatment_arm"]: item
            for item in analyze_records(records)["matched_arm_comparisons"]
        }
        self.assertEqual(set(comparisons), {"subtractive_rubric", "task_type_gate"})
        self.assertEqual(comparisons["task_type_gate"]["status"], "matched")
        self.assertEqual(
            comparisons["task_type_gate"]["tokens"]["input_tokens"]["delta_treatment_minus_neutral"],
            -10,
        )
        self.assertNotIn(
            "delta_subtractive_minus_neutral",
            comparisons["task_type_gate"]["tokens"]["input_tokens"],
        )
        self.assertEqual(
            comparisons["subtractive_rubric"]["tokens"]["input_tokens"][
                "delta_subtractive_minus_neutral"
            ],
            -20,
        )


if __name__ == "__main__":
    unittest.main()
