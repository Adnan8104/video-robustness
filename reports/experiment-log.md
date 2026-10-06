# Experiment log: encoding control

Date: 2026-10-02. Detector, checkpoint, four source clips, and centered frame sampling
are unchanged from milestone 1. This follow-up adds one condition, not new source videos.

## Question and design

Was real_01's large score shift caused by any re-encoding, or is it sensitive to the
encoding settings? Add a no-spatial-edit H.264 encode at CRF 18, matching the existing
resize/crop codec, preset, pixel format, and audio removal. Compare each score to
both its original and its control. Retain CRF 35 as the stronger compression case.
This yields 20 cases from four source observations.

## Observations

| real_01 condition | AI-like score | Difference from control |
|---|---:|---:|
| Original | 0.966411 | -0.014717 |
| Encode only, CRF 18 | 0.981128 | 0 |
| Encode only, CRF 35 | 0.023794 | -0.957334 |
| Half-size, CRF 18 | 0.999983 | +0.018855 |
| Center crop, CRF 18 | 0.907487 | -0.073641 |

The model gives high AI-like scores to original real_01 and its CRF 18 control,
despite its source label being real. The stronger encode changes that behavior.
The other real clip stays near zero, and the two Sora clips stay near one.
Scores are model outputs, not calibrated authenticity probabilities.

## Visual inspection

A contact sheet uses frames 90, 129, 168, and 208 (about 3.01, 4.31, 5.62, 6.95 seconds)
from the exact temporal window used by the model. The clip depicts a small rodent
eating inside a wire cage. Scene composition is stable across original, control,
and stronger compression; CRF 35 visibly softens some texture and cage detail.
Looking at these frames does not independently verify the dataset's real label.
The local contact sheet is `real_01_frames.png`; it is excluded from Git and the
shareable archive along with source media.

## Interpretation and limits

The large shift is not reproduced by the CRF 18 encode-only control. That supports
sensitivity to compression settings on this particular clip. It does not identify
which learned features are responsible. A texture/frequency explanation is a
hypothesis, not an established mechanism.

Resize and crop relative to the CRF 18 control are useful paired comparisons, but
encoding changes with content and resolution; subtracting scores is not a clean
causal decomposition. Four clips, one generated source, unknown training overlap,
and inherited source labels remain major limits. Do not tune a threshold on this case.

## Verification and next step

All 20 cases preserve frame counts and frame rates and have the expected dimensions.
Input/output hashes and exact settings are in run.json and scores.csv. Repeat checks
are recorded in validation.json. Milestone 1's reports remain in milestone1/.

Next 3–4 hour session: expand to a fixed small sample (10 real plus 10 generated,
with two generator sources if available), freeze selection before scoring, and run
these same five conditions. Report per-clip score shifts before aggregate claims.
A small compression-quality sweep can follow if similar failures recur. Keep model
training and a UI outside the current scope.
