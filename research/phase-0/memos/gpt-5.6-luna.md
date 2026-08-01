# GPT-5.6 Luna — Phase 0 memo

## Stance

My prior is that addition bias is primarily a task-mix and incentive problem, not a transformer-level inevitability.
I rank task mix first: most successful coding traces ask for capability, so positive diffs are the learned default for “helpful.”
Second is risk asymmetry: deleting an apparently unused path can cause an invisible compatibility failure, while leaving it costs less immediate blame.
Third is preference shaping: “complete” answers reward wrappers, validation, comments, and fallback paths that look responsible locally.
Fourth is tooling: patch APIs make insertion and additive scaffolding easier to express than proving that a distributed dependency is dead.
Measurement is a material confounder, especially for moves, regeneration, formatting, and delete-and-readd edits.
Architecture is last: decoding may favor continuation and elaboration, but it should not survive strong task and review controls as the dominant cause.
The actionable hypothesis is therefore conditional: refactor prompts plus cheap deletion gates should move net LOC below zero without requiring retraining.

## Mechanisms

1. **Capability prior from task distribution.** If the training and interaction mixture overrepresents feature requests, the policy learns “solve missing requirement by adding a path.” On a cleanup task, that prior can manifest as compatibility wrappers, new tests, or observability rather than deletion. Measure this by holding the repository and task constant while varying task label (`add`, `refactor`, `remove`) and recording net LOC, added symbols, and behavior changes.

2. **Asymmetric loss under uncertainty.** A deletion has a large, delayed failure surface: reflection, configuration, external callers, generated code, and undocumented API consumers can break. An addition usually has a smaller immediate failure surface, even if it increases maintenance cost. A model optimizing expected reviewer reward can rationally preserve questionable code and add a safer replacement. Perturb the risk signal with explicit test requirements and a rollback budget; test whether deletion rises while regression rate stays flat.

3. **Completeness rewards create defensive surface area.** Preference signals favor answers that mention edge cases and “make it robust.” In code, that can become guards, adapters, deprecation shims, explanatory comments, and duplicate validation. These additions are locally legible but often substitute for asking whether the old path can disappear. Classify added lines by purpose and compare a plain concise rubric with a “minimal surface area” rubric.

4. **Local edit economics.** An agent can append a branch after reading one function; deletion requires tracing callers, tests, exports, configuration, and ownership boundaries. Tools that expose small hunks amplify this asymmetry. A patch that moves code may also be represented as delete-plus-add, encouraging conservative regeneration. Compare tool-call count, inspected-file count, and diff entropy for insert-first versus delete-first workflows.

5. **Context preservation and sunk-cost effects.** Once an agent has introduced an abstraction, later turns treat it as context rather than a candidate for removal. Each follow-up patch routes around the new surface, compounding `+` lines. A longitudinal replay across three tasks in one module should reveal whether early additive patches predict later wrapper and exception counts.

6. **Measurement artifacts.** Raw `+` and `-` counts cannot distinguish net-new behavior from moves, formatting, generated output, or a failed replacement. Use rename-aware diffs, token-level similarity, symbol identity, and behavior tests. The addition hypothesis is weaker if high positive churn mostly resolves to moved code or generated files.

## Disconfirmers

- On a balanced benchmark of feature, refactor, and deletion tasks with identical tools, agents still add at the same rate on behavior-preserving cleanup tasks, even when tests and explicit deletion acceptance criteria are present. That would elevate architecture or an unmodeled tool constraint.
- A prompt that only changes task framing has no effect, while a model or checkpoint change has a large, replicated effect after controlling for task, repository, and tool. That would challenge the claim that the bias is mainly elicited.
- Deletion-first gates increase regression rate or review rework enough to erase any LOC reduction. Then risk asymmetry is not merely a bias to correct; it is useful calibration.
- Rename-aware, token- and symbol-matched accounting shows that most apparent `+ >> -` diffs are moves, regeneration, or formatting. The measurement class would dominate the causal story.
- A tool with symmetric “remove unused” and “insert replacement” operations does not change deletion behavior, despite equal task and prompt conditions. Tool friction would then be secondary.
- Across a multi-task horizon, leaner patches do not reduce context tokens, conflict rate, or follow-up cleanup. The deferred-savings hypothesis would fail even if first-order LOC falls.

## Intervention map

| Rank | Intervention | Expected leverage | Cost / failure mode | Measurement |
|---|---|---:|---|---|
| 1 | Refactor-specific rubric: state “no new capability,” require a deletion candidate, and require evidence for every retained branch | High | Low; can induce performative deletions or under-fixing | Net LOC, changed symbols, tests, reviewer score |
| 2 | Delete-first process gate: inventory callers/tests, make a reversible deletion, run checks, then add only if a failing check requires it | High | One or two extra turns; may over-trace tiny tasks | Tool calls, inspected files, regression rate, net LOC |
| 3 | Net-LOC budget with an exception requiring an explanation and test evidence | Medium-high | Can game the metric with compressed or moved code; harms legitimate migrations | Rename-aware net LOC, token count, behavior coverage |
| 4 | Narrow reviewer agent that flags additive refactor patches and asks for a keep/delete justification | Medium | Review tokens and correlated model errors; should not auto-delete | Rework tokens, accepted deletions, escaped regressions |
| 5 | Tooling that makes dependency tracing, symbol references, rename detection, and reversible deletion first-class | Medium | Engineering cost; better UX cannot fix wrong task objective | Time-to-first-delete, trace completeness, diff classification |
| 6 | Training/reward changes using minimal, behavior-preserving patches as positive examples | Potentially high, slow | Expensive data curation; may overfit to negative diffs or produce brittle minimalism | Cross-task generalization and regression-adjusted net LOC |

The first experiment should combine ranks 1–3 rather than use a rigid “always subtract” rule. Feature tasks should retain additive behavior; the gate should key off task type and expected capability change. A hard net-negative reviewer is an unsafe oracle because a necessary replacement can legitimately have positive churn.

## Token economics

Fighting addition bias saves money when the code is long-lived, frequently loaded into context, or touched by multiple agents. A one-time dependency inventory and deletion-proof pass can pay back through smaller file snapshots, fewer conflicting symbols, fewer compatibility wrappers, and less follow-up cleanup. A useful accounting identity is:

`total tokens = initial implementation + review/gate + follow-up context + rework after regressions`.

The intervention wins when the marginal gate cost is less than the reduction in the last two terms over the maintenance horizon. Phase 1 should estimate each term separately rather than infer savings from LOC alone. Three follow-on tasks is a plausible minimum horizon from the working hypothesis, but it is not an established threshold.

It wastes tokens on disposable prototypes, generated code, short-lived branches, and changes whose added capability is the requirement. It also wastes tokens when the agent repeatedly proves a deletion that tests and static analysis already make obvious. A net-LOC budget can increase output if the model spends turns narrating why it cannot delete, or if it deletes and then re-adds equivalent code to satisfy a superficial diff metric. Token economics must therefore include regression rework and semantic equivalence, not just prompt length or tool-call count.

## Phase-1 experiments

1. **Fixed-task factorial benchmark.** Select 12 small repository tasks: four features, four behavior-preserving refactors, and four removals. Run each with the same model and tools under neutral, concise, and subtractive rubrics. Record raw and rename-aware `+/-` LOC, changed tokens, symbols added/removed, tool calls, test outcomes, and blind human quality ratings. This separates task framing from task mix and tests H-risk/H-pref cheaply.

2. **Deletion-gate ablation.** For the refactor/removal set, compare: no gate; a caller/test inventory; delete-first plus tests; and delete-first plus a net-LOC budget. Keep the initial prompt fixed and cap total turns. Primary outcomes are regression rate and median net LOC; secondary outcomes are extra tokens, time to first deletion, retained dead branches, and reviewer rework. This directly tests whether cheap gates beat a later cleanup pass.

3. **Three-task maintenance replay.** Start each condition from the same module, apply one feature or refactor, then give the agent three realistic follow-up tasks with fresh contexts but the resulting repository. Compare cumulative input/output tokens, files loaded, conflict/rework events, test failures, and final semantic quality between laissez-faire and subtractive conditions. Use symbol- and token-aware diff classification to estimate deferred savings and detect whether early additions compound.
