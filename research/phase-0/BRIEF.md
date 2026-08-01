# Phase 0 — Multi-model framing brief

Each worker writes an independent memo. Do not coordinate with other models' outputs.

## Deliverable

Write exactly one file:

`research/phase-0/memos/<model-slug>.md`

where `<model-slug>` is one of:

- `gpt-5.6-luna` (maximum available effort)
- `grok-4.5`
- `composer-2.5`

## Memo structure (required)

1. **Stance (5–10 lines)** — Your prior: is addition bias mostly task-mix, preference/incentive, risk asymmetry, tooling, architecture, or measurement? Rank them.
2. **Mechanisms** — Concrete mechanisms (not slogans) that would produce `+ >> -` in agent diffs.
3. **Disconfirmers** — What evidence would falsify your top mechanism?
4. **Intervention map** — Rank interventions by expected leverage / cost:
   - prompt & rubric
   - process gates (net-LOC budgets, delete-first)
   - multi-agent review
   - training / reward changes
   - tooling (diff UX, apply_patch incentives)
5. **Token economics** — When does fighting addition bias save money? When does it waste tokens?
6. **Phase-1 experiments** — Propose 3 cheap empirical tests we can run in this repo next.

## Constraints

- Research memo only. Do not refactor unrelated code.
- Be opinionated and specific. Name failure modes.
- Prefer mechanisms we can measure over vibes.
- Read `README.md`, `research/QUESTIONS.md`, and `research/HYPOTHESES.md` first.
