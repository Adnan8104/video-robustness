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
| `manifest` | Existing JSON source list with pinned revisions/versions and SHA256 hashes. Relative paths start at the repository root. |
| `sample_ids` | Optional ordered subset of the manifest. Omit to use every clip. |
| `source_directory` | Local download cache under `data/`. A matching hash allows reuse. |
| `detectors` | Registered adapter names (currently `aegis`, `waverep`, `aigvdet_rgb` and ranking-only `d3_resnet18`). Models load one at a time to limit memory. |
| `preparation` | `native` preserves source geometry/timing. `centered_4s_504_24fps` creates a common lossless 504×504, 96-frame master. |
| `variants` | Named transforms and encoding settings. Each starts independently from the source or common master. |
| `baseline` | Variant used for score deltas and midpoint crossings. |
| `analysis` | Default `midpoint`; `ranking` reports pair orderings/AUC without a cutoff. Ranking-only adapters require it. |
| `sampling` | Default `centered_4s_16`; `centered_2s_8fps` selects 16 nominal 8 fps positions in a centered two-second window. |
| `notes` | Optional experiment-specific context, included in the report. |

A manifest contains `samples`, each with `id`, `label` (`real` or `ai`) and `sha256`.
By default, sources are Hugging Face files with `dataset`, a pinned 40-character
`revision`, and `remote_path`. An explicit `provider: "http"` instead requires
`source_url`, `source_page` and `source_revision`: public HTTPS media, a provenance
page, and a recorded version/revision. SHA256 still pins exact downloaded bytes.
Media URLs with embedded credentials or fragments are rejected. Include author,
source-date and license fields when using external camera footage. Dataset and revision may also be specified
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
- **Shared decoded RGB frames:** all selected models get the same 16 centered-window frames per condition. Each keeps its native spatial preprocessing. RGB and normalized tensor hashes are recorded alongside logits.
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
- `ranking_only = True`: required when the bounded score has no decision meaning; configs must select `analysis: "ranking"`. Save the raw score too and explain the coordinate mapping.

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
all eight configs with `--dry-run`. It does not download dataset media or pretrained
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

## Compare a different pretrained backbone

```sh
uv run python run.py experiment configs/experiments/third-detector.json
uv run python scripts/verify_experiment.py configs/experiments/third-detector.json reports/experiments/source-panel/scores.csv --detectors aegis waverep
uv run python scripts/audit_aigvdet.py configs/experiments/third-detector.json --clips panel_ego4d_01 panel_wan_04 panel_wan_05
uv run python scripts/repeat_experiment.py configs/experiments/third-detector.json --variants original --source-errors --detectors aigvdet_rgb
```

Same frozen 20 source clips, three models, one unchanged-source condition: **60 scores**. The two existing models must exactly match their earlier 40 scores, frame indices, logits and RGB/model-tensor hashes. All 60 rows are independently reanalyzed even when reference parity selects only two detectors.

The new `aigvdet_rgb` adapter uses the released **AIGVDet RGB branch only**, with its ResNet50 trained backbone and classifier. This changes the feature extractor from DINOv2 without adding dependencies or training. The full AIGVDet detector also uses optical flow, which this CPU baseline omits.

Native spatial input is a 448×448 center crop and ImageNet-normalized RGB. Smaller inputs receive CenterCrop's zero padding; none of the source-panel inputs need it. Frames are scored individually, and their sigmoid probabilities are averaged. This differs from WaveRep's sigmoid after averaging logits. Batch size 1 matches author inference. Temporal sampling is the harness's shared centered 16 frames, instead of AIGVDet's all-frame inference. The RGB-only and sparse-frame adaptations prevent direct comparisons with paper metrics.

The checkpoint is pinned by SHA256 and loaded strictly, including the trained classifier. It is about **270 MiB** because the released artifact also contains optimizer state; the adapter only uses model weights. Native architecture, preprocessing, per-frame logits, probabilities and aggregation are checked against unchanged upstream code at the pinned revision. The audit also checks score arithmetic on all 20 saved RGB rows and exact stored-run parity on the three native audit clips.

The adapter is discovered automatically without runner/report changes. [Predeclared criteria](../configs/third-detector-policy.md) · [Native code and weight provenance](../vendor/aigvdet/ORIGIN.md) · [Comparison results](../reports/experiments/third-detector/report.md).

## Check similar construction scenes

```sh
uv run python run.py experiment configs/experiments/construction-scenes.json
uv run python scripts/verify_experiment.py configs/experiments/construction-scenes.json
uv run python scripts/audit_media.py configs/experiments/construction-scenes.json
uv run python scripts/audit_aigvdet.py configs/experiments/construction-scenes.json --clips construction_real_01 construction_ai_01 construction_ai_03
uv run python scripts/repeat_experiment.py configs/experiments/construction-scenes.json --variants original --source-errors
```

Six new source files: three real camera recordings and three generated clips, with
daylight crane/construction subject matter and two ground/one elevated viewpoints
per origin. All three adapters score unchanged bytes: **18 scores**. This is a
coarse subject/viewpoint comparison; the sources are not exact real/generated pairs.

Real footage is directly downloaded from Wikimedia Commons and pinned by SHA256,
with page revision IDs, authors, dates and licenses. Clips remain in their original
WebM containers; the local cache filename is standardized to `.mp4`, and the decoder
recognizes the actual container. No conversion is introduced. Generated sources
are pinned SynthSite MP4 files from Sora 2 Pro and Veo 3.1.

OpenCV can estimate a WebM frame count from duration and frame rate, rounding it
up by one. If that count differs from its full decode, the runner checks the actual
count with an independent FFmpeg decode using passthrough timing before accepting
the file. Both decoders must agree; failures remain fatal. Ordinary MP4 count
mismatches remain errors. The media audit independently checks presentation
timestamps and records their agreement with nominal sampled times.

Only the centered four-second window is scored, even for the longer camera sources.
Native crops can omit the hoist or workers, and real/AI clips still differ in codecs,
resolution and camera geometry. No calibrated verdict or detector promotion follows
from this small pilot. The [selection policy](../configs/construction-scenes-selection.md)
and [candidate audit](../configs/construction-scenes-candidate-audit.json) were committed
before inference. [Results and interpretation](construction-scenes.md).

## Evaluate a temporal ranking candidate

```sh
uv run python run.py experiment configs/experiments/temporal-shared.json
uv run python run.py experiment configs/experiments/temporal-8fps.json
```

Both configs reuse all 26 source clips from the source and construction panels.
Each writes 26 scores, with no edit, training, threshold tuning or demo change.
This is a regression/feasibility check on previously examined clips. It is not a
new held-out accuracy test.

D3's documented ResNet18 option uses an official **45 MiB** ImageNet encoder and
existing locked dependencies. This is a lightweight temporal-feature candidate,
not optical flow and not the main paper's XCLIP model. The adapter preserves the
author's BGR order, long-axis crop, linear resize and normalization. It measures
the standard deviation of changes between consecutive feature distances. Lower
raw discrepancy is more AI-like. The bounded `ai_score = 1/(1+temporal_std)` column
only stores a monotonic ranking coordinate; **0.5 has no decision meaning** for it.

The runner rejects this adapter with midpoint analysis before any downloads.
Ranking reports omit classification errors and agreement verdicts, and their
plots have no midpoint line. AUC counts AI/real pair orderings, with ties worth
half. It does not establish a useful threshold or independent-trial accuracy.

The two-second profile uses frame-index rounding at nominal 8 fps and keeps source
frames directly decoded. It is closer to upstream's timing, but upstream extracts
JPEGs from a random window. The profiles also change window duration, so any
ranking difference cannot be attributed solely to frame rate.

For either config, run the following checks (replace the config path for the
second profile):

```sh
uv run python scripts/verify_experiment.py configs/experiments/temporal-shared.json
uv run python scripts/audit_media.py configs/experiments/temporal-shared.json
uv run python scripts/audit_d3.py configs/experiments/temporal-shared.json --clips panel_wan_04 panel_wan_05 construction_ai_02 construction_real_02 panel_ego4d_01 panel_youtube_vos_01
uv run python scripts/repeat_experiment.py configs/experiments/temporal-shared.json --variants original --clips panel_wan_04 panel_wan_05 construction_ai_02 construction_real_02 panel_ego4d_01 panel_youtube_vos_01
```

The audit executes unchanged author forward/crop and normalization code on six
fixed clips. It checks all 26 score arithmetic/rank counts independently. Explicit
repeat IDs replace midpoint-based selection, which is invalid for a ranker.
[Predeclared criteria](../configs/temporal-ranking-policy.md) ·
[Source, encoder and adaptation details](../vendor/d3/ORIGIN.md).
