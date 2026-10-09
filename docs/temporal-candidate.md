# Testing changes between frames

We tried D3's lightweight ResNet18 option to see whether changes between frames
could help with the AI videos the other models missed. It helped with some cases,
but the time window made a difference.

Both runs used all 26 clips from the earlier panels: 13 real and 13 AI.

| Sampling | AI/real pairs ranked correctly | AUC |
|---|---:|---:|
| Four-second window, 16 frames | 154/169 | 0.911 |
| Two-second window, nominal 8 fps | 141/169 | 0.834 |

AUC measures ordering, not classification accuracy. These are previously tested
clips with repeated scenes, not a fresh accuracy benchmark.

## Did it help with the misses?

Lower raw discrepancy is more AI-like. To catch all three targets with one cutoff
and no real-video errors, each must score below every real control.

| Shared miss | Real controls blocking separation, 4s / 13 | Real controls blocking separation, 2s / 13 |
|---|---:|---:|
| `panel_wan_04` | 0 | 1 |
| `panel_wan_05` | 2 | 5 |
| `construction_ai_02` | 0 | 2 |

In the four-second test, two misses ranked ahead of every real control. The other
Wan clip overlapped the real Beynost and Prague crane videos. In the two-second
test, all three overlapped real footage. Neither setting passed the requirement.

Both duration and frame spacing changed, so we can't say which caused the drop.
No cutoff was fitted and the demo stays unchanged.

## Implementation and checks

The ResNet18 encoder is 45 MiB and runs on CPU with existing dependencies. It is a
documented D3 option, but the paper's main encoder is XCLIP. We also use centered,
directly decoded source frames instead of upstream's random-window JPEG extraction.

The saved `ai_score` is a ranking coordinate, not a probability; 0.5 has no decision
meaning here. Raw discrepancy is saved alongside it.

The adapter matched author preprocessing and inference on six clips per setting.
All 12 fresh-model repeats matched exactly. Arithmetic and ranking checks covered
all 52 scores. Independent decoder checks matched frame counts, with sampled
timing within 1 ms.

The temporal signal is worth testing further. The full encoder or an optical-flow
branch could be the next comparison, followed by separate calibration and test footage.

[Four-second results](../reports/experiments/temporal-shared/report.md) ·
[Two-second results](../reports/experiments/temporal-8fps/report.md) ·
[Technical setup](experiments.md#evaluate-a-temporal-ranking-candidate)
