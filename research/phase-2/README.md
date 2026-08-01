# Phase 2 — Controlled ablation

Phase 2 is a provider-neutral setup and measurement harness for a fixed
factorial ablation. The default matrix crosses all eight Phase 1 fixtures with
`neutral_control` and `subtractive_rubric`, the three explicit Cursor adapter
models (`gpt-5.6-luna`, `grok-4.5`, and `composer-2.5`), their recorded effort
levels, and 10 independent repetitions. Repetitions are configurable.

## Plan and summary

From a clean repository checkout:

```sh
python -m research.phase_2.cli plan \
  --output research/phase-2/design.json \
  --runs-root /tmp/subtraction-phase-2-runs \
  --repetitions 10
python -m research.phase_2.cli plan \
  --output research/phase-2/design-r5.json \
  --runs-root /tmp/subtraction-phase-2-r5-runs \
  --repetitions 5 \
  --tasks refactor-shared-strip cleanup-legacy-flag feature-format-total control-rename
python -m research.phase_2.cli summary --output summary.json \
  /tmp/subtraction-phase-2-runs/cell-*/candidate/result.json
python -m research.phase_2.cli variance --output variance.json \
  /tmp/subtraction-phase-2-runs/cell-*/candidate/result.json
```

Planning makes no API calls. Each cell has a deterministic ID and an isolated
directory containing `manifest.json`, immutable `initial/source.py` and task
metadata, and a separate `candidate/` directory. Candidate ingestion checks
the manifest, initial-source hash, and actual model/effort against the prepared
cell before calling the existing Phase 1 `measure_candidate_patch`. Completed
candidate artifacts are never overwritten.

Live adapter runs must begin from a clean, git-backed checkout for every
prepared run. A plain temporary directory is insufficient because the Cursor
worker's diff gate will classify it as a no-change run. Adapters must not edit
`initial/source.py` or task metadata. The contract is to provide the complete
candidate source plus actual model, reasoning effort, execution source, turns,
tool calls, and input/output/total token telemetry.
Reported token fields are preserved exactly; `total_tokens` is never derived
from input and output. Failed and abandoned attempts should remain result
records. A candidate may also be retained with a non-`completed`
`adapter_status` and optional adapter job ID for provenance, but it must not be
reported as a successful adapter run. The variance report counts failed,
timed-out, and missing adapter statuses, but excludes them from completed
repetition statistics and neutral/subtractive comparisons.

## What is measured

Results preserve Phase 1 behavior-oracle status, raw added/removed/net lines,
structural symbol heuristics, failure reasons, and gaming warnings. Summaries
group by explicit model and arm and report run count, passed tests, failures,
raw LOC totals/mean, and only the token values actually reported by the
adapter. Missing token values remain missing — including `total_tokens` when
only input/output are present — and the harness does not infer prices or costs.

The preregistered r5 wave can expand to 10 repetitions only under the stated
variance trigger. Phase 1 pilot token receipts are not causal cost estimates:
those runs were exploratory, had unequal effort and telemetry conditions, and
were affected by repository-state confounding. Token totals here are
descriptive telemetry until a controlled cost protocol is specified.

## Repeated-variance semantics and preregistered r5 wave

`variance` validates each receipt's `cell`, `actual`, and `record` mappings and
analyzes only receipts with `actual.adapter_status == "completed"`. Results
are grouped by task, model, reasoning effort, and arm. Each group reports
repetition IDs, raw-net values and sample standard deviation (null when fewer
than two values), behavior pass/failure counts, and observed input/output/total
token values with non-missing counts, means, and sample standard deviations.
It never synthesizes `total_tokens`. Duplicate completed repetition IDs within
an arm are rejected. Paired comparisons require equal, non-empty repetition ID
sets; otherwise they are reported as unmatched with a reason. Matched
comparisons report subtractive-minus-neutral raw-net deltas and both-pass,
neutral-only, and subtractive-only behavior counts.

The preregistered r5 wave uses tasks `refactor-shared-strip`,
`cleanup-legacy-flag`, `feature-format-total`, and `control-rename`; the three
frozen Cursor model/effort pairs above; both arms; and repetitions 1..5, for
120 cells. Expand to 10 repetitions only if the `refactor-shared-strip`
within-cell raw-net variance or observed `total_tokens` variance exceeds 4.0.
Live runs require clean git-backed checkouts for every cell.
