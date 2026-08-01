# Phase 1 live pilot findings

## Scope

The corrected pilot crossed three Cursor-adapter models with two arms on one
behavior-preserving refactor:

- GPT-5.6 Luna with maximum effort (`gpt-5.6-luna`)
- Grok 4.5 (`grok-4.5`)
- Composer 2.5 (`composer-2.5`)
- `neutral_control`
- `subtractive_rubric`

The task was to preserve `display_name` behavior while removing duplicated
name normalization. All six behavior oracles passed. Candidate hashes,
Puppetmaster usage receipts, and harness measurements are in
`research/phase-1/live/pilot-2026-08-01-v2.json`.

The first six-run artifact is retained as
`pilot-2026-08-01.json`, but is marked `pre_correction`: its neutral prompt
inherited deletion-oriented maintenance language. It is provenance, not the
clean comparison.

## Directional observation

All three corrected neutral candidates were byte-identical. Each added a
`normalize_name` helper while retaining the existing `first_name` and
`last_name` wrappers:

- raw diff: `+6 -2`, net `+4`
- structural symbols: `+1 / -0`
- behavior oracle: passed

The corrected subtractive candidates all had negative raw net LOC:

- Luna: `+3 -6`, net `-3`
- Grok: `+3 -6`, net `-3`
- Composer: `+3 -5`, net `-2`

Luna and Grok matched the fixture's hand-authored subtractive target. Composer
made the same structural deletion/reuse choice with different blank-line
churn. All three behavior oracles passed. This is evidence that an explicit
subtractive rubric can alter patch direction on this task; it is not evidence
that the effect generalizes.

## Cleanup-task replication

The second corrected pilot used an inherently subtractive cleanup task:
removing an unused flag and obsolete debug helper while preserving parsing.
All three models produced the same `-5` raw LOC candidate under both arms, and
all six behavior checks passed. The subtractive rubric did not change the
direction when the task itself made deletion explicit.

This task contrast is important. The intervention appears task-dependent: it
was consequential on the refactor fixture, but redundant on explicit cleanup.
That argues against using raw positive LOC as a universal model trait and
supports measuring task mix separately from maintenance behavior.

## Token observations

The Puppetmaster receipts totaled 533,016 tokens for the neutral arm and
461,444 for the subtractive arm. That aggregate reduction is not a clean
inference-time savings result:

- Luna increased from 178,271 to 245,430 total receipt tokens.
- Grok increased from 109,360 to 129,408.
- Composer decreased from 245,385 to 86,606.

Input context dominates these small-task receipts, and the three models used
different reasoning settings. Turns and tool calls were not exposed by the
receipts. Therefore, the pilot supports measuring token economics, not a claim
that subtraction is cheaper yet.

## What this changes

The leading mechanism is now more specific than “LLMs like addition.” On a
fixed maintenance task, all three models selected an additive reuse shape
under a direction-neutral prompt, while an explicit deletion-oriented rubric
selected a subtractive reuse shape for all three in the corrected run. That
supports testing task framing, deletion gates, and risk language as causal
interventions before attributing the effect to architecture.

The next experiment must use isolated clean checkouts, equalized effort
settings where possible, multiple independent fixtures per task class, and
trajectory-level tool/turn capture. It should compare patch direction,
behavioral and structural quality, and receipt tokens jointly.
