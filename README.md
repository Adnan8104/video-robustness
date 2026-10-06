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

The first download includes a ~433 MiB pretrained checkpoint and four short clips.
Inference runs on CPU. Model weights, videos, and the local environment are excluded from Git.

## Initial result

Four source clips, five conditions, 20 scored cases. One source-labeled real clip
shows sensitivity to compression strength:

| Original | Encode control (CRF 18) | Compression (CRF 35) |
|---:|---:|---:|
| 0.966411 | 0.981128 | 0.023794 |

Higher scores mean more AI-like according to AEGIS; they are not calibrated
probabilities. This small sample does not establish detector accuracy.

[Full comparison](reports/comparison.md) · [Experiment notes](reports/experiment-log.md) · [Methodology](docs/methodology.md)

## Sources

Uses [AEGIS](https://huggingface.co/MusapYildiz/aegis-video-detector) and clips from
[ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid). Vendored detector code
retains its [MIT license](vendor/aegis/LICENSE). Dataset media are not redistributed.
