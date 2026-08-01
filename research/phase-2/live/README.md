# Phase 2 live pilot evidence

This directory records a six-cell candidate-generation pilot for
`refactor-shared-strip`. It crosses `neutral_control` and
`subtractive_rubric` with GPT-5.6 Luna, Grok 4.5, and Composer 2.5 at the
explicit Phase 2 effort levels.

## Provenance boundary

The six model workers edited isolated working copies, but those temporary
directories were not git worktrees. Puppetmaster therefore ended each run
with `require_diff: edit task produced no diff`, even though each working
copy changed. The candidate files and measurements are retained, and every
behavior oracle passed, but each result is marked
`adapter_status: "failed_require_diff"` and must not be counted as a
successful adapter execution.

The git-backed Grok seam check is separate. It completed successfully with
`adapter_status: "completed"` and demonstrates the required setup for future
live cells: a clean baseline with a tracked candidate file and a visible
diff. It is a seam validation, not a balanced experiment.

## Artifacts

- `pilot-2026-08-01-refactor-isolation-results.json` — six complete result
  records with model receipts, job IDs, hashes, and adapter status.
- `pilot-2026-08-01-refactor-isolation-summary.json` — grouped metrics. Each
  group has `adapter_failure_count: 1`.
- The six `.py` files — exact model-produced candidate sources.
- `seam-check-2026-08-01-grok-neutral-result.json` and its `.py` source —
  the successful git-backed seam check.

All six isolated candidates passed the behavior oracle. Their observed raw
net LOC was negative in both arms: Luna `-6/-6`, Grok `-3/-6`, and Composer
`-3/-6` for neutral/subtractive respectively. The result is directional
candidate evidence only: it is one repetition, all six adapter gates failed,
and the isolated file-only context differs from the earlier repository-root
pilot. It does not establish a causal prompt effect or a token-cost effect.
