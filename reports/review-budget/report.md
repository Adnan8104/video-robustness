# The trained head put 5 AI clips in the top 10

Both models ranked the same batch of 100 heavily compressed videos. The
trained WaveRep head surfaced **5 of the 10** Veo 3 clips in ten review
slots. Released WaveRep surfaced **3 of the 10**.

| Model | AI clips in top 10 | Real clips in top 10 | AI clips outside top 10 |
|---|---:|---:|---:|
| Released WaveRep | 3 | 7 | 7 |
| Trained WaveRep head | 5 | 5 | 5 |

The trained head freed two review slots for AI clips. Half its queue
was still real footage, and half of the Veo 3 clips fell below the
review budget. The local demo now has an experimental review mode that
ranks a batch for a person to check.

## How the test was run

The [plan](../../configs/review-budget-selection.md) fixed the batch
and review budget before scoring. The 100 clips came from
[ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid): 90 real
MSVD clips and ten Veo 3 clips. There are 94 native 720p files and six
native 1080p files, all six from MSVD. The models saw the same 16 frames
from each four-second, 504 × 504 H.264 CRF 35 encode. Ranking used raw
scores, with source hashes breaking ties. There was no cutoff fitting.

The trained head was fitted earlier on RA-Bench. This test uses one
source collection per class and one generator at a 10% generated mix.
That mix and the counts apply to this batch. An independent check
verified the 100 input and sampled-frame hashes and recomputed both queues
from the saved scores. The demo matched the saved margins on three clips.

[Scores](scores.csv) · [Ordered queues](summary.json) ·
[Input manifest](../../configs/review-budget.json) ·
[Reproduce](../../docs/experiments.md#rank-100-clips-for-ten-review-slots)
