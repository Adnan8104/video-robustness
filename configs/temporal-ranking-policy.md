# Temporal candidate: fixed before scoring

Evaluate D3's documented ResNet18 encoder option with L2 feature distances on
every clip from the published source and construction panels: 13 real and 13 AI.
Retain all hashes, labels and difficult cases. This is a regression/feasibility
check on previously examined data, not a fresh held-out test. Creator and scene
clusters, source differences and unknown training overlap remain.

Use two predeclared configs with unchanged source bytes: the shared centered
four-second/16-frame window, and a centered two-second window sampled at nominal
8 fps (16 positions, last position 1.875 seconds after the first). Both preserve
the author's BGR channel order, long-axis 10%-per-side crop, 224px linear resize,
ImageNet normalization and ResNet18 pooled features. Compute the sample standard
deviation of differences between consecutive L2 frame-feature distances, as in
the pinned author code. Lower discrepancy is the author's more AI-like direction.

Save raw discrepancy, distances and changes. For the harness's bounded score
column only, use `ai_score = 1/(1+temporal_std)`, a strictly decreasing coordinate.
It preserves ranking and supplies **no probability or 0.5 decision**. The registry
marks this adapter ranking-only; configs without ranking analysis must fail before
downloads. No threshold may be fitted on these clips, and model-agreement decisions
must not be emitted. Report AI/real ordering counts and tie-adjusted AUC, not fixed
threshold accuracy. AUC pairs are dependent and are not independent trials.

The three shared misses to inspect are `panel_wan_04`, `panel_wan_05` and
`construction_ai_02`. A necessary condition for recovering all three without a
real-video error by one global discrepancy cutoff is that each has **strictly
lower discrepancy than every real control**, since equal scores cannot be
separated. Report each target's ordering against all 13 real clips. If this fails
in either profile, that profile is not a candidate for a zero-real-error repair
on these data. Passing only motivates separate development/calibration footage
and additional held-out sources; it does not justify demo promotion.

Audit unchanged author forward/crop code and the normalization dependency against
the adapter on the three targets plus `construction_real_02`, `panel_ego4d_01`
and `panel_youtube_vos_01`. Independently recompute score arithmetic and ranking
counts for all 26 rows. Reload the model and repeat those same six clips for both
sampling profiles. Record exact input/output hashes and pinned encoder/source hashes.

The 8 fps profile is **native-like timing**, not exact paper reproduction. Upstream
extracts JPEG frames in a random three-second window and reads its first 16 at 8 fps.
We directly decode original source frames and choose deterministic centered windows;
native-frame rounding also differs from FFmpeg's fps filter. The main paper encoder
is XCLIP; ResNet18 is a documented lightweight option. Keep these adaptations visible.
Do not describe a poor lightweight result as failure of the full paper method.

No demo change, classifier training, threshold tuning or source-media publication.
