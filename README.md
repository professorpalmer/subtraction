# Subtraction

Research on why agentic LLMs prefer **adding** code over **subtracting** it — and what (if anything) can shift that bias without killing usefulness.

## Thesis (working)

Pre-LLM elite craft often meant *leaning out*: fewer abstractions, tighter control flow, deleting dead paths. LLM-era agentic coding often produces the opposite shape of diff: large `+`, tiny `-`, even on "refactors."

Two competing explanations (not mutually exclusive):

1. **Demand / task-mix bias** — We ask models to ship features faster than we ever did by hand, so the corpus of successful agent traces is addition-heavy. The bias looks architectural because the workload changed.
2. **Model / objective bias** — Preference training, tool loops, and risk asymmetry make *additive patches* the path of least resistance even when subtraction would be better.

This repo stages research to separate those, then pressure-test interventions and token-cost implications.

## Research questions

### A. Why `+` over `-`?

- Is the bias mostly **prompt/task distribution** (feature factory era)?
- Is it a **genuine training/architecture/incentive fault** (RLHF helpfulness, completion bias, local patch tools, fear of breakage)?
- How much is **measurement illusion** (refactors that move/copy look like adds)?

### B. Can we improve the mechanism?

- Prompt / rubric / gate interventions (net-negative budgets, delete-first passes, "prove deletion" checklists)
- Training / reward / routing interventions
- Is correction **expensive** at inference time?
- If we bend the curve even a little, do we **save tokens** later via smaller contexts and less rework?

## Staging plan

| Phase | Goal | Artifacts |
|-------|------|-----------|
| **0 — Frame** | Multi-model synthesis of causes + intervention space | `research/phase-0/` |
| **1 — Measure** | Define metrics; sample real agent diffs for `+/−` shape | `research/phase-1/` |
| **2 — Intervene** | Controlled prompts/gates on fixed tasks; compare net LOC & quality | `research/phase-2/` |
| **3 — Cost** | Model token/$ impact of leaner diffs over multi-turn work | `research/phase-3/` |

Phase 0 starts with three Cursor-adapter models writing independent memos:

- GPT-5.6 Luna with maximum effort (`gpt-5.6-luna`)
- Grok 4.5 (`grok-4.5`)
- Composer 2.5 (`composer-2.5`)

Then we reconcile into a single frame doc before measuring.

## Repo layout

```
research/
  QUESTIONS.md          # frozen research questions
  HYPOTHESES.md         # falsifiable claims
  literature/           # prior work, datasets, and open-source tools
  phase-0/              # multi-model framing memos + synthesis
  phase-1/              # measurement protocol + samples
  phase-2/              # intervention experiments
  phase-3/              # cost models
notes/                  # scratch, session notes
```

## Status

- [x] Repo created
- [x] Phase 0 multi-model memos
- [x] Prior-work reconnaissance
- [x] Phase 0 synthesis
- [x] Phase 1 measurement protocol and offline benchmark
- [x] Phase 1 three-model live pilot
- [x] Phase 1 cleanup-task replication
