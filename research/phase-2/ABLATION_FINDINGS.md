# Phase 2 atomic component-ablation findings

## Scope and completion

The completed live screen crossed one task (`refactor-shared-strip`), three
models, eight factorial arms, and five repetitions: `1 × 3 × 8 × 5 = 120`
receipts. All 120 adapters completed, and all 120 behavior oracles passed.
The control arm was `neutral_control`.

The three prompt components were:

- **T** — task-type gate
- **D** — delete-first/reference-proof
- **B** — semantic net-LOC budget

## Findings

- **D is the only cross-model factorial component with a consistently negative
  main effect.** Factorial on-minus-off raw-net mean effects (sample SD) were:
  - Composer 2.5: T `+0.70` (`1.66`), D `-5.40` (`1.66`), B `-0.20`
    (`4.39`)
  - GPT-5.6 Luna: T `+0.65` (`3.02`), D `-4.05` (`3.85`), B `+0.95`
    (`2.22`)
  - Grok 4.5: T `+0.05` (`0.45`), D `-2.95` (`0.87`), B `+2.05`
    (`2.53`)
- Every factor contrast had 20/20 behavior passes with the factor off and
  20/20 with it on.
- The single-factor treatment-minus-neutral deltas were:
  - Composer 2.5: T `+4.0`, D `+0.2`, B `+2.8`
  - GPT-5.6 Luna: T `+0.2`, D `-3.4`, B `+1.4`
  - Grok 4.5: T `+3.0`, D `-0.6`, B `+4.0`
- The single D arm is therefore not uniformly negative. Interaction and
  trajectory effects remain plausible, but this one task does not identify
  them. T is near zero as a factorial main effect. B is unstable and
  model-dependent.

These are descriptive effects from this completed screen. They do not
establish statistical significance, generalization beyond this task and
receipt design, or causal cost savings.

## Token boundary and fixture status

Token results in `ablation-screen-r5-token-analysis.json` are descriptive
telemetry only. They follow the Phase 3 accounting boundary: analyze only
receipts with `actual.adapter_status == "completed"`; preserve input, output,
and total tokens independently; do not derive one token field from another;
and do not infer dollar costs without explicit field-level rates. No pricing
was supplied for this screen.

The corrected feature-format-total cents contract is offline infrastructure,
not part of this live screen. It must not be used to reinterpret these
receipts.

## Artifacts

- `ablation-screen-r5-results.json` — completed per-cell receipts
- `ablation-screen-r5-report.json` — grouped results and paired comparisons
- `ablation-screen-r5-factor-effects.json` — factorial component contrasts
- `ablation-screen-r5-summary.json` — aggregate model-by-arm results
- `ablation-screen-r5-token-analysis.json` — descriptive Phase 3 token
  accounting

## Next work

- Prepare the exact 240-cell confirmation wave: four tasks
  (`refactor-shared-strip`, `cleanup-legacy-flag`, corrected
  `feature-format-total`, and `control-rename`) × three models × four arms
  (`neutral_control`, `delete_first_gate`,
  `task_type_delete_first_net_loc_budget`, and `subtractive_rubric`) × five
  repetitions. This is a planned wave; no results are claimed here.
