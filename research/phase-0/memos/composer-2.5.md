# Phase 0 memo — Composer 2.5

Independent framing for the Subtraction research program. Written from Cursor Composer 2.5 judgment; no coordination with other model memos.

---

## 1. Stance

**Prior ranking (strongest → weakest cause of `+ >> -` in agent diffs):**

1. **H-risk (risk asymmetry)** — Deletion is irreversible-looking in a single turn; addition is reversible and testable incrementally. Agents (and their human reviewers) treat "add a wrapper" as lower-variance than "delete 200 lines and hope tests pass."
2. **H-tool (edit-tool economics)** — Line-oriented patch tools (`search_replace`, `apply_patch`, hashline inserts) make *local extension* the default action. Shrinking requires reading more context, matching exact strings, and often multiple coordinated deletes. The tool loop literally charges tokens per edit; agents learn (via system prompts and trace shape) that fewer, additive hunks succeed more often.
3. **H-task (task-mix / prompt distribution)** — "Implement X," "add feature Y," and "fix this bug" dominate real sessions. Even "refactor" prompts often smuggle additive requirements ("while you're in there, also…"). Task mix sets the prior; it does not fully explain addition-heavy diffs on explicitly subtractive tasks.
4. **H-pref (preference / helpfulness elicitation)** — Models trained to be helpful and complete produce verbose, defensive code (extra guards, comments, fallbacks) when uncertainty is high. This is *soft*: rubrics can partially suppress it without fine-tuning.
5. **H-measure (counting artifact)** — Moves, renames, and extract-method refactors inflate `+` in naive LOC diffs. Material but not sufficient to explain order-of-magnitude skew on "delete dead code" tasks where ground truth is net-negative.
6. **H-arch (architectural inevitability)** — Weakest. If decoding inherently favored elaboration, subtractive rubrics and risk-reversal gates would fail uniformly across models; I expect partial, model-dependent success instead.

**Bottom line:** Addition bias is mostly *incentive-aligned behavior under asymmetric failure costs*, amplified by tool UX and task wording—not a hard law of transformers.

---

## 2. Mechanisms

Concrete paths from objective + environment to positive net LOC:

### M1 — Asymmetric failure signal (H-risk)

- **Mechanism:** Test failures and linter errors after deletion are attributed to the delete hunk. Test failures after addition are often attributed to "incomplete implementation" → more addition. The agent's implicit utility function penalizes visible breakage more than invisible bloat.
- **Observable signature:** On identical refactor prompts, net LOC drops sharply when CI runs *before* the session ends and failed runs block submission; smaller drop when tests are advisory only.
- **Failure mode:** Agent deletes working code and hides behind "simplification" — measurable via regression rate, not LOC alone.

### M2 — Patch granularity bias (H-tool)

- **Mechanism:** Single-hunk insertions succeed on first try; multi-file deletes require exact whitespace matches and ordered edits. Agents rationally choose "add new function + deprecate old" over "delete old" because the former composes in one tool call.
- **Observable signature:** Correlation between number of edit tool invocations and net LOC; additive diffs have higher first-attempt apply success rate (if logged).
- **Failure mode:** Forced delete-first passes that leave the repo uncompilable mid-session unless paired with a "keep green" gate.

### M3 — Scope creep in instruction parsing (H-task)

- **Mechanism:** User messages bundle primary task + implicit quality bar ("production-ready," "handle edge cases"). Models expand scope additively because refusing scope reads as unhelpful.
- **Observable signature:** Net LOC scales with prompt length and count of auxiliary requirements, even when primary task is subtractive.
- **Failure mode:** Over-narrow prompts that forbid necessary additive fixes (e.g., deleting code without updating imports).

### M4 — Defensive completeness (H-pref)

- **Mechanism:** Under ambiguity, models add null checks, type widening, logging, and comments to reduce perceived error risk. RLHF-style helpfulness rewards visible thoroughness.
- **Observable signature:** Excess `+` concentrates in boilerplate categories (comments, guards, re-exports) detectable by static heuristics or line classifiers.
- **Failure mode:** Rubrics that demand minimalism produce under-documented, brittle deletes.

### M5 — Move/copy diff inflation (H-measure)

- **Mechanism:** Extract-function and rename-via-copy leave old and new code in the diff simultaneously; git counts both sides.
- **Observable signature:** Semantic diff (or copy-detection) collapses apparent `+` by 30–70% on refactor-labeled tasks *(speculative range — needs Phase-1 measurement)*.
- **Failure mode:** Over-correcting metrics hides real addition when semantic diff is wrong.

### M6 — Completion pressure in multi-turn loops (H-task + H-tool)

- **Mechanism:** Agent harnesses cap turns or urge "finish the task." When deletion requires exploration (find all references, confirm dead code), the cheapest terminal action is often "add shim" or "leave old path."
- **Observable signature:** Last-turn diffs are disproportionately additive vs mid-session turns.
- **Failure mode:** Unlimited turns without a delete objective → unbounded accretion.

---

## 3. Disconfirmers

Evidence that would **falsify or demote** the top mechanisms:

| If we observe… | Then… |
|----------------|--------|
| Fixed subtractive task ("remove feature X, no new code"), strong CI, net LOC still >> 0 **across all three Phase-0 models** with comparable regression rates | H-risk is not first-order; look harder at H-arch or H-pref as hard constraints. |
| Semantic-adjusted diffs show move/copy explains **>80%** of gross `+` on refactor tasks | H-measure dominates; intervention focus shifts to diff UX, not agent behavior. |
| Delete-first + net-LOC budget **increases** regression rate with **no** net LOC improvement vs control | H-pref/risk story is wrong about elicitation — subtractive rubrics fight the model rather than revealing a cheaper policy. |
| Tool success rate is **higher for deletes than inserts** on the same files *(if instrumented)* | M2 (patch granularity) is not a driver; demote H-tool. |
| Feature tasks under subtractive rubrics show **large** net-negative diffs without quality loss | The bias is over-correctable; task-type matching (H7) matters more than mechanism ranking. |
| Single-turn, no-tools completion on "list lines to delete" produces **addition-shaped** natural language plans | Would support stronger H-arch / completion prior *(speculative test)*. |

---

## 4. Intervention map

Ranked by **expected leverage / token cost** (high leverage, lower immediate cost first):

| Rank | Intervention | Leverage | Immediate token cost | Notes |
|------|----------------|----------|----------------------|-------|
| 1 | **Process gate: net-LOC budget on refactor/cleanup tasks** (e.g., median net LOC ≤ 0, gross delete ≥ N lines) | High | Low–medium (one extra self-check turn) | Directly targets M1/M6; measurable pass/fail. Risk: gaming via comment deletion. |
| 2 | **Prompt & rubric: delete-first + prove-deletion checklist** ("cite symbol refs, run tests, no new exports") | High | Low | Elicits H-pref without training; pairs with M1. |
| 3 | **Tooling: incentivize shrink patches** (reward successful `DEL` hunks, multi-line delete helpers, semantic move detection in diff summary) | Medium–high | Medium (harness work, not model tokens) | Attacks M2/M5 at the source. |
| 4 | **Process gate: keep-green CI between delete tranches** | Medium | Medium (extra test runs) | Makes H-risk symmetric; deletion failures surface early. |
| 5 | **Multi-agent review: reviewer accepts only net-negative or zero-net refactors** | Medium | High (full second pass) | Good for quality; poor token ROI unless deferred savings are large. |
| 6 | **Prompt: "minimal diff" without delete obligation** | Low | Low | Weak alone (contradicts H2 in HYPOTHESES.md); useful as control arm. |
| 7 | **Second-pass cleanup agent after feature work** | Low–medium | Very high | Post-hoc subtraction; usually loses to cheap gates (H5). |
| 8 | **Training / reward changes** (RLHF for brevity, delete-positive rewards) | High *(speculative)* | N/A at inference; expensive offline | Out of scope for this repo until Phase 2+ shows prompt/gates plateau. |

**Expected failure modes:** Net-LOC gaming (delete comments/tests), brittle deletes that pass budget but fail H7 task-type matching, reviewer deadlock when feature tasks need additive work.

---

## 5. Token economics

### When fighting addition bias **saves** money

- **Multi-turn maintenance on the same module (≥3 sessions)** — Smaller files reduce every subsequent prompt's context window. If deferred context savings exceed ~1–2k tokens per turn × turns, subtractive discipline wins (supports H6).
- **Large monorepos / long agent traces** — Addition compounds context; deletion is a one-time exploration cost with repeated dividend.
- **Refactor and cleanup task classes** — Goal is net LOC ≤ 0; any positive net LOC is *pure waste* relative to task spec (supports H7).
- **Human review time** *(not tokens but coupled)* — Leaner diffs reduce reviewer load; worth noting for product ROI though Phase 3 focuses on tokens.

### When fighting addition bias **wastes** tokens

- **Greenfield feature delivery** — Forcing net-negative diffs on new capability is wrong task-type; gates should be conditional (H7).
- **Heavy delete-first on unfamiliar code** — Exploration tokens (reference search, read_file sprawl) can exceed the cost of leaving dead code one session.
- **Multi-agent review on every PR** — Second full pass rarely pays off on single-shot tasks; B2 immediate cost dominates B3 on short horizons.
- **Over-long prove-deletion checklists** — Checklist length scales with model obedience, not code quality; diminishing returns after ~1 self-verify turn.

**Breakeven heuristic *(speculative)*:** Subtract-first + net-LOC gate is net-positive in token terms when the same files re-enter context within **3 agent sessions** or when baseline file size exceeds **~500 LOC** in the touched module. Phase 1 should estimate context bytes saved per net line removed.

---

## 6. Phase-1 experiments

Three cheap, repo-local tests:

### E1 — Fixed-task, cross-model LOC shape (A2/A3)

- **Setup:** 5 identical subtractive tasks (e.g., "remove unused flag and all references; no new features; tests must pass") run on Luna, Grok, Composer with **frozen harness** (same tools, same test command).
- **Measure:** Gross `+`, gross `-`, net LOC, regression pass rate, edit tool call count, last-turn vs mid-turn LOC split.
- **Cost:** ~15 agent runs + diff scripts; no training.
- **Discriminates:** H-task vs H-risk vs H-tool (if prompts identical, task mix removed).

### E2 — Semantic diff decomposition (A1 / H-measure)

- **Setup:** Sample 30–50 real or synthetic agent diffs labeled "refactor/cleanup." Run naive LOC + semantic diff (copy/move detection via git diff `--numstat` + simple AST/hash matching, or manual annotation on a subset).
- **Measure:** Share of gross `+` explained by move/copy vs true new lines vs comments/guards.
- **Cost:** Script + human spot-check on 10 diffs.
- **Discriminates:** H-measure vs behavioral bias; sets baseline for all later phases.

### E3 — Gate A/B on refactor tasks (B1/B2)

- **Setup:** Same 5 tasks as E1, split: **Control** ("refactor cleanly") vs **Gate** (delete-first rubric + net LOC ≤ 0 + single self-check turn).
- **Measure:** Δ net LOC, Δ total tokens (prompt + completion), Δ tool calls, regression rate.
- **Cost:** 10 runs; directly tests H2, H5, and B2 vs B3 proxy.
- **Success criterion:** Gate arm median net LOC ≤ 0 with regression rate ≤ control + ε.

---

## Summary

Addition bias is best treated as **risk- and tool-shaped agent policy**, not mysticism about transformers. Phase 1 should hold tasks fixed, classify diff semantics, and A/B cheap gates before investing in multi-agent cleanup or training. Composer 2.5 expects **partial** success from subtractive rubrics + net-LOC budgets across models—enough to justify Phase 2, not enough to declare the problem solved.
