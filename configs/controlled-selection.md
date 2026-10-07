# Controlled content panel: selection and analysis fixed before scoring

## Question and quotas

Twenty previously unscored source clips: five real animal, five real non-animal,
five generated animal, and five generated non-animal. Test whether high AEGIS
real-animal scores recur under common preparation, and whether WaveRep's
compression response recurs in both content strata. This is a stratified
convenience panel, not a representative or declared training holdout.

Use pinned ComGenVid `c5093999e799c897c977a8699da95ebbc59cc9cb`: MSVD for all
real clips and VEO3 for all generated clips. One source within each label prevents
the animal/non-animal split from also changing source or generator. Sora is omitted
because only seven of its 1,700 metadata rows meet the native-size/timing criteria;
mixing it in would make this panel difficult to balance without upscaling.

## Eligibility and content annotation

Inspect the first 1,000 pinned directory entries per source, ordered by filename.
Native shortest side at least 504 pixels, landscape width/height at least 1.4,
duration at least four seconds, native FPS at least 24, and file size at most
30 MiB. Confirm actual metadata after downloading. Exclude all hashes and MSVD
source IDs used in the earlier 35-source experiment; retain at most one new segment
per MSVD source ID. Record every downloaded candidate, eligibility decision,
content annotation and selection result in an audit. No detector scores are read.

Inspect three cropped frames near the beginning, middle and end of the centered
four-second interval, then inspect the sampled 16 frames of each selected clip.
Animal: a recognizable non-human living animal is a prominent subject of the
retained crop. Non-animal: no salient non-human animal is visible. Exclude ambiguous
cases (including tiny/background-only animals, animal likenesses or uncertain
rendered/animated style). Depicted AI animals qualify when recognizable and in
photographic style. Humans alone are non-animal for this operational category.
Manual annotation is fallible; preserve notes and crop-check results, not source
frames. Take the first five qualifying unique sources per cell without score-based
replacements. Freeze the exact final manifest before any model inference.

## Common preparation and paired conditions

Center a four-second interval, snapping its start down to the nearest source frame
using the decoded frame count and FPS (less than one native frame from the nominal
center). Reset timestamps before FPS conversion and after preparation, convert to 24 fps, downscale the shortest side to
504 with bicubic interpolation, center-crop to 504×504, set square pixels, remove
audio, and retain exactly 96 frames. No selected source is upscaled. Encode the
same prepared frames independently with H.264, medium preset, yuv420p, at CRF 18
(baseline) and CRF 35 (compression). Both encodes start from the same lossless
prepared intermediate, so compression is not applied to an already compressed
baseline. Intermediate files, source media and inspections remain local.

Run AEGIS and sparse-frame WaveRep with unchanged pretrained weights and native
model preprocessing. Both sample the same 16 indices across the 96 frames. CPU,
four threads, seed 0, deterministic algorithms; WaveRep batches two frames.
Twenty sources × two conditions × two models = 80 scores.

## Fixed descriptive analysis

For each model and each five-clip cell report every baseline/compressed score,
the signed compression-minus-baseline change, median signed change, median
absolute change, absolute changes at least 0.10, and every score-0.5 midpoint
crossing. Record source-label conflicts before and after compression. The midpoint
is descriptive, not a calibrated threshold; do not tune it on this panel.
Compare real-animal and real-non-animal cells without claiming a learned mechanism,
a significance test, an accuracy ranking or a low false-positive rate from n=5.

Matching output size, duration, FPS and encoding does not equalize original camera
quality, native compression, motion, species, backgrounds, provenance, source
resolution or training overlap. Selection can emphasize large central subjects.
This panel tests recurrence under a common preparation recipe, not a causal
animal/texture effect or an estimate for arbitrary social-media videos.

Validate all source and prepared decodes, 504×504/24fps/96-frame geometry, paired
sampling, checksums, complete cell coverage and native aggregation. Repeat key
scores with freshly loaded models. Keep all previous experiments unchanged.
