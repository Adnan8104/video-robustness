# Kitten preparation steps: fixed frames and exact endpoint checks

One previously selected real kitten. This diagnoses the observed original-to-
prepared score change; it does not test population accuracy or learn a biological
mechanism. Freeze this specification and the two exact source-frame lists before
new model inference. The original indices come from the preceding original-file
run. The alternate indices are traced through the exact previous FFmpeg FPS recipe
using unique raw YUV checksums plus plane checksums, then verified against the
parent lossless master. Do not estimate these indices by rounding timestamps.

Use all eight resize × crop × H.264-encoding combinations on each frame set:
16 conditions, 32 scores. Every single-step spatial/encoding comparison holds the
16 native source-frame identities fixed. Sampling comparisons change only which
frames are scored from that same transformed video. Resize = bicubic shortest
side 504, aspect retained; crop = centered square after optional resize. Both off
retain 1280×720. Lossless FFV1 yuv420p provides the non-H.264 reference. Encoding
on means libx264 medium CRF 18 yuv420p, independently from that reference. The
full native 240-frame sequence and 30000/1001 fps remain fixed in the factorial.
Require the lossless identity decode to equal original RGB pixels exactly.

Add a metadata-only 24-fps file with the same 240 images and original explicit
indices (no dropping, duplication or interpolation). The models consume images,
not timestamps; this checks timestamp metadata with the input pixels held fixed.
Ordinary file-based sampling can respond to FPS, which is measured separately
by changing the source-frame list. Direct-frame inference retains native model
preprocessing, 16 frames, native aggregation, CPU/four threads, seed 0 and strict
pretrained weights. Require exact agreement with both published original scores.

Add the exact previously prepared CRF 18 video as an encoding-context bridge.
The factorial's H.264 conditions encode all 240 native-rate frames, whereas the
previous prepared baseline encodes 96 frames at 24 fps. Their codec contexts can
differ. Require the lossless resized/cropped alternate-frame inputs to equal the
parent lossless master's sampled RGB pixels. Require direct scoring of the actual
parent CRF 18 video to reproduce both published prepared scores exactly. This
provides a path from the actual original to the actual prepared endpoint without
assuming that a short clip's encoding is interchangeable with a full clip's.

Report all scores/logits/branch outputs, source indices, decoded RGB hashes and
model-input tensor hashes. Compare single-factor changes conditionally; report
resize/crop difference-of-differences in fused logits on both frame sets without
H.264 encoding. Also show the sequential path: original → changed sample list →
resize → crop → exact parent encoding, keeping all other inputs fixed at each
step. These conditional effects depend on order and setting; do not assign global
percentages or assume additive independent causes. Midpoint 0.5 stays descriptive.

Reload each model and repeat the original reference, largest lossless score on
original frames and the exact prepared endpoint. All outputs must match exactly.
Hash/geometry/frame-count checks and native preprocessing remain mandatory. Stop
if identity pixels or endpoint inputs fail equivalence checks; fix the preparation
rather than interpreting an invalid comparison. Preserve all previous reports.

Even a sufficient edit explains this clip's pipeline response, not why the model
learned it or what all animal videos will do. Resize/crop also change the field of
view or effective scale after native model preprocessing. Encoding results depend
on codec context, and changing sampled frames can interact with those edits.
Source labels are inherited; training overlap is unknown. No new media, weights,
training, threshold tuning or third detector is needed. Only measurements and
charts are published; frame data and transformed media stay local.
