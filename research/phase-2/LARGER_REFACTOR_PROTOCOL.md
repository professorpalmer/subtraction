# Phase 2 larger-refactor replication protocol

Protocol status: completed interaction-focused replication  
Protocol scope: larger deterministic multi-function refactor fixtures

This protocol tested whether the T/D/B component pattern observed in the
completed component screen and confirmation wave interacts with task scale and
refactor structure. The live wave is complete. The validity gates below passed
for the selected observations, but the result remains interaction-focused and
does not establish broad generalization.

## Fixtures and factorial design

The wave uses two new deterministic tasks:

- `refactor-shared-normalizer`
- `refactor-dead-compatibility-path`

Each task is crossed with the full eight atomic arms in
`COMPONENT_SCREEN_ARMS`:

1. `neutral_control` — no T/D/B components
2. `task_type_gate` — T
3. `delete_first_gate` — D
4. `semantic_net_loc_budget` — B
5. `task_type_delete_first` — T+D
6. `task_type_net_loc_budget` — T+B
7. `delete_first_net_loc_budget` — D+B
8. `task_type_delete_first_net_loc_budget` — T+D+B

The model and effort pairs are frozen:

| Model | Reasoning effort |
|---|---|
| `gpt-5.6-luna` | `maximum` |
| `grok-4.5` | `high` |
| `composer-2.5` | `default` |

Repetitions are `1..5`. The planned size is **2 × 3 × 8 × 5 = 240
cells**. The frozen manifest is
`research/phase-2/design-larger-refactor-screen-r5.json`.

Planning is deterministic and makes no adapter calls. The exact planning
command is:

```sh
python -m research.phase_2.cli plan \
  --output research/phase-2/design-larger-refactor-screen-r5.json \
  --runs-root /tmp/subtraction-larger-refactor-screen-r5-runs \
  --repetitions 5 \
  --tasks refactor-shared-normalizer refactor-dead-compatibility-path \
  --arms neutral_control task_type_gate delete_first_gate semantic_net_loc_budget \
  task_type_delete_first task_type_net_loc_budget \
  delete_first_net_loc_budget task_type_delete_first_net_loc_budget
```

## Validity boundary

The existing `control-rename` evidence and prior confirmation artifacts remain
validity anchors for control drift and the earlier task-conditional result.
They are not silently pooled with this larger-refactor wave. Comparisons must
identify their source wave and protocol explicitly.

The primary analysis reuses Phase 2 variance semantics:

- analyze only receipts with `actual.adapter_status == "completed"`;
- retain non-completed adapter receipts as status and transport provenance, but
  exclude them from completed-run statistics and arm comparisons;
- require unique, matched repetition IDs for every paired or factorial
  comparison;
- require passing behavior oracles before interpreting a raw-net effect;
- preserve `input_tokens`, `output_tokens`, and `total_tokens` exactly as
  reported by the adapter; never synthesize a missing field or infer cost.

The primary interaction contrasts are task- and model-conditional arm effects
against `neutral_control`, followed by T/D/B factor effects across the eight
arms. A negative raw-net result is not sufficient on its own: behavior
validity, matched repetitions, and control behavior must be reported with it.

The r5 design expands to ten repetitions only under the existing trigger:
within-cell raw-net variance or observed `total_tokens` variance for the
relevant refactor wave exceeds `4.0`. The trigger is a decision rule, not
permission to increase repetitions after inspecting a preferred effect.

## Live dispatch safety

Before dispatching the wave, run one seam check against a representative
prepared cell and verify the complete candidate/receipt path. Cap live
concurrency at two. Provider rate-limit retries must remain separate
provenance: preserve the initial failure records and the retry records rather
than collapsing them into an apparently uninterrupted run.

Every live cell must use a clean, git-backed checkout. Preserve the immutable
initial source and task metadata, and retain failed or abandoned attempts as
receipts. A receipt that is not a completed adapter run cannot be treated as a
successful observation.

## Interpretation rule

This wave can establish whether the earlier effect pattern replicates or
interacts with these two larger refactor structures under the registered
conditions. It cannot, by itself, establish universality across maintenance
tasks, repositories, or model families. Interpret the result only after the
live wave, validity gates, and provenance review are complete.

## Completed result

The selected dataset contains 240 completed adapter receipts and 240/240
behavior-oracle passes. Six initial adapter failures were retained as separate
transport provenance and excluded from completed comparisons. The full report
is [`live/larger-refactor-r5-report.json`](live/larger-refactor-r5-report.json);
the findings memo is
[`LARGER_REFACTOR_FINDINGS.md`](LARGER_REFACTOR_FINDINGS.md).

The D effect was negative on `refactor-shared-normalizer` for GPT-5.6 Luna
and Grok 4.5, but null for Composer. It was null or positive for all three
models on `refactor-dead-compatibility-path`. The registered result is
therefore a task- and model-conditional interaction, not a standalone
universal D component. This wave did not include the legacy
`subtractive_rubric` arm; prior legacy comparisons remain separate evidence.

The priced multi-turn cost wave is not authorized by the result: its
precondition, survival of the patch-shape effect across both larger fixtures,
was not met. Observed token fields remain descriptive telemetry and are not
converted into dollar savings.
