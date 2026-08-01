# Phase 0 memo — Grok 4.5

Independent framing. Speculative claims marked *(spec)*. No invented citations.

## 1. Stance

Addition bias is **overdetermined**, but the ranking for agentic coding sessions (especially "refactor / cleanup / optimize" prompts that still ship `+ >> -`) is:

1. **H-risk** — asymmetric downside of deletion under uncertainty
2. **H-tool** — local insert/replace patch UX makes shrink expensive
3. **H-pref** — helpfulness/completeness rubrics elicit elaboration
4. **H-task** — feature-factory corpus and user prompts amplify the above
5. **H-measure** — move/regen inflation is real but secondary
6. **H-arch** — next-token elaboration may nudge, but is weak as sole cause

**Prior:** Holding task fixed, bias shrinks but does not vanish — so H-task is large, not decisive. The residual is mostly *fear of breakage + cheapest safe edit*, not transformer inevitability. I expect prompt/gate interventions to move median net LOC materially across models; if they do not, H-arch rises. Hypothesis 7 in `HYPOTHESES.md` is correct: the goal is sign-matching by task type, not universal minimalism.

## 2. Mechanisms

Concrete paths that produce `+ >> -` in agent diffs:

1. **Asymmetric regret under partial observability.** The agent lacks a full behavioral model of the module. Deleting a path can fail distant tests; wrapping/duplicating "preserves" behavior. Rational policy under uncertainty: add a shim, leave the old path, or copy-then-edit. Measurable as: high rate of *orphaned* dual implementations (old + new) after "refactor" tasks.

2. **Local patch cost gradient.** Tools that apply hunks or search-replace favor *insert near cursor / replace a small span*. Global deletion (dead exports, unused helpers, whole files) requires wider read + confidence. Measurable as: `|deleted lines|` correlates with files already fully loaded into context; deletions outside the opened window stay near zero.

3. **Completeness-as-helpfulness elicitation.** Preference-shaped models treat "handle edge cases," "add types/docs/tests," and "leave migration helpers" as upside-only. On cleanup prompts they still emit scaffolding the human did not request. Measurable as: share of `+` lines that are comments, stubs, TODOs, or unused parameters — tagged by a simple classifier.

4. **Failed-delete / regen artifact.** Agents rewrite a function in place by pasting a new body nearby, then fail to remove the old one; or regenerate a file and leave the previous path. Diff stats count this as pure addition. Measurable via clone detection (near-duplicate blocks within ±N lines / same symbol rename).

5. **Task-mix amplification (not root).** Success traces and evals reward "feature shipped." That trains operators and routers to ask for more surface area. It explains base rates on product work; it does *not* alone explain positive net LOC on explicitly subtractive prompts. *(spec on training data composition — mark as prior, not fact.)*

6. **Measurement illusion (partial).** `git diff --stat` treats moves poorly unless rename detection is tuned; agent "rewrite file" patterns look like delete+add of whole files. That inflates both sides but can still bias *net* if the rewrite grows. Measurable by comparing `--find-renames` / AST-symbol tracking vs raw line stats.

**What I downweight:** Pure H-arch ("transformers must elaborate"). If true as sole cause, identical-task gates would fail uniformly. I expect partial success — so architecture is a soft prior, not the main lever.

## 3. Disconfirmers

Evidence that would falsify or demote my top mechanisms:

| Claim | Disconfirmer |
|-------|----------------|
| **H-risk is first-order** | On fixed refactor tasks, adding "prefer delete; failing tests abort the run" moves median net LOC by ≤10% of the move from a hard net-LOC ≤0 gate that *does not* mention breakage. Risk framing should beat vague "be concise" by a clear margin (hypothesis 2). If "be concise" ≈ risk framing ≈ net-LOC gate, risk is not first-order. |
| **H-tool is second** | Same model + same prompt, but edit interface switched from local patch to whole-file rewrite-with-required-delete-quota, yields little change in net LOC / orphan-dual rate. Tooling would then be weak. |
| **H-pref is soft / elicited** | Subtractive rubrics with no fine-tune fail to change net LOC across Luna / Grok / Composer (hypothesis 3/4). Bias would look hard-wired. |
| **H-task dominates residual** | Holding wording fixed ("refactor, no new features, net LOC ≤ 0 preferred") collapses addition bias to noise (≈0 median net after measurement correction). Then preference/risk/tool are minor. |
| **H-measure is primary** | After rename/move/clone correction, "addition bias" on cleanup tasks disappears; raw `--stat` was the story. |
| **H-arch sole cause** | Strong, consistent failure of all prompt/gate interventions across models on fixed tasks. |

## 4. Intervention map

Ranked by expected **leverage per token spent** on refactor/cleanup tasks (not feature work):

| Rank | Class | Intervention | Why / failure mode |
|------|-------|--------------|--------------------|
| 1 | **Process gates** | **Delete-first pass** then implement: require a candidate deletion list (symbols/files) before any `+`. | Forces search for dead weight; fails if list is theatrical (delete comments only). Gate: ≥1 semantic delete (AST-level) before accept. |
| 2 | **Process gates** | **Net-LOC budget** on non-feature tasks: reject or loop until `net ≤ 0` (or ≤ task-type target). | Cheap, measurable; fails via comment-stripping / renaming games — pair with quality tests + "no behavior change" oracle. |
| 3 | **Prompt & rubric** | Explicit risk-flipped objective: "deletion preferred; tests are the safety net; unused dual paths fail review." | High leverage if H-risk/H-pref hold; fails if model cannot find safe deletes (then budget alone causes thrash). |
| 4 | **Tooling** | Diff UX that surfaces *unused after edit*, rename detection, and "prove deletion" checklist in the apply loop. | Aligns cost gradient with shrink; expensive to build; Phase 1 can fake with scripts. |
| 5 | **Multi-agent review** | Reviewer that only accepts net-negative refactors (or demands delete proofs). | Strong filter; **immediate** token cost high; thrash if generator and reviewer disagree. Prefer as second line after gates. |
| 6 | **Training / reward** | Penalize orphan duals, unused exports, and positive net LOC on labeled cleanup tasks. | Highest ceiling, slowest/most expensive; do not block Phase 1–2 on this. |

**Cheap gates beat post-hoc cleanup agents** (hypothesis 5): a budget + delete-first on the *same* turn sequence should beat a laissez-faire patch followed by a dedicated cleanup agent, measured as Δmedian(`net LOC`) / tokens.

## 5. Token economics

**Fighting bias saves money when:**

- The module stays **hot** (≥3 follow-on agent tasks reading the same files) — deferred context tokens dominate (hypothesis 6).
- Tasks are **refactor/cleanup** and unconstrained agents leave dual implementations; each extra 50–200 lines is re-embedded many times.
- Interventions are **front-loaded gates** (budget, delete-first) that add ~0.5–1.5 turns, not full second agents.

**Fighting bias wastes tokens when:**

- **One-shot feature** work where `+` is the correct sign (hypothesis 7) — subtractive discipline fights the task.
- **Cold modules** never revisited — deferred savings ≈ 0; you paid for a lean aesthetic.
- **Thrash loops**: hard `net ≤ 0` without a test oracle → agent deletes, breaks, re-adds wrappers → more tokens than laissez-faire.
- **Reviewer swarms** on tiny diffs: multi-agent overhead exceeds any later context win.

**Rule of thumb *(spec, for Phase 3 to fit):*** If intervention adds cost \(C\) tokens once, and removes \(L\) lines that would have been in context for \(K\) later turns at ~\(T\) tokens/line effective, break-even when \(K \cdot L \cdot T > C\). For hot modules, \(K\) is large; for cold, skip the fight.

## 6. Phase-1 experiments

Three cheap tests runnable in this repo next (no training runs):

### E1 — Fixed-task net-LOC by framing (tests H-task residual, H-risk, H-pref)

- **Fixture:** One small module with intentional dead code + a slightly tangled helper (hand-authored).
- **Task (identical across arms):** "Refactor for clarity; no new features; keep tests green."
- **Arms (n≥10 runs each, same model):** (a) neutral prompt; (b) "be concise"; (c) risk-flip + prefer delete; (d) hard net-LOC ≤0 gate with retry.
- **Metrics:** median/IQR of `net LOC`, `+`/`-` raw and rename-corrected; orphan-dual count (near-duplicate symbols); test pass rate; tokens/run.
- **Pass criteria for priors:** (c) beats (b) on net LOC; (d) beats (c) but may raise retries/failures — quantify the trade.

### E2 — Measurement correction audit (tests H-measure)

- On the same corpus of agent diffs from E1, compute net LOC three ways: raw `diff --stat`; with rename detection; with AST symbol move/clone discount.
- **Metric:** fraction of apparent `+` explained as move/regen vs true net-new / boilerplate.
- **Decision:** If >40% of "bias" vanishes under correction, Phase 2 must use corrected metrics or we will optimize the wrong number.

### E3 — Delete-first vs cleanup-after (tests hypothesis 5)

- Same fixture + neutral task wording.
- **Arm A:** Mandatory delete-candidate list + at least one applied delete before further edits; stop when tests pass.
- **Arm B:** Unconstrained patch to green, then a second "cleanup / subtract" agent turn.
- **Metrics:** final net LOC, total tokens (both turns), regression rate, time-to-green.
- **Expectation:** A achieves lower or equal net LOC at lower total tokens than B; if B wins on quality-adjusted net LOC per token, revise intervention ranking.

---

**Bottom line for synthesis:** Treat addition bias as **risk + tool locality + soft preference**, amplified by task mix, inflated somewhat by measurement. Phase 1 should hold tasks fixed, correct diffs, and put delete-first + net-LOC gates on the critical path before multi-agent or training bets.
