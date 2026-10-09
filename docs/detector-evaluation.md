# Detector comparison

Adding AIGVDet's RGB branch didn't fix the two AI clips that AEGIS and WaveRep
both missed. It also flagged a real video. The demo still uses AEGIS and WaveRep.

On the separate 20-clip source panel:

| Detector | Real clips flagged / 10 | AI clips missed / 10 |
|---|---:|---:|
| AEGIS | 1 | 5 |
| WaveRep | 0 | 3 |
| AIGVDet RGB branch | 1 | 7 |

These counts use 0.5 as a comparison point. They don't establish an overall model
ranking. Each model saw the same 16 frames from a centered four-second window.

We tried the RGB branch because it uses ResNet50, a different feature extractor
from the two DINOv2-based models. This check uses sampled frames and leaves out
AIGVDet's optical-flow branch; it doesn't test the full paper method.

Requiring all three models to agree still left two wrong answers. It increased
inconclusive results from five to seven. Agreement alone didn't solve the problem.

## Later checks

On six construction clips, WaveRep caught two of three AI videos. AEGIS and
AIGVDet RGB caught none. All three missed the same Sora clip, and the RGB branch
flagged one real recording.

D3's lightweight temporal check gave AUC 0.911 with a four-second window and
0.834 with a two-second window. AUC measures score ordering, not detection
accuracy. Neither setting cleanly separated all three shared misses from every
real control.

The next model needs to help with those misses without adding real-video errors.
If it does, we'll need separate footage to choose a cutoff and test it.

## Checks

All 60 scores passed input, weight and code checks. The 40 AEGIS/WaveRep scores
matched the earlier run exactly. The RGB adapter matched author inference on
three clips, and six repeated RGB scores matched after reloading the model.

The footage is a small sample with repeated scenes and different sources, codecs
and viewpoints. It can't tell us how a detector will perform on arbitrary uploads.

[Full three-model results](../reports/experiments/third-detector/report.md) ·
[Construction test](construction-scenes.md) · [D3 test](temporal-candidate.md)
