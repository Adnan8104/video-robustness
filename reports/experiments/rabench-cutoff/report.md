# rabench-cutoff

16 clips × 1 variants × 2 detectors = 32 scores.

Baseline: **baseline**. Preparation: `native`.

![Detector scores](pairs.png)

Higher scores mean more AI-like. Scores are uncalibrated; 0.5 is a fixed reference, not a validated decision threshold.

## Both error directions

| Variant | Detector | Real scored AI-like / real clips | AI scored real-like / AI clips |
|---|---|---:|---:|
| baseline | aegis | 3/8 | 6/8 |
| baseline | waverep | 1/8 | 2/8 |

## When models agree

All scores ≥0.5: AI-like. All scores <0.5: real-like. Mixed sides: inconclusive. This fixed rule measures a coverage/error tradeoff; agreement does not establish authenticity.

| Variant | Agreed clips / all | Correct agreed | Real scored AI-like | AI scored real-like | Inconclusive |
|---|---:|---:|---:|---:|---:|
| baseline | 6/16 | 5 | 0 | 1 | 10 |

Inconclusive clips stay in the denominator; they are not counted as correct predictions. Inspect per-source counts below because source and content can affect these totals.

## Changes from baseline

| Detector | Variant | Group | Clips | Median change | Median absolute change | Changes ≥0.10 | Scores against label at 0.5 | Crossings |
|---|---|---|---:|---:|---:|---:|---:|---:|
| aegis | baseline | ai | 8 | +0.000000 | 0.000000 | 0 | 6 | 0 |
| aegis | baseline | real | 8 | +0.000000 | 0.000000 | 0 | 3 | 0 |
| waverep | baseline | ai | 8 | +0.000000 | 0.000000 | 0 | 2 | 0 |
| waverep | baseline | real | 8 | +0.000000 | 0.000000 | 0 | 1 | 0 |

## Scores

| Clip | Label | Detector | Variant | Score | Change |
|---|---|---|---|---:|---:|
| ra_L1-01_L2-01a_0012__scene_002_real | real | aegis | baseline | 0.004707 | +0.000000 |
| ra_L1-01_L2-01a_0012__scene_002_ai | ai | aegis | baseline | 0.000326 | +0.000000 |
| ra_L1-01_L2-01b_0012__scene_007_real | real | aegis | baseline | 0.037640 | +0.000000 |
| ra_L1-01_L2-01b_0012__scene_007_ai | ai | aegis | baseline | 0.359102 | +0.000000 |
| ra_L1-02_L2-02a_0011__scene_017_real | real | aegis | baseline | 0.000190 | +0.000000 |
| ra_L1-02_L2-02a_0011__scene_017_ai | ai | aegis | baseline | 0.000077 | +0.000000 |
| ra_L1-02_L2-02b_0012__scene_003_real | real | aegis | baseline | 0.999539 | +0.000000 |
| ra_L1-02_L2-02b_0012__scene_003_ai | ai | aegis | baseline | 0.923881 | +0.000000 |
| ra_L1-04_L2-04a_0013__scene_010_real | real | aegis | baseline | 0.000163 | +0.000000 |
| ra_L1-04_L2-04a_0013__scene_010_ai | ai | aegis | baseline | 0.001503 | +0.000000 |
| ra_L1-04_L2-04b_0003__scene_015_real | real | aegis | baseline | 0.998004 | +0.000000 |
| ra_L1-04_L2-04b_0003__scene_015_ai | ai | aegis | baseline | 0.998687 | +0.000000 |
| ra_L1-07_L2-07a_0012__scene_022_real | real | aegis | baseline | 0.000116 | +0.000000 |
| ra_L1-07_L2-07a_0012__scene_022_ai | ai | aegis | baseline | 0.001728 | +0.000000 |
| ra_L1-07_L2-07b_0007__scene_006_real | real | aegis | baseline | 0.672640 | +0.000000 |
| ra_L1-07_L2-07b_0007__scene_006_ai | ai | aegis | baseline | 0.134303 | +0.000000 |
| ra_L1-01_L2-01a_0012__scene_002_real | real | waverep | baseline | 0.002328 | +0.000000 |
| ra_L1-01_L2-01a_0012__scene_002_ai | ai | waverep | baseline | 0.998748 | +0.000000 |
| ra_L1-01_L2-01b_0012__scene_007_real | real | waverep | baseline | 0.000056 | +0.000000 |
| ra_L1-01_L2-01b_0012__scene_007_ai | ai | waverep | baseline | 0.999850 | +0.000000 |
| ra_L1-02_L2-02a_0011__scene_017_real | real | waverep | baseline | 0.007205 | +0.000000 |
| ra_L1-02_L2-02a_0011__scene_017_ai | ai | waverep | baseline | 0.961444 | +0.000000 |
| ra_L1-02_L2-02b_0012__scene_003_real | real | waverep | baseline | 0.052475 | +0.000000 |
| ra_L1-02_L2-02b_0012__scene_003_ai | ai | waverep | baseline | 0.071823 | +0.000000 |
| ra_L1-04_L2-04a_0013__scene_010_real | real | waverep | baseline | 0.000248 | +0.000000 |
| ra_L1-04_L2-04a_0013__scene_010_ai | ai | waverep | baseline | 0.256095 | +0.000000 |
| ra_L1-04_L2-04b_0003__scene_015_real | real | waverep | baseline | 0.090039 | +0.000000 |
| ra_L1-04_L2-04b_0003__scene_015_ai | ai | waverep | baseline | 0.997224 | +0.000000 |
| ra_L1-07_L2-07a_0012__scene_022_real | real | waverep | baseline | 0.963726 | +0.000000 |
| ra_L1-07_L2-07a_0012__scene_022_ai | ai | waverep | baseline | 0.995630 | +0.000000 |
| ra_L1-07_L2-07b_0007__scene_006_real | real | waverep | baseline | 0.058283 | +0.000000 |
| ra_L1-07_L2-07b_0007__scene_006_ai | ai | waverep | baseline | 0.891203 | +0.000000 |

## Run details

Every variant starts independently from the source or the common lossless master. Models receive the same decoded RGB frames, with their own native preprocessing. Inference runs on CPU with four threads. Configs and source manifests must be committed before scoring.

These clips measure score changes, not general detector accuracy. Labels come from the dataset. Source quality and training overlap are unknown. Common preparation changes geometry and can change sampled physical frames; comparisons within the prepared variants keep those choices fixed.

| Adapter | Native preprocessing and aggregation |
|---|---|
| aegis | 16 RGB frames; linear resize to 224×224; ImageNet normalization; released fusion head |
| waverep | 16 RGB frames; 504×504 center crop with zero padding for smaller inputs; ImageNet normalization; sigmoid of mean frame logits; batch size 2 |

Eight matched RA-Bench pairs for choosing cutoffs. CRF 18 only, with native geometry and the centered 16-frame window. Test anchors, original recordings and file hashes are disjoint. See configs/rabench-selection.md.

Reproduce: `uv run python run.py experiment configs/experiments/rabench-cutoff.json`.

[Scores and logits](scores.csv) · [Summary](summary.json) · [Errors and agreement](decisions.json) · [Config, hashes and preparation commands](run.json) · [Checks](validation.json)
