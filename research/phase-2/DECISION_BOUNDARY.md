# Decision boundary: current subtraction claim

Decision date: 2026-08-01
Decision status: active research boundary

## Claim we can make

Deletion-first/reference-proof prompting is a credible, behavior-safe
intervention for some larger refactor structures, but not a universal
standalone component. In the completed 240-cell larger-refactor replication,
the D factorial main effect was negative for GPT-5.6 Luna and Grok 4.5 on
`refactor-shared-normalizer`, while the effect was null for Composer. On
`refactor-dead-compatibility-path`, D was null or positive across all three
models. The supported result is task- and model-conditional subtraction.

## Evidence boundary

- Atomic screen: `live/ablation-screen-r5-report.json`,
  `live/ablation-screen-r5-factor-effects.json`, and
  `ABLATION_FINDINGS.md`.
- Confirmation wave: `live/confirmation-r5-results.json`,
  `live/confirmation-r5-report.json`, and `CONFIRMATION_FINDINGS.md`.
- Larger-refactor replication: `live/larger-refactor-r5-results.json`,
  `live/larger-refactor-r5-report.json`,
  `live/larger-refactor-r5-factor-effects.json`, and
  `LARGER_REFACTOR_FINDINGS.md`.
- The larger-refactor selected dataset has 240/240 completed receipts and
  behavior-oracle passes. Six initial adapter failures remain separate in
  `live/larger-refactor-r5-initial-failures.json` and
  `live/larger-refactor-r5-retry-provenance.json`.
- Token artifacts are descriptive telemetry. No pricing or causal cost
  estimate is supported by the current data.

## Claims we are not making

- The result is not general across maintenance tasks, repositories, or model
  families; the larger replication was negative on only one of its two new
  fixtures.
- Five repetitions do not establish statistical significance.
- Smaller patches have not been shown to reduce multi-turn dollar cost.

## Current decision

Publish the task/model interaction and stop calling D a universal component.
The larger-refactor validity gates passed for the selected observations, but
the intervention did not survive on both new fixtures. The existing
`control-rename` and confirmation artifacts remain separate validity anchors;
they must not be silently pooled with the larger-refactor report.

Do not run the priced multi-turn token wave from the original plan. Its
precondition was a patch-shape effect surviving the larger replication, which
was not met. The next evidence gate is an independently specified
refactor-task or repository replication, followed separately by priced
multi-turn trajectories only if that gate survives.
