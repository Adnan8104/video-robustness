# Expanded paired score experiment

20 source clips, 100 scored cases, 16 newly selected clips. The original four discovery clips remain in the panel.

The manifest and descriptive rule were committed before expanded scoring; see [selection policy](../configs/selection.md). Score changes of at least 0.10 are counted as sizable output shifts for this report. This cutoff is not a confidence threshold or a significance test.

## All selected clips

| Source | Clips | Median original score | Encode shift ≥0.10 | Compression shift ≥0.10 | Resize shift ≥0.10 | Crop shift ≥0.10 |
|---|---:|---:|---:|---:|---:|---:|
| MSVD | 10 | 0.000179 | 0 | 1 | 0 | 0 |
| Sora | 5 | 0.999966 | 0 | 0 | 0 | 0 |
| VEO3 | 5 | 0.999904 | 0 | 0 | 0 | 0 |

## Newly selected clips only

| Source | Clips | Median original score | Encode shift ≥0.10 | Compression shift ≥0.10 | Resize shift ≥0.10 | Crop shift ≥0.10 |
|---|---:|---:|---:|---:|---:|---:|
| MSVD | 8 | 0.000179 | 0 | 0 | 0 | 0 |
| Sora | 3 | 0.999476 | 0 | 0 | 0 | 0 |
| VEO3 | 5 | 0.999904 | 0 | 0 | 0 | 0 |

## Median absolute score changes (all clips)

| Source | Encode control − original | Compression − control | Resize − control | Crop − control |
|---|---:|---:|---:|---:|
| MSVD | 0.000008 | 0.000063 | 0.000212 | 0.000122 |
| Sora | 0.000000 | 0.000624 | 0.000008 | 0.000022 |
| VEO3 | 0.000013 | 0.000262 | 0.000065 | 0.000495 |

## Largest change per clip (top five)

| Clip | Source | Newly selected? | Condition | Control score | Variant score | Signed change |
|---|---|---|---|---:|---:|---:|
| real_01 | MSVD | no | compression | 0.981128 | 0.023794 | -0.957334 |
| real_08 | MSVD | yes | resize | 0.003006 | 0.075086 | +0.072080 |
| ai_06 | VEO3 | yes | compression | 0.999892 | 0.945282 | -0.054609 |
| ai_03 | Sora | yes | crop | 0.946256 | 0.999681 | +0.053425 |
| ai_04 | Sora | yes | compression | 0.999422 | 0.982723 | -0.016699 |

[All paired scores](comparison.md) · [Raw scores](scores.csv) · [Run metadata](run.json)

The size cap, filename ordering, one real-video dataset, and five clips per generator make this a convenience sample. Existing discovery cases are not independent confirmation. Low shifts can also reflect saturated scores near zero or one. Labels are inherited, training overlap is unknown, and re-encoding interacts with spatial edits. These results do not estimate population robustness, accuracy, calibration, or low-FPR performance. All variants of a clip are paired observations, not independent samples.
