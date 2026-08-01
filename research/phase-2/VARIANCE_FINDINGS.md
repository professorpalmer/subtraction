# Phase 2 r5 variance findings

The preregistered r5 wave crossed four tasks, three Cursor adapter models,
two prompt arms, and five repetitions: 120 cells in total. The combined
receipt artifact contains 119 completed adapter runs and one recorded adapter
failure. The failed run was Grok 4.5 on `feature-format-total`,
`subtractive_rubric`, repetition 4; it produced no candidate diff and is
excluded from completed-run statistics.

## Findings

1. The subtractive rubric shifted the refactor task toward smaller patches.
   Paired subtractive-minus-neutral raw-net means were:
   - GPT-5.6 Luna: `-6.2` lines, sample SD `4.09`
   - Grok 4.5: `-7.2` lines, sample SD `2.68`
   - Composer 2.5: `-1.2` lines, sample SD `1.64`

   All five repetitions in each refactor comparison passed the behavior
   oracle. This is evidence for a task-dependent intervention effect, not a
   universal model shift.

2. The cleanup replication showed no consistent arm effect. Composer and Grok
   had paired mean delta `0.0`; Luna had `+0.8` lines because two repetitions
   differed by two lines. Every completed cleanup repetition passed.

3. The measurement control behaved as intended. All 30 control-rename runs
   produced raw-net `0` and passed the behavior oracle. The intervention did
   not create a spurious deletion signal on a semantic-zero task.

4. The feature task is not interpretable as quality evidence in this wave
   (`oracle_invalid` for cross-wave memos). Models consistently produced
   additive patches, but the historical fixture's expected behavior contract
   was semantically confusing about whether the formatter input is a dollar
   value or cents. Behavior failures therefore cannot be cleanly attributed to
   the prompt arm. Composer's feature runs passed the ambiguous oracle; Luna
   and Grok had behavior failures, and Grok also had the adapter failure noted
   above. Historical r5 feature receipts are retained unchanged and must not
   be reinterpreted after the later cents-contract fixture correction.

5. The preregistered variance trigger was met. For example, the Luna neutral
   refactor group had raw-net sample SD `4.80`, implying sample variance about
   `23.0`, above the threshold of `4.0`. The protocol therefore permits an
   expansion to ten repetitions, but this report stops at the completed r5
   wave rather than silently spending on an additional wave.

## Interpretation boundary

The strongest result is the refactor contrast: an explicit subtractive rubric
made already-valid refactor patches more negative for all three models, with
different effect sizes. The cleanup contrast shows that the intervention adds
little when deletion is already explicit in the task. The feature task needs a
corrected fixture and a new preregistered run before it can test addition bias
without confounding task semantics and behavior validity.

Token receipts are preserved in the result and variance artifacts as
descriptive telemetry. They show substantial trajectory variance, especially
for Composer, but they are not causal cost estimates.

## Artifacts

- `research/phase-2/design-variance-r5.json` — frozen 120-cell design.
- `research/phase-2/live/variance-r5-results.json` — combined per-cell
  receipts.
- `research/phase-2/live/variance-r5-report.json` — repeated-variance groups,
  paired comparisons, and adapter status counts.
- `research/phase-2/live/variance-r5-summary.json` — six model-by-arm
  aggregate groups.
