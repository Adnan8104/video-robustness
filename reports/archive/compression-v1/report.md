# compression

20 clips × 2 variants × 2 detectors = 80 scores.

Baseline: **baseline**. Preparation: `centered_4s_504_24fps`.

![Scores before and after each edit](pairs.png)

Higher scores mean more AI-like. Scores are uncalibrated; 0.5 is a fixed reference, not a validated decision threshold.

## Changes from baseline

| Detector | Variant | Group | Clips | Median change | Median absolute change | Changes ≥0.10 | Scores against label at 0.5 | Crossings |
|---|---|---|---:|---:|---:|---:|---:|---:|
| aegis | baseline | ai_animal | 5 | +0.000000 | 0.000000 | 0 | 0 | 0 |
| aegis | baseline | ai_non_animal | 5 | +0.000000 | 0.000000 | 0 | 0 | 0 |
| aegis | baseline | real_animal | 5 | +0.000000 | 0.000000 | 0 | 1 | 0 |
| aegis | baseline | real_non_animal | 5 | +0.000000 | 0.000000 | 0 | 0 | 0 |
| aegis | compression | ai_animal | 5 | -0.000000 | 0.000005 | 0 | 0 | 0 |
| aegis | compression | ai_non_animal | 5 | -0.000606 | 0.000606 | 0 | 0 | 0 |
| aegis | compression | real_animal | 5 | -0.000002 | 0.000371 | 0 | 1 | 0 |
| aegis | compression | real_non_animal | 5 | -0.000092 | 0.000092 | 0 | 0 | 0 |
| waverep | baseline | ai_animal | 5 | +0.000000 | 0.000000 | 0 | 2 | 0 |
| waverep | baseline | ai_non_animal | 5 | +0.000000 | 0.000000 | 0 | 2 | 0 |
| waverep | baseline | real_animal | 5 | +0.000000 | 0.000000 | 0 | 1 | 0 |
| waverep | baseline | real_non_animal | 5 | +0.000000 | 0.000000 | 0 | 0 | 0 |
| waverep | compression | ai_animal | 5 | -0.598130 | 0.598130 | 5 | 5 | 3 |
| waverep | compression | ai_non_animal | 5 | -0.431239 | 0.431239 | 4 | 4 | 2 |
| waverep | compression | real_animal | 5 | -0.000443 | 0.000443 | 0 | 1 | 0 |
| waverep | compression | real_non_animal | 5 | -0.005177 | 0.005177 | 0 | 0 | 0 |

## Scores

| Clip | Label | Detector | Variant | Score | Change |
|---|---|---|---|---:|---:|
| controlled_ai_animal_01 | ai | aegis | baseline | 0.999464 | +0.000000 |
| controlled_ai_animal_01 | ai | aegis | compression | 0.999620 | +0.000156 |
| controlled_ai_animal_02 | ai | aegis | baseline | 0.999982 | +0.000000 |
| controlled_ai_animal_02 | ai | aegis | compression | 0.999985 | +0.000003 |
| controlled_ai_animal_03 | ai | aegis | baseline | 0.999962 | +0.000000 |
| controlled_ai_animal_03 | ai | aegis | compression | 0.997467 | -0.002496 |
| controlled_ai_animal_04 | ai | aegis | baseline | 0.999999 | +0.000000 |
| controlled_ai_animal_04 | ai | aegis | compression | 0.999998 | -0.000000 |
| controlled_ai_animal_05 | ai | aegis | baseline | 0.999999 | +0.000000 |
| controlled_ai_animal_05 | ai | aegis | compression | 0.999994 | -0.000005 |
| controlled_ai_non_animal_01 | ai | aegis | baseline | 0.999886 | +0.000000 |
| controlled_ai_non_animal_01 | ai | aegis | compression | 0.999280 | -0.000606 |
| controlled_ai_non_animal_02 | ai | aegis | baseline | 0.999938 | +0.000000 |
| controlled_ai_non_animal_02 | ai | aegis | compression | 0.999651 | -0.000287 |
| controlled_ai_non_animal_03 | ai | aegis | baseline | 0.999909 | +0.000000 |
| controlled_ai_non_animal_03 | ai | aegis | compression | 0.931091 | -0.068818 |
| controlled_ai_non_animal_04 | ai | aegis | baseline | 0.999884 | +0.000000 |
| controlled_ai_non_animal_04 | ai | aegis | compression | 0.983481 | -0.016402 |
| controlled_ai_non_animal_05 | ai | aegis | baseline | 0.999997 | +0.000000 |
| controlled_ai_non_animal_05 | ai | aegis | compression | 0.999996 | -0.000001 |
| controlled_real_animal_01 | real | aegis | baseline | 0.999967 | +0.000000 |
| controlled_real_animal_01 | real | aegis | compression | 0.904924 | -0.095043 |
| controlled_real_animal_02 | real | aegis | baseline | 0.000507 | +0.000000 |
| controlled_real_animal_02 | real | aegis | compression | 0.006549 | +0.006042 |
| controlled_real_animal_03 | real | aegis | baseline | 0.000094 | +0.000000 |
| controlled_real_animal_03 | real | aegis | compression | 0.000092 | -0.000002 |
| controlled_real_animal_04 | real | aegis | baseline | 0.000034 | +0.000000 |
| controlled_real_animal_04 | real | aegis | compression | 0.000038 | +0.000004 |
| controlled_real_animal_05 | real | aegis | baseline | 0.000501 | +0.000000 |
| controlled_real_animal_05 | real | aegis | compression | 0.000130 | -0.000371 |
| controlled_real_non_animal_01 | real | aegis | baseline | 0.000182 | +0.000000 |
| controlled_real_non_animal_01 | real | aegis | compression | 0.000090 | -0.000092 |
| controlled_real_non_animal_02 | real | aegis | baseline | 0.000548 | +0.000000 |
| controlled_real_non_animal_02 | real | aegis | compression | 0.000133 | -0.000415 |
| controlled_real_non_animal_03 | real | aegis | baseline | 0.000044 | +0.000000 |
| controlled_real_non_animal_03 | real | aegis | compression | 0.000085 | +0.000041 |
| controlled_real_non_animal_04 | real | aegis | baseline | 0.002146 | +0.000000 |
| controlled_real_non_animal_04 | real | aegis | compression | 0.000784 | -0.001362 |
| controlled_real_non_animal_05 | real | aegis | baseline | 0.000175 | +0.000000 |
| controlled_real_non_animal_05 | real | aegis | compression | 0.000200 | +0.000025 |
| controlled_ai_animal_01 | ai | waverep | baseline | 0.151260 | +0.000000 |
| controlled_ai_animal_01 | ai | waverep | compression | 0.000174 | -0.151086 |
| controlled_ai_animal_02 | ai | waverep | baseline | 0.996280 | +0.000000 |
| controlled_ai_animal_02 | ai | waverep | compression | 0.000879 | -0.995401 |
| controlled_ai_animal_03 | ai | waverep | baseline | 0.113080 | +0.000000 |
| controlled_ai_animal_03 | ai | waverep | compression | 0.000288 | -0.112792 |
| controlled_ai_animal_04 | ai | waverep | baseline | 0.971400 | +0.000000 |
| controlled_ai_animal_04 | ai | waverep | compression | 0.007834 | -0.963566 |
| controlled_ai_animal_05 | ai | waverep | baseline | 0.998909 | +0.000000 |
| controlled_ai_animal_05 | ai | waverep | compression | 0.400779 | -0.598130 |
| controlled_ai_non_animal_01 | ai | waverep | baseline | 0.432082 | +0.000000 |
| controlled_ai_non_animal_01 | ai | waverep | compression | 0.000843 | -0.431239 |
| controlled_ai_non_animal_02 | ai | waverep | baseline | 0.999582 | +0.000000 |
| controlled_ai_non_animal_02 | ai | waverep | compression | 0.675879 | -0.323702 |
| controlled_ai_non_animal_03 | ai | waverep | baseline | 0.989897 | +0.000000 |
| controlled_ai_non_animal_03 | ai | waverep | compression | 0.002951 | -0.986946 |
| controlled_ai_non_animal_04 | ai | waverep | baseline | 0.983940 | +0.000000 |
| controlled_ai_non_animal_04 | ai | waverep | compression | 0.000974 | -0.982967 |
| controlled_ai_non_animal_05 | ai | waverep | baseline | 0.092674 | +0.000000 |
| controlled_ai_non_animal_05 | ai | waverep | compression | 0.000168 | -0.092506 |
| controlled_real_animal_01 | real | waverep | baseline | 0.732082 | +0.000000 |
| controlled_real_animal_01 | real | waverep | compression | 0.688378 | -0.043705 |
| controlled_real_animal_02 | real | waverep | baseline | 0.000581 | +0.000000 |
| controlled_real_animal_02 | real | waverep | compression | 0.000323 | -0.000258 |
| controlled_real_animal_03 | real | waverep | baseline | 0.001034 | +0.000000 |
| controlled_real_animal_03 | real | waverep | compression | 0.000591 | -0.000443 |
| controlled_real_animal_04 | real | waverep | baseline | 0.000123 | +0.000000 |
| controlled_real_animal_04 | real | waverep | compression | 0.000102 | -0.000021 |
| controlled_real_animal_05 | real | waverep | baseline | 0.008413 | +0.000000 |
| controlled_real_animal_05 | real | waverep | compression | 0.001460 | -0.006954 |
| controlled_real_non_animal_01 | real | waverep | baseline | 0.000859 | +0.000000 |
| controlled_real_non_animal_01 | real | waverep | compression | 0.000108 | -0.000751 |
| controlled_real_non_animal_02 | real | waverep | baseline | 0.006569 | +0.000000 |
| controlled_real_non_animal_02 | real | waverep | compression | 0.001391 | -0.005177 |
| controlled_real_non_animal_03 | real | waverep | baseline | 0.001167 | +0.000000 |
| controlled_real_non_animal_03 | real | waverep | compression | 0.000140 | -0.001028 |
| controlled_real_non_animal_04 | real | waverep | baseline | 0.009175 | +0.000000 |
| controlled_real_non_animal_04 | real | waverep | compression | 0.000246 | -0.008930 |
| controlled_real_non_animal_05 | real | waverep | baseline | 0.051373 | +0.000000 |
| controlled_real_non_animal_05 | real | waverep | compression | 0.009657 | -0.041715 |

## Run details

Every variant starts independently from the source or the common lossless master. Models receive the same decoded RGB frames, with their own native preprocessing. WaveRep averages 16 frame logits before applying sigmoid; AEGIS uses its released fusion head. Inference runs on CPU with four threads. Configs and source manifests must be committed before scoring.

These clips measure score changes, not general detector accuracy. Labels come from the dataset. Source quality and training overlap are unknown. Common preparation changes geometry and can change sampled physical frames; comparisons within the prepared variants keep those choices fixed.

Reproduces the existing 20-clip content panel. Five clips per real/AI × animal/non-animal group. The manifest includes the reviewed labels and crop audit.

Reproduce: `uv run python run.py experiment configs/experiments/compression.json`.

[Scores and logits](scores.csv) · [Summary](summary.json) · [Config, hashes and preparation commands](run.json) · [Checks](validation.json)
