# A stricter cutoff lost the extra AI catches

On eight new scene pairs, the trained head at zero caught **4/8** heavily
compressed AI clips and wrongly flagged **1/8** real clips. Raising the
cutoff removed that false flag and lost all four catches.

| Rule | CRF 18: real flagged | CRF 18: AI missed | CRF 35: real flagged | CRF 35: AI missed |
|---|---:|---:|---:|---:|
| Released WaveRep | 0/8 | 5/8 | 0/8 | 8/8 |
| Trained head, margin 0 | 2/8 | 3/8 | 1/8 | 4/8 |
| Trained head, stricter cutoff | 0/8 | 6/8 | 0/8 | 8/8 |

The trained head still ranked compressed AI above real in **52/64**
comparisons, versus **33/64** for released WaveRep. Changing the cutoff
does not change that ranking. These comparisons share 16 clips and do
not establish a population error rate.

## How we checked it

The [previous test scores](../linear-head/scores.csv) became development
data for this follow-up. The [fixed selection rule](../../configs/head-cutoff-selection.md)
allowed at most one real flag per compression level there. It selected
a margin of 0.48477551234743466, which kept one of four compressed AI
catches in development and none in the new test. The cutoff was
committed in `1065369` before the new clips were scored.

The test uses eight fresh RA-Bench pairs, four LTX and four Kling v3.
Original recording IDs, parent anchors and file hashes were checked
against the earlier RA-Bench panels. The three rules used the same
16 frame positions per encode. The original head weights were checked
by hash, and the captured features exactly reconstructed released logits.
All 32 encode hashes and the error and ranking counts were verified.

The stricter rule did not meet the predeclared target of keeping at
least two compressed AI catches. Keep the demo unchanged. Before
another cutoff search, test whether adding diverse real training
footage, including compressed real clips the head tends to flag, helps
separate the classes on fresh recordings.

[Locked rule](cutoff.json) · [Per-clip results](scores.csv) ·
[Counts and provenance](summary.json) ·
[Reproduce](../../docs/experiments.md#check-a-stricter-cutoff-on-new-recordings)
