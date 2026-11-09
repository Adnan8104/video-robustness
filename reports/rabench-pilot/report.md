# A new cutoff did not fix the compression misses

On eight held-out RA-Bench pairs, both fitted cutoffs made the same decisions
as 0.5. Stronger compression made WaveRep miss **8/8** generated clips, up from
**3/8**. AEGIS missed **7/8** in both conditions. Neither flagged a real clip.

## Test results

Counts below apply to both 0.5 and the locked cutoffs.

| Model | CRF 18: real flagged | CRF 18: AI missed | CRF 35: real flagged | CRF 35: AI missed |
|---|---:|---:|---:|---:|
| AEGIS | 0/8 | 7/8 | 0/8 | 7/8 |
| WaveRep | 0/8 | 3/8 | 0/8 | 8/8 |

All eight generated clips lost at least 0.10 on WaveRep under stronger
compression. Five crossed both cutoffs in the wrong direction. For example,
one LTX clip went from **0.999 to 0.001**. None of the 16 AEGIS scores changed
by 0.10, but that stability did not make it a good detector on these clips:
it already missed seven generated clips at CRF 18.

## How the cutoffs were chosen

On the first eight pairs, each rule could flag at most one real clip. We
chose the cutoff that caught the most AI clips within that budget, then
committed the exact values before test inference.

| Model | Fitted cutoff (rounded) | Real flagged: 0.5 → fitted | AI missed: 0.5 → fitted |
|---|---:|---:|---:|
| AEGIS | 0.998687 | 3/8 → 1/8 | 6/8 → 7/8 |
| WaveRep | 0.256095 | 1/8 → 1/8 | 2/8 → 1/8 |

WaveRep's one extra catch on the cutoff group did not carry over to the test
group. Neither change qualified as an improvement under the
[fixed rule](../../configs/rabench-selection.md). The demo still shows the
original model scores.

## What this test covers

The two groups have different source recordings and subcategories. Each group
has eight real anchors and their generated counterparts, four from LTX and
four from Kling v3. CRF 18 and CRF 35 start directly from the same source;
within each clip, geometry and the 16 sampled frame positions stay fixed.
Across clips, resolution, frame rate and source pipelines still differ.

All 32 sources passed hash, decode and timing checks. All 96 score rows
matched the preflight encodes and sampled indices. This is a small pilot on
one dataset: 0/8 real flags does not establish a reliable false-positive
rate. The cutoffs apply to raw scores, which are not probabilities.

[Exact cutoffs](cutoffs.json) · [Paired crossings](summary.json) ·
[Input checks](input-checks.json) ·
[Cutoff scores](../experiments/rabench-cutoff/scores.csv) ·
[Test scores](../experiments/rabench-test/scores.csv) ·
[Reproduce](../../docs/experiments.md#test-frozen-cutoffs-on-separate-footage)
