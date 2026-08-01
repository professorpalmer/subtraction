# Phase 2 confirmation findings

## Scope and data validity

The completed confirmation wave crossed four tasks
(`refactor-shared-strip`, `cleanup-legacy-flag`, corrected
`feature-format-total`, and `control-rename`), three models, four arms
(`neutral_control`, `delete_first_gate`,
`task_type_delete_first_net_loc_budget`, and `subtractive_rubric`), and five
repetitions: `4 × 3 × 4 × 5 = 240` cells. The first dispatch completed 63
cells and encountered 177 provider rate-limit failures. All 177 failures were
retried from fresh cells at lower concurrency. The final selected dataset has
240/240 completed adapter receipts and 240/240 behavior-oracle passes; paired
cells matched repetitions.

The transport record is preserved in
`live/confirmation-r5-initial-rate-limit-failures.json` and
`live/confirmation-r5-retry-provenance.json`. The results below are primary
treatment-minus-neutral raw-net mean deltas, with sample SD in parentheses.

## Primary results

The treatment-minus-neutral raw-net mean deltas (sample SD) were:

- `cleanup-legacy-flag`: Composer D `0.0 (0.0)`, T+D+B `0.0 (0.0)`,
  legacy `0.0 (0.0)`; Luna D `+0.2 (0.45)`, T+D+B `+0.2 (0.45)`,
  legacy `0.0 (0.0)`; Grok D/T+D+B/legacy `0.0 (0.0)`.
- `control-rename`: Composer, Luna, and Grok were `0.0 (0.0)` for all
  treatment arms.
- Corrected `feature-format-total`: Composer D/T+D+B/legacy
  `0.0 (0.0)`; Luna D `+1.0 (1.87)`, T+D+B `0.0 (1.41)`, legacy
  `-1.2 (1.30)`; Grok D `-1.0 (2.35)`, T+D+B `-1.0 (2.12)`, legacy
  `-1.2 (2.39)`.
- `refactor-shared-strip`: Composer D/T+D+B/legacy `-3.2 (5.22)`; Luna
  D `-6.2 (5.36)`, T+D+B `-5.6 (5.41)`, legacy `-9.6 (1.52)`; Grok D
  `0.0 (2.12)`, T+D+B `-2.4 (3.91)`, legacy `-3.0 (3.67)`.

The earlier component screen's factorial D main effect was negative across
all three models. This confirmation does not show a universal standalone
D-arm effect: D-only on `refactor-shared-strip` is 0 for Grok, while the T+D+B
composition is -2.4 and the legacy rubric is -3.0. The differentiated result
is task- and model-conditional subtraction. Prompt effects are concentrated
in the refactor task, absent on the measurement control, nearly absent on
cleanup, and model-dependent on the corrected feature task. These descriptive
results do not establish statistical significance, broad generalization, or a
causal mechanism.

## Token boundary

No pricing was supplied; token analysis is descriptive only. For
`refactor-shared-strip`, total-token means versus neutral were:

- Composer: neutral `292045.2`; D `192095.2 (-34.2%)`; T+D+B
  `262917.2 (-10.0%)`; legacy `207525.0 (-28.9%)`.
- Luna: neutral `158019.8`; D `180102.4 (+14.0%)`; T+D+B
  `160614.2 (+1.6%)`; legacy `183197.0 (+15.9%)`.
- Grok: neutral `270550.6`; D `353843.8 (+30.8%)`; T+D+B
  `153993.0 (-43.1%)`; legacy `118668.0 (-56.1%)`.

These are descriptive matched receipts, not causal cost savings. Total tokens
are reported telemetry, not inferred pricing or a cost estimate.

## Artifacts

- `live/confirmation-r5-results.json`
- `live/confirmation-r5-report.json`
- `live/confirmation-r5-summary.json`
- `live/confirmation-r5-token-analysis.json`
- `live/confirmation-r5-initial-rate-limit-failures.json`
- `live/confirmation-r5-retry-provenance.json`

## Next work

Pre-register either a larger-task replication or an interaction-focused
factorial follow-up. This wave supports no broader claim beyond its matched
tasks, models, arms, repetitions, and validity gates.
