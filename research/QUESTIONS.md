# Research questions

## A — Cause of addition bias

**A1.** When agentic coding sessions produce strongly positive net LOC on non-feature tasks (refactors, "cleanup", "optimize"), what share of that net is:

- true net-new capability,
- defensive duplication / wrappers,
- failed delete + re-add (move/copy artifacts),
- commentary / boilerplate the human never asked for?

**A2.** Is addition preference better explained as:

| Hypothesis class | Claim |
|------------------|--------|
| H-task | Task mix + user prompts reward shipping features; models mirror that. |
| H-pref | Preference/RL signals treat verbosity and "completeness" as helpful. |
| H-risk | Deletion has asymmetric downside (breakage); addition looks safer under uncertainty. |
| H-tool | Edit tools and patch formats make local inserts cheaper than global shrinks. |
| H-arch | Something in transformer decoding / next-token objectives inherently favors elaboration. |
| H-measure | Our diffs mis-count moves/regens as pure addition. |

**A3.** Which of the above survive when we hold the *task* fixed and only vary model, prompt framing, or review gates?

## B — Interventions and cost

**B1.** Which interventions move median net LOC toward zero/negative without raising regression rate: subtract-first pass, net-LOC budget, delete-proof checklist, reviewer agent that only accepts net-negative refactors, etc.?

**B2.** What is the *immediate* token cost of those interventions (extra turns, extra review)?

**B3.** What is the *deferred* token savings from leaner code (smaller files in context, fewer follow-up cleanups, less conflicting surface area)?

**B4.** Under what horizons (single PR vs multi-week agentic maintenance) does B3 exceed B2?
