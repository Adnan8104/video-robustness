# Robustness experiment with encoding control

20 source clips; paired scores only. Higher scores mean more AI-like according to AEGIS, not calibrated probabilities.

| Clip (label) | Original | Encode control (CRF 18) | Compression (CRF 35) | Resize | Crop |
|---|---:|---:|---:|---:|---:|
| real_01 (real) | 0.966411 | 0.981128 | 0.023794 | 0.999983 | 0.907487 |
| real_02 (real) | 0.000131 | 0.000130 | 0.000201 | 0.000164 | 0.000211 |
| real_03 (real) | 0.001133 | 0.001463 | 0.000378 | 0.001197 | 0.001426 |
| real_04 (real) | 0.000174 | 0.000160 | 0.000105 | 0.000318 | 0.000322 |
| real_05 (real) | 0.000116 | 0.000118 | 0.000119 | 0.000089 | 0.000074 |
| real_06 (real) | 0.000406 | 0.000405 | 0.000540 | 0.004544 | 0.000188 |
| real_07 (real) | 0.000112 | 0.000112 | 0.000117 | 0.000114 | 0.000139 |
| real_08 (real) | 0.003090 | 0.003006 | 0.008092 | 0.075086 | 0.024165 |
| real_09 (real) | 0.000184 | 0.000203 | 0.000209 | 0.000497 | 0.000189 |
| real_10 (real) | 0.000070 | 0.000068 | 0.000089 | 0.000100 | 0.000267 |
| ai_01 (ai) | 0.999966 | 0.999967 | 0.999951 | 0.999973 | 0.999945 |
| ai_02 (ai) | 0.999995 | 0.999995 | 0.999996 | 0.999998 | 0.999985 |
| ai_03 (ai) | 0.941124 | 0.946256 | 0.974809 | 0.974732 | 0.999681 |
| ai_04 (ai) | 0.999476 | 0.999422 | 0.982723 | 0.999764 | 0.999716 |
| ai_05 (ai) | 0.999989 | 0.999989 | 0.999365 | 0.999997 | 0.999996 |
| ai_06 (ai) | 0.999904 | 0.999892 | 0.945282 | 0.999667 | 0.990866 |
| ai_07 (ai) | 0.999064 | 0.999871 | 0.998914 | 0.999936 | 0.999376 |
| ai_08 (ai) | 0.999965 | 0.999964 | 0.999962 | 0.999971 | 0.999946 |
| ai_09 (ai) | 0.999997 | 0.999997 | 0.999994 | 0.999997 | 0.999927 |
| ai_10 (ai) | 0.999165 | 0.999592 | 0.999854 | 0.999717 | 0.993290 |

Largest observed shift versus original: real_01 (real), compression: 0.966411 → 0.023794 (signed delta -0.942617). This is a case to investigate, not an estimate of population robustness.

The encode-only control uses exactly the resize/crop codec, CRF 18, preset, pixel format, and audio removal, with no spatial filter. Every variant still starts from the original.

| Clip | Control − original | Compression − control | Resize − control | Crop − control |
|---|---:|---:|---:|---:|
| real_01 | +0.014717 | -0.957334 | +0.018855 | -0.073641 |
| real_02 | -0.000001 | +0.000071 | +0.000034 | +0.000081 |
| real_03 | +0.000330 | -0.001085 | -0.000266 | -0.000037 |
| real_04 | -0.000014 | -0.000054 | +0.000158 | +0.000162 |
| real_05 | +0.000001 | +0.000002 | -0.000029 | -0.000043 |
| real_06 | -0.000001 | +0.000135 | +0.004138 | -0.000217 |
| real_07 | +0.000000 | +0.000006 | +0.000002 | +0.000027 |
| real_08 | -0.000084 | +0.005086 | +0.072080 | +0.021159 |
| real_09 | +0.000019 | +0.000007 | +0.000294 | -0.000013 |
| real_10 | -0.000002 | +0.000021 | +0.000032 | +0.000199 |
| ai_01 | +0.000000 | -0.000015 | +0.000006 | -0.000022 |
| ai_02 | +0.000000 | +0.000001 | +0.000003 | -0.000010 |
| ai_03 | +0.005131 | +0.028553 | +0.028476 | +0.053425 |
| ai_04 | -0.000054 | -0.016699 | +0.000342 | +0.000294 |
| ai_05 | +0.000000 | -0.000624 | +0.000008 | +0.000007 |
| ai_06 | -0.000013 | -0.054609 | -0.000225 | -0.009026 |
| ai_07 | +0.000807 | -0.000957 | +0.000065 | -0.000495 |
| ai_08 | -0.000001 | -0.000002 | +0.000007 | -0.000018 |
| ai_09 | +0.000000 | -0.000003 | -0.000001 | -0.000071 |
| ai_10 | +0.000427 | +0.000262 | +0.000125 | -0.006302 |

See scores.csv for deltas versus both original and control, timings, dimensions, and hashes; run.json records exact inputs and environment. validation.json checks all case geometries and timing. Earlier four-clip experiments are preserved in milestone1/ and milestone2/.

Control-relative differences help isolate spatial edits, but are not a causal decomposition: encoding interacts with image content and resolution. Compression versus control compares CRF 35 and CRF 18 encodes. This convenience sample does not establish accuracy, low-FPR performance, calibration, or population robustness. Dataset labels are inherited, not independently audited. Possible training overlap is unknown.
