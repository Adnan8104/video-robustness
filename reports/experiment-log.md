# Experiment log: fixed 20-clip expansion

Date: 2026-10-06. Detector, checkpoint, centered 16-frame sampling, and all five
conditions remain unchanged. Sample policy was frozen in commit 001190d; the
0.10 descriptive score-shift rule was recorded in 30bf3e8 before expanded scoring.
The previous four-clip log and results remain in milestone2/.

## Design

10 real MSVD clips, five Sora clips, and five VEO3 clips from the pinned ComGenVid
revision. Select first eligible filenames within the first 100 listed files per
source, cap each file at 10 MiB, and keep one real segment per source video ID.
All source hashes are unique. Selection does not inspect detector scores.

The original four discovery clips remain in the panel. The 16 new clips are
reported separately to avoid presenting the known failure as new confirmation.
Original, CRF 18 encode-only control, CRF 35 compression, half-size resize, and
center crop produce 100 cases from 20 source observations.

## Findings

The original real_01 compression shift reproduced: control 0.981128, compressed
0.023794, signed difference −0.957334. None of the 16 new clips shows a shift of
at least 0.10, whether measuring the encode control against original or the three
transformed variants against control.

| New case | Condition | Control score | Variant score | Signed change |
|---|---|---:|---:|---:|
| real_08 (MSVD) | Resize | 0.003006 | 0.075086 | +0.072080 |
| ai_06 (VEO3) | Compression | 0.999892 | 0.945282 | −0.054609 |
| ai_03 (Sora) | Crop | 0.946256 | 0.999681 | +0.053425 |

The expanded panel does not reproduce the original dramatic compression failure
on new cases. It does show smaller, condition-dependent score changes. Per-source
medians and sizable-shift counts are in summary.md and summary.json.

## Interpretation and limits

This is a negative replication of a large score shift within a small convenience
sample. It does not establish general robustness. Most model scores saturate near
zero or one; small probability-like changes can conceal larger logit changes.
The file-size cap and filename ordering can bias content, duration, and original
encoding. All real footage comes from MSVD, only five clips represent each
generator, source labels are inherited, and training overlap is unknown.
Adding Veo is generator coverage, not proof of unseen-generator generalization.

Spatial edits interact with encoding, so control-relative subtraction is not a
clean causal decomposition. The 0.10 rule is a descriptive score-change cutoff;
it is not calibrated confidence, a detection threshold, or a significance test.
Do not turn these results into an accuracy or low-FPR claim.

## Verification

All 20 source clips pass SHA-256 and full decoding checks. All 100 cases preserve
frame counts and FPS and match intended geometry. All 20 prior case scores and
video hashes are unchanged. Repeat checks for the leading new real and Veo cases
are recorded in validation.json. Tests cover provenance failures, repeatable
sampling, signed-versus-absolute summaries, and exclusion of discovery cases.

## Next small experiment

Use a second real-video source with clear labels and source terms; pair or match
content and resolution where possible. Keep this detector and settings fixed.
Test whether the rodent-cage failure follows similar texture/content or original
encoding. A short CRF sweep on the original failure and selected controls can
then test the compression-response curve. Keep model training and a UI out of
scope until these measurements support a clearer question.
