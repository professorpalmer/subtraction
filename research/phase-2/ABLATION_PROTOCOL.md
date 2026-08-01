# Phase 2 component-ablation screening protocol

Protocol ID: `phase-2-component-ablation-v1`

This note preregisters an offline-first component screen that separates the
bundled `subtractive_rubric` intervention into three atomic prompt factors.
It does **not** re-run or rewrite the completed variance-r5 wave. Historical
r5 receipts remain provenance; the r5 `feature-format-total` cells stay
`oracle_invalid` / non-interpretable as quality evidence.

## Factors

| Factor | Code | Meaning |
|--------|------|---------|
| Task-type / no-new-capability | T | Match task type; add no capability on refactor/cleanup |
| Delete-first / reference proof | D | Inventory callers/references; prefer a safe deletion first |
| Semantic net-LOC budget | B | Prefer non-positive structural symbol net without gaming |

Arms are the full 2³ cross of atomic T/D/B fragments with a neutral baseline:

1. `neutral_control` — no T/D/B
2. `task_type_gate` — T
3. `delete_first_gate` — D
4. `semantic_net_loc_budget` — B
5. `task_type_delete_first` — T+D
6. `task_type_net_loc_budget` — T+B
7. `delete_first_net_loc_budget` — D+B
8. `task_type_delete_first_net_loc_budget` — T+D+B (atomic composed fragments)

`subtractive_rubric` remains the backward-compatible historical composite and
may be used later as an optional bridge/legacy comparator against r5; it is
**not** the eighth cell of this 120-cell atomic screen. `concise_control` and
`post_hoc_cleanup_comparator` are also out of scope. Feature-safe routing
remains in force for every arm: feature tasks explicitly allow required
additions, and pure T/B arms must not inherit D routing language.

## Screening matrix (120 cells)

- Tasks: `refactor-shared-strip` only
- Models / efforts: the frozen Phase 2 pairs
  (`gpt-5.6-luna`/`maximum`, `grok-4.5`/`high`, `composer-2.5`/`default`)
- Arms: the eight component-screen arms above
- Repetitions: 1..5
- Cardinality: 1 × 3 × 8 × 5 = **120 cells**

Frozen design manifest: `research/phase-2/design-ablation-screen-r5.json`.

Regenerate deterministically (planning only; no adapter calls):

```sh
python -m research.phase_2.cli plan \
  --ablation-screen \
  --repetitions 5 \
  --output research/phase-2/design-ablation-screen-r5.json \
  --runs-root /tmp/subtraction-ablation-screen-r5-runs
```

Equivalent Python entry point: `research.phase_2.design.build_ablation_screen_design(5)`.

Cell/receipt schema reuses `phase-2-controlled-ablation-v1` fields from
`DesignCell` / `prepare_run` / `ingest_candidate`. The design document protocol
label is `phase-2-component-ablation-v1`.

## Primary contrasts

1. For each non-neutral screen arm, paired **arm − neutral** `raw_net_delta` on
   matched completed repetition IDs, with both-behavior-pass counts.
2. Secondary: main-effect averages for T, D, and B across the factorial.
3. Optional bridge (not part of the 120-cell screen): if
   `subtractive_rubric` cells are run separately, compare
   `subtractive_rubric − neutral` to the completed r5 refactor contrast
   (do not pool r5 and screen receipts).

Token fields remain descriptive telemetry under the Phase 3 protocol; they are
not causal cost estimates.

## Validity gates

Before interpreting LOC effects:

- Offline dry-run / gold checks pass for all eight screen arms on the
  refactor fixture.
- Only `actual.adapter_status == "completed"` receipts enter completed-run
  statistics.
- Paired comparisons require equal, non-empty matched repetition ID sets.
- Primary refactor contrasts require `behavior_pass_count == R` on both arms
  before claiming a LOC effect.
- Non-completed statuses are counted and excluded.
- Historical r5 feature receipts remain non-interpretable; do not rewrite them.

Variance trigger reuse: expand R to 10 only if a `refactor-shared-strip`
within-cell raw-net or observed `total_tokens` sample variance exceeds 4.0.

## Confirmation wave (later; not this screen)

Only after the screening contrasts land, run a reduced confirmation wave:

- Tasks: `refactor-shared-strip`, `refactor-inline-default`, corrected
  `feature-format-total`, and `control-rename`
- Arms: `neutral_control` + screening winners + optional legacy
  `subtractive_rubric` bridge comparator
- Models/efforts: same three pairs
- Repetitions: 5

That confirmation wave tests generalization and feature sign-matching; it is
not part of the 120-cell atomic screen materialized here.
