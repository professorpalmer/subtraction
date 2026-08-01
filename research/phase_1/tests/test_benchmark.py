from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.phase_1.arms import (
    ARM_NAMES,
    COMPONENT_B,
    COMPONENT_D,
    COMPONENT_SCREEN_ARMS,
    COMPONENT_T,
    ARMS,
    choose_arm,
    compose_components,
    prompt_for,
)
from research.phase_1.fixtures import build_fixture_corpus
from research.phase_1.harness import (
    TokenUsage,
    aggregate_token_usage,
    classify_patch,
    measure_candidate_patch,
    run_dry_run,
    run_task,
)
from research.phase_1.metrics import measure_diff


class BenchmarkTests(unittest.TestCase):
    def test_fixture_corpus_has_all_task_classes_and_valid_oracles(self):
        tasks = build_fixture_corpus()
        self.assertEqual({task.task_type for task in tasks}, {"feature", "refactor", "cleanup", "measurement_control"})
        self.assertTrue(all(task.is_valid() for task in tasks))

    def test_feature_format_total_uses_cents_contract(self):
        tasks = {task.task_id: task for task in build_fixture_corpus()}
        task = tasks["feature-format-total"]
        self.assertTrue(task.is_valid())
        self.assertIn("$12.50", task.instruction)
        self.assertIn("$1,250.00", task.instruction)
        whole_dollar = """def summarize_total(cents):
    return f"{cents / 100:.2f}"

def format_total(cents):
    return f"${cents:,}"
"""
        self.assertFalse(task.is_source_valid(whole_dollar))
        record = measure_candidate_patch(
            task,
            "neutral_control",
            task.after,
            execution_source="offline_fixture",
            turns=None,
            tool_calls=None,
            dry_run=True,
        )
        self.assertTrue(record.tests.passed)
        self.assertEqual(record.failure_reasons, ())
        self.assertGreater(record.diff.raw_net, 0)

    def test_arm_routing_is_explicit_and_feature_safe(self):
        for arm in ARM_NAMES:
            self.assertIn("Feature task", prompt_for(arm, "feature", "add a feature"))
            choose_arm(arm, "cleanup")
        neutral_prompt = prompt_for("neutral_control", "cleanup", "remove dead code")
        self.assertNotIn("prove semantic deletions", neutral_prompt)
        subtractive_prompt = prompt_for("subtractive_rubric", "cleanup", "remove dead code")
        self.assertIn("prove semantic deletions", subtractive_prompt)
        with self.assertRaises(ValueError):
            choose_arm("missing", "cleanup")

    def test_atomic_components_compose_in_canonical_order(self):
        self.assertEqual(compose_components(("T",)), COMPONENT_T)
        self.assertEqual(compose_components(("D",)), COMPONENT_D)
        self.assertEqual(compose_components(("B",)), COMPONENT_B)
        self.assertEqual(
            compose_components(("B", "T", "D")),
            f"{COMPONENT_T} {COMPONENT_D} {COMPONENT_B}",
        )
        self.assertEqual(
            compose_components(name for name in ("B", "T", "D")),
            f"{COMPONENT_T} {COMPONENT_D} {COMPONENT_B}",
        )
        with self.assertRaises(ValueError):
            compose_components(())
        with self.assertRaises(ValueError):
            compose_components(("T", "X"))

    def test_component_screen_covers_all_eight_combinations(self):
        self.assertEqual(len(COMPONENT_SCREEN_ARMS), 8)
        self.assertEqual(
            COMPONENT_SCREEN_ARMS[-1],
            "task_type_delete_first_net_loc_budget",
        )
        self.assertNotIn("subtractive_rubric", COMPONENT_SCREEN_ARMS)
        self.assertIn("subtractive_rubric", ARMS)
        expected = {
            frozenset(),
            frozenset({"T"}),
            frozenset({"D"}),
            frozenset({"B"}),
            frozenset({"T", "D"}),
            frozenset({"T", "B"}),
            frozenset({"D", "B"}),
            frozenset({"T", "D", "B"}),
        }
        actual = {ARMS[name].components for name in COMPONENT_SCREEN_ARMS}
        self.assertEqual(actual, expected)
        atomic_tdb = ARMS["task_type_delete_first_net_loc_budget"]
        self.assertEqual(atomic_tdb.components, frozenset({"T", "D", "B"}))
        self.assertEqual(
            atomic_tdb.prompt,
            compose_components(("T", "D", "B")),
        )
        self.assertNotEqual(
            atomic_tdb.prompt,
            ARMS["subtractive_rubric"].prompt,
        )
        for name in COMPONENT_SCREEN_ARMS:
            prompt = prompt_for(name, "feature", "add a feature")
            self.assertIn("Feature task", prompt)

    def test_atomic_component_presence_and_legacy_routing(self):
        common_routing = "Task type: cleanup. Preserve behavior and keep tests green."
        legacy_routing = (
            "Maintenance task: do not force additions; prove semantic deletions."
        )
        for name in COMPONENT_SCREEN_ARMS:
            if name == "neutral_control":
                continue
            prompt = prompt_for(name, "cleanup", "remove dead code")
            self.assertTrue(prompt.startswith(common_routing))
            self.assertNotIn(legacy_routing, prompt)
            components = ARMS[name].components
            if "T" in components:
                self.assertIn(COMPONENT_T, prompt)
            else:
                self.assertNotIn(COMPONENT_T, prompt)
            if "D" in components:
                self.assertIn(COMPONENT_D, prompt)
                self.assertIn("prove semantic deletions", prompt)
            else:
                self.assertNotIn(COMPONENT_D, prompt)
                self.assertNotIn("prove semantic deletions", prompt)
                self.assertNotIn("inventory callers", prompt.lower())
            if "B" in components:
                self.assertIn(COMPONENT_B, prompt)
            else:
                self.assertNotIn(COMPONENT_B, prompt)
            self.assertEqual(ARMS[name].requires_delete, "D" in components)
        # Legacy composite keeps historical routing + bundled prompt semantics.
        subtractive_prompt = prompt_for(
            "subtractive_rubric", "cleanup", "remove dead code"
        )
        self.assertTrue(subtractive_prompt.startswith(legacy_routing))
        self.assertIn("prove semantic deletions", subtractive_prompt)
        self.assertEqual(
            ARMS["subtractive_rubric"].prompt,
            (
                "For refactor or cleanup work, add no capability: inventory references, "
                "identify safe deletions, preserve behavior, and run tests. "
                "Feature work remains sign-matched."
            ),
        )
        self.assertFalse(ARMS["subtractive_rubric"].requires_delete)

    def test_diff_distinguishes_churn_and_move_like_changes(self):
        metrics = measure_diff("def old():\n    return 1\n", "def new():\n    return 1\n")
        self.assertEqual(metrics.raw_added, 1)
        self.assertEqual(metrics.raw_removed, 1)
        self.assertTrue(metrics.likely_move_or_copy)
        self.assertEqual(metrics.structural_symbols_added, 1)
        self.assertEqual(metrics.structural_symbols_removed, 1)
        self.assertEqual(metrics.structural_symbols_net, 0)

    def test_token_aggregation_preserves_missing_adapter_values(self):
        task = build_fixture_corpus()[0]
        first = run_task(task, "neutral_control")
        second = run_task(task, "neutral_control")
        first = first.__class__(**{**first.to_dict(), "token_usage": TokenUsage(10, 5)})
        second = second.__class__(**{**second.to_dict(), "token_usage": TokenUsage(None, 7)})
        result = aggregate_token_usage([first, second])
        self.assertEqual(result["reported_input_tokens"], 10)
        self.assertEqual(result["reported_output_tokens"], 12)

    def test_dry_run_exercises_every_task_and_arm(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.json"
            records = run_dry_run(path)
            self.assertEqual(len(records), len(build_fixture_corpus()) * len(ARM_NAMES))
            self.assertTrue(path.exists())
            self.assertTrue(all(record.dry_run and record.tests.passed for record in records))
            self.assertTrue(all(record.execution_source == "offline_fixture" for record in records))
            self.assertTrue(all(record.model is None and record.reasoning_effort is None for record in records))

    def test_expected_sign_and_class_are_enforced(self):
        task = build_fixture_corpus()[0]
        invalid = task.__class__(**{**task.__dict__, "expected_sign": "negative"})
        record = run_task(invalid, "neutral_control")
        self.assertIn("expected_negative_diff", record.failure_reasons)

    def test_delete_first_gate_requires_deletion_for_maintenance(self):
        task = build_fixture_corpus()[3]
        record = run_task(task, "delete_first_gate")
        self.assertNotIn("delete_first_gate_violation", record.failure_reasons)
        control = build_fixture_corpus()[-1]
        record = run_task(control, "delete_first_gate")
        self.assertNotIn("delete_first_gate_violation", record.failure_reasons)
        unchanged = task.__class__(**{**task.__dict__, "before": task.after})
        record = run_task(unchanged, "delete_first_gate")
        self.assertIn("delete_first_gate_violation", record.failure_reasons)

    def test_cleanup_fixtures_are_distinct(self):
        tasks = {task.task_id: task for task in build_fixture_corpus()}
        self.assertNotEqual(tasks["cleanup-legacy-flag"].before, tasks["cleanup-dead-branch"].before)
        self.assertIn("if False", tasks["cleanup-dead-branch"].before)

    def test_invalid_or_gaming_patch_is_flagged(self):
        flags = classify_patch("def check():\n    # required context\n    assert True\n", "def check():\n    return True\n")
        self.assertIn("comment_deletion_candidate", flags)
        self.assertIn("test_assertion_removed", flags)

    def test_gaming_flags_are_heuristic_warnings_not_failures(self):
        tasks = {task.task_id: task for task in build_fixture_corpus()}
        record = run_task(tasks["refactor-shared-strip"], "neutral_control")
        self.assertIn("possible_compression", record.diff.gaming_flags)
        self.assertEqual(record.failure_reasons, ())

    def test_formatting_control_accepts_raw_churn(self):
        tasks = {task.task_id: task for task in build_fixture_corpus()}
        record = run_task(tasks["control-formatting"], "neutral_control")
        self.assertNotEqual(record.diff.raw_net, 0)
        self.assertEqual(record.diff.structural_symbols_net, 0)
        self.assertEqual(record.failure_reasons, ())

    def test_valid_gold_transformations_have_no_failure_reasons(self):
        tasks = {task.task_id: task for task in build_fixture_corpus()}
        gold_ids = {
            "refactor-shared-strip",
            "refactor-inline-default",
            "cleanup-legacy-flag",
            "cleanup-dead-branch",
            "control-rename",
            "control-formatting",
        }
        for task_id in gold_ids:
            for arm in ARM_NAMES:
                record = run_task(tasks[task_id], arm)
                self.assertEqual(record.failure_reasons, (), f"{task_id}/{arm}")

    def test_candidate_patch_records_adapter_metadata(self):
        task = build_fixture_corpus()[0]
        record = measure_candidate_patch(
            task,
            "neutral_control",
            task.after,
            model="candidate-model",
            reasoning_effort="high",
            execution_source="cursor_adapter",
            turns=3,
            tool_calls=7,
            token_usage=TokenUsage(120, 45),
        )
        self.assertTrue(record.tests.passed)
        self.assertEqual(record.execution_source, "cursor_adapter")
        self.assertEqual(record.turns, 3)
        self.assertEqual(record.tool_calls, 7)
        self.assertEqual(record.token_usage, TokenUsage(120, 45))
        self.assertFalse(record.dry_run)

    def test_broken_candidate_patch_records_behavior_failure(self):
        task = build_fixture_corpus()[0]
        broken_source = "def summarize_total(cents):\n    return 'broken'\n"
        record = measure_candidate_patch(
            task,
            "neutral_control",
            broken_source,
            execution_source="cursor_adapter",
            turns=1,
            tool_calls=1,
        )
        self.assertFalse(record.tests.passed)
        self.assertEqual(record.tests.failure_reason, "behavior oracle failed")
        self.assertIn("behavior oracle failed", record.failure_reasons)

    def test_run_task_is_explicitly_offline_fixture_evidence(self):
        record = run_task(build_fixture_corpus()[0], "neutral_control")
        self.assertEqual(record.execution_source, "offline_fixture")
        self.assertTrue(record.dry_run)
        self.assertIsNone(record.model)
        self.assertIsNone(record.reasoning_effort)


if __name__ == "__main__":
    unittest.main()
