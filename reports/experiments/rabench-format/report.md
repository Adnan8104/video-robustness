# rabench-format

16 clips × 2 variants × 2 detectors = 64 scores.

Baseline: **baseline**. Preparation: `centered_4s_504_24fps`.

![Detector scores](pairs.png)

Higher scores mean more AI-like. Scores are uncalibrated; 0.5 is a fixed reference, not a validated decision threshold.

## Both error directions

| Variant | Detector | Real scored AI-like / real clips | AI scored real-like / AI clips |
|---|---|---:|---:|
| baseline | aegis | 2/8 | 7/8 |
| baseline | waverep | 3/8 | 3/8 |
| compression | aegis | 2/8 | 7/8 |
| compression | waverep | 0/8 | 8/8 |

## When models agree

All scores ≥0.5: AI-like. All scores <0.5: real-like. Mixed sides: inconclusive. This fixed rule measures a coverage/error tradeoff; agreement does not establish authenticity.

| Variant | Agreed clips / all | Correct agreed | Real scored AI-like | AI scored real-like | Inconclusive |
|---|---:|---:|---:|---:|---:|
| baseline | 9/16 | 5 | 1 | 3 | 7 |
| compression | 13/16 | 6 | 0 | 7 | 3 |

Inconclusive clips stay in the denominator; they are not counted as correct predictions. Inspect per-source counts below because source and content can affect these totals.

## Changes from baseline

| Detector | Variant | Group | Clips | Median change | Median absolute change | Changes ≥0.10 | Scores against label at 0.5 | Crossings |
|---|---|---|---:|---:|---:|---:|---:|---:|
| aegis | baseline | ai | 8 | +0.000000 | 0.000000 | 0 | 7 | 0 |
| aegis | baseline | real | 8 | +0.000000 | 0.000000 | 0 | 2 | 0 |
| aegis | compression | ai | 8 | -0.000040 | 0.000106 | 1 | 7 | 0 |
| aegis | compression | real | 8 | -0.000036 | 0.000546 | 0 | 2 | 0 |
| waverep | baseline | ai | 8 | +0.000000 | 0.000000 | 0 | 3 | 0 |
| waverep | baseline | real | 8 | +0.000000 | 0.000000 | 0 | 3 | 0 |
| waverep | compression | ai | 8 | -0.833046 | 0.833046 | 8 | 8 | 5 |
| waverep | compression | real | 8 | -0.078975 | 0.078975 | 3 | 0 | 3 |

## Scores

| Clip | Label | Detector | Variant | Score | Change |
|---|---|---|---|---:|---:|
| rfc_real_01 | real | aegis | baseline | 0.000071 | +0.000000 |
| rfc_real_01 | real | aegis | compression | 0.000078 | +0.000007 |
| rfc_ai_01 | ai | aegis | baseline | 0.154463 | +0.000000 |
| rfc_ai_01 | ai | aegis | compression | 0.022589 | -0.131873 |
| rfc_real_02 | real | aegis | baseline | 0.000024 | +0.000000 |
| rfc_real_02 | real | aegis | compression | 0.000022 | -0.000001 |
| rfc_ai_02 | ai | aegis | baseline | 0.000282 | +0.000000 |
| rfc_ai_02 | ai | aegis | compression | 0.000447 | +0.000164 |
| rfc_real_03 | real | aegis | baseline | 0.015148 | +0.000000 |
| rfc_real_03 | real | aegis | compression | 0.001164 | -0.013985 |
| rfc_ai_03 | ai | aegis | baseline | 0.001797 | +0.000000 |
| rfc_ai_03 | ai | aegis | compression | 0.000836 | -0.000960 |
| rfc_real_04 | real | aegis | baseline | 0.991007 | +0.000000 |
| rfc_real_04 | real | aegis | compression | 0.994900 | +0.003893 |
| rfc_ai_04 | ai | aegis | baseline | 0.995662 | +0.000000 |
| rfc_ai_04 | ai | aegis | compression | 0.901434 | -0.094227 |
| rfc_real_05 | real | aegis | baseline | 0.000061 | +0.000000 |
| rfc_real_05 | real | aegis | compression | 0.000064 | +0.000003 |
| rfc_ai_05 | ai | aegis | baseline | 0.000175 | +0.000000 |
| rfc_ai_05 | ai | aegis | compression | 0.000133 | -0.000042 |
| rfc_real_06 | real | aegis | baseline | 0.001292 | +0.000000 |
| rfc_real_06 | real | aegis | compression | 0.000271 | -0.001022 |
| rfc_ai_06 | ai | aegis | baseline | 0.000350 | +0.000000 |
| rfc_ai_06 | ai | aegis | compression | 0.000385 | +0.000034 |
| rfc_real_07 | real | aegis | baseline | 0.994439 | +0.000000 |
| rfc_real_07 | real | aegis | compression | 0.988516 | -0.005924 |
| rfc_ai_07 | ai | aegis | baseline | 0.000610 | +0.000000 |
| rfc_ai_07 | ai | aegis | compression | 0.000657 | +0.000047 |
| rfc_real_08 | real | aegis | baseline | 0.000218 | +0.000000 |
| rfc_real_08 | real | aegis | compression | 0.000147 | -0.000071 |
| rfc_ai_08 | ai | aegis | baseline | 0.000186 | +0.000000 |
| rfc_ai_08 | ai | aegis | compression | 0.000149 | -0.000037 |
| rfc_real_01 | real | waverep | baseline | 0.000293 | +0.000000 |
| rfc_real_01 | real | waverep | compression | 0.000087 | -0.000206 |
| rfc_ai_01 | ai | waverep | baseline | 0.999674 | +0.000000 |
| rfc_ai_01 | ai | waverep | compression | 0.000241 | -0.999433 |
| rfc_real_02 | real | waverep | baseline | 0.086301 | +0.000000 |
| rfc_real_02 | real | waverep | compression | 0.002092 | -0.084209 |
| rfc_ai_02 | ai | waverep | baseline | 0.991674 | +0.000000 |
| rfc_ai_02 | ai | waverep | compression | 0.027023 | -0.964652 |
| rfc_real_03 | real | waverep | baseline | 0.915384 | +0.000000 |
| rfc_real_03 | real | waverep | compression | 0.000101 | -0.915283 |
| rfc_ai_03 | ai | waverep | baseline | 0.335030 | +0.000000 |
| rfc_ai_03 | ai | waverep | compression | 0.001507 | -0.333523 |
| rfc_real_04 | real | waverep | baseline | 0.000464 | +0.000000 |
| rfc_real_04 | real | waverep | compression | 0.001019 | +0.000555 |
| rfc_ai_04 | ai | waverep | baseline | 0.738076 | +0.000000 |
| rfc_ai_04 | ai | waverep | compression | 0.001286 | -0.736790 |
| rfc_real_05 | real | waverep | baseline | 0.073854 | +0.000000 |
| rfc_real_05 | real | waverep | compression | 0.000114 | -0.073741 |
| rfc_ai_05 | ai | waverep | baseline | 0.999311 | +0.000000 |
| rfc_ai_05 | ai | waverep | compression | 0.000542 | -0.998769 |
| rfc_real_06 | real | waverep | baseline | 0.996982 | +0.000000 |
| rfc_real_06 | real | waverep | compression | 0.009237 | -0.987745 |
| rfc_ai_06 | ai | waverep | baseline | 0.998266 | +0.000000 |
| rfc_ai_06 | ai | waverep | compression | 0.068963 | -0.929303 |
| rfc_real_07 | real | waverep | baseline | 0.800104 | +0.000000 |
| rfc_real_07 | real | waverep | compression | 0.047751 | -0.752352 |
| rfc_ai_07 | ai | waverep | baseline | 0.235428 | +0.000000 |
| rfc_ai_07 | ai | waverep | compression | 0.005149 | -0.230279 |
| rfc_real_08 | real | waverep | baseline | 0.000420 | +0.000000 |
| rfc_real_08 | real | waverep | compression | 0.000046 | -0.000374 |
| rfc_ai_08 | ai | waverep | baseline | 0.278482 | +0.000000 |
| rfc_ai_08 | ai | waverep | compression | 0.000050 | -0.278432 |

## Run details

Every variant starts independently from the source or the common lossless master. Models receive the same decoded RGB frames, with their own native preprocessing. Inference runs on CPU with four threads. Configs and source manifests must be committed before scoring.

These clips measure score changes, not general detector accuracy. Labels come from the dataset. Source quality and training overlap are unknown. Common preparation changes geometry and can change sampled physical frames; comparisons within the prepared variants keep those choices fixed.

| Adapter | Native preprocessing and aggregation |
|---|---|
| aegis | 16 RGB frames; linear resize to 224×224; ImageNet normalization; released fusion head |
| waverep | 16 RGB frames; 504×504 center crop with zero padding for smaller inputs; ImageNet normalization; sigmoid of mean frame logits; batch size 2 |

Fresh RA-Bench scene pairs, with real and generated inputs standardized to 504×504, 24 fps and 96 frames. Each clip's two encodes start directly from one lossless master. Read configs/rabench-format-selection.md for the selection rule. Report ordering and fixed 0.5 errors, with no fitted cutoff. Crop and resampling change the inputs, and comparison to the previous native pilot uses different clips.

Reproduce: `uv run python run.py experiment configs/experiments/rabench-format.json`.

[Scores and logits](scores.csv) · [Summary](summary.json) · [Errors and agreement](decisions.json) · [Config, hashes and preparation commands](run.json) · [Checks](validation.json)
