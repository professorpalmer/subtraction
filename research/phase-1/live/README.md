# Phase 1 live pilot

This directory contains a six-run Cursor-adapter pilot on
`refactor-shared-strip`. Each run started from the same fixture source and
used a separate candidate file. The pilot crossed three models with two arms:
`neutral_control` and `subtractive_rubric`.

The measured records are in `pilot-2026-08-01.json`. Their token receipts come
from the corresponding Puppetmaster job receipts, while patch metrics and
behavior checks come from `measure_candidate_patch`. `turns` and `tool_calls`
are null because the receipt did not expose those counts; they must not be
inferred from the job status.

This is directional evidence, not a conclusion. It has one task, one
repetition per model/arm, shared repository context, and a narrow behavior
oracle. The useful next replication is a larger fixture-balanced run with
independent task seeds, structural review, and explicit capture of every
trajectory event.
