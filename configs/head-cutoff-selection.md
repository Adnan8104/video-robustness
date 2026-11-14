# Check a stricter trained-head cutoff

The previous two-level head caught four of eight compressed generated
clips but flagged three of eight real ones. Test whether a stricter
cutoff makes it useful without changing or retraining the head.

Use the previous [test margins](../reports/linear-head/scores.csv) as
development data for this follow-up. They no longer count as untouched
data for the new rule. Compare nonnegative observed boundaries, zero,
and a threshold above every observed margin. Flag at or above the cutoff.
Allow at most one development real flag at **each** compression level.
Among eligible rules, catch the most CRF 35 generated clips, then the
most CRF 18 generated clips, then minimize total real flags, then prefer
the higher cutoff. Use one cutoff for both encodes and commit it before
scoring the fresh test set.

Use eight fresh pairs from the pinned RA-Bench release and the
[format selection rules](rabench-format-selection.md). Use the prefix
`vidrobust-head-cutoff-v1:`, and exclude all earlier RA-Bench, format,
and linear-head recordings by DVIDS ID, parent anchor and file hashes.
Keep four LTX and four Kling v3 pairs. A single 504 × 504, 24 fps, 96-frame
lossless master per clip supplies independent CRF 18 and 35 encodes.
Reuse the fixed 16-frame positions and frozen encoder. Compare released
WaveRep and the trained head at zero and at the locked cutoff on the same
clips. The original fitted weights and their environment are hash checked.

Treat the stricter rule as useful on this pilot if it has at most one
real flag at each level, reduces the total real flags from trained-head
zero, and catches at least two CRF 35 generated clips and no fewer than
released WaveRep. Report both error counts at both levels even if the rule
misses that target. The point is to test an operating tradeoff, not to
call margins probabilities. No fit, cutoff search, or demo change on the
fresh test data.
