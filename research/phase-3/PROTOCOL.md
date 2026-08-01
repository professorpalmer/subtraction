# Phase 3 Protocol

1. Read one or more Phase 2 JSON artifacts. Each may be a single result
   object, a list of result objects, or an object with a `results` list.
   Every loaded record must be a Phase 2 receipt with object-shaped `cell` and
   `actual` fields. Phase 2 summary artifacts such as `{protocol, groups}` are
   rejected rather than silently analyzed as empty input.
2. Preserve the receipt's adapter metadata. Include only completed adapter
   records in comparative analysis. Treat absent status as unknown, not
   success, unless the record explicitly declares the pre-status schema.
3. Group included records by `task_id`, `model`, `reasoning_effort` when
   present, and `arm`. Report sums, available-value means, and observed-value
   counts separately for input, output, and total tokens.
4. Compare each treatment arm against `neutral_control` only when both arms
   exist with equal included repetition counts, aligned repetition IDs when IDs
   are present, and equal non-null coverage for each token field. The default
   two-arm API still treats `subtractive_rubric` as the classic treatment and
   preserves historical `subtractive_*` comparison fields for that contrast.
   Multi-arm receipts emit one comparison per non-neutral arm. Unmatched groups
   report a precise reason and omit token deltas. Matched groups report token
   totals, means, deltas, and relative changes; missing values remain null.
5. Apply caller-supplied per-million-token rates only where both a rate and the
   corresponding reported usage exist. A lone scalar rate does not populate
   input, output, and total costs. Object pricing may price input and output
   independently; total cost stays null unless a total rate is explicitly
   supplied.

No token field is derived from another token field. No dollar amount is
estimated from a billing plan. The scenario calculator is a hypothetical
projection and must not be mixed with observed receipt summaries.
