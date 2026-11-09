# rabench-test

16 clips × 2 variants × 2 detectors = 64 scores.

Baseline: **baseline**. Preparation: `native`.

![Detector scores](pairs.png)

Higher scores mean more AI-like. Scores are uncalibrated; 0.5 is a fixed reference, not a validated decision threshold.

## Both error directions

| Variant | Detector | Real scored AI-like / real clips | AI scored real-like / AI clips |
|---|---|---:|---:|
| baseline | aegis | 0/8 | 7/8 |
| baseline | waverep | 0/8 | 3/8 |
| compression | aegis | 0/8 | 7/8 |
| compression | waverep | 0/8 | 8/8 |

## When models agree

All scores ≥0.5: AI-like. All scores <0.5: real-like. Mixed sides: inconclusive. This fixed rule measures a coverage/error tradeoff; agreement does not establish authenticity.

| Variant | Agreed clips / all | Correct agreed | Real scored AI-like | AI scored real-like | Inconclusive |
|---|---:|---:|---:|---:|---:|
| baseline | 12/16 | 9 | 0 | 3 | 4 |
| compression | 15/16 | 8 | 0 | 7 | 1 |

Inconclusive clips stay in the denominator; they are not counted as correct predictions. Inspect per-source counts below because source and content can affect these totals.

## Changes from baseline

| Detector | Variant | Group | Clips | Median change | Median absolute change | Changes ≥0.10 | Scores against label at 0.5 | Crossings |
|---|---|---|---:|---:|---:|---:|---:|---:|
| aegis | baseline | ai | 8 | +0.000000 | 0.000000 | 0 | 7 | 0 |
| aegis | baseline | real | 8 | +0.000000 | 0.000000 | 0 | 0 | 0 |
| aegis | compression | ai | 8 | -0.000007 | 0.000010 | 0 | 7 | 0 |
| aegis | compression | real | 8 | -0.000006 | 0.000013 | 0 | 0 | 0 |
| waverep | baseline | ai | 8 | +0.000000 | 0.000000 | 0 | 3 | 0 |
| waverep | baseline | real | 8 | +0.000000 | 0.000000 | 0 | 0 | 0 |
| waverep | compression | ai | 8 | -0.892462 | 0.892462 | 8 | 8 | 5 |
| waverep | compression | real | 8 | -0.000151 | 0.000327 | 0 | 0 | 0 |

## Scores

| Clip | Label | Detector | Variant | Score | Change |
|---|---|---|---|---:|---:|
| ra_L1-01_L2-01c_0019__scene_013_real | real | aegis | baseline | 0.000071 | +0.000000 |
| ra_L1-01_L2-01c_0019__scene_013_real | real | aegis | compression | 0.000065 | -0.000006 |
| ra_L1-01_L2-01c_0019__scene_013_ai | ai | aegis | baseline | 0.999753 | +0.000000 |
| ra_L1-01_L2-01c_0019__scene_013_ai | ai | aegis | compression | 0.999775 | +0.000022 |
| ra_L1-01_L2-01d_0016__scene_005_real | real | aegis | baseline | 0.000091 | +0.000000 |
| ra_L1-01_L2-01d_0016__scene_005_real | real | aegis | compression | 0.000116 | +0.000025 |
| ra_L1-01_L2-01d_0016__scene_005_ai | ai | aegis | baseline | 0.000040 | +0.000000 |
| ra_L1-01_L2-01d_0016__scene_005_ai | ai | aegis | compression | 0.000028 | -0.000012 |
| ra_L1-02_L2-02c_0003__scene_005_real | real | aegis | baseline | 0.000400 | +0.000000 |
| ra_L1-02_L2-02c_0003__scene_005_real | real | aegis | compression | 0.000125 | -0.000275 |
| ra_L1-02_L2-02c_0003__scene_005_ai | ai | aegis | baseline | 0.000305 | +0.000000 |
| ra_L1-02_L2-02c_0003__scene_005_ai | ai | aegis | compression | 0.000297 | -0.000008 |
| ra_L1-02_L2-02d_0014__scene_015_real | real | aegis | baseline | 0.000277 | +0.000000 |
| ra_L1-02_L2-02d_0014__scene_015_real | real | aegis | compression | 0.000155 | -0.000121 |
| ra_L1-02_L2-02d_0014__scene_015_ai | ai | aegis | baseline | 0.000761 | +0.000000 |
| ra_L1-02_L2-02d_0014__scene_015_ai | ai | aegis | compression | 0.000253 | -0.000508 |
| ra_L1-04_L2-04c_0013__scene_003_real | real | aegis | baseline | 0.000071 | +0.000000 |
| ra_L1-04_L2-04c_0013__scene_003_real | real | aegis | compression | 0.000082 | +0.000011 |
| ra_L1-04_L2-04c_0013__scene_003_ai | ai | aegis | baseline | 0.000084 | +0.000000 |
| ra_L1-04_L2-04c_0013__scene_003_ai | ai | aegis | compression | 0.000078 | -0.000006 |
| ra_L1-04_L2-04d_0010__scene_028_real | real | aegis | baseline | 0.000098 | +0.000000 |
| ra_L1-04_L2-04d_0010__scene_028_real | real | aegis | compression | 0.000082 | -0.000016 |
| ra_L1-04_L2-04d_0010__scene_028_ai | ai | aegis | baseline | 0.003127 | +0.000000 |
| ra_L1-04_L2-04d_0010__scene_028_ai | ai | aegis | compression | 0.000582 | -0.002545 |
| ra_L1-07_L2-07c_0015__scene_005_real | real | aegis | baseline | 0.000055 | +0.000000 |
| ra_L1-07_L2-07c_0015__scene_005_real | real | aegis | compression | 0.000048 | -0.000006 |
| ra_L1-07_L2-07c_0015__scene_005_ai | ai | aegis | baseline | 0.000120 | +0.000000 |
| ra_L1-07_L2-07c_0015__scene_005_ai | ai | aegis | compression | 0.000114 | -0.000006 |
| ra_L1-07_L2-07d_0010__scene_002_real | real | aegis | baseline | 0.000027 | +0.000000 |
| ra_L1-07_L2-07d_0010__scene_002_real | real | aegis | compression | 0.000023 | -0.000004 |
| ra_L1-07_L2-07d_0010__scene_002_ai | ai | aegis | baseline | 0.000024 | +0.000000 |
| ra_L1-07_L2-07d_0010__scene_002_ai | ai | aegis | compression | 0.000017 | -0.000007 |
| ra_L1-01_L2-01c_0019__scene_013_real | real | waverep | baseline | 0.004225 | +0.000000 |
| ra_L1-01_L2-01c_0019__scene_013_real | real | waverep | compression | 0.003352 | -0.000873 |
| ra_L1-01_L2-01c_0019__scene_013_ai | ai | waverep | baseline | 0.998835 | +0.000000 |
| ra_L1-01_L2-01c_0019__scene_013_ai | ai | waverep | compression | 0.000937 | -0.997898 |
| ra_L1-01_L2-01d_0016__scene_005_real | real | waverep | baseline | 0.007376 | +0.000000 |
| ra_L1-01_L2-01d_0016__scene_005_real | real | waverep | compression | 0.003457 | -0.003918 |
| ra_L1-01_L2-01d_0016__scene_005_ai | ai | waverep | baseline | 0.823484 | +0.000000 |
| ra_L1-01_L2-01d_0016__scene_005_ai | ai | waverep | compression | 0.009123 | -0.814361 |
| ra_L1-02_L2-02c_0003__scene_005_real | real | waverep | baseline | 0.000627 | +0.000000 |
| ra_L1-02_L2-02c_0003__scene_005_real | real | waverep | compression | 0.000151 | -0.000476 |
| ra_L1-02_L2-02c_0003__scene_005_ai | ai | waverep | baseline | 0.169555 | +0.000000 |
| ra_L1-02_L2-02c_0003__scene_005_ai | ai | waverep | compression | 0.001329 | -0.168225 |
| ra_L1-02_L2-02d_0014__scene_015_real | real | waverep | baseline | 0.000798 | +0.000000 |
| ra_L1-02_L2-02d_0014__scene_015_real | real | waverep | compression | 0.000621 | -0.000177 |
| ra_L1-02_L2-02d_0014__scene_015_ai | ai | waverep | baseline | 0.998222 | +0.000000 |
| ra_L1-02_L2-02d_0014__scene_015_ai | ai | waverep | compression | 0.000249 | -0.997973 |
| ra_L1-04_L2-04c_0013__scene_003_real | real | waverep | baseline | 0.000090 | +0.000000 |
| ra_L1-04_L2-04c_0013__scene_003_real | real | waverep | compression | 0.000091 | +0.000001 |
| ra_L1-04_L2-04c_0013__scene_003_ai | ai | waverep | baseline | 0.999919 | +0.000000 |
| ra_L1-04_L2-04c_0013__scene_003_ai | ai | waverep | compression | 0.029355 | -0.970564 |
| ra_L1-04_L2-04d_0010__scene_028_real | real | waverep | baseline | 0.000171 | +0.000000 |
| ra_L1-04_L2-04d_0010__scene_028_real | real | waverep | compression | 0.000047 | -0.000124 |
| ra_L1-04_L2-04d_0010__scene_028_ai | ai | waverep | baseline | 0.148580 | +0.000000 |
| ra_L1-04_L2-04d_0010__scene_028_ai | ai | waverep | compression | 0.000144 | -0.148436 |
| ra_L1-07_L2-07c_0015__scene_005_real | real | waverep | baseline | 0.006310 | +0.000000 |
| ra_L1-07_L2-07c_0015__scene_005_real | real | waverep | compression | 0.010331 | +0.004021 |
| ra_L1-07_L2-07c_0015__scene_005_ai | ai | waverep | baseline | 0.999972 | +0.000000 |
| ra_L1-07_L2-07c_0015__scene_005_ai | ai | waverep | compression | 0.009851 | -0.990120 |
| ra_L1-07_L2-07d_0010__scene_002_real | real | waverep | baseline | 0.000088 | +0.000000 |
| ra_L1-07_L2-07d_0010__scene_002_real | real | waverep | compression | 0.000057 | -0.000032 |
| ra_L1-07_L2-07d_0010__scene_002_ai | ai | waverep | baseline | 0.224785 | +0.000000 |
| ra_L1-07_L2-07d_0010__scene_002_ai | ai | waverep | compression | 0.000184 | -0.224601 |

## Run details

Every variant starts independently from the source or the common lossless master. Models receive the same decoded RGB frames, with their own native preprocessing. Inference runs on CPU with four threads. Configs and source manifests must be committed before scoring.

These clips measure score changes, not general detector accuracy. Labels come from the dataset. Source quality and training overlap are unknown. Common preparation changes geometry and can change sampled physical frames; comparisons within the prepared variants keep those choices fixed.

| Adapter | Native preprocessing and aggregation |
|---|---|
| aegis | 16 RGB frames; linear resize to 224×224; ImageNet normalization; released fusion head |
| waverep | 16 RGB frames; 504×504 center crop with zero padding for smaller inputs; ImageNet normalization; sigmoid of mean frame logits; batch size 2 |

Eight new matched RA-Bench pairs. Both encodes start from the same source with native geometry and the same centered 16-frame indices. This report uses the 0.5 reference; the separately frozen cutoffs are evaluated in reports/rabench-pilot/. No retuning on test clips. See configs/rabench-selection.md.

Reproduce: `uv run python run.py experiment configs/experiments/rabench-test.json`.

[Scores and logits](scores.csv) · [Summary](summary.json) · [Errors and agreement](decisions.json) · [Config, hashes and preparation commands](run.json) · [Checks](validation.json)
