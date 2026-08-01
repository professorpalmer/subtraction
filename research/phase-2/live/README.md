# Phase 2 live pilot evidence

This directory records two six-cell pilots for `refactor-shared-strip`. Each
crosses `neutral_control` and `subtractive_rubric` with GPT-5.6 Luna, Grok
4.5, and Composer 2.5 at the explicit Phase 2 effort levels.

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
- The twelve pilot `.py` files — exact model-produced candidate sources.
- `seam-check-2026-08-01-grok-neutral-result.json` and its `.py` source —
  the first successful git-backed seam check.

All six successful candidates passed the behavior oracle. Their observed raw
net LOC was negative in both arms: Luna `-6/-6`, Grok `-3/-6`, and Composer
`-3/-6` for neutral/subtractive respectively. Successful receipt totals were
`1,366,801` neutral and `512,291` subtractive tokens. This is directional
one-repetition evidence, not a causal prompt or cost estimate: the isolated
file-only context differs from the earlier repository-root pilot, and
trajectory-level effort and tool counts were not reported.
