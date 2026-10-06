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
