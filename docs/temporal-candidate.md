# Temporal features: useful ordering, no reliable repair yet

D3's lightweight ResNet18 option gives a useful new signal on our existing clips,
but its ordering depends on the time window. Neither checked profile can recover
all three shared misses by one discrepancy cutoff without flagging a real control.
We keep the upload demo unchanged.

All **26 clips** from the two published panels are retained: 13 real and 13 AI.
This is a regression check on already examined footage, not a new held-out test.

| Sampling profile | AI/real pairs in expected order | All-panel AUC | Old 20-clip panel AUC | Construction 6-clip AUC |
|---|---:|---:|---:|---:|
| Centered 4s, 16 frames | 154/169 | 0.911 | 0.940 (94/100 pairs) | 1.000 (9/9 pairs) |
| Centered 2s, nominal 8 fps | 141/169 | 0.834 | 0.940 (94/100 pairs) | 0.444 (4/9 pairs) |

AUC here counts AI/real score orderings, not classification accuracy. The nine
construction comparisons come from only six clips; perfect ordering in that tiny
panel is not evidence of general reliability. Creator/scene clusters make pairs
dependent. Cross-source appearance, codecs and motion remain confounded.

## What happened to the shared misses

Lower raw temporal discrepancy is more AI-like. For a single cutoff to catch
all three targets with zero real errors on these controls, each target must have
strictly lower discrepancy than every real clip. No cutoff was fitted.

| Shared miss | 4s discrepancy | Real controls blocking separation / 13 | 2s discrepancy | Real controls blocking separation / 13 |
|---|---:|---:|---:|---:|
| `panel_wan_04` | 0.621714 | 0 | 0.678358 | 1 |
| `panel_wan_05` | 0.984461 | 2 | 1.342866 | 5 |
| `construction_ai_02` (Sora) | 0.469000 | 0 | 1.022395 | 2 |

The four-second profile places two targets ahead of every real control. The
remaining Wan target overlaps the real Beynost and Prague crane footage. The
two-second profile overlaps at least one real control for every target.
[Exact overlapping clips and panel counts](../reports/experiments/temporal-shared/target-separation.json)
· [Two-second check](../reports/experiments/temporal-8fps/target-separation.json).

Both duration and frame spacing changed between profiles, so the drop cannot be
attributed solely to frame rate. We report both predeclared results rather than
select the better one after scoring. This candidate fails our necessary condition
for repairing all three misses at zero real errors in either profile.

## Why this candidate

[D3](https://github.com/Zig-HS/D3/tree/c798fbc57fe0c4198d63a73732c2c0f9e4b4816c)
measures changes in distances between consecutive frame features, using their
sample standard deviation as a temporal discrepancy. It tests an additional cue
instead of adding another independently scored RGB-frame classifier. This is a
temporal feature statistic, not optical flow. ResNet18 is a documented lightweight
encoder option, with a 45 MiB official ImageNet checkpoint and no new runtime
dependencies. The main paper model uses XCLIP; these results do not evaluate it.

We preserve the author's BGR channel order, crop, linear resize and normalization.
Our deterministic center windows and direct source decoding differ from upstream
random-window JPEG extraction. The 8 fps profile checks native-like timing but
does not remove those adaptations. [Source and weight details](../vendor/d3/ORIGIN.md).

Raw discrepancy is preserved in the CSV. The harness's `ai_score` column stores
`1/(1+temporal_std)` only to provide a bounded ranking coordinate. It is not a
probability, and **0.5 has no decision meaning**. Ranking-only adapters require
ranking analysis; their reports omit midpoint verdicts and agreement counts.

## Checks and next step

Native preprocessing and forward outputs match the pinned author code on six
predeclared clips per profile. Fresh model loads reproduce every output and input
hash for those same 12 scores. Independent arithmetic/ranking checks cover all
52 scores. Full OpenCV and FFmpeg frame counts agree on all sources, and sampled
presentation times differ from nominal timing by less than one millisecond in both
profiles. Configs and the 26-source manifest were committed before inference.

The signal merits further investigation, but these results do not support a
replacement detector yet. A next candidate can test the main D3 encoder or a
released optical-flow branch, using the same regression criteria. Any candidate
that passes needs separately selected development/calibration footage and held-out
sources before choosing a threshold or changing the demo.

[Four-second report](../reports/experiments/temporal-shared/report.md) ·
[Two-second report](../reports/experiments/temporal-8fps/report.md) ·
[Predeclared policy](../configs/temporal-ranking-policy.md) ·
[Reproduction commands](experiments.md#evaluate-a-temporal-ranking-candidate).
