# Four-clip failure follow-up fixed before new inference

Use four existing clips from the frozen controlled panel: real kitten, first
selected real horse, the AI elephant with the largest preceding animal-cell
WaveRep compression drop, and the sunset people clip with the largest preceding
non-animal-cell WaveRep drop. The kitten is a shared error case; the horse is a
low-score real comparison with the same native 1280×720 size and 29.97 fps.
The elephant and sunset scene span the two content cells. These targets were
selected using previous results; this is a diagnostic study, not fresh validation.

Score both detectors on each unchanged original file and prepared CRF 23 and 28
encodes. Combine with prior prepared CRF 18 and 35 endpoints: four sources ×
five conditions × two models = 40 rows (24 new model scores and up to 16 reused).
Reuse requires identical bytes, recorded temporal indices, model checkpoints,
preprocessing/sampler hashes and package versions; otherwise score the endpoints
again and record that fact. Preserve all previous reports.

Every prepared encode starts independently from the exact same lossless prepared
frames: 4 seconds, 24 fps, 504×504, 96 frames. Use libx264, medium preset, yuv420p,
no audio. Confirm regenerated intermediate hashes match the parent run, or record
that a new intermediate was produced and rescore every endpoint. Record every
command, source/output hash, native logit, auxiliary output and sampled index.
Original files retain their native geometry/FPS; both models sample the same
centered window on each file. The original and prepared windows can use different
physical frames because FPS changes and centering is rounded.

For each model/clip record original → prepared-baseline score change, all adjacent
CRF changes, changes per CRF unit, the largest step, monotonicity (1e-6 tolerance),
every crossing of the fixed 0.5 midpoint, and the first tested below-midpoint CRF
when the CRF 18 score is above the midpoint. The crossing is only bracketed by the
tested levels. Report absolute changes ≥0.10 without averaging opposite signs.

Plot original and compression scores in one four-panel chart. Distinguish the
original → baseline combined-preparation comparison from the fixed-preparation
CRF curve. Also retain logits because saturated scores can hide raw output shifts.
Reload both models to repeat the kitten original and the newly scored midpoint
bracket of each AI curve (or the first tested medium CRF when no bracket exists).

Original → prepared compares the entire recipe: spatial crop/scale, FPS conversion,
window/frame selection and encoding. It cannot isolate which stage caused a
change. A low-scoring horse is not a matched species/texture/motion control. These
four selected cases cannot establish general accuracy or causal animal effects.
The midpoint is descriptive, not calibrated; inherited labels and unknown training
overlap remain limitations. Scores are AI-like outputs, not confidence estimates.
