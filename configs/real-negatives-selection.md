# Extra real footage comparison

Add all 16 real recordings from the original trained-head test and its
stricter-cutoff follow-up. They are now development material. This includes
the four real clips that the original trained head flagged at CRF 35,
without selecting the additions by their scores. Use both CRF 18 and 35
for every added clip. The original 18 real and 18 AI training clips stay
in the fit. No synthetic footage is added.

Keep the WaveRep encoder, features, 16-frame sampling, ridge penalty
(0.01) and decision margin (zero) fixed. Give each class half the fit
loss so adding real clips doesn't make errors on real footage inherently
more costly than errors on AI footage. Within each class, each encode
receives equal weight. Verify on the original balanced set that the same
objective reproduces the original head. The added training footage
comes from distinct recordings, but the dataset and its two generators
are the same.

Select eight new scene pairs from the pinned RA-Bench release using the
[format selection rules](rabench-format-selection.md), increasing the
metadata shortlist to 48 per slot and using `vidrobust-real-negatives-v1:`
as the hash prefix. Keep four LTX and four Kling v3 pairs. Exclude all
earlier RA-Bench panels by DVIDS ID, parent anchor and exact file hash.
Freeze the input manifests and training policy in Git before extracting
features. Commit the fitted-head record before scoring the test set.

Compare released WaveRep, the previous trained head and the new head on
the same test encodes. At CRF 35, success means strictly fewer real
flags than the previous trained head, no additional AI misses, and
at least one AI catch. Report CRF 18 results and ordering independently.
If the previous head has no real flags here, this pilot cannot
demonstrate a reduction. Don't tune on these clips or change the demo.
