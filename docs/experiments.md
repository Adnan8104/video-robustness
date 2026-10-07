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
| `detectors` | `aegis`, `waverep`, or both. Models load one at a time to limit memory. |
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
The shared runner is the default for new paired experiments. It handles native edits
and common-preparation compression; it does not replace the diagnostic frame-tracing study.
See [experiment history](experiment-history.md) for those results and commands.

A future VidAudit integration belongs at the detector/score boundary. It has not
been implemented. A new detector needs an adapter and registration in the shared
runner; the media and report stages can stay the same.

## Refactor checks

The shared-runner smoke test is compared with the published two-detector CSV;
the compression run is compared with the published common-preparation CSV.
The checks require exact input hashes, scores, recorded frame lists and available
branch/frame logits. They also recompute summaries from the saved CSV and verify
local media, checkpoint and code hashes.

```sh
uv run python scripts/verify_experiment.py configs/experiments/smoke.json reports/two-detectors/scores.csv
uv run python scripts/verify_experiment.py configs/experiments/compression.json reports/controlled/scores.csv
```

These are regression checks against existing clips, not additional evaluation data.
Results are saved in each run's `validation.json`.
