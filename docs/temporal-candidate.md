# Testing changes between frames

We tested D3 with ResNet18, then its main X-CLIP encoder, to see whether changes
between frames help with the AI videos the other models missed. Neither encoder
separated all three difficult clips from every real control.

All four runs used the same 26 clips: 13 real and 13 AI. Within each sampling
setting, both encoders received exactly the same source bytes and RGB frames.

| Encoder | Sampling | AI/real pairs ranked correctly | AUC |
|---|---|---:|---:|
| ResNet18 | Four seconds, 16 frames | 154/169 | 0.911 |
| X-CLIP | Four seconds, 16 frames | 152/169 | 0.899 |
| ResNet18 | Two seconds, nominal 8 fps | 141/169 | 0.834 |
| X-CLIP | Two seconds, nominal 8 fps | 143/169 | 0.846 |

AUC measures ordering, not classification accuracy. These are previously tested
clips with repeated scenes, not a fresh accuracy benchmark.

## Did it help with the misses?

Lower raw discrepancy is more AI-like. To catch all three targets with one cutoff
and no real-video errors, each must score below every real control.

| Shared miss | ResNet18, 4s / 13 | X-CLIP, 4s / 13 | ResNet18, 2s / 13 | X-CLIP, 2s / 13 |
|---|---:|---:|---:|---:|
| `panel_wan_04` | 0 | 3 | 1 | 4 |
| `panel_wan_05` | 2 | 3 | 5 | 4 |
| `construction_ai_02` | 0 | 0 | 2 | 0 |

X-CLIP put the construction miss ahead of every real control in both settings.
Both Wan misses still overlapped real footage: three real controls in the
four-second setting and four in the two-second setting. Its small two-second
AUC improvement did not fix that. Neither X-CLIP setting passed the
[requirement fixed before inference](../configs/xclip-ranking-policy.md).

Both duration and frame spacing changed between profiles, so we can't say which
caused the ranking difference. No cutoff was fitted and the demo stays unchanged.
This candidate stops here; we did not collect fresh clips to rescue a failed
comparison.

## Implementation and checks

ResNet18 is 45 MiB and uses existing dependencies. X-CLIP adds a pinned 744 MiB
checkpoint and optional Transformers dependency; both run on CPU without training.
The author's `XCLIP-16` branch selects 16px patches and an eight-frame encoder.
We preserve its two groups of eight input frames and per-frame vision features.
Both paths use centered, directly decoded source frames instead of upstream's
random-window JPEG extraction. This is an encoder comparison, not a full paper
reproduction. [Weights, configuration and loading details](../vendor/d3/XCLIP-ORIGIN.md).

The saved `ai_score` is a ranking coordinate, not a probability; 0.5 has no decision
meaning here. Raw discrepancy is saved alongside it.

Each adapter matched author preprocessing and inference on six clips per setting.
For X-CLIP the audit also independently loaded and compared all vision weights.
All 12 X-CLIP fresh-model repeats matched exactly. Arithmetic and ranking checks
covered all 52 new scores. Independent decoder checks matched frame counts,
with sampled timing within 1 ms.

[Full comparison, control IDs and score hashes](../reports/temporal-encoder-comparison/report.md) ·
[Reproduction commands](experiments.md#compare-d3s-x-clip-encoder).

[ResNet18 four-second results](../reports/experiments/temporal-shared/report.md) ·
[ResNet18 two-second results](../reports/experiments/temporal-8fps/report.md) ·
[X-CLIP four-second results](../reports/experiments/xclip-shared/report.md) ·
[X-CLIP two-second results](../reports/experiments/xclip-8fps/report.md)
