# The trained head flagged 3 of 30 real clips

On 30 new camera recordings, the original RA-Bench trained head
wrongly flagged **3/30** clips at each compression level. Released
WaveRep flagged **2/30** at CRF 18 and **0/30** at CRF 35.

| Classifier | CRF 18: sports | CRF 18: vlogs | CRF 18: total | CRF 35: sports | CRF 35: vlogs | CRF 35: total |
|---|---:|---:|---:|---:|---:|---:|
| Released WaveRep | 2/20 | 0/10 | 2/30 | 0/20 | 0/10 | 0/30 |
| RA-Bench trained head | 3/20 | 0/10 | 3/30 | 1/20 | 2/10 | 3/30 |

The trained head's three CRF 18 flags cleared at CRF 35, while three
different clips crossed the cutoff in the other direction. It did not flag
any recording at both levels. The equal totals conceal a change in which
clips are misclassified.

## What was tested

The [fixed plan](../../configs/false-flags-selection.md) selected 20 sports
and 10 vlog clips from the 2019
[YouTube UGC research dataset](https://research.google/pubs/youtube-ugc-dataset-for-video-compression-research/).
The clips have 30 distinct credited creators. Selection used the published
catalog, technical eligibility and sampled-frame review before any detector
run. The source clips are already VP9 encodes. Each new H.264 encode starts
from the same 504 × 504, four-second lossless master at 24 fps. Both heads
see the same 16 frames and flag at margin zero.

The original weight and encoder hashes passed, and captured features
reconstructed released logits exactly. Independent checks verified the
60 encode hashes, frame counts, dimensions and timing, then recomputed the
paired results from all 120 margins. The manifest retains source generations
and creator credits. Videos, review frames and model weights stay local.

## What it means

The [ComGenVid transfer test](../head-transfer/report.md) showed a benefit:
the trained head caught 10 heavily compressed Veo 3 clips that released
WaveRep missed. This separate audit shows a real cost: three camera clips
were wrongly flagged after heavy compression. The samples cover two
categories and are not representative of all uploads; 3/30 is the observed
count here, not a deployment false-positive rate. There are no generated
clips in this audit. The demo stays unchanged.

[Per-clip margins](scores.csv) · [Counts and transitions](summary.json) ·
[Sources and credits](../../configs/false-flags.json) ·
[Reproduce](../../docs/experiments.md#measure-false-flags-on-independent-camera-clips)
