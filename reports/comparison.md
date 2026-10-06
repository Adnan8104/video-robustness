# Robustness experiment with encoding control

Four clips; paired scores only. Higher scores mean more AI-like according to AEGIS, not calibrated probabilities.

| Clip (label) | Original | Encode control (CRF 18) | Compression (CRF 35) | Resize | Crop |
|---|---:|---:|---:|---:|---:|
| real_01 (real) | 0.966411 | 0.981128 | 0.023794 | 0.999983 | 0.907487 |
| real_02 (real) | 0.000131 | 0.000130 | 0.000201 | 0.000164 | 0.000211 |
| ai_01 (ai) | 0.999966 | 0.999967 | 0.999951 | 0.999973 | 0.999945 |
| ai_02 (ai) | 0.999995 | 0.999995 | 0.999996 | 0.999998 | 0.999985 |

Largest observed shift versus original: real_01 (real), compression: 0.966411 → 0.023794 (signed delta -0.942617). This is a case to investigate, not an estimate of population robustness.

The encode-only control uses exactly the resize/crop codec, CRF 18, preset, pixel format, and audio removal, with no spatial filter. Every variant still starts from the original.

| Clip | Control − original | Compression − control | Resize − control | Crop − control |
|---|---:|---:|---:|---:|
| real_01 | +0.014717 | -0.957334 | +0.018855 | -0.073641 |
| real_02 | -0.000001 | +0.000071 | +0.000034 | +0.000081 |
| ai_01 | +0.000000 | -0.000015 | +0.000006 | -0.000022 |
| ai_02 | +0.000000 | +0.000001 | +0.000003 | -0.000010 |

See scores.csv for deltas versus both original and control, timings, dimensions, and hashes; run.json records exact inputs and environment. validation.json checks all case geometries and timing. The initial experiment is preserved in milestone1/.

Control-relative differences help isolate spatial edits, but are not a causal decomposition: encoding interacts with image content and resolution. Compression versus control compares CRF 35 and CRF 18 encodes. No accuracy, AUC, low-FPR, calibration, or population robustness claims are supported by four clips. Dataset labels are inherited, not independently audited. Possible training overlap is unknown.
