# Experiment configs

Run any supported experiment through the same pipeline:

```sh
uv run python run.py experiment configs/experiments/smoke.json
uv run python run.py experiment configs/experiments/compression.json --dry-run
```

## Config fields

| Field | Purpose |
|---|---|
| `schema_version` | `1`; rejects unknown versions and misspelled top-level fields. |
| `name` | Output folder name. Each run writes to `reports/experiments/<name>/`; media go to ignored `data/experiments/<name>/`. Rerunning a name replaces its generated outputs. |
| `manifest` | Existing JSON source list with pinned dataset revisions and SHA256 hashes. Relative paths start at the repository root. |
| `sample_ids` | Optional ordered subset of the manifest. Omit to use every clip. |
| `source_directory` | Local download cache under `data/`. A matching hash allows reuse. |
| `detectors` | Registered adapter names (currently `aegis` and `waverep`). Models load one at a time to limit memory. |
| `preparation` | `native` preserves source geometry/timing. `centered_4s_504_24fps` creates a common lossless 504×504, 96-frame master. |
| `variants` | Named transforms and encoding settings. Each starts independently from the source or common master. |
| `baseline` | Variant used for score deltas and midpoint crossings. |
| `notes` | Optional experiment-specific context, included in the report. |

A manifest contains `samples`, each with `id`, `label` (`real` or `ai`), `dataset`,
`revision`, `remote_path`, and `sha256`. Dataset and revision may also be specified
at the manifest's top level. `source`, `content`, `cell` and `actual_metadata` are optional.
The existing manifests include selection policies and audits; a new manifest needs its own selection notes.

### Variants

Supported transforms: `identity`, `half_resize`, `center_crop_80`, `center_square`,
and `short_side_504`. Resize uses bicubic interpolation; crops are centered and
use even dimensions. The 504-pixel transform refuses upscaling.

Encoding choices: `source` for native identity passthrough, `ffv1` for a lossless
AVI, or `h264` with integer `crf` from 0 to 51. H.264 uses medium preset and yuv420p.
Audio is removed from generated media.

For example, change the compression level without writing another runner:

```json
{"name": "compression", "transform": "identity", "encoding": "h264", "crf": 28}
```

For separate fixed-frame crop/resize tests, use `native` preparation and `ffv1`
variants. The runner holds the centered frame indices constant across variants.
It does not reproduce the historical kitten study's alternate frame list or timestamp control.

Commit the config and source manifest before scoring. This records the plan before
results are available. `--dry-run` validates the config and reports counts without
requiring a commit, accessing the network or loading models. It does not decode media.

## Technical choices

- **Plain JSON:** reviewable in Git; no config library or framework dependency.
- **One scoring loop and report writer:** adding clips, CRF levels or supported transforms is a config change. Model-specific preprocessing stays in the adapters.
- **Shared decoded RGB frames:** both models get the same 16 centered-window frames per condition. Each keeps its native spatial preprocessing. RGB and normalized tensor hashes are recorded alongside logits.
- **CPU, four threads:** works on a laptop. WaveRep batches two frames. AEGIS processes the 16-frame window. This is sparse-frame WaveRep inference, not its native all-frame evaluation.
- **Independent encodes:** variants start from a common input rather than from each other. The compression config matches the historical panel's preparation exactly. Native resize/crop with H.264 also measures re-encoding; the encode-only baseline controls that part.
- **Full decode and complete case matrix:** reject damaged files, changed timing, mismatched detector inputs and missing/duplicate observations before publishing a report.
- **Hashes and run metadata:** record sources, checkpoint hashes, code, config, commands and dependency versions. Exact agreement is checked on this environment; other decoders or hardware can differ.

Outputs: `scores.csv`, `summary.json`, `run.json`, `validation.json`, `pairs.png`,
`pairs.svg` and `report.md`. Scores are uncalibrated; summary counts use the fixed
0.5 midpoint and a 0.10 absolute-change rule. The counts describe the selected clips.

## Historical studies and extensions

The old commands still reproduce their published studies. Their modules retain
special controls, cached-score checks and report layouts used for those experiments.
These modules live in `src/vidrobust/legacy/`; shared decoding and artifact helpers live in the core.
The shared runner is the default for new paired experiments. It handles native edits
and all three edits after common preparation; it does not replace the diagnostic frame-tracing study.
See [experiment history](experiment-history.md) for those results and commands.

## Add a detector

Create a module under `src/vidrobust/adapters/` and decorate its class with
`@register("your_detector")` from `vidrobust.registry`. Discovery imports the
adapter modules but does not load checkpoints. The registered name becomes valid
in configs without editing the runner, config validator or report.

The class follows the [detector contract](../src/vidrobust/detectors.py):

- `checkpoint`: dictionary with `path` under `models/`, an HTTPS `url`, and a SHA256; include an upstream revision where available.
- `preprocessing`: a short description recorded in the report.
- `__init__(root)`: load the verified trained checkpoint and set evaluation mode.
- `prepare_frames(frames)`: convert the 16 RGB arrays into the native normalized PyTorch tensor.
- `predict(tensor)`: return numeric outputs including `ai_score` in [0,1]; include logits where available.

The registry downloads/verifies the checkpoint before initialization. The shared
scorer runs inference mode, checks finite outputs, and hashes the RGB frames and
model tensor. Duplicate registrations and invalid checkpoint paths are rejected.
Adapters must use deterministic CPU settings (four threads and seed 0), preserve
their released preprocessing, and retain upstream attribution and licenses.
The AEGIS and WaveRep adapters are working examples. Tests use a clearly marked
fixture adapter to check extension points; fixture scores are not benchmark results.

## All-edit panel

`compression.json` now contains four conditions on the same 20 selected clips:
CRF 18 baseline, CRF 35 compression, half-size resize at CRF 18, and an 80% center
crop at CRF 18. All start independently from the same prepared lossless master.
The panel produces 160 scores and keeps the original source selection unchanged.
The added edits are follow-ups on that panel, not a fresh holdout.

Resize produces 252×252 frames; crop produces 402×402 frames. WaveRep adds zero
padding to reach 504×504. AEGIS still resizes to 224×224. These results measure
each complete input pipeline, including padding and re-encoding, rather than
isolated geometric effects. The fixed-frame kitten study uses separate lossless
controls and remains a supporting diagnostic case.

The full `pairs.png` chart shows every edit. `compression-pairs.png` is a focused
pair from the same run and is used in the README. The previous 80-score shared
run is preserved in [compression-v1](../reports/archive/compression-v1/report.md),
and the earlier smoke run in [smoke-v1](../reports/archive/smoke-v1/report.md).
Their `run.json` files retain the original config, code hashes and frozen commit;
use the recorded Git revision to reproduce those historical versions.

## Continuous integration

[GitHub Actions](https://github.com/Adnan8104/video-robustness/actions/workflows/ci.yml)
installs locked dependencies on Python 3.11, runs the test suite, then validates
both configs with `--dry-run`. It does not download dataset media or pretrained
weights. Tests create small synthetic videos locally. The workflow follows
[uv's official integration guide](https://docs.astral.sh/uv/guides/integration/github/)
and pins its setup actions to commit hashes.

## Refactor checks

The shared-runner smoke test is compared with the published two-detector CSV;
the compression run is compared with the published common-preparation CSV.
The compression reference comparison checks the original baseline/compression subset; the full 160-row matrix is validated separately.
The checks require exact input hashes, scores, recorded frame lists and available
branch/frame logits. They also recompute summaries from the saved CSV and verify
local media, checkpoint and code hashes.

```sh
uv run python scripts/verify_experiment.py configs/experiments/smoke.json reports/two-detectors/scores.csv
uv run python scripts/verify_experiment.py configs/experiments/compression.json reports/controlled/scores.csv --variants baseline compression
```

These are regression checks against existing clips, not additional evaluation data.
Results are saved in each run's `validation.json`.

Repeat the added-edit midpoint crossings and the largest absolute change per
model and label with freshly loaded models:

```sh
uv run python scripts/repeat_experiment.py configs/experiments/compression.json --variants half_resize center_crop_80
```

The script repeats each selected baseline/edit pair, checks every numeric output
and RGB/model-tensor hash, and records the checks in `validation.json`. This is a
diagnostic repeat of selected results, not a new evaluation sample.

## Check archived real footage

`configs/experiments/real-footage.json` selects eight new real source clips: six kitchen
actions and two music performances. It scores unchanged source bytes with both models.
The source manifest and selection policy record historical provenance, content review,
source hashes and a rejected candidate whose video did not match its captions.

```sh
uv run python scripts/check_sections.py configs/experiments/real-footage.json
```

This reusable follow-up accepts a real-only native config with one unchanged-source variant.
It runs the shared experiment runner, then the demo inference service on distinct
beginning/middle/end windows. It verifies that every middle score, logit and input hash
exactly reproduces the runner. Section results go beside the ordinary report, with
full raw output, a compact CSV and a chart. The config, manifest, selection policy
and script must be committed before inference.

Short clips may share most frames across windows. Identical endpoint and middle
windows are scored once, retaining the middle reference. This avoids counting duplicate
inputs as extra observations. The real-only sample measures specific score conflicts;
it cannot measure AI recall or rank overall model accuracy.

## Compare both error directions on additional sources

```sh
uv run python run.py experiment configs/experiments/source-panel.json
```

This 20-clip pilot uses five real Ego4D, five real YouTube-VOS, five generated
Cosmos and five generated Wan 2.2-14B clips. All are new to this project's prior
configs. Native source bytes and the existing 16-frame centered sampling keep the
comparison focused on the same detector setup used in the demo. No clip needs padding.

The shared report now writes `decisions.json`: real-to-AI errors, AI-to-real errors,
and agreement/inconclusive counts at the fixed 0.5 reference. Leaving disagreement
inconclusive can reduce wrong calls while leaving more videos unresolved; the report
keeps those unresolved clips in the denominator. No score averaging or threshold fitting
is used. Source-level counts show whether aggregate results hide different behavior.

The [selection policy](../configs/source-panel-selection.md) and candidate audit
record eligibility and review before scoring. Some clips share a room or scene,
recorded as visual clusters. Content, encoding and viewpoint differ between source
groups. This is a convenience pilot and cannot establish a population error rate
or an overall winning detector. Videos and review frames stay out of Git.

Repeat the first label conflict and disagreement in each source group, plus correct
controls, with freshly loaded models:

```sh
uv run python scripts/repeat_experiment.py configs/experiments/source-panel.json --variants original --source-errors
```

The stored pilot includes 11 exact repeats. See [interpretation and next milestone](detector-evaluation.md).
