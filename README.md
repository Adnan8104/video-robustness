# Video Robustness

Paired robustness tests for pretrained AI-generated video detectors.

Runs AEGIS on real and generated clips, then compares scores after compression,
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

## Sources

Uses [AEGIS](https://huggingface.co/MusapYildiz/aegis-video-detector) and clips from
[ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid). Vendored detector code
retains its [MIT license](vendor/aegis/LICENSE). Dataset media are not redistributed.
