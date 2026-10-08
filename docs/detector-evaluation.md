# What the additional-source test tells us

Neither detector is ready to give a reliable authenticity verdict. On this pilot,
WaveRep made fewer wrong calls at 0.5, and both models missed the same two generated clips.

Twenty new source clips: ten real (Ego4D and YouTube-VOS) and ten AI-generated
(Cosmos and Wan 2.2-14B). Original bytes, centered four-second/16-frame sampling,
unchanged pretrained weights. Clips and analysis were fixed before scoring.

| Detector | Real clips with high AI-like scores | Generated clips with low AI-like scores |
|---|---:|---:|
| AEGIS | 1/10 | 5/10 |
| WaveRep | 0/10 | 3/10 |

AEGIS gave a real owl clip 0.999404, yet missed all five Wan clips. WaveRep missed
one Cosmos clip and two Wan clips. This behavior shows why a single high or low score
cannot be treated as proof of a video's origin.

## Does requiring agreement help?

The fixed rule gives AI-like only if both scores are >=0.5, real-like only if both
are below 0.5, and otherwise inconclusive. On this panel it returned:

- 13 agreed results consistent with source labels: nine real and four AI clips.
- Two agreed real-like results for generated Wan clips.
- Five inconclusive clips: one real and four generated.

The unresolved clips are kept in the denominator. Agreement reduces some wrong
calls by declining to answer, but also leaves generated clips undetected. It does
not repair shared failures, and agreement cannot be presented as authentication.

## What to improve next

Keep the frozen panel as a regression check. Compare a pretrained detector that
uses a different feature extractor or detection signal; both current adapters use
DINOv2 features. Require the candidate to recover the shared misses without adding
real-footage errors, then confirm on separately selected clips before accepting it.
This is the next model-comparison milestone; it has not been achieved yet.

Expand the confirmation clips with real construction footage alongside generated
construction footage, plus additional camera viewpoints and creators. This checks
whether apparent improvements depend on scene content rather than origin.
Threshold calibration requires separate labeled development data and a held-out test.
We have not fitted a threshold, trained a model or changed the demo's verdict policy.

## Limits and verification

These are clip counts from a convenience pilot. Source, content, encoding and viewpoint
are different across groups. Five Ego4D clips show two room setups; three Wan clips
share a construction scene. Files are new to this project, but original-video grouping
and checkpoint training overlap are unknown. The pilot cannot establish a population
error rate, statistical independence or an overall model ranking. The 0.5 reference
is uncalibrated, and WaveRep uses a central crop and 16 frames rather than full-video
inference.

All 40 scores passed source/checkpoint/code hash checks, complete pairing, unique
frame sampling and raw score-arithmetic checks. Eleven representative errors,
disagreements and controls reproduced exactly after two fresh model loads.
Source videos and inspection frames remain local.

[Complete scores and chart](../reports/experiments/source-panel/report.md) ·
[Selection policy](../configs/source-panel-selection.md) ·
[Candidate audit](../configs/source-panel-candidate-audit.json) ·
[Verification](../reports/experiments/source-panel/validation.json)
