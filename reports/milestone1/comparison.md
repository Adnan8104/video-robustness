# First robustness smoke experiment

Four clips; paired scores only. Higher scores mean more AI-like according to AEGIS, not calibrated probabilities.

| Clip (label) | Original | Compression | Resize | Crop |
|---|---:|---:|---:|---:|
| real_01 (real) | 0.966411 | 0.023794 | 0.999983 | 0.907487 |
| real_02 (real) | 0.000131 | 0.000201 | 0.000164 | 0.000211 |
| ai_01 (ai) | 0.999966 | 0.999951 | 0.999973 | 0.999945 |
| ai_02 (ai) | 0.999995 | 0.999996 | 0.999998 | 0.999985 |

Largest observed shift: real_01 (real), compression: 0.966411 → 0.023794 (signed delta -0.942617). This is a case to investigate, not an estimate of population robustness.

See scores.csv for signed deltas, timings, dimensions, and hashes; run.json records exact inputs and environment.

Resize and crop also require H.264 re-encoding (CRF 18), so their changes combine the spatial edit with encoding. Compression uses CRF 35. No accuracy, AUC, low-FPR, calibration, or population robustness claims are supported by this sample. Dataset labels are inherited, not independently audited. Possible training overlap is unknown.
