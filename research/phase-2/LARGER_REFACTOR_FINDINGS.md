# Phase 2 larger-refactor replication findings

Decision date: 2026-08-01  
Decision status: completed interaction-focused replication

## Scope and validity

The preregistered wave crossed two larger deterministic refactors
(`refactor-shared-normalizer` and `refactor-dead-compatibility-path`), three
frozen model/effort pairs, the complete eight-arm T/D/B factorial, and five
repetitions: `2 × 3 × 8 × 5 = 240` cells.

The selected dataset contains 240 completed adapter receipts and 240/240
behavior-oracle passes. Six initial adapter failures were retained separately
and retried from fresh isolated roots. The variance report includes those six
non-completed statuses as provenance, but excludes them from completed
comparisons. Every task/model/arm group has matched repetitions `1..5`.

Primary artifacts:

- [`larger-refactor-r5-results.json`](live/larger-refactor-r5-results.json)
- [`larger-refactor-r5-report.json`](live/larger-refactor-r5-report.json)
- [`larger-refactor-r5-factor-effects.json`](live/larger-refactor-r5-factor-effects.json)
- [`larger-refactor-r5-summary.json`](live/larger-refactor-r5-summary.json)
- [`larger-refactor-r5-wave-meta.json`](live/larger-refactor-r5-wave-meta.json)
- [`larger-refactor-r5-initial-failures.json`](live/larger-refactor-r5-initial-failures.json)
- [`larger-refactor-r5-retry-provenance.json`](live/larger-refactor-r5-retry-provenance.json)

## Result

The larger-task replication does not support a universal standalone D
component. It supports a task- and model-conditional interaction:

- On `refactor-shared-normalizer`, the D factorial main effect was
  `-0.65` raw-net lines for Composer, `-3.10` for GPT-5.6 Luna, and `-3.25`
  for Grok 4.5. The matched D-only treatment-minus-neutral effects were
  `0.0`, `-6.4`, and `-10.0`, respectively. The full T+D+B effects were
  `0.0`, `-5.6`, and `-9.0`.
- On `refactor-dead-compatibility-path`, the D factorial main effect was
  `0.0` for Composer, `+0.30` for GPT-5.6 Luna, and `+2.0` for Grok 4.5.
  The matched D-only effects were `0.0`, `+0.8`, and `+3.4`; the full T+D+B
  effects were `0.0`, `+1.2`, and `+3.0`.

All completed treatment and neutral observations passed their behavior
oracles. The negative D result therefore replicated across two models on one
larger fixture, but not across both fixtures. The second fixture is a
behavior-safe null or positive result under these registered conditions, not
evidence that deletion-first prompting is harmful in general.

The pattern is also compositional: on the normalizer task, the D-only arm and
the full T+D+B arm agree for Luna and Grok but not for Composer, while the
factorial main effect is slightly negative for Composer despite a zero
D-only paired contrast. This is evidence against treating D as a portable
one-component mechanism.

## Interpretation boundary

This wave establishes a stronger boundary, not broad generalization:

- Deletion-first/reference-proof prompting can produce materially more
  subtractive patches on some larger refactor structures.
- The effect depends on task structure and model; it did not reproduce on
  `refactor-dead-compatibility-path`.
- The existing `control-rename` and prior confirmation artifacts remain
  validity anchors, but were not silently pooled with this interaction-focused
  wave. This wave itself contains no independent measurement-control task.
- Five repetitions and descriptive raw-net deltas do not establish
  statistical significance, causality, a mechanism, or universality across
  repositories and maintenance tasks.
- This wave has no `subtractive_rubric` legacy arm. Prior legacy comparisons
  remain separate confirmation evidence rather than a direct result of this
  factorial.

Observed token fields are preserved in the JSON receipts, but no priced
multi-turn trajectory was collected. Because the negative patch-shape effect
did not survive on both larger fixtures, the planned priced cost wave is
deferred; no dollar-saving claim is made.

## Decision

Publish the interaction as the result and stop calling D a universal
component. The next evidence gate is an independently specified refactor
replication that tests whether the normalizer-like interaction survives a new
task or repository. Do not model multi-turn dollar savings until a patch-shape
effect survives that broader validity gate and a separate priced trajectory
protocol is run.
