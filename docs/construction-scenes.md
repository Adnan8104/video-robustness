# Construction footage check

WaveRep caught two of three AI construction videos. The other two models caught
none, and all three missed the same Sora clip.

We used six new videos: three camera recordings and three generated scenes. Each
group had two ground views and one elevated view. The models saw 16 frames from
the same centered four-second window, with the original files left unchanged.

| Detector | AI clips caught / 3 | Real clips flagged / 3 |
|---|---:|---:|
| AEGIS | 0 | 0 |
| WaveRep | 2 | 0 |
| AIGVDet RGB branch | 0 | 1 |

Counts use the fixed 0.5 comparison point, not a calibrated cutoff.

![Construction video scores](../reports/experiments/construction-scenes/pairs.png)

## The errors

The shared miss, `construction_ai_02`, scored 0.001518 with AEGIS, 0.001390 with
WaveRep and about 3.24e-8 with AIGVDet RGB. All three placed this generated clip
on the real-like side. Requiring agreement didn't help.

AIGVDet RGB also gave a real 2019 crane video a score of 0.992684. Adding it made
one more real clip inconclusive without fixing the shared miss.

The real recordings come from Wikimedia Commons and date from 2015, 2019 and
2022. The AI clips are two Sora 2 Pro videos and one Veo 3.1 video from SynthSite.
Its hazard labels describe safety conditions; every clip is generated.

The scenes broadly match, but they aren't exact real/generated pairs. Lighting,
codecs and framing differ, and the models' center crops can leave out workers or
machinery. This test doesn't tell us which of those differences caused an error.

## Checks

All 18 scores passed the saved checks. Fifteen repeated scores matched exactly,
as did native RGB-branch inference on three clips. Independent decoder checks
matched frame counts, with sampled timing within 1 ms. Selection was committed before scoring.

[Full results and checks](../reports/experiments/construction-scenes/report.md) ·
[Sources and credits](sources.md) · [Follow-up with D3](temporal-candidate.md)
