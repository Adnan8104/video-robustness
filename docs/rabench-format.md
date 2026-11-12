# Compression still caused misses after matching the format

WaveRep missed **3/8** generated clips at CRF 18 and **8/8** at CRF 35 on
fresh footage, even when real and generated clips had the same resolution,
frame rate and duration. Matching the format did not fix the failure.

| Detector | Real flagged, CRF 18 → 35 | AI missed, CRF 18 → 35 | AI scores above real scores, CRF 18 → 35 |
|---|---:|---:|---:|
| WaveRep | 3/8 → 0/8 | 3/8 → 8/8 | 51/64 → 40/64 |
| AEGIS | 2/8 → 2/8 | 7/8 → 7/8 | 37/64 → 39/64 |

Error counts use 0.5 as a reference. The last column compares each generated
score with each real score, regardless of cutoff. The 64 comparisons share
16 clips; they are not 64 independent trials.

WaveRep's score fell by at least 0.10 on all eight generated clips. Real
scores fell too, and only one compressed generated clip ranked above every
real clip. Within matched scenes, WaveRep still ranked the generated clip
higher in **7/8** pairs after compression, up from **6/8** at CRF 18. Some
relative signal remains when a matching real reference is available. That
does not make it a reliable standalone classifier.

## What was held fixed

Eight fresh RA-Bench scene pairs: four LTX and four Kling v3. No DVIDS
recording IDs or exact file hashes were reused from the prior pilot. The
[selection rule](../configs/rabench-format-selection.md) and
[manifest](../configs/rabench-format.json) were committed before scoring.

Every source was prepared as a four-second lossless 504 × 504 master at
24 fps. Both encodes started from that master, and both detectors saw
the same 16 frame positions. An independent decode checked geometry and
timing on all 32 encodes. All 64 scores passed input and summary checks.

The [earlier native test](../reports/rabench-pilot/report.md) used different
clips. This follow-up shows that the compression failure can happen with
matched output formats; it does not isolate aspect ratio or remove all
source and camera differences. The demo still uses the existing scores.
The [trained-head follow-up](../reports/linear-head/report.md) recovered
some compression misses on separate recordings but added false flags.

```sh
uv run python run.py experiment configs/experiments/rabench-format.json
uv run python scripts/verify_experiment.py configs/experiments/rabench-format.json
```

[Plots and scores](../reports/experiments/rabench-format/report.md) ·
[Ordering counts](../reports/experiments/rabench-format/format-comparison.json) ·
[Decode checks](../reports/experiments/rabench-format/encode-timing-audit.json)
