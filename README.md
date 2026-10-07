# Video Robustness

Paired robustness tests for pretrained AI-generated video detectors.

Runs pretrained detectors on real and generated clips, then compares scores after compression,
resizing, cropping, and an encode-only control. No model training is required.

## Quick start

Requires Python 3.11 and [uv](https://docs.astral.sh/uv/). From this repository:

```sh
uv sync --locked
uv run python run.py fetch
uv run python run.py run
uv run python run.py check
```

The first download includes a ~433 MiB pretrained checkpoint and 20 short clips (~71 MiB total).
Inference runs on CPU. Model weights, videos, and the local environment are excluded from Git.

## Expanded experiment

20 source clips: 10 real MSVD, 5 Sora, and 5 Veo clips. Five conditions produce
100 scored cases. The manifest was frozen before expanded scoring.

The original real clip's large compression drop did not repeat on the 16 newly
selected clips. Their largest control-relative changes were +0.072 for a resized
real clip, −0.055 for a compressed Veo clip, and +0.053 for a cropped Sora clip.

Higher scores mean more AI-like according to AEGIS; they are not calibrated
probabilities. This convenience sample does not establish detector accuracy.

[Results summary](reports/summary.md) · [All scores](reports/comparison.md) · [Experiment notes](reports/experiment-log.md) · [Methodology](docs/methodology.md)

## Diagnostic follow-up

49 additional cases: five compression strengths on four diagnostic clips, plus
five real DAVIS clips. The original failure drops sharply at stronger compression;
a new DAVIS bear clip shows a similar drop (0.993 → 0.237).
[Plots and findings](reports/diagnostics/report.md) · [Validation](reports/diagnostics/validation.json)

Reproduce this follow-up with `uv run python run.py diagnose` (~14 MiB of new media).

## Two-detector comparison

Compare AEGIS with WaveRep on the same frames, including ten fresh clips:
`uv run python run.py compare`. This adds ~331 MiB of model weights and ~42 MiB
of media. WaveRep uses sparse frame sampling and its native crop/pad preprocessing.
Across 35 clips, it avoids the known real-clip high scores but loses several
generated-video signals under compression. AEGIS also makes errors on fresh originals.
[Comparison report](reports/two-detectors/report.md) · [Selection](configs/two-detectors-selection.md)

## Balanced content check

Twenty fresh clips, five each: real animal, real non-animal, Veo animal, and Veo
non-animal. Common four-second, 504×504, 24 fps preparation avoids upscaling and
WaveRep padding. Both detectors score independent CRF 18/35 encodes: 80 scores.
Both put one real kitten above the fixed midpoint in both conditions. WaveRep
has large compression changes on 9/10 generated clips. These are descriptive
findings on this panel, with uncalibrated scores.

Reproduce with `uv run python run.py controlled` (~263 MiB of source media).
[Paired chart and findings](reports/controlled/report.md) ·
[Selection rules](configs/controlled-selection.md) · [Content audit](configs/controlled-candidate-audit.json).
This small panel tests recurrence; it cannot establish a causal animal effect.

## Four-clip failure study

Check original files and medium compression on the real kitten, a real horse,
an AI elephant and an AI sunset scene. Adds CRF 23/28 to the prepared 18/35
endpoints: 40 score rows, with 24 new scores when the endpoints match.
The kitten crosses the midpoint after preparation in both models. WaveRep drops
below it between CRF 23–28 for the AI elephant and CRF 18–23 for the AI sunset
scene. These transitions are specific to the selected clips.

Run `uv run python run.py followup`.
[Chart and findings](reports/failure-followup/report.md) ·
[Frozen diagnostic selection](configs/failure-followup-selection.md).
Original-to-prepared comparisons measure the whole preparation recipe; the CRF
curve keeps that preparation fixed.

## Isolating the kitten preparation steps

Hold source-frame identities fixed while testing resizing, cropping, encoding
and their combinations. Compare a second frame list traced through the FPS
conversion, a metadata-only FPS control and the exact prepared endpoint: 36 scores.
On fixed original frames, crop alone flips AEGIS across the midpoint; resize
alone flips WaveRep. This is a finding about the selected kitten clip.

Run `uv run python run.py isolate`.
[Step chart and findings](reports/kitten-isolation/report.md) ·
[Frozen controls and frame checks](configs/kitten-isolation-selection.md).
This isolates conditional pipeline effects on one clip without claiming a
learned animal/texture mechanism.

## Sources

Uses [AEGIS](https://huggingface.co/MusapYildiz/aegis-video-detector) and clips from
[ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid) and DAVIS clips via
[VLM4D](https://huggingface.co/datasets/shijiezhou/VLM4D), plus
[WaveRep](https://github.com/grip-unina/WaveRep-SyntheticVideoDetection).
WaveRep is for informational/nonprofit use; its [license](vendor/waverep/LICENSE.md)
and author attribution are retained. AEGIS vendored detector code
retains its [MIT license](vendor/aegis/LICENSE). Dataset media are not redistributed.
