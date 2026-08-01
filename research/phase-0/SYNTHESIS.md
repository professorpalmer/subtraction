# Phase 0 Synthesis — Why Agents Add More Than They Remove

This synthesis reconciles the independent memos from GPT-5.6 Luna, Grok 4.5, and Composer 2.5. It is a framing document, not a report of measured experiments. Rankings, thresholds, and numerical ranges labeled “hypothesis” or “spec” are priors to test in Phase 1, not established facts.

## Executive conclusion

The consensus is that `+ >> -` is a conditional policy shaped primarily by task incentives, deletion risk, and the local economics of agent tools. It is not currently justified to treat the effect as an architectural inevitability of transformers. Task mix is the leading explanation for addition-heavy workloads overall, while risk asymmetry and tool locality better explain why positive diffs persist on explicitly subtractive refactor and cleanup tasks.

Consensus ranking, with the important distinction between workload prevalence and residual behavior:

1. **H-task — task mix and task wording.** Feature requests dominate many successful coding traces, and “helpful” completion therefore often means adding capability. The memos agree this is the largest explanation of the overall base rate, but it cannot by itself explain positive diffs on fixed cleanup tasks.
2. **H-risk — asymmetric downside of deletion.** Deletion can break undocumented callers, reflection, configuration, generated code, or compatibility surfaces. Addition, wrappers, and preservation are safer under partial observability. Grok and Composer rank this first; Luna ranks it second. All three treat it as a first-order explanation for residual bias.
3. **H-tool — local edit economics.** Insertion or a small replacement is often easier to execute and verify than tracing distributed references and coordinating several deletes. Grok and Composer rank this second; Luna ranks it fourth. The disagreement is about magnitude, not direction.
4. **H-pref — completeness and helpfulness incentives.** Extra guards, tests, comments, adapters, fallbacks, and migration shims are visibly responsible and can be rewarded even when they expand a cleanup patch. All three expect this to be soft and prompt-sensitive.
5. **H-measure — diff accounting artifacts.** Moves, renames, copy-then-edit operations, regeneration, formatting, and failed delete-and-readd sequences can inflate gross additions. The memos agree this is material, but generally secondary to actual behavior. It must be corrected before causal claims are made.
6. **H-arch — architectural or decoding inevitability.** Continuation and elaboration may be a weak prior, but no memo finds evidence that it should dominate once task, prompt, tools, and review gates are controlled.

This ranking is not a claim that the mechanisms are independent. Task mix supplies the prior; risk and tools determine the locally attractive policy; preference shaping makes that policy look complete; measurement sometimes exaggerates its apparent size.

## What the memos agree on, and where they differ

The three memos agree on five actionable points:

- Holding the task fixed should reduce, but not necessarily eliminate, addition bias.
- A behavior-preserving cleanup needs a different objective from a feature task; universal minimalism is the wrong target.
- “Be concise” is likely weaker than an explicit delete-first, prove-deletion, and keep-tests-green protocol.
- Net LOC alone is unsafe: it can reward comment deletion, test deletion, compressed code, or other metric gaming.
- Cheap gates should be tested before expensive reviewer swarms or training changes.

Their meaningful disagreement should remain visible:

- **Primary residual cause:** Grok and Composer put H-risk first and H-tool second. Luna puts H-task first overall, risk second, preference third, and tooling fourth. This is a testable disagreement about whether the dominant intervention should flip the risk signal or reduce edit friction.
- **Gate ordering:** Grok favors delete-first, then a net-LOC budget, then risk-flipped prompting. Composer puts the budget first, then delete-first proof, followed by tooling and keep-green CI. Luna favors a refactor rubric first, then delete-first, then a budget. Phase 1 should therefore isolate these components rather than assume one ordering.
- **Measurement thresholds:** Grok proposes a hypothesis that more than 40% of apparent bias disappearing under correction should change the metric plan; Composer offers a speculative 30–70% gross-addition collapse and an 80% threshold for declaring measurement dominant. These are incompatible priors, not evidence. The protocol should report the continuous decomposition and avoid adopting either cutoff in advance.
- **Break-even horizon:** Luna calls three follow-on tasks a plausible minimum; Grok describes a hot module as at least three follow-on tasks; Composer proposes a speculative three-session or roughly 500-LOC heuristic. None is established. Phase 1 should estimate a curve rather than treat three or 500 as a law.

## Why `+` dominates `-`

For feature work, the answer is straightforward: the requested capability is new, so additions are often the correct sign. A feature-heavy task distribution also trains users, evaluators, routers, and agents to interpret visible surface area as progress. This explains prevalence, not necessarily a defect.

For cleanup and refactor work, the combined mechanism is:

1. The agent has incomplete knowledge of callers and behavioral contracts.
2. A delete has a large, delayed, and difficult-to-attribute failure surface.
3. An additive wrapper, fallback, duplicate implementation, or compatibility path preserves more possibilities while tests are still green.
4. Local patch tools make an insertion or small replacement cheaper than discovering and editing every dependent location.
5. “Production-ready” and “handle edge cases” language makes defensive additions legible as helpfulness.
6. Once an abstraction is added, later turns preserve it as context and route around it, creating a sunk-cost and compounding-surface effect.

The result is rational under an uncertainty-sensitive, reviewer-sensitive objective even when it is poor long-term maintenance. The architecture-only account is weaker because prompt and gate changes are expected to move behavior at least partially. This is a prior to test, not proof of rationality or of any particular training-data cause.

## Measurement artifacts versus agent behavior

Raw diff statistics and agent behavior must be separate variables.

**Raw measurement artifacts include:**

- a move or rename represented as additions and deletions;
- extract-method or copy-then-edit workflows that temporarily retain both bodies;
- generated files or formatting churn;
- delete-and-readd operations that preserve semantics;
- line-based accounting that treats changed lines as entirely new;
- comments, tests, or boilerplate that inflate `+` without adding runtime capability.

These can make `+` look larger without the agent choosing to add durable behavior. Conversely, a real additive behavior can be hidden by a simultaneous deletion. `git diff --stat` is therefore a descriptive artifact, not a causal metric.

**Behavioral outcomes include:**

- new symbols, exports, branches, dependencies, or runtime paths;
- orphaned dual implementations and retained dead code;
- true capability change;
- regression rate and test coverage;
- reviewer rework and later cleanup;
- context size and conflict surface in subsequent tasks.

Phase 1 should report at least raw line additions/deletions, rename-aware line counts, token similarity or clone matches, symbol additions/removals, generated-file status, and behavioral/test outcomes. A human or audited classifier should label additions as capability, defensive duplication, move/regen artifact, tests/docs, or unexplained boilerplate. If semantic correction removes most of the apparent skew, the conclusion is about accounting. If corrected additions remain and correlate with orphaned paths or later rework, it is agent behavior.

## Which mechanisms can change, and at what cost?

The most changeable mechanisms are elicitation, process, and tool friction:

- **Prompt/rubric:** State the task type, prohibit new capability on cleanup, require a deletion candidate, require caller/test evidence, and require tests before acceptance. Immediate cost is usually a longer instruction and possibly one self-check turn.
- **Process gates:** Require delete-first inventory and a keep-green check; use a task-type-specific net-LOC target with an exception for necessary replacement code. Cost is extra exploration, test runs, and possible retries.
- **Tooling:** Make reference tracing, semantic rename detection, reversible deletion, and shrink-oriented diff summaries easy. This has engineering cost but can reduce per-run model tokens.
- **Review:** A focused reviewer can flag additive refactor patches and request proof. It costs a second model pass and can create correlated thrash or deadlock.
- **Training/reward:** Positive examples of behavior-preserving deletion and penalties for orphan duals could change the default policy. This has the highest offline data and evaluation cost and should follow evidence that prompts and gates plateau.

The mechanisms that should not be changed indiscriminately are task sign and safety standards. Feature tasks may legitimately require positive net LOC. A hard “net negative always” reviewer can reject necessary migrations or force deletions that damage quality. Regression-adjusted semantic quality is the acceptance criterion, not a negative number.

## Phase 1 protocol

### Fixture and task matrix

Build a small, hand-authored fixture corpus with the same harness and test command:

| Fixture class | Tasks | Required ground truth |
|---|---:|---|
| Feature | 4 | New capability and expected positive behavior |
| Behavior-preserving refactor | 4 | At least one safe deletion candidate, tangled helper, and unchanged public behavior |
| Removal/cleanup | 4 | A removable flag, dead export, or obsolete branch with known references |
| Measurement control | 2–4 | Rename, move, formatting, and generated-file cases with known semantic equivalence |

The 12 primary tasks are a minimum starting matrix; the measurement controls are analyzed separately and must not be used as evidence that agents added behavior. Hold repository snapshot, tool availability, task text, test command, turn cap, and initial context constant within each comparison.

### Model arms and prompt/gate arms

Run all three Phase 0 model identities—`gpt-5.6-luna`, `grok-4.5`, and `composer-2.5`—with the same harness. For each model, use these prompt/process arms:

1. **Neutral control:** task text and “keep tests green,” with no sign instruction.
2. **Concise control:** neutral task plus “make the smallest clear change.”
3. **Subtractive rubric:** no new capability for refactors/removals, identify deletion candidates, prove references, and run tests.
4. **Delete-first gate:** require an inventory and at least one semantic delete before additions, with an exception when the inventory finds no safe deletion.
5. **Budget gate:** task-type-specific target (for refactor/removal, provisional `net LOC ≤ 0` preferred, not an unconditional pass condition), plus explanation and test evidence for exceptions.
6. **Post-hoc cleanup comparator:** unconstrained implementation followed by one cleanup turn, to test whether an extra agent pass beats a cheap front-loaded gate.

The feature arm must remain a sign-matching control: subtractive requirements should not be applied to it. A run fails the gate only after checking semantic quality and required behavior; otherwise the metric can induce deletion theater.

### Metrics and analysis

Primary metrics:

- semantic net LOC and raw `+`/`-` LOC;
- regression and required-test pass rates;
- capability correctness and blind reviewer quality score;
- symbols/exports/dependencies added and removed;
- orphan dual implementations and retained dead paths.

Secondary metrics:

- input/output/tool tokens, turns, test invocations, and time to first semantic delete;
- files and lines loaded into context;
- rework, conflicts, and reviewer-requested changes;
- classifications of gross additions: capability, defensive code, tests/docs, move/regen, or unexplained boilerplate;
- later-task context tokens and failures.

Use rename-aware diffing, token/hash clone matching, symbol identity, and generated-file tagging. Report medians and distributions, not only averages. Compare model, task class, and arm with a factorial analysis or predeclared pairwise contrasts. Blind reviewers should score quality without seeing the arm or LOC target.

### Sample sizes and decision criteria

For an initial cheap screen, run at least 10 independent repetitions per model × task class × principal arm, using 12 primary tasks balanced across repetitions. If variance is high, expand to 20 repetitions before making an intervention decision; these sample sizes are proposed thresholds, not validated power calculations.

Advance an intervention to Phase 2 only if it:

1. reduces median semantic net LOC for refactor/removal tasks versus neutral control;
2. does not increase regression rate beyond a predeclared tolerance `ε` (proposed hypothesis: 5 percentage points);
3. improves or preserves blind quality;
4. has a measured token cost that can plausibly be recovered in the maintenance replay.

Treat the following as disconfirming results: no prompt/gate movement across models; lower LOC accompanied by material regression or quality loss; or semantic correction explaining nearly all apparent positive skew. Do not use the proposed ε or any 40%, 70%, 80%, three-task, or 500-LOC value as an established fact.

Add a three-follow-on-task replay only after the single-task screen. Start from identical outputs, give each condition three fresh-context maintenance tasks, and measure cumulative context, rework, conflicts, failures, and quality. This tests deferred savings rather than assuming them.

## Ranked intervention roadmap

1. **Task-type-aware subtractive rubric.** Low token cost and directly testable; require no new capability, deletion candidates, reference evidence, and tests.
2. **Delete-first plus keep-green gate.** Make deletion a real investigation step, but permit an evidence-based no-delete outcome and test after coherent tranches.
3. **Semantic net-LOC budget.** Use as a review signal, not a blind oracle; require explanation for positive refactor net and measure symbols and behavior.
4. **Shrink-oriented tooling.** Add reference tracing, reversible deletes, rename-aware diffs, and explicit move/regen classification.
5. **Focused reviewer.** Review only refactor/removal patches for additive surface and deletion proof; avoid full second-agent passes on every task.
6. **Training or reward changes.** Pursue only if controlled prompt and gate effects are replicated and insufficient; reward semantic minimality, not negative LOC in isolation.

## Failure modes and safeguards

- **Net-LOC gaming:** delete comments, tests, formatting, or public API names to hit a budget. Safeguard with behavior tests, symbol accounting, coverage, blind quality review, and a semantic deletion requirement.
- **Regression by forced deletion:** remove compatibility paths or undocumented callers. Safeguard with caller/configuration/reference inventory, keep-green checks, and reversible commits.
- **Feature starvation:** apply cleanup targets to new capability. Safeguard with task-type routing and a feature control arm.
- **Metric laundering through moves or compression:** make code look smaller without reducing semantic surface. Safeguard with clone/symbol/token analysis and maintainability review.
- **Reviewer deadlock or correlated errors:** generator and reviewer share the same mistaken deletion. Safeguard with narrow reviewer scope, tests, and sampled human adjudication.
- **Exploration thrash:** repeated searches and proof obligations cost more than the safe status quo. Cap gate turns, record exploration tokens, and allow “no safe deletion found.”
- **Over-documenting the intervention:** long checklists cause compliance theater. Test one self-check turn against longer protocols.
- **Confounding model and harness:** different tools or context windows make model comparisons invalid. Freeze the harness and randomize task order.
- **Survivorship bias:** inspect only accepted patches. Retain failed, reverted, and abandoned runs in the dataset.

## Token economics

Let:

- `C0` = baseline tokens for the initial task;
- `Ci` = immediate intervention tokens, including prompt, extra reads, tests, gates, and retries;
- `F0(h)` and `Fi(h)` = cumulative follow-up context, tool, and completion tokens through maintenance horizon `h`;
- `R0(h)` and `Ri(h)` = cumulative regression, conflict, and rework tokens;
- `Q` = any token-equivalent review or human-cost term included by the study;
- `ΔF(h) = F0(h) - Fi(h)` and `ΔR(h) = R0(h) - Ri(h)`.

The intervention breaks even at horizon `h` when:

`Ci + (Fi(h) - F0(h)) + (Ri(h) - R0(h)) + (Qi(h) - Q0(h)) ≤ 0`

Equivalently, when review cost is omitted:

`ΔF(h) + ΔR(h) ≥ Ci`.

For a simplified per-line model, if `L` durable semantic lines are avoided, each later task loads `T` effective tokens per line, the files are revisited `K` times, and expected rework savings are `S`, then the speculative break-even equation is:

`K × L × T + S ≥ Ci`.

Phase 1/3 must measure `L`, `T`, `K`, `S`, `Ci`, and regression probability rather than infer them from LOC. Measure file bytes and tokens actually loaded, task frequency, added tool turns, tests, retries, conflict events, and the lifetime of the module. The intervention is likely wasteful for disposable prototypes, cold modules, and legitimate feature additions; it is more promising for hot modules with repeated context and additive cleanup debt. The exact horizon at which it wins is an empirical result, not a Phase 0 conclusion.
