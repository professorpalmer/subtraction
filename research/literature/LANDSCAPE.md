# Literature landscape

Reconnaissance run on 2026-08-01 across arXiv, Zenodo, and GitHub. This is a
targeted first pass, not a systematic review. The central question was whether
someone has already studied the specific pattern: agentic coding systems
producing additive, verbose, or redundant patches when a smaller or
subtractive change would satisfy the task.

## The closest match

### More is More: Addition Bias in Large Language Models

**arXiv:** [2409.02569](https://arxiv.org/abs/2409.02569)<br>
**Authors:** Luca Santagata and Cristiano De Nobili

This is the direct conceptual predecessor. It tests GPT-3.5 Turbo, Claude 3.5
Sonnet, Mistral, Mathstral, and Llama models on controlled non-coding tasks
where either adding or removing an element can solve the problem. The paper
reports a strong additive preference across all tested models, including
99.5% additive responses for one GPT-3.5 palindrome condition and 100%
additive responses for Claude 3.5 on the reported palindrome tasks.

What it gives us:

- Evidence that the phenomenon is not unique to coding agents.
- A task-level way to measure addition preference without conflating it with
  code quality.
- A plausible inherited-human-bias framing.

What it does not give us:

- No repository navigation, edit tools, tests, or multi-turn agent trajectory.
- No causal separation of task mix, risk, tool affordances, and training.
- No direct token-cost or code-maintenance analysis.

This means the subtraction project is not claiming the existence of addition
bias for the first time. The open question is whether that general bias becomes
an especially costly policy in agentic software maintenance, and why.

## Direct coding-agent research

### TRIM: Reducing AI-Generated CodeSlop via Agent Trajectory Minimization

**arXiv:** [2607.18161](https://arxiv.org/abs/2607.18161)

This is the closest match to the coding-specific problem. TRIM defines
**CodeSlop** behaviorally as removable functional redundancy: edits that can
be removed while preserving the successful agent patch. Its key claim is
causal at the process level: agents retain speculative edits, abandoned
hypotheses, and temporary changes from their repair trajectory after tests
pass. It reports 17.9%–32.9% CodeSlop reduction across agentic scaffolds with
negligible correctness regression and roughly half the validation cost of
Delta Debugging baselines.

Implication for us: the final diff is not enough. We need to capture the
trajectory and distinguish necessary edits from search residue. TRIM is an
obvious Phase 2 comparator, but it studies post-hoc patch minimization more
than the initial decision to add instead of delete.

### SlopCodeBench: Benchmarking How Coding Agents Degrade Over Long-Horizon
Iterative Tasks

**arXiv:** [2603.24755](https://arxiv.org/abs/2603.24755)<br>
**Runner:** [SprocketLab/slop-code-bench](https://github.com/SprocketLab/slop-code-bench)<br>
**Problems:** [gabeorlanski/scb-problems](https://github.com/gabeorlanski/scb-problems)<br>
**Checker:** [gabeorlanski/scb-check](https://github.com/gabeorlanski/scb-check)<br>
**Zenodo DOI:** [10.5281/zenodo.19257129](https://doi.org/10.5281/zenodo.19257129)

SlopCodeBench evaluates 15 coding agents over 36 problems and 196
checkpoints, where each new requirement extends the agent's own prior code.
It reports structural erosion in 77% of trajectories and verbosity growth in
75.5%; agent code is reported as 2.3x more verbose and 2.0x more eroded than
the human repository comparison. Explicit quality guidance reduces initial
verbosity and erosion by up to a third, but does not stop degradation across
later checkpoints. The guidance costs 12.1% more per checkpoint on average in
the reported study.

Implication for us: a single successful patch is the wrong unit of analysis.
The deferred-cost hypothesis should use repeated maintenance checkpoints, and
prompt guidance must be evaluated for both initial improvement and trajectory
stability.

## Adjacent empirical work

### Debt Behind the AI Boom

**arXiv:** [2603.28592](https://arxiv.org/abs/2603.28592)<br>
**Replication package:** [yueyueL/tech-debt-ai-coding](https://github.com/yueyueL/tech-debt-ai-coding)

This study analyzes 302.6k verified AI-authored commits across 6,299 GitHub
repositories and identifies 484,366 issues. Code smells account for 89.3% of
the issue set; 22.7% of tracked AI-introduced issues survive at the latest
revision in the version reported on arXiv. The net effect is mixed: AI
commits fix slightly more code smells than they introduce, while runtime and
security issues are more often introduced than fixed.

Implication for us: “more lines” is not a sufficient outcome measure. A
subtractive patch can be bad, and an additive patch can fix a smell. We need
semantic task success, regressions, maintainability, and token use alongside
raw `+`/`-` counts.

### Agentic Refactoring: An Empirical Study of AI Coding Agents

**arXiv:** [2511.04824](https://arxiv.org/abs/2511.04824)<br>
**Replication package:** [Mont9165/Agent_Refactoring_Analysis](https://github.com/Mont9165/Agent_Refactoring_Analysis)

Across 15,451 refactoring instances in Java projects, refactoring appears in
26.1% of agentic commits. The observed work is dominated by low-level
consistency edits such as type changes and renames. Reported motivations are
maintainability (52.5%) and readability (28.1%). Structural metrics improve
slightly for some refactorings, including a reported median class-LOC change
of -15.25, but the study finds no overall reduction in known design and
implementation smells.

Implication for us: agents do subtract in some real-world maintenance work,
but their subtraction is mostly local and syntactic. “Agent refactoring” is
not equivalent to architectural simplification.

### Needle in the Repo (NITR)

**arXiv:** [2603.27745](https://arxiv.org/abs/2603.27745)<br>
**Benchmark:** [ucr-riple/NITR](https://github.com/ucr-riple/NITR)

NITR tests maintainability preservation with hidden structural oracles in 21
repository probes. Across 23 configurations, the average solved rate is
36.2%, the best reported configuration reaches 57.1%, and 13.3% of outcomes
pass functional tests while failing the structural oracle. Dependency control
and responsibility decomposition are especially difficult.

Implication for us: tests alone are not a sufficient subtraction gate. A
useful benchmark needs structural checks that can catch duplication,
abstraction bypasses, and change amplification even when behavior passes.

## Benchmarks and datasets on Zenodo

### SWE-Refactor

**Zenodo:** [17655592](https://zenodo.org/records/17655592)

SWE-Refactor contains 1,099 verified pure refactorings from 18 Java projects.
Instances are checked with compilation, tests, and automated refactoring
detection. It is a strong source for behavior-preserving refactor fixtures,
but it does not target addition bias or agent trajectories.

### MaRV

**Zenodo:** [14450098](https://zenodo.org/records/14450098)

MaRV contains 693 manually evaluated before/after code pairs from 126 Java
repositories, covering four refactoring types. It can support human-quality
comparisons and annotation design, but it is not an agent-specific
subtraction study.

### Greening AI-Assisted Code Generation by Reducing Babbling

**Zenodo:** [19231259](https://zenodo.org/records/19231259)

This artifact studies excessive code-generation output (“babbling”) and
introduces Babbling Suppression: execute intermediate generations and stop
when tests pass. It is primarily code completion rather than repository
maintenance, but it directly supports the token-cost question. Early
termination and patch minimization should be measured separately: one reduces
generation tokens, the other reduces the code that future turns must read.

## Intervention and reduction research

### ReGAL: Refactoring Programs to Discover Generalizable Abstractions

**arXiv:** [2401.16467](https://arxiv.org/abs/2401.16467)

ReGAL uses LLM-generated programs, execution-based equivalence checks, and
pruning of overly specific or incorrect abstractions. It supports a
programmatic, verifier-backed alternative to asking an LLM to rewrite code
directly.

### Don't Transform the Code, Code the Transforms

**arXiv:** [2410.08806](https://arxiv.org/abs/2410.08806)

This work asks the LLM to synthesize an inspectable transformation program
from examples instead of directly rewriting the target code. The resulting
transform is easier to inspect and execute, and the transformation runtime is
much cheaper than repeated direct LLM rewriting.

### Semantic-aware and Self-improving Program Reduction via Agentic LLMs

**arXiv:** [2607.03766](https://arxiv.org/abs/2607.03766)

PROJ uses a reducer agent to propose semantic-preserving reductions and a
reflector to distill successful reductions into deterministic reusable
strategies. This is adjacent to subtraction because it turns successful
deletions into executable, reusable rules rather than paying for the same
reasoning on every future task.

### Reducing Cost of LLM Agents with Trajectory Reduction

**arXiv:** [2509.23586](https://arxiv.org/abs/2509.23586)

AgentDiet reduces redundant trajectory context with a bounded reflection
window and skips reduction below a token threshold. It is not source-code
subtraction, but it offers a useful cost-design pattern: only pay for
reduction when the expected future context savings exceed the reduction cost.

## GitHub practitioner tools

These are useful implementations and taxonomies, not causal evidence. Their
star counts and documentation are time-sensitive; they should not be treated
as validated research results.

- [parkktech/shrinkage](https://github.com/parkktech/shrinkage) — reuse-first
  gate, evidence-backed atomic deletions, and green-test/revert safety model.
- [jetmirrama/debloatify](https://github.com/jetmirrama/debloatify) — reviewer
  taxonomy for factory-for-one, defensive-null theatre, scaffolding,
  comment-slop, dead files, and related patterns.
- [blakecyze/kanso](https://github.com/blakecyze/kanso) — audit and
  behavior-preserving refactor skills with manual approval and verification.
- [LeonardNJU/code-humanizer](https://github.com/LeonardNJU/code-humanizer) —
  guard mode for duplicated helpers, broad exception handling, speculative
  abstractions, and other AI-code patterns; report-only when there is no
  test oracle.
- [JordanGunn/agent-slop-lint](https://github.com/JordanGunn/agent-slop-lint) —
  static structural, information-theoretic, and lexical metrics for agent-era
  codebases.
- [giuliastro/HarnessTrim](https://github.com/giuliastro/HarnessTrim) —
  cross-harness reduction of noisy tool output, context, and trajectory costs;
  relevant to token economics rather than source-code subtraction.

## What appears unclaimed

This first pass found a real research neighborhood, including one direct
general addition-bias paper and several very recent coding-agent papers. It
did not find a single study that combines all of the following:

1. The same repository tasks across multiple agent models.
2. A controlled decomposition of task wording, risk framing, tool interface,
   and review gate.
3. Trajectory-aware classification of necessary edits versus speculative
   residue.
4. Raw, rename-aware, and semantic `+`/`-` measurement.
5. Immediate intervention cost plus deferred context/rework savings.

That combination is the useful research gap for `subtraction`. The project
should cite and reuse the metrics and artifacts above rather than present
“LLMs add more” as an unstudied observation.

## Immediate changes to our plan

1. Add `More is More` as the non-code baseline for A.
2. Use SlopCodeBench and TRIM terminology carefully: distinguish verbosity,
   structural erosion, CodeSlop, and raw positive net LOC.
3. Treat semantic diff and trajectory capture as first-class Phase 1 data.
4. Include a quality-guidance cost arm, because SlopCodeBench reports a
   measurable cost increase even when initial quality improves.
5. Add at least one SWE-Refactor-style pure refactoring fixture and one NITR-
   style structural oracle.
6. Compare prompt/gate subtraction with post-hoc TRIM-like minimization and
   early-stop babbling suppression.
