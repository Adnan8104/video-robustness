# Which detector helped?

The third candidate did not improve this panel. AIGVDet's RGB branch missed both
shared Wan failures and added a real-video error, so it remains an evaluated baseline.
The demo continues to use AEGIS and WaveRep; neither provides a reliable authenticity verdict.

Twenty frozen source clips: ten real (Ego4D and YouTube-VOS) and ten generated
(Cosmos and Wan 2.2-14B). All models received the same centered four-second/16-frame
window from unchanged source bytes, with their own native spatial preprocessing.
The 0.5 reference was fixed; no thresholds or weights were fitted.

| Detector | Real clips scored AI-like | Generated clips scored real-like |
|---|---:|---:|
| AEGIS | 1/10 | 5/10 |
| WaveRep | 0/10 | 3/10 |
| AIGVDet RGB branch | 1/10 | 7/10 |

AEGIS flagged a real owl clip and missed all five Wan clips. WaveRep missed one
Cosmos clip and two Wan clips. AIGVDet RGB flagged one real painting clip and
missed two Cosmos clips and all five Wan clips. Counts describe this panel, not
an overall model ranking.

## Why this candidate

Both existing adapters use DINOv2. AIGVDet's released RGB branch uses a ResNet50
convolutional network, giving us a different feature extractor with existing CPU
dependencies. We loaded the full trained branch strictly, including its classifier.
It uses a 448×448 center crop, ImageNet-normalized RGB, and the mean of individual
frame probabilities.

The full AIGVDet method also uses a separately trained optical-flow branch. This
baseline omits that branch and uses 16 sampled frames rather than every frame,
so these results evaluate **our RGB-only sparse-frame adaptation**. They do not
establish how the full paper detector performs. [Author code and provenance](../vendor/aigvdet/ORIGIN.md).

The [predeclared criterion](../configs/third-detector-policy.md) required recovering
`panel_wan_04` and `panel_wan_05` without adding real errors relative to WaveRep.
The RGB branch gave those AI clips scores of approximately 1.67e-8 and 1.05e-7,
while giving a real control 0.789934. It failed that criterion. Matching native
inference rules out an adapter discrepancy on the audited clips; it does not
identify which visual feature causes the errors.

## Does agreement help?

AI-like requires every selected model >=0.5; real-like requires every model below
0.5; otherwise the result is inconclusive.

| Models required to agree | Correct agreed | Wrong agreed | Inconclusive | All clips |
|---|---:|---:|---:|---:|
| AEGIS + WaveRep | 13 | 2 | 5 | 20 |
| All three | 11 | 2 | 7 | 20 |

The same two generated Wan clips remain incorrectly real-like under either rule.
Adding this third model creates two more inconclusive clips without removing a
shared error. Inconclusive clips stay in the denominator. Agreement is not authentication.

## Additional construction check and next step

We also ran a [six-clip construction-scene check](construction-scenes.md) using new
camera footage and Sora/Veo clips, with the same broad viewpoint counts per origin.
WaveRep caught 2/3 new AI clips; AEGIS and AIGVDet RGB caught none. All three missed
one Sora clip, and the RGB branch flagged a real camera recording. Similar subject
matter did not remove the failures; source/codec/framing differences remain.

Keep both panels as regression checks. A temporal or optical-flow detector would
test a different signal from this RGB baseline. Require it to recover the shared
Sora and Wan misses without new real-video errors, then confirm on additional
sources before changing the demo.

Threshold calibration needs separate labeled development data and a held-out test.
We have not calibrated a threshold or trained a detector. A candidate passing this
known regression panel still needs confirmation on independently selected footage.

## Verification and limits

All 60 rows passed source/checkpoint/code hash checks, complete pairing, full decode,
unique frame sampling and independent CSV summaries/error counts. The existing 40
scores, logits, frame indices and input hashes matched the earlier source-panel run
exactly. All 20 RGB-branch scores passed independent probability-arithmetic checks.

On one real control and both shared misses, the adapter matched the pinned author
ResNet code exactly in preprocessing, all 16 logits, probabilities and aggregation.
Those fresh native outputs also matched the saved run. Six representative RGB-branch
errors, disagreements and correct controls reproduced every output and input hash
after another fresh load. The earlier two-model panel retains its eleven exact repeats.

Source, content, encoding and viewpoint differ across groups. Five Ego4D files show
two room setups, and three Wan files share a construction scene. Source videos are
new to this project, but original-video grouping and training overlap are unknown.
Twenty files are not twenty independent origins, and this convenience pilot cannot
establish a population error rate. Source videos, weights and inspection frames remain local.

[Complete three-model scores and chart](../reports/experiments/third-detector/report.md) ·
[Verification](../reports/experiments/third-detector/validation.json) ·
[Native audit](../reports/experiments/third-detector/native-adapter-audit.json) ·
[Earlier two-model panel](../reports/experiments/source-panel/report.md) ·
[Source selection policy](../configs/source-panel-selection.md).

## Temporal ranking follow-up

[D3's lightweight temporal check](temporal-candidate.md) is now complete on all
26 existing source/construction clips. AUC is 0.911 with the shared four-second
window and 0.834 with native-like two-second/8 fps timing. The raw temporal signal
is useful for ordering, but neither profile separates all three shared AI misses
from every real control. There is no fitted cutoff, classification error claim or
demo promotion. The main XCLIP version and released optical-flow branches remain
candidates for a next check; these lightweight results do not evaluate them.
