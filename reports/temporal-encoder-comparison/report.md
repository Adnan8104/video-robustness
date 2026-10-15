# Temporal encoder comparison

All runs use the same 13 real and 13 AI source files. These are previously examined clips; AUC measures ordering, not detection accuracy. No cutoff is fitted.

| Run | Correctly ordered pairs / total | AUC | All targets strictly ahead of every real control |
|---|---:|---:|---|
| temporal-shared | 154/169 | 0.911 | No |
| xclip-shared | 152/169 | 0.899 | No |
| temporal-8fps | 141/169 | 0.834 | No |
| xclip-8fps | 143/169 | 0.846 | No |

## Shared misses

A blocking control has an equal or more AI-like ranking coordinate than the AI target. Any blocker prevents a single cutoff from recovering that target without a real-video error on these data.

| Run | Target | Blocking controls / real clips | Control IDs |
|---|---|---:|---|
| temporal-shared | panel_wan_04 | 0/13 | None |
| temporal-shared | panel_wan_05 | 2/13 | construction_real_02, construction_real_03 |
| temporal-shared | construction_ai_02 | 0/13 | None |
| xclip-shared | panel_wan_04 | 3/13 | panel_youtube_vos_02, construction_real_02, construction_real_03 |
| xclip-shared | panel_wan_05 | 3/13 | panel_youtube_vos_02, construction_real_02, construction_real_03 |
| xclip-shared | construction_ai_02 | 0/13 | None |
| temporal-8fps | panel_wan_04 | 1/13 | construction_real_01 |
| temporal-8fps | panel_wan_05 | 5/13 | panel_ego4d_01, panel_ego4d_03, construction_real_01, construction_real_02, construction_real_03 |
| temporal-8fps | construction_ai_02 | 2/13 | construction_real_01, construction_real_03 |
| xclip-8fps | panel_wan_04 | 4/13 | panel_ego4d_02, construction_real_01, construction_real_02, construction_real_03 |
| xclip-8fps | panel_wan_05 | 4/13 | panel_ego4d_02, construction_real_01, construction_real_02, construction_real_03 |
| xclip-8fps | construction_ai_02 | 0/13 | None |

Sources, score hashes and exact target/control values: [comparison.json](comparison.json).
