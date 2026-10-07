# Two-detector comparison fixed before scoring

Retain all 25 previously tested source clips, including both known real failures.
Add ten fresh clips from the pinned ComGenVid revision: five MSVD, three Sora,
and two VEO3. Within the first 100 listing entries per source, take the first
lexicographically eligible MP4s at most 10 MiB, excluding all previous hashes
and MSVD source IDs. No model score informs selection or exclusion.

Use original, encode-only CRF 18, compression CRF 35, half-size resize, and
centered 80% crop for all 35 clips. Also retain CRF 23, 28, and 32 on the four
previous diagnostic sweep clips. This yields 187 paired cases, 374 model scores.
Reuse 137 existing AEGIS results after checking exact input hashes and model
provenance; score AEGIS on the 50 new cases and WaveRep on all 187 cases.

WaveRep G4 is selected because its original release supplies a trained detector
checkpoint. ReStraV's inspected release provides features and training scripts,
but no released classifier head was found. Do not train on these evaluation clips.

Use the same 16 indices in the centered four-second window for both detectors.
Keep AEGIS's native 224-pixel resize and WaveRep's native 504-pixel center crop
with zero padding for small frames and ImageNet normalization. WaveRep's original
demo processes every frame; sparse sampling is an explicit CPU-budget adaptation.
Mean its frame logits, then apply sigmoid, as in the original demo. Retain all
individual frame logits. Batch two frames at a time on CPU, four threads, seed 0.

Compare within-model changes to CRF 18, retaining signs. Use the previous
descriptive absolute-change rule of 0.10, and tabulate score-0.5 midpoint conflicts
with source labels and between models. Midpoints are not calibrated thresholds.
Report all clips and fresh clips separately and retain non-monotone curves.
Do not compare raw score magnitudes as equally calibrated confidence, tune a
threshold, rank general accuracy, or infer shared mechanisms from shared errors.

Weights, videos and source frames stay local. Cite WaveRep's authors and retain
its informational/nonprofit-use license. Validate input hashes, paired indices,
geometry, timing, strict checkpoint loading, aggregation and key repeat scores.
