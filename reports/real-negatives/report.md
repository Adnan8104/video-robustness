# Extra real footage did not reduce false flags

On eight fresh RA-Bench pairs, the original trained head and the refit
caught the same **4/8** heavily compressed AI clips and wrongly flagged
the same **2/8** real clips. The refit added one false flag at lighter
compression and missed the same two AI clips.

| Classifier | CRF 18: real flagged | CRF 18: AI missed | CRF 35: real flagged | CRF 35: AI missed |
|---|---:|---:|---:|---:|
| Released WaveRep | 0/8 | 5/8 | 0/8 | 8/8 |
| Original trained head | 1/8 | 2/8 | 2/8 | 4/8 |
| Trained with extra real clips | 2/8 | 2/8 | 2/8 | 4/8 |

At CRF 35, correct AI–real score orderings were **34/64**, **48/64** and
**49/64**, respectively. The new fit made only one additional correct
ordering compared with the original trained head. These comparisons share
clips and are not independent trials.

## What changed

The [selection policy](../../configs/real-negatives-selection.md) adds all
16 real recordings from the two earlier trained-head tests, including
the four compressed real clips the original trained head flagged. Both
encodes of each addition enter training. The encoder, frame sampling,
ridge penalty and decision margin stayed fixed. Each class contributed
half of the fit loss, so adding real clips did not increase the class's
total weight. The fit was locked in `f56ebeb` before test inference.

The new test used eight previously unscored recording IDs: four LTX and
four Kling v3 scene pairs. The 32 encodes share the same 504 × 504
geometry, 24 fps and four-second duration. All heads used the same
16 sampled frames per encode. Training and test use the same dataset
and generators, so this does not establish transfer to another source.

## Checks and decision

The original features matched the saved hash and reproduced the original
fit within numerical precision. The extra inputs matched 32 earlier
encode hashes, frame hashes and released scores. An independent check
verified the weighted fit, the hashes and full decodes of all 32 test
encodes, and the counts computed from the 96 classifier margins.

The refit failed the predeclared target of reducing false flags while
keeping AI catches. The demo remains unchanged. The original trained
head still found four heavily compressed clips that released WaveRep
missed. Before another fit, broaden the footage to a different source
or generator and set aside enough real recordings to measure false flags.

[Locked fit](fit.json) · [Per-clip margins](scores.csv) ·
[Exact counts](summary.json) ·
[Reproduce](../../docs/experiments.md#train-with-extra-real-footage)
