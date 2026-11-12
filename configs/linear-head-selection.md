# Frozen encoder experiment

Test whether training with stronger compression helps a small classifier
on new recordings. Compare the released WaveRep head with two replacements
that use exactly the same frozen encoder and frame inputs.

- Train on all 18 pairs from the earlier RA-Bench panels that meet the
  existing common preparation requirements. This is development footage,
  including previously scored clips: 18 real, eight LTX and ten Kling v3.
  Keep both members of each pair. Previous scores do not select clips.
- Test on eight new pairs from the same pinned RA-Bench release. Apply the
  [format follow-up selection rules](rabench-format-selection.md), with the
  hash prefix `vidrobust-linear-head-v1:` and both prior RA-Bench manifests
  excluded by original DVIDS recording ID, parent anchor and file hash.
  Select four LTX and four Kling v3 pairs. These recordings were not
  previously scored in the project; pretrained encoder overlap is unknown.
- Use the same four-second 504 × 504 master, 24 fps, 16 positions and
  independent CRF 18/35 encodes as the format follow-up. Capture the
  feature vector entering WaveRep's released final classifier. Verify that
  passing those features into the original layer reproduces its logits.

Average each clip's 16 feature vectors and normalize the result to unit
length. Fit a linear ridge model with labels −1/+1, a free intercept and
mean squared error plus 0.01 times the squared weight norm. This uses
existing NumPy and fits only a small head, with no encoder updates or
hyperparameter search. Light-only training uses CRF 18; both-levels
training uses CRF 18 and 35 of the same recordings. Variants increase
training examples, not the number of independent recordings.

Commit the fitted-head record and hashes before any test inference.
Weights stay in ignored local storage. Use margin zero for both new
heads and the released logit (equivalent to score 0.5). Report both
error directions and ranking for each compression level. Treat the
two-level recipe as an improvement on this panel if it misses fewer
heavily compressed AI clips than **both** alternatives without more
real flags than either, and neither light-condition error count is worse
than light-only training. No test tuning or demo change follows from
this small, same-dataset pilot.
