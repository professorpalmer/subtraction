# Phase 3 — Token and Cost Analysis

Phase 3 reports token usage from Phase 2 receipts; it does not manufacture
usage. Input, output, and total tokens remain independently nullable. In
particular, `total_tokens` is never inferred by adding input and output.

Only records with `actual.adapter_status == "completed"` enter summaries and
matched-arm comparisons by default. Missing status is excluded too, unless the
artifact explicitly identifies the pre-status `phase-2-controlled-ablation-v0`
schema (or `adapter_status_schema: "pre-adapter-status"`). The report retains
the excluded count and status breakdown.

Costs are optional and usage-first. A caller may provide a JSON pricing map
such as:

```json
{"gpt-5.6-luna": {"input": 2.0, "output": 8.0, "total": 4.0}}
```

Rates are dollars per million tokens. Missing rates or missing usage produce
`null`, never zero. A lone scalar entry in the pricing map does not apply to
input, output, and total simultaneously; use an object with explicit field
rates when independent costs are needed. Total cost remains null unless a total
rate is explicitly supplied. This keeps plan-billed Cursor runs token-visible
while remaining dollar-unknown without an explicit rate.

The `scenario` command is a transparent hypothetical multi-turn calculation.
It assumes a fixed baseline input-token count per future turn and applies one
constant reduction fraction to every future turn. Its result is labeled
`observed_data: false`; it is not a measurement of Phase 2.

The generated `phase2-token-analysis.json` combines the successful refactor and
cleanup pilot receipts. Those receipts establish reported usage for those
runs, but their one-repetition, task-specific design does not prove that the
subtractive rubric caused token savings. Causal conclusions require a repeated
and appropriately powered comparison.

## Usage

```bash
python -m research.phase_3.cli analyze result-a.json result-b.json \
  --output phase2-token-analysis.json
python -m research.phase_3.cli analyze results.json --pricing pricing.json \
  --output analysis.json
python -m research.phase_3.cli scenario \
  --baseline-input-tokens-per-turn 100000 \
  --reduction-fraction 0.2 \
  --future-turn-count 12 \
  --output scenario.json
```
