from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from research.phase_1.arms import ARMS, COMPONENT_SCREEN_ARMS
from research.phase_1.fixtures import build_fixture_corpus
from research.phase_2.aggregation import aggregate_results
from research.phase_2.design import (
    DEFAULT_MODEL_EFFORTS,
    DesignCell,
    FactorialDesign,
    build_ablation_screen_design,
    build_default_design,
)
from research.phase_2.harness import (
    ingest_adapter_failure,
    ingest_candidate,
    prepare_run,
)
from research.phase_2.variance import analyze_component_effects, analyze_variance_records


class PhaseTwoTests(unittest.TestCase):
    def test_default_factorial_cardinality_and_completeness(self):
        design = build_default_design(2)
        self.assertEqual(len(design.cells), 8 * 3 * 2 * 2)
        self.assertEqual(len({cell.cell_id for cell in design.cells}), len(design.cells))
        self.assertEqual({cell.task_id for cell in design.cells}, {
            task.task_id for task in build_fixture_corpus()
        })

    def test_invalid_cells_are_rejected(self):
        valid = build_default_design(1).cells[0]
        for replacement in (
            DesignCell.create("missing", valid.task_class, valid.model, valid.reasoning_effort, valid.arm, 1),
            DesignCell.create(valid.task_id, "wrong", valid.model, valid.reasoning_effort, valid.arm, 1),
            DesignCell.create(valid.task_id, valid.task_class, "unknown", "high", valid.arm, 1),
            DesignCell.create(valid.task_id, valid.task_class, valid.model, valid.reasoning_effort, valid.arm, 0),
        ):
            with self.assertRaises(ValueError):
                FactorialDesign([replacement])
        with self.assertRaises(ValueError):
            FactorialDesign([valid, valid])
        with self.assertRaises(ValueError):
            FactorialDesign([])

    def test_default_model_effort_pairings_are_enforced(self):
        valid = build_default_design(1).cells[0]
        bad_pairings = (
            ("gpt-5.6-luna", "default"),
            ("gpt-5.6-luna", "high"),
            ("grok-4.5", "maximum"),
            ("grok-4.5", "default"),
            ("composer-2.5", "high"),
            ("composer-2.5", "maximum"),
        )
        for model, effort in bad_pairings:
            with self.assertRaises(ValueError):
                FactorialDesign([
                    DesignCell.create(
                        valid.task_id, valid.task_class, model, effort, valid.arm, 1,
                    )
                ])
        for model, effort in DEFAULT_MODEL_EFFORTS:
            self.assertIn(
                (model, effort),
                {(cell.model, cell.reasoning_effort) for cell in build_default_design(1).cells},
            )

    def test_run_isolation_and_candidate_provenance(self):
        task = build_fixture_corpus()[0]
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            self.assertTrue((run_dir / "initial" / "source.py").exists())
            self.assertTrue((run_dir / "candidate").is_dir())
            with self.assertRaises(FileExistsError):
                prepare_run(cell, directory)
            with self.assertRaises(ValueError):
                prepare_run(cell.__class__(
                    cell.task_id, cell.task_class, cell.model, cell.reasoning_effort,
                    cell.arm, cell.repetition, "../escape",
                ), directory)
            with self.assertRaises(ValueError):
                ingest_candidate(
                    cell, run_dir, task.before, model=cell.model,
                    reasoning_effort=cell.reasoning_effort, execution_source="cursor_adapter",
                    turns=1, tool_calls=0,
                )
            self.assertFalse((run_dir / "candidate" / "result.json").exists())
            valid = ingest_candidate(
                cell, run_dir, task.after, model=cell.model,
                reasoning_effort=cell.reasoning_effort, execution_source="cursor_adapter",
                turns=2, tool_calls=3, input_tokens=10, output_tokens=5,
            )
            self.assertTrue(valid["record"]["tests"]["passed"])
            self.assertEqual(valid["actual"]["adapter_status"], "completed")
            self.assertIsNone(valid["actual"]["adapter_job_id"])
            self.assertEqual(json.loads((run_dir / "candidate" / "result.json").read_text()), valid)

    def test_nullable_adapter_telemetry_is_preserved(self):
        task = build_fixture_corpus()[0]
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            result = ingest_candidate(
                cell, run_dir, task.after, model=cell.model,
                reasoning_effort=cell.reasoning_effort, execution_source="cursor_adapter",
                turns=None, tool_calls=None,
            )
            self.assertIsNone(result["actual"]["turns"])
            self.assertIsNone(result["actual"]["tool_calls"])

    def test_adapter_status_and_job_provenance_are_persisted(self):
        task = build_fixture_corpus()[0]
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            result = ingest_candidate(
                cell, run_dir, task.after, model=cell.model,
                reasoning_effort=cell.reasoning_effort, execution_source="cursor_adapter",
                turns=None, tool_calls=None, adapter_status="timed_out",
                adapter_job_id="job-123",
            )
            self.assertEqual(result["actual"]["adapter_status"], "timed_out")
            self.assertEqual(result["actual"]["adapter_job_id"], "job-123")
            self.assertEqual(result["actual"]["execution_source"], "cursor_adapter")

    def test_adapter_failure_receipt_persists_provenance_without_candidate(self):
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            result = ingest_adapter_failure(
                cell,
                run_dir,
                model=cell.model,
                reasoning_effort=cell.reasoning_effort,
                execution_source="cursor_adapter",
                adapter_status="timed_out",
                failure_reason="adapter exceeded timeout",
                adapter_job_id="job-456",
            )
            self.assertEqual(
                json.loads((run_dir / "candidate" / "result.json").read_text()),
                result,
            )
            self.assertEqual(result["protocol"], "phase-2-controlled-ablation-v1")
            self.assertEqual(result["actual"]["adapter_job_id"], "job-456")
            self.assertIsNone(result["actual"]["input_tokens"])
            self.assertIsNone(result["actual"]["output_tokens"])
            self.assertIsNone(result["actual"]["total_tokens"])
            self.assertEqual(result["record"]["tests"]["tests_run"], 0)
            self.assertFalse(result["record"]["tests"]["passed"])
            self.assertIsNone(result["record"]["diff"])
            self.assertEqual(result["record"]["failure_reasons"], ["adapter exceeded timeout"])
            self.assertFalse((run_dir / "candidate" / "source.py").exists())

    def test_adapter_failure_receipt_refuses_overwrite(self):
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            ingest_adapter_failure(
                cell,
                run_dir,
                model=cell.model,
                reasoning_effort=cell.reasoning_effort,
                execution_source="cursor_adapter",
                adapter_status="failed",
                failure_reason="adapter crashed",
            )
            with self.assertRaises(FileExistsError):
                ingest_adapter_failure(
                    cell,
                    run_dir,
                    model=cell.model,
                    reasoning_effort=cell.reasoning_effort,
                    execution_source="cursor_adapter",
                    adapter_status="failed",
                    failure_reason="different failure",
                )

    def test_adapter_failure_receipt_rejects_completed_status(self):
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            with self.assertRaises(ValueError):
                ingest_adapter_failure(
                    cell,
                    run_dir,
                    model=cell.model,
                    reasoning_effort=cell.reasoning_effort,
                    execution_source="cursor_adapter",
                    adapter_status="completed",
                    failure_reason="should not be accepted",
                )
            self.assertFalse((run_dir / "candidate" / "result.json").exists())

    def test_actual_metadata_mismatch_is_rejected_before_artifacts(self):
        task = build_fixture_corpus()[0]
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            with self.assertRaises(ValueError):
                ingest_candidate(
                    cell, run_dir, task.after, model="wrong-model",
                    reasoning_effort=cell.reasoning_effort, execution_source="cursor_adapter",
                    turns=1, tool_calls=0,
                )
            with self.assertRaises(ValueError):
                ingest_candidate(
                    cell, run_dir, task.after, model=cell.model,
                    reasoning_effort="wrong-effort", execution_source="cursor_adapter",
                    turns=1, tool_calls=0,
                )
            self.assertFalse((run_dir / "candidate" / "result.json").exists())
            self.assertFalse((run_dir / "candidate" / "source.py").exists())

    def test_completed_cell_ingestion_refuses_overwrite(self):
        task = build_fixture_corpus()[0]
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            first = ingest_candidate(
                cell, run_dir, task.after, model=cell.model,
                reasoning_effort=cell.reasoning_effort, execution_source="cursor_adapter",
                turns=2, tool_calls=3, input_tokens=10, output_tokens=5, total_tokens=99,
            )
            original = (run_dir / "candidate" / "result.json").read_text()
            with self.assertRaises(FileExistsError):
                ingest_candidate(
                    cell, run_dir, "def summarize_total(cents):\n    return 'broken'\n",
                    model=cell.model, reasoning_effort=cell.reasoning_effort,
                    execution_source="cursor_adapter", turns=9, tool_calls=9,
                    input_tokens=1, output_tokens=1, total_tokens=2,
                )
            self.assertEqual((run_dir / "candidate" / "result.json").read_text(), original)
            self.assertEqual(json.loads(original), first)

    def test_total_tokens_are_not_synthesized(self):
        task = build_fixture_corpus()[0]
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            result = ingest_candidate(
                cell, run_dir, task.after, model=cell.model,
                reasoning_effort=cell.reasoning_effort, execution_source="cursor_adapter",
                turns=2, tool_calls=3, input_tokens=10, output_tokens=5,
            )
            self.assertEqual(result["actual"]["input_tokens"], 10)
            self.assertEqual(result["actual"]["output_tokens"], 5)
            self.assertIsNone(result["actual"]["total_tokens"])
            persisted = json.loads((run_dir / "candidate" / "result.json").read_text())
            self.assertIsNone(persisted["actual"]["total_tokens"])

    def test_invalid_candidate_is_measured_as_failure(self):
        cell = build_default_design(1).cells[0]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = prepare_run(cell, directory)
            result = ingest_candidate(
                cell, run_dir, "def summarize_total(cents):\n    return 'broken'\n",
                model=cell.model, reasoning_effort=cell.reasoning_effort,
                execution_source="cursor_adapter", turns=1, tool_calls=1,
            )
            self.assertFalse(result["record"]["tests"]["passed"])

    def test_aggregation_preserves_missing_tokens(self):
        cell = build_default_design(1).cells[0]
        records = []
        for input_tokens, output_tokens, total_tokens in ((10, 5, 15), (None, 7, None)):
            record = {
                "cell": cell.to_dict(),
                "actual": {
                    "adapter_status": "completed",
                    "input_tokens": input_tokens, "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                },
                "record": {
                    "diff": {"raw_net": -2}, "tests": {"passed": True},
                    "failure_reasons": [],
                },
            }
            records.append(record)
        group = aggregate_results(records)["groups"][0]
        self.assertEqual(group["adapter_failure_count"], 0)
        self.assertEqual(group["reported_input_tokens"], 10)
        self.assertEqual(group["reported_output_tokens"], 12)
        self.assertEqual(group["reported_total_tokens"], 15)
        self.assertEqual(group["runs_with_input_tokens"], 1)

    def test_aggregation_counts_non_completed_adapters_and_missing_status(self):
        cell = build_default_design(1).cells[0]
        records = []
        for status in ("completed", "failed", None):
            actual = {}
            if status is not None:
                actual["adapter_status"] = status
            records.append({
                "cell": cell.to_dict(),
                "actual": actual,
                "record": {
                    "diff": {"raw_net": 0}, "tests": {"passed": True},
                    "failure_reasons": [],
                },
            })
        group = aggregate_results(records)["groups"][0]
        self.assertEqual(group["adapter_failure_count"], 2)
        self.assertEqual(group["completed_count"], 1)

    def test_aggregation_excludes_adapter_failure_receipts(self):
        cell = build_default_design(1).cells[0]
        completed = {
            "cell": cell.to_dict(),
            "actual": {
                "adapter_status": "completed",
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
            },
            "record": {
                "diff": {"raw_net": 4},
                "tests": {"passed": True},
                "failure_reasons": [],
            },
        }
        failure = {
            "cell": cell.to_dict(),
            "actual": {
                "adapter_status": "failed",
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
            },
            "record": {
                "diff": None,
                "tests": {"passed": False, "tests_run": 0},
                "failure_reasons": ["adapter crashed"],
            },
        }
        group = aggregate_results([completed, failure])["groups"][0]
        self.assertEqual(group["run_count"], 2)
        self.assertEqual(group["completed_count"], 1)
        self.assertEqual(group["adapter_failure_count"], 1)
        self.assertEqual(group["passed_tests"], 1)
        self.assertEqual(group["failure_count"], 0)
        self.assertEqual(group["raw_loc_total"], 4)
        self.assertEqual(group["reported_total_tokens"], 15)

    def test_design_manifest_is_deterministic(self):
        first = build_default_design(1).to_dict()
        second = build_default_design(1).to_dict()
        self.assertEqual(first, second)

    def test_task_subset_is_canonical_and_validated(self):
        selected = [
            "control-rename",
            "refactor-shared-strip",
            "feature-format-total",
            "cleanup-legacy-flag",
        ]
        design = build_default_design(5, task_ids=selected)
        self.assertEqual(len(design.cells), 4 * 3 * 2 * 5)
        self.assertEqual(
            [task["task_id"] for task in design.to_dict()["tasks"]],
            ["feature-format-total", "refactor-shared-strip",
             "cleanup-legacy-flag", "control-rename"],
        )
        self.assertEqual(
            design.to_dict(),
            build_default_design(5, task_ids=reversed(selected)).to_dict(),
        )
        with self.assertRaisesRegex(ValueError, "unknown task IDs"):
            build_default_design(1, task_ids=["not-a-fixture"])

    def test_variance_reports_sample_sd_and_observed_token_missingness(self):
        task = build_fixture_corpus()[0]
        records = []
        for arm, raw_values in (
            ("neutral_control", [1, 3]),
            ("subtractive_rubric", [2, 6]),
        ):
            for repetition, raw_net in enumerate(raw_values, start=1):
                cell = next(
                    cell for cell in build_default_design(2).cells
                    if cell.task_id == task.task_id and cell.arm == arm
                    and cell.model == "gpt-5.6-luna"
                )
                records.append({
                    "cell": DesignCell.create(
                        cell.task_id, cell.task_class, cell.model,
                        cell.reasoning_effort, cell.arm, repetition,
                    ).to_dict(),
                    "actual": {
                        "adapter_status": "completed",
                        "input_tokens": 10 if repetition == 1 else None,
                        "output_tokens": 5 + repetition,
                        "total_tokens": None,
                    },
                    "record": {
                        "diff": {"raw_net": raw_net},
                        "tests": {
                            "passed": repetition == 1 or arm == "subtractive_rubric"
                        },
                    },
                })
        result = analyze_variance_records(records)
        neutral = next(group for group in result["groups"] if group["arm"] == "neutral_control")
        self.assertEqual(neutral["raw_net_sample_sd"], 2**0.5)
        self.assertEqual(neutral["token_stats"]["input_tokens"]["count"], 1)
        self.assertIsNone(neutral["token_stats"]["total_tokens"]["mean"])
        pair = result["paired_comparisons"][0]
        self.assertEqual(pair["status"], "matched")
        self.assertEqual(pair["raw_net_deltas"], [1, 3])
        self.assertEqual(pair["both_behavior_pass_count"], 1)
        self.assertEqual(pair["neutral_only_behavior_pass_count"], 0)
        self.assertEqual(pair["subtractive_only_behavior_pass_count"], 1)

    def test_variance_excludes_adapter_failures_and_retains_status_counts(self):
        cell = build_default_design(1).cells[0].to_dict()
        records = []
        for status in ("failed", "timed_out", None):
            records.append({
                "cell": cell,
                "actual": {} if status is None else {"adapter_status": status},
                "record": {},
            })
        result = analyze_variance_records(records)
        group = result["groups"][0]
        self.assertEqual(group["completed_count"], 0)
        self.assertEqual(group["status_counts"], {"failed": 1, "missing": 1, "timed_out": 1})
        self.assertEqual(result["status_counts"], {"failed": 1, "missing": 1, "timed_out": 1})

    def test_variance_rejects_duplicate_and_misaligned_repetitions(self):
        cell = build_default_design(1).cells[0].to_dict()
        receipt = {
            "cell": cell,
            "actual": {"adapter_status": "completed"},
            "record": {"diff": {"raw_net": 0}, "tests": {"passed": True}},
        }
        with self.assertRaisesRegex(ValueError, "duplicate completed repetition"):
            analyze_variance_records([receipt, receipt])
        subtractive_cell = dict(cell, arm="subtractive_rubric")
        subtractive_cell["cell_id"] = DesignCell.create(
            subtractive_cell["task_id"], subtractive_cell["task_class"],
            subtractive_cell["model"], subtractive_cell["reasoning_effort"],
            subtractive_cell["arm"], subtractive_cell["repetition"],
        ).cell_id
        result = analyze_variance_records([
            receipt,
            dict(receipt, cell=subtractive_cell),
        ])
        self.assertEqual(result["paired_comparisons"][0]["status"], "matched")
        extra = dict(receipt, cell=DesignCell.create(
            cell["task_id"], cell["task_class"], cell["model"],
            cell["reasoning_effort"], cell["arm"], 2,
        ).to_dict())
        result = analyze_variance_records([receipt, extra, dict(receipt, cell=subtractive_cell)])
        self.assertEqual(result["paired_comparisons"][0]["status"], "unmatched")

    def test_cli_subset_plan_and_variance_smoke(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "design.json"
            runs_root = root / "runs"
            command = [
                "python", "-m", "research.phase_2.cli", "plan",
                "--output", str(manifest), "--runs-root", str(runs_root),
                "--repetitions", "1", "--tasks", "control-rename",
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            planned = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(len(planned["cells"]), 6)
            self.assertEqual(planned["arms"], ["neutral_control", "subtractive_rubric"])
            receipt_path = root / "receipt.json"
            receipt_path.write_text(json.dumps({
                "cell": planned["cells"][0],
                "actual": {"adapter_status": "completed"},
                "record": {
                    "diff": {"raw_net": 0},
                    "tests": {"passed": True},
                },
            }), encoding="utf-8")
            output = root / "variance.json"
            subprocess.run([
                "python", "-m", "research.phase_2.cli", "variance",
                "--output", str(output), str(receipt_path),
            ], check=True, capture_output=True, text=True)
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["protocol"],
                "phase-2-controlled-ablation-variance-v1",
            )

    def test_explicit_arms_list_is_validated_and_complete(self):
        design = build_default_design(
            1,
            task_ids=["refactor-shared-strip"],
            arms=["neutral_control", "task_type_gate", "delete_first_gate"],
        )
        self.assertEqual(len(design.cells), 9)
        self.assertEqual(
            design.to_dict()["arms"],
            ["neutral_control", "task_type_gate", "delete_first_gate"],
        )
        with self.assertRaisesRegex(ValueError, "unknown arms"):
            build_default_design(1, arms=["not-an-arm"])
        with self.assertRaisesRegex(ValueError, "unique"):
            build_default_design(1, arms=["neutral_control", "neutral_control"])

    def test_ablation_screen_design_has_120_cells(self):
        design = build_ablation_screen_design(5)
        self.assertEqual(len(design.cells), 120)
        payload = design.to_dict()
        self.assertEqual(payload["protocol"], "phase-2-component-ablation-v1")
        self.assertEqual(payload["arms"], list(COMPONENT_SCREEN_ARMS))
        self.assertEqual(
            payload["arms"][-1],
            "task_type_delete_first_net_loc_budget",
        )
        self.assertNotIn("subtractive_rubric", payload["arms"])
        self.assertEqual(
            {task["task_id"] for task in payload["tasks"]},
            {"refactor-shared-strip"},
        )
        self.assertEqual(len({cell.cell_id for cell in design.cells}), 120)
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "design.json"
            design.write_manifest(manifest)
            self.assertEqual(
                json.loads(manifest.read_text(encoding="utf-8")),
                payload,
            )

    def test_variance_compares_each_treatment_arm_to_neutral(self):
        task = next(
            task for task in build_fixture_corpus()
            if task.task_id == "refactor-shared-strip"
        )
        records = []
        for arm, raw_net in (
            ("neutral_control", 4),
            ("task_type_gate", 2),
            ("subtractive_rubric", -2),
        ):
            cell = DesignCell.create(
                task.task_id, task.task_type, "gpt-5.6-luna", "maximum", arm, 1,
            )
            records.append({
                "cell": cell.to_dict(),
                "actual": {"adapter_status": "completed", "input_tokens": 10},
                "record": {
                    "diff": {"raw_net": raw_net},
                    "tests": {"passed": True},
                },
            })
        result = analyze_variance_records(records)
        treatments = {
            item["treatment_arm"]: item for item in result["paired_comparisons"]
        }
        self.assertEqual(set(treatments), {"task_type_gate", "subtractive_rubric"})
        self.assertEqual(treatments["task_type_gate"]["status"], "matched")
        self.assertEqual(treatments["task_type_gate"]["raw_net_deltas"], [-2])
        self.assertEqual(treatments["subtractive_rubric"]["status"], "matched")
        self.assertEqual(
            treatments["subtractive_rubric"]["subtractive_only_behavior_pass_count"],
            0,
        )
        self.assertEqual(
            treatments["subtractive_rubric"]["both_behavior_pass_count"],
            1,
        )

    def _component_screen_receipts(self, raw_net_by_arm_rep, *, behavior_pass=True):
        task = next(
            task for task in build_fixture_corpus()
            if task.task_id == "refactor-shared-strip"
        )
        records = []
        for arm in COMPONENT_SCREEN_ARMS:
            for repetition, raw_net in raw_net_by_arm_rep[arm]:
                cell = DesignCell.create(
                    task.task_id, task.task_type, "gpt-5.6-luna", "maximum",
                    arm, repetition,
                )
                passed = (
                    behavior_pass(arm, repetition)
                    if callable(behavior_pass) else bool(behavior_pass)
                )
                records.append({
                    "cell": cell.to_dict(),
                    "actual": {"adapter_status": "completed"},
                    "record": {
                        "diff": {"raw_net": raw_net},
                        "tests": {"passed": passed},
                    },
                })
        return records

    def test_component_effects_exact_coverage_and_deterministic_deltas(self):
        # raw_net = 100*T + 10*D + B, constant across repetitions 1..2
        raw_net_by_arm_rep = {}
        for arm in COMPONENT_SCREEN_ARMS:
            components = ARMS[arm].components
            value = (
                (100 if "T" in components else 0)
                + (10 if "D" in components else 0)
                + (1 if "B" in components else 0)
            )
            raw_net_by_arm_rep[arm] = [(1, value), (2, value + 2)]
        records = self._component_screen_receipts(
            raw_net_by_arm_rep,
            behavior_pass=lambda arm, repetition: not (
                arm == "delete_first_gate" and repetition == 2
            ),
        )
        report = analyze_component_effects(records)
        self.assertEqual(report["protocol"], "phase-2-component-effects-v1")
        effects = {
            item["factor"]: item for item in report["effects"]
        }
        self.assertEqual(set(effects), {"T", "D", "B"})
        self.assertEqual(
            effects["T"]["on_arms"],
            [
                "task_type_gate",
                "task_type_delete_first",
                "task_type_net_loc_budget",
                "task_type_delete_first_net_loc_budget",
            ],
        )
        self.assertEqual(
            effects["T"]["off_arms"],
            [
                "neutral_control",
                "delete_first_gate",
                "semantic_net_loc_budget",
                "delete_first_net_loc_budget",
            ],
        )
        # mean(on)-mean(off) = 100 for T, 10 for D, 1 for B at every repetition
        self.assertEqual(effects["T"]["raw_net_deltas"], [100.0, 100.0])
        self.assertEqual(effects["D"]["raw_net_deltas"], [10.0, 10.0])
        self.assertEqual(effects["B"]["raw_net_deltas"], [1.0, 1.0])
        self.assertEqual(effects["T"]["raw_net_delta_mean"], 100.0)
        self.assertEqual(effects["T"]["raw_net_delta_sample_sd"], 0.0)
        self.assertEqual(effects["T"]["on_behavior_pass_count"], 8)
        self.assertEqual(effects["T"]["off_behavior_pass_count"], 7)

        variance = analyze_variance_records(records)
        self.assertIn("component_effects", variance)
        self.assertEqual(variance["component_effects"], report)
        # Historical two-arm fields remain present and unchanged in shape.
        self.assertEqual(variance["protocol"], "phase-2-controlled-ablation-variance-v1")
        self.assertTrue(variance["paired_comparisons"])

    def test_component_effects_rejects_missing_arms(self):
        raw_net_by_arm_rep = {
            arm: [(1, 0)] for arm in COMPONENT_SCREEN_ARMS
        }
        records = self._component_screen_receipts(raw_net_by_arm_rep)
        incomplete = [
            receipt for receipt in records
            if receipt["cell"]["arm"] != "semantic_net_loc_budget"
        ]
        with self.assertRaisesRegex(ValueError, "exact coverage"):
            analyze_component_effects(incomplete)
        two_arm = analyze_variance_records([
            receipt for receipt in records
            if receipt["cell"]["arm"] in {"neutral_control", "task_type_gate"}
        ])
        self.assertNotIn("component_effects", two_arm)

    def test_component_effects_rejects_duplicate_repetitions(self):
        raw_net_by_arm_rep = {
            arm: [(1, 0)] for arm in COMPONENT_SCREEN_ARMS
        }
        records = self._component_screen_receipts(raw_net_by_arm_rep)
        duplicate = dict(records[0])
        with self.assertRaisesRegex(ValueError, "duplicate completed repetition"):
            analyze_component_effects(records + [duplicate])

    def test_component_effects_fail_closed_through_variance_on_unmatched_reps(self):
        # Full COMPONENT_SCREEN_ARMS set enters the variance branch, but mismatched
        # repetition IDs must propagate from analyze_component_effects (not be swallowed).
        raw_net_by_arm_rep = {
            arm: [(1, 0)] for arm in COMPONENT_SCREEN_ARMS
        }
        raw_net_by_arm_rep["semantic_net_loc_budget"] = [(2, 0)]
        records = self._component_screen_receipts(raw_net_by_arm_rep)
        with self.assertRaisesRegex(ValueError, "matched unique repetition"):
            analyze_component_effects(records)
        with self.assertRaisesRegex(ValueError, "matched unique repetition"):
            analyze_variance_records(records)


if __name__ == "__main__":
    unittest.main()
