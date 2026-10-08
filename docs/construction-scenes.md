# Construction scene comparison

WaveRep caught two of the three new generated clips. AEGIS and the AIGVDet RGB
branch caught none, and all three missed the same Sora clip. Similar subject
matter did not remove the detection failures.

Six new clips: three real camera recordings and three AI-generated construction
scenes. Each origin has two ground views and one elevated view, all in daylight.
Selection and analysis were committed before any scores. Models received the
same centered four-second/16-frame window from each unchanged source file.

| Detector | AI clips caught at 0.5 | Real clips wrongly flagged at 0.5 |
|---|---:|---:|
| AEGIS | 0/3 | 0/3 |
| WaveRep | 2/3 | 0/3 |
| AIGVDet RGB branch | 0/3 | 1/3 |

These counts use the fixed, uncalibrated 0.5 reference. They are not population
accuracy estimates or evidence that WaveRep is ready to authenticate uploads.

![Three-model construction scene scores](../reports/experiments/construction-scenes/pairs.png)

## The shared miss

`construction_ai_02` is a Sora 2 Pro scene containing cranes, excavators, a mixer
and workers. AEGIS scored it 0.001518, WaveRep 0.001390, and AIGVDet RGB about
3.24e-8. All three treated it as real-like. The source curator identifies every
SynthSite clip as fully generated; its hazard labels describe safety, not origin.

WaveRep scored the other Sora clip 0.573257 and the Veo 3.1 clip 0.999419.
The Sora score is close to the reference and cannot be read as a calibrated
probability. AIGVDet RGB gave the real 2019 tower-crane clip 0.992684. A high
score still does not establish that footage is generated.

## Agreement does not recover it

| Required agreement | Correct agreed | Wrong agreed | Inconclusive | All clips |
|---|---:|---:|---:|---:|
| AEGIS + WaveRep | 3 | 1 | 2 | 6 |
| All three | 2 | 1 | 3 | 6 |

AI-like requires all selected models >=0.5, real-like requires all below 0.5;
otherwise the result is inconclusive. Both rules still agree incorrectly on the
shared Sora miss. Adding the RGB branch makes one more real clip inconclusive,
without removing that error. Inconclusive clips are not counted as correct.

## Sources and matching

| Real source | Camera author | Documented date | License |
|---|---|---|---|
| [Ambérieux construction crane](https://commons.wikimedia.org/w/index.php?oldid=805766832) | Benoît Prieur | 2022-01-04 | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) |
| [Beynost sports-site crane](https://commons.wikimedia.org/w/index.php?oldid=1032231965) | Benoît Prieur | 2019-08-04 | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) |
| [Prague rail crane loading a site cabin](https://commons.wikimedia.org/w/index.php?oldid=836118434) | ŠJů, Wikimedia Commons | 2015-01-10 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

The AI clips are two Sora 2 Pro and one Veo 3.1 file from the pinned
[SynthSite author card](https://huggingface.co/datasets/govtech/SynthSite/blob/2904ec01c3dbf2efba09f2cb1b7bdf17841d4d39/README.md).
All six source hashes are new to this project. Original files stay local; no media
or frames are redistributed. The real files retain their original WebM bytes.

This is **coarse scene/viewpoint matching**, not exact real/generated scene pairs.
The actual center crops were reviewed before scoring. They preserve some crane
structure but can remove the hoist, workers or most of the ground worksite. The
rail-crane crop largely shows its cabin/body; the generated mixer scene crop
emphasizes vehicles. Framing, machinery type, lighting, codecs, resolution and
source histories remain different across origins. We cannot isolate construction
content, codec effects or generator shift as the cause of an error.

## What this changes

Keep the default demo and its uncertainty language. The RGB candidate remains
unsuitable as an upgrade on these checks. WaveRep supplied two useful AI signals
here, but it shares a new miss and retains its earlier false-positive and
compression failures. No threshold was fitted and no model was trained.

The next useful model test should add a different temporal signal and require
recovery of the shared Sora and Wan misses without new real-video errors. Any
improvement needs confirmation on additional sources before a demo change.

## Verification

See the [saved checks](../reports/experiments/construction-scenes/validation.json),
[media timing audit](../reports/experiments/construction-scenes/media-timing-audit.json)
and [native RGB-branch audit](../reports/experiments/construction-scenes/native-adapter-audit.json).
Source, checkpoint and code hashes, complete pairing, shared RGB inputs and
independent CSV error/coverage analysis are checked. Full FFmpeg and OpenCV frame
counts agree; sampled presentation times differ from nominal timing by less than
one millisecond on these files, with all six records matching the pre-scoring
audit. Native RGB-branch outputs match exactly on three clips. Reloading all
three models reproduced all outputs and input hashes exactly for 15 selected
scores, including all generated clips, a correct real control and the flagged
real clip. Stored logits reproduce all 18 final scores under their recorded
aggregation rules (AEGIS sigmoid tolerance 1e-7; the other two exact).

[Every score and logit](../reports/experiments/construction-scenes/scores.csv) ·
[Predeclared selection](../configs/construction-scenes-selection.md) ·
[Candidate audit](../configs/construction-scenes-candidate-audit.json) ·
[How to reproduce](experiments.md#check-similar-construction-scenes).
