# Hypotheses (falsifiable)

Working claims. Phase 0 should attack or refine these; Phase 1+ should test them.

## Cause

1. **H-task dominates H-arch.** Holding task wording fixed (especially "refactor with no new features"), addition bias shrinks but does not vanish — so task mix is large, architecture alone is insufficient.
2. **H-risk is first-order.** When agents are given an explicit "prefer delete; breaking tests fail the run" objective, net LOC drops more than when they are only told "be concise."
3. **H-pref is real but soft.** Models will produce leaner patches under subtractive rubrics without fine-tuning, implying the bias is partly *elicited*, not hard-wired.
4. **H-arch is weak as a sole cause.** If strong architectural inevitability held, prompt/gate interventions would fail across models; we expect partial success across Luna / Grok / Composer.

## Intervention & cost

5. **Cheap gates beat expensive rewrites.** A net-LOC budget + delete-first pass on refactor tasks reduces median `+` more per token spent than a full second "cleanup" agent after the fact.
6. **Deferred savings dominate.** Over ≥3 follow-on tasks in the same module, token spend with subtractive discipline is lower than laissez-faire addition, even if the first task costs more.
7. **Feature tasks still want addition.** The goal is not universal minimalism — it is matching sign of net LOC to task type (feature → +, refactor/cleanup → ≤0).
