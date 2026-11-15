# The compression gains carried over to Veo 3

The original head trained on RA-Bench caught **10/12** heavily compressed
Veo 3 clips on ComGenVid. Released WaveRep caught **0/12** on the same
inputs. The trained head also wrongly flagged **3/12** camera clips,
while the released head flagged none. It missed the predeclared target
of improving catches without adding false flags.

| Classifier | CRF 18: real flagged | CRF 18: AI missed | CRF 35: real flagged | CRF 35: AI missed |
|---|---:|---:|---:|---:|
| Released WaveRep | 0/12 | 2/12 | 0/12 | 12/12 |
| RA-Bench trained head | 2/12 | 2/12 | 3/12 | 2/12 |

At CRF 35, the trained head ranked AI above real in **129/144**
comparisons, versus **110/144** for released WaveRep. At CRF 18,
ordering went from **140/144** to **135/144**. These comparisons share
24 clips and are not independent trials. At light compression, each
head caught ten AI clips, with one different catch apiece.

## What this test covers

The trained head was fitted on LTX and Kling v3 outputs and real
RA-Bench recordings. The [fixed test plan](../../configs/head-transfer-selection.md)
used 12 fresh Veo 3 clips and 12 MSVD camera clips from
[ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid).
ComGenVid was used in earlier baseline studies; this test excludes
prior file paths, hashes and MSVD recording IDs. No part of this
panel was used to fit the head or choose the cutoff.

All sources start at 1280 × 720. Both classifiers see the same 16
frames per encode, after standardizing each source to 504 × 504,
24 fps and four seconds. Each compression level starts from the same
lossless master. Original frame rates, scenes and recording pipelines
are not matched between real and AI. The result is evidence of transfer
on this particular dataset and generator, not a general error rate.

## Checks and decision

The original weights and scoring code passed hash checks. Extracted
features reconstructed released WaveRep logits exactly. The 48 encode
hashes and independent full decodes passed, and the 96 saved margins
reproduced both error counts and all ordering counts.

The demo stays unchanged. Detecting more compressed clips on a different
dataset is useful evidence, but three real clips were still flagged.
Before considering deployment, measure that tradeoff on a larger,
independent real-footage set.

[Per-clip margins](scores.csv) · [Counts and provenance](summary.json) ·
[Reproduce](../../docs/experiments.md#check-transfer-to-comgenvid)
