# Phase 2 live pilot evidence

This directory records three six-cell pilots for `refactor-shared-strip` and
`cleanup-legacy-flag`. Each crosses `neutral_control` and
`subtractive_rubric` with GPT-5.6 Luna, Grok 4.5, and Composer 2.5 at the
explicit Phase 2 effort levels.

## Provenance boundary

The isolation pilot used plain temporary directories. Puppetmaster therefore
ended each run with `require_diff: edit task produced no diff`, even though
each working copy changed. Every behavior oracle passed, but those records
are marked `adapter_status: "failed_require_diff"` and are not successful
adapter executions.

The successful pilot used a clean git-backed cell for every run. All six
workers completed, produced a visible diff, and are marked
`adapter_status: "completed"`. The earlier Grok seam check is retained as an
independent setup validation.

## Artifacts

- `pilot-2026-08-01-refactor-isolation-results.json` and
  `pilot-2026-08-01-refactor-isolation-summary.json` — six candidate records
  with failed adapter-gate status.
- `pilot-2026-08-01-refactor-git-results.json` and
  `pilot-2026-08-01-refactor-git-summary.json` — six successful records with
  receipts, job IDs, hashes, and grouped metrics.
- `pilot-2026-08-01-cleanup-git-results.json` and
  `pilot-2026-08-01-cleanup-git-summary.json` — six successful cleanup
  records.
- The eighteen pilot `.py` files — exact model-produced candidate sources.
- `seam-check-2026-08-01-grok-neutral-result.json` and its `.py` source —
  the first successful git-backed seam check.

All six successful candidates passed the behavior oracle. Their observed raw
net LOC was negative in both arms: Luna `-6/-6`, Grok `-3/-6`, and Composer
`-3/-6` for neutral/subtractive respectively. Successful receipt totals were
`1,366,801` neutral and `512,291` subtractive tokens. This is directional
one-repetition evidence, not a causal prompt or cost estimate: the isolated
file-only context differs from the earlier repository-root pilot, and
trajectory-level effort and tool counts were not reported.

The cleanup replication removed the unused flag and debug helper in all six
runs, with raw net LOC `-5` under both arms for every model. Its successful
receipt totals were `361,412` tokens for neutral and `309,400` for
subtractive; the exact per-cell values are preserved in the JSON artifacts.
This task contrast is the stronger result: when the task itself explicitly
requires deletion, the rubric adds no directional change.

## r5 repeated wave

The five-repetition wave combines the twelve successful repetition-1
git-backed pilot receipts with 108 newly executed cells. The final artifact
contains all 120 preregistered cells: 119 completed adapter runs and one
recorded no-diff failure for Grok's subtractive feature repetition 4.

- `variance-r5-results.json` — combined per-cell receipts.
- `variance-r5-report.json` — sample-SD summaries and paired comparisons.
- `variance-r5-summary.json` — aggregate model-by-arm totals.

The paired refactor raw-net deltas favored the subtractive rubric for Luna
(`-6.2` mean), Grok (`-7.2`), and Composer (`-1.2`). Cleanup showed no
consistent arm effect, while the control task remained raw-net zero. The
feature fixture's behavior contract is ambiguous, so its failures are not
treated as quality evidence.

## Atomic component-ablation screen

The completed live screen crossed `refactor-shared-strip`, three models, eight
atomic T/D/B arms, and five repetitions for 120 receipts. All 120 adapters
completed and all 120 behavior oracles passed. Its control was
`neutral_control`; T is the task-type gate, D is delete-first/reference-proof,
and B is the semantic net-LOC budget.

The findings memo is [`../ABLATION_FINDINGS.md`](../ABLATION_FINDINGS.md).
The screen artifacts are:

- `ablation-screen-r5-results.json`
- `ablation-screen-r5-report.json`
- `ablation-screen-r5-factor-effects.json`
- `ablation-screen-r5-summary.json`
- `ablation-screen-r5-token-analysis.json`

The token analysis is descriptive only and follows the Phase 3 accounting
boundary. The corrected feature-format-total cents contract is offline
infrastructure, not part of this live screen.

## Confirmation wave

The completed confirmation crossed four tasks
(`refactor-shared-strip`, `cleanup-legacy-flag`, corrected
`feature-format-total`, and `control-rename`), three models, four arms
(`neutral_control`, `delete_first_gate`,
`task_type_delete_first_net_loc_budget`, and `subtractive_rubric`), and five
repetitions: `240` cells. The first dispatch completed 63 cells and had 177
provider rate-limit failures. All 177 were retried from fresh cells at lower
concurrency. The final selected dataset contains 240/240 completed adapter
receipts and 240/240 behavior-oracle passes.

Results and provenance:

- `confirmation-r5-results.json`
- `confirmation-r5-report.json`
- `confirmation-r5-summary.json`
- `confirmation-r5-token-analysis.json`
- `confirmation-r5-initial-rate-limit-failures.json`
- `confirmation-r5-retry-provenance.json`

The evidence-first interpretation is in
[`../CONFIRMATION_FINDINGS.md`](../CONFIRMATION_FINDINGS.md). Its raw-net
comparisons are descriptive, task- and model-conditional, and do not establish
statistical significance, broad generalization, causal mechanism, or cost
savings. No pricing was supplied.
