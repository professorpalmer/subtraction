# Phase 1 — Offline subtraction benchmark

This is the first runnable measurement artifact for the project. It is a
small, deterministic Python benchmark with no provider SDK and no API-key
requirement.

## Run

From the repository root:

```sh
python -m unittest discover -s research/phase_1/tests -v
python -m research.phase_1.run --output research/phase-1/dry-run.json
```

The dry run applies hand-authored fixture transformations, executes each
behavior oracle, measures every fixture under all six arms, and writes
deterministic JSON. It is an `offline_fixture` transformation, not a model
run: offline records leave `model` and `reasoning_effort` empty. Later Cursor
adapter records may populate those fields from actual telemetry.

The first live pilot and its limitations are summarized in
`PILOT_FINDINGS.md`. Corrected raw records are under `live/`; the v2 pilot is
the valid neutral-versus-subtractive refactor comparison, and v3 adds the
cleanup-task replication. The earlier v1 artifact is retained and explicitly
marked pre-correction for provenance.

## Fixtures and arms

The corpus includes feature, behavior-preserving refactor, removal/cleanup,
and measurement-control tasks. Feature tasks are sign-matched: a positive
diff is expected when capability is required. Maintenance arms explicitly
route around that exception:

1. `neutral_control`
2. `concise_control`
3. `subtractive_rubric`
4. `delete_first_gate`
5. `semantic_net_loc_budget`
6. `post_hoc_cleanup_comparator`

The arm strings are frozen in `arms.py`; changing them changes the experiment
and should be versioned as a protocol revision.

## Data and later Cursor-adapter runs

Each JSON record contains execution source, optional model and reasoning
effort, task and arm, complete prompt, turns, tool calls, optional
input/output token counts, raw and structural diff metrics, symbols,
dependencies, test results, failure reasons, and dry-run status. Structural
symbol counts compare only Python function/class name sets; they are not
semantic LOC or proof of semantic equivalence.

### Cursor adapter contract

Live adapters should call `measure_candidate_patch(task, arm,
candidate_source, ...)` from `research.phase_1.harness`. The candidate source
must be the complete post-edit source produced by the model, while `task.before`
remains the unchanged fixture source. Supply the actual `model`,
`reasoning_effort`, `execution_source`, `turns`, `tool_calls`, and
`TokenUsage(input_tokens=..., output_tokens=...)` telemetry. Set `dry_run=False`
for live adapter input. The harness executes the candidate against the task
oracle, measures its diff from `task.before`, and records sign, class, and
delete-first gate failures. Heuristic gaming flags remain warnings in
`DiffMetrics`; behavior-oracle failures are recorded in `failure_reasons`.

`run_task` is the offline wrapper: it measures the hand-authored `task.after`
with `execution_source="offline_fixture"` and `dry_run=True`. Adapters must
preserve task text, initial source, test command, and arm strings. Failed,
reverted, and abandoned runs should remain records rather than being silently
dropped.

Proposed screen: 10 independent repetitions per model × task class ×
principal arm, expanding to 20 if variance is high. The fixture dry run is a
pipeline check, not evidence about model behavior.

## Measurement policy and limitations

Raw line counts are authoritative descriptions of the textual diff. AST symbol
and import changes are deterministic for parseable Python, but symbol-set
differences are structural heuristics only. Token deltas,
similar-line matches, likely move/copy labels, boilerplate counts, and gaming
flags are heuristics; they are signals for review, not semantic truth. Tests
and task oracles are the local correctness gate, but they cannot detect every
API, reflection, maintainability, or security regression. Rename-aware
matching is intentionally conservative and is not a replacement for audited
semantic equivalence.
