# Video Robustness

[![Tests](https://github.com/Adnan8104/video-robustness/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Adnan8104/video-robustness/actions/workflows/ci.yml)

A Python project to test how well existing models detect AI-generated videos,
and what happens after compression, resizing or cropping.

It compares AEGIS, WaveRep and AIGVDet's RGB branch. There's also a local upload
demo and a lightweight D3 experiment looking at changes between frames.

## Key findings

- Compression made WaveRep miss more AI clips: **4/10 before, 9/10 after** on the 20-clip panel.
- Resizing pushed one real video's AEGIS score from **0.0005 to 0.839**.
- On later tests, adding a third model didn't fix the shared misses. D3 helped separate some cases, but the result changed with the time window.

![Scores before and after compression](reports/experiments/compression/compression-pairs.png)

These are small tests. Scores aren't confidence percentages, and 0.5 is only a
comparison point, not a validated cutoff.

## Try the demo

Requires Python 3.11 and uv.

```sh
uv sync --locked --extra demo
uv run --extra demo python run.py demo
```

Open `http://127.0.0.1:8501`, upload a short video and click **Check video**.
It runs AEGIS and WaveRep locally. Temporary uploads are deleted after the check.
The first run downloads about 764 MiB of model weights.

## Run an experiment

```sh
uv run python run.py experiment configs/experiments/compression.json
uv run python run.py check
```

The 20-clip experiment compares original, compressed, resized and cropped inputs:
**160 scores** across two models. Add `--dry-run` to check a config first.

The shared runner checks file hashes and saves scores, charts and run details
under `reports/experiments/`. Models and videos stay out of Git. There are
**55 tests**, with tests and config checks running in GitHub Actions.

[Setup and configs](docs/experiments.md) · [Model comparison](docs/detector-evaluation.md) · [Sources and credits](docs/sources.md)
