# Demo implementation checks

The local upload pipeline reproduces the existing centered scores exactly on two public sample clips.
The five vendored AEGIS source files also match their pinned upstream revision byte for byte.
This verifies the implementation on those samples; it does not establish accuracy on arbitrary uploads.

## Checks

- All five source files match upstream commit `d86a774fd971954a023e1cd00ed7ff5b2575e0d1`.
- Both model checkpoints match their recorded SHA256 hashes; adapters load weights strictly.
- AEGIS's native `load_video` path, with the centered four-second window explicitly selected, produces the
  same normalized tensor as the upload path on both clips.
- Direct native-model outputs match the upload score, fused logit and all three component scores exactly.
- Both models' centered scores, logits, sampled indices and RGB/tensor hashes match the previous smoke
  report's `original` condition: four model/clip combinations.
- Three-section mode makes twelve model/window measurements. The centered result stays unchanged.

## Section scores

| Clip | Label | Section | AEGIS | WaveRep |
|---|---|---|---:|---:|
| real_01 | real | beginning | 0.1412 | 0.0002 |
| real_01 | real | middle | 0.9664 | 0.0002 |
| real_01 | real | end | 0.9729 | 0.0002 |
| ai_01 | AI | beginning | 1.0000 | 0.6745 |
| ai_01 | AI | middle | 1.0000 | 0.4914 |
| ai_01 | AI | end | 1.0000 | 0.4911 |

These are previously selected clips, not a new accuracy benchmark. AEGIS already flags the middle and
end of this known-real sample above the reference midpoint. Its lower beginning score shows why a single
window is an incomplete description of a video, but it does not identify the cause of the error. The AI
sample is five seconds long, so its three windows overlap heavily. No scores are averaged and no thresholds
are tuned on these clips. Component scores are diagnostic learned heads, not causal explanations.

The user's uploaded video is not included: temporary upload files are deleted after scoring. Its false
positive remains unexplained until the video is checked again.

## Reproduce

Download the smoke sources and weights first, then run:

```sh
uv run python run.py experiment configs/experiments/smoke.json
uv run python scripts/verify_demo.py
```

The verification script reads the pinned upstream source over HTTPS, loads both actual checkpoints and
recreates [validation.json](validation.json). That file records exact hashes, full numerical outputs and
frame indices. No media or model weights are published. The comparison reference is
[the smoke CSV](../experiments/smoke/scores.csv).
