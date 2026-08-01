from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research.phase_1.fixtures import build_fixture_corpus
from research.phase_2.aggregation import aggregate_results
from research.phase_2.design import (
    DEFAULT_MODEL_EFFORTS,
    DesignCell,
    FactorialDesign,
    build_default_design,
)
from research.phase_2.harness import ingest_candidate, prepare_run


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

    def test_aggregation_counts_non_completed_adapters_and_defaults_missing_status(self):
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
        self.assertEqual(group["adapter_failure_count"], 1)

    def test_design_manifest_is_deterministic(self):
        first = build_default_design(1).to_dict()
        second = build_default_design(1).to_dict()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
