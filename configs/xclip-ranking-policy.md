# X-CLIP follow-up: fixed before inference

Use D3's `XCLIP-16` branch, L2 discrepancy and the author's exact encoder choice:
`microsoft/xclip-base-patch16`, revision
`d6184e3fd8780d04c85d0f1eabe5f94bf44d98f6`. This is the eight-frame encoder,
not the separate `-16-frames` checkpoint. Pass sixteen normalized frames together;
the encoder groups them into two groups of eight. Retain per-frame pooler outputs,
then the sample standard deviation of second differences of L2 feature distances.
Do not replace this with action-classification logits or temporal pooling.

Reuse **all 26 clips** and both sampling profiles of the previous ResNet18 check.
The manifest, bytes, labels, centered windows and BGR preprocessing stay fixed.
This isolates an encoder comparison within each profile. It does not make the
already examined footage a holdout. It also retains the earlier adaptations:
directly decoded frames, deterministic center windows and no JPEG extraction.

Report raw discrepancy, pair orderings and tie-adjusted AUC for both profiles.
`ai_score=1/(1+temporal_std)` is a decreasing ranking coordinate, never a probability.
No midpoint errors, classifier fitting, cutoff search, or model-agreement verdicts.

The targets remain `panel_wan_04`, `panel_wan_05`, `construction_ai_02`.
For each, count real controls with discrepancy less than or equal to its score.
A global discrepancy cutoff could recover all three without real-video errors on
these data only if **every target is strictly below every real control**. Apply
this same criterion to each profile; show every blocking control and report a
failure rather than moving the criterion. A pass in one profile alone is sampling
sensitive, and motivates a fresh labeled calibration/test collection, not demo use.
If neither profile passes, stop this candidate; do not collect new clips to rescue it.

Audit all score arithmetic and raw ranking counts independently. On the same six
predeclared clips as before (the three targets plus `construction_real_02`,
`panel_ego4d_01`, `panel_youtube_vos_01`), compare unchanged author crop/normalization
and forward code against the adapter, including exact pretrained vision weights.
Independently load the native model via the Transformers pretrained loader from
local safetensors; the adapter instead strictly loads the vision tensors directly.
Freshly reload and repeat those six clips in each profile. Verify source hashes,
metadata, decode timing, model/config hashes, normalized input hashes and code.

Use the fixed Transformers 4.57.6 patch release in the author's 4.57 series (4.57.0
was yanked for installation errors). Keep torch/torchvision and the other detector
dependencies unchanged. This is a CPU encoder comparison, not full paper reproduction.
No demo change, training, threshold fitting or source-media publication.
