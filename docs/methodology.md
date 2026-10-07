# Methodology

## Technical choices

| Choice | Reason and tradeoff |
|---|---|
| AEGIS pretrained checkpoint | Public downloadable weights and readable inference code; no training budget. It is a DINOv2-based multi-branch model, so lightweight here means a small experiment, not a tiny model. |
| Twenty clips (10 MSVD real, 5 Sora, 5 VEO3) | Expand the smoke test with two generators and 16 new clips. Freeze filename-based selection before scoring, cap files at 10 MiB, and retain one MSVD segment per source ID. Labels come from the benchmark; this is a convenience sample, not representative evaluation. |
| Pinned upstream code + strict checkpoint loading | Avoid changing architecture or accidentally measuring random weights. Full backbone is in the checkpoint, so the author's extra local cache is unnecessary. |
| CPU, four threads | Works on this Apple Silicon Mac and is easy to reproduce. CUDA/MPS optimization can wait until data volume justifies it. |
| 16 frames in centered four-second window | Retains upstream inference window length and frame count, removes random window selection so variants use the same temporal region. |
| Upstream RGB, 224×224, ImageNet normalization | Keeps the input convention expected by the detector. Smaller resized inputs are expanded to 224 during inference, which tests lost detail. |
| OpenCV decoding | Upstream supported fallback, avoiding Decord's macOS installation friction. Decoder differences can still affect numerical scores. |
| H.264 compression at CRF 35 | Visible lossy compression with a single interpretable setting; larger CRF means lower quality. |
| Half-width/half-height bicubic resize; centered 80% crop per dimension | Simple spatial edits with even dimensions required by H.264. Crop keeps 64% of the area. Neither changes timing intentionally. |
| CRF 18 encoding for resize/crop | Keeps extra encoding loss modest, but the measured effect still includes re-encoding. The encode-only control uses these same settings without a spatial filter; compare spatial variants to that control. Audio is removed; detector is visual-only. |
| Permit spatial variants below upstream 128px quality threshold | A robustness study must score degraded inputs rather than reject them silently. Still check duration, frame count, and readable metadata. |
| CSV + JSON + Markdown | Easy to inspect in interviews and script later; no dashboard, database, or framework overhead. |
| Small `Detector.score(path)` boundary | A future VidAudit adapter can provide scores without rewriting transformation and report logic. This is an extension point, not a claim of current VidAudit compatibility. |
| Dependency lock and input/output hashes | Preserve environment and provenance. Deterministic CPU settings help, but byte-identical results across hardware/decoders are not guaranteed. |

## What this proves

A functioning pretrained inference pipeline and paired score comparison. Twenty source clips
are twenty observations, not one hundred independent observations after augmentation. The original four discovery clips are also reported separately from the 16 new clips. Do not tune
thresholds on these clips, report AUC/low-FPR results, or claim the detector is reliable.
Training-set overlap is unknown. Real and fake sources differ in content and encoding, so
between-class score differences can reflect dataset artifacts. An output near zero or one
can be confidently wrong. Keep such failures in the report.


Run artifacts record exact model and dataset revisions, input/output hashes, environment versions, and transformation commands. Paths in those commands are relative to the repository root.

## Expanded-sample analysis

[Selection policy](../configs/selection.md) specifies source quotas, file-size cap,
deduplication, retained discovery cases, and the descriptive 0.10 score-change rule.
The rule counts absolute differences; opposite signed changes must not cancel.
Summary tables separate all clips and new clips, and give per-source medians. No
classification threshold is tuned. Small shifts in saturated outputs can conceal
changes in unreported model logits, so they do not establish trustworthy detection.

Prior four-clip results are preserved in reports/milestone1/ and reports/milestone2/.
The expanded sample stays inside the same dataset, so the second generator expands
generator coverage but does not establish cross-dataset generalization.

## Compression sweep and second-source check

The [frozen diagnostic policy](../configs/diagnostics-selection.md) adds 49 cases:
four previously observed clips at CRF 18, 23, 28, 32, and 35 plus their originals,
and five new DAVIS clips at the usual five conditions. These add five source
observations, not 49 independent videos. DAVIS selection uses filenames and size,
not model scores. The source is pinned separately through VLM4D; benchmark labels
and any prior encoding are inherited, and training overlap remains unknown.

The five CRF levels locate broad changes while keeping CPU work small. CRF is not
a linear scale of perceptual degradation. Report signed adjacent steps, steps per
CRF unit, non-monotonicity, and all crossings of the descriptive 0.5 midpoint.
The grid cannot locate the precise transition or establish its mechanism.

Plot fused raw outputs alongside scores because the sigmoid saturates near zero
and one. Auxiliary heads are stored for inspection, but they do not establish why
the fused model responds. Matplotlib adds one locked dependency and exports
portable PNG/SVG charts without a dashboard. Geometry, timing, paired sampling,
and hashes are checked; source frames stay local. Five key cases were rescored
with a freshly loaded model, and 12 overlapping cases match prior scores and
encoded hashes. See the [report](../reports/diagnostics/report.md) and its validation.

## Second detector and fresh panel

The [frozen comparison](../configs/two-detectors-selection.md) retains 25 previous
source clips and adds ten fresh filename-selected clips (five MSVD, three Sora,
two VEO3). Thirty-five sources produce 187 paired conditions, including the
previous four sweeps. Existing AEGIS scores are reused only on identical input
bytes with verified checkpoint provenance. Its legacy root CSV lacks explicit
indices; those are reconstructed using the original run's documented centered
sampler and checked against WaveRep. The diagnostic CSV records its indices directly.

WaveRep G4 supplies a full trained detector checkpoint. The inspected ReStraV
release supplies feature extraction and training code, but no pretrained
classifier head was found; feature extraction alone would not be a second trained
detector. WaveRep fits the locked torch/timm environment without extra packages.
Its original informational/nonprofit license and authors' attribution are retained.

Use native 504-pixel torchvision center crop (zero padding for smaller frames),
ImageNet normalization, and sigmoid of mean frame logits. The checkpoint contains
the backbone, so load it strictly without an additional backbone download.
Process two frames at a time to limit memory. This adapter samples the same 16
frames as AEGIS instead of scoring every frame as WaveRep's demo does; it is a
sparse-frame adaptation, not a reproduction of published benchmark results.

Different spatial preprocessing is part of each model's input pipeline. AEGIS
rescales to 224; WaveRep preserves native pixel scale and crops/pads. For WaveRep,
half-size inputs may increase padded area. A shared temporal window controls one
source of variation without pretending the full input pipelines are identical.
Strict decoding rejects missing selected frames rather than silently filling them.

Summaries separate previous and fresh clips, count absolute shifts of at least
0.10 relative to encoding control, and report fixed-midpoint label conflicts and
model disagreements. These descriptive counts do not rank deployable accuracy.
Training overlap, sample selection, source differences and lack of calibration
remain limits. No training or threshold tuning is performed. Model disagreement
narrows the observation to particular pipelines; it does not reveal a learned cause.
Both detectors use DINOv2 backbones, so this comparison does not span independent
backbone families even though their trained heads and input pipelines differ.

Extraction saves an ignored resumable cache keyed by model, adapter, environment,
configuration and individual input hashes. The final CSV retains every WaveRep
frame logit. Reports include only numerical outputs and measurement plots.

## Balanced content and common preparation

The [controlled policy](../configs/controlled-selection.md) and
[reviewed manifest](../configs/controlled.json) add 20 fresh sources with five per
real/AI × animal/non-animal cell. MSVD and Veo hold source constant within each
label. Native shortest sides must be at least 504, durations at least four seconds,
FPS at least 24, landscape aspect at least 1.4, and files no more than 30 MiB.
Previous hashes and MSVD source IDs are excluded. Manual inspection proceeds in
pinned filename order without detector scores; every downloaded candidate has an
[audit entry](../configs/controlled-candidate-audit.json). Review all 16 sampled
frames of each selected prepared crop before committing the exact manifest.

Downscale with bicubic interpolation, center-crop to 504×504, convert to 24 fps,
and retain 96 frames. Snap the centered interval start down to a native frame,
within one frame of the nominal center, then reset output timestamps. This avoids
a fractional seek dropping a boundary frame on four-second sources. The lossless
FFV1 AVI intermediate stores exactly those prepared pixels; both H.264 encodes
start from it independently (medium preset, yuv420p, CRF 18 and 35, no audio).
Check metadata and sequential decode counts for sources, intermediates and encodes.
Reset timestamps remove gaps that can inflate reported frame counts; AVI provides
an explicit frame index for validation.

AEGIS keeps its native 224-pixel preprocessing; WaveRep receives its native
504-pixel crop without padding. Their temporal indices and encoded input hashes
must match. This controls prepared geometry, not native capture quality or all
model preprocessing. Native frame-rate conversion, prior compression, embedded
letterboxing, scene transitions and camera artifacts remain possible influences.
Species and motion are not matched, and training overlap is unknown. Previous
low-resolution animal failures were excluded from this fresh panel; this test
cannot establish that common preparation fixes those earlier failures.

Report signed and absolute compression-relative changes, every fixed-midpoint
crossing, and conflicts against inherited labels per five-clip cell. Scores are
uncalibrated and the midpoint is descriptive. Keep counts separate by model,
content and label; n=5 supports case-level follow-up rather than an accuracy
ranking, significance claim or a low-FPR estimate. Use the existing adapter
boundary and numerical artifacts to support a future VidAudit integration.
