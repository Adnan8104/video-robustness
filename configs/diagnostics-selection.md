# Diagnostic selection fixed before scoring

Compression sweep: real_01 (known failure), real_08 (new real spatial case), ai_06
(Veo compression case), and ai_03 (Sora spatial case). These are deliberately chosen
from earlier results to investigate mechanisms; they are not new confirmation.
Each has an unencoded original plus CRF 18, 23, 28, 32, and 35 H.264 encodes.
No filters change size or framing during the compression sweep.

Second source: first five eligible filenames in the pinned VLM4D DAVIS directory,
within its first 100 entries, maximum 10 MiB each. No detector score is used in
selection or exclusion. Score original, CRF 18 encode-only, CRF 35 compression,
half-size resize, and centered 80%-per-dimension crop. That adds 25 cases.
The full experiment contains 49 scored cases and nine source clips.

Use unchanged model weights, CPU settings, and centered frame sampling. Save
scores, fused logits, auxiliary branch outputs, hashes, frame counts, dimensions,
FPS, and actual sampled frame indices. Validate timing and geometry and record any
failure explicitly. Auxiliary heads are diagnostic outputs, not causal attributions.

Characterize the curve by its largest adjacent score step and slope per CRF unit.
Report every midpoint crossing and non-monotonicity; do not force a monotone curve.
A midpoint crossing is descriptive, not a calibrated decision rule. The five-point
spacing can bracket a transition but cannot locate it precisely or establish why
it occurs. Stronger CRF means more compression, not a linear perceptual-loss scale.

Plot the score curve and the fused raw output (logit). Separately plot all five
conditions for the new source. Five DAVIS clips provide a source check, not an
estimate of false-positive rate or a content-matched experiment. Both benchmarks
can overlap detector training; neither is a declared training holdout.

Source: https://huggingface.co/datasets/shijiezhou/VLM4D identifies its DAVIS folder
as real third-person footage. It declares MIT for the benchmark; inherited video
source rights can differ. Keep source videos and extracted frames out of Git.
