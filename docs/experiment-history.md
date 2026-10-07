# Experiment history

The project started with one pretrained detector, added a second, then tightened
input controls. The [shared runner](experiments.md) is now the default for new experiments.

| Stage | What changed | Result |
|---|---|---|
| Initial panel | AEGIS on 20 clips and five conditions: 100 scores. | The first large compression drop did not repeat on the 16 new clips. |
| Diagnostics | Five CRF levels on four clips, plus five real DAVIS clips: 49 scores. | A second real clip, a bear, dropped from 0.993 to 0.237 under compression. |
| Two detectors | AEGIS and WaveRep on 35 clips: 187 paired conditions, 374 scores. | The models disagreed on real clips; WaveRep also lost AI signal under compression. |
| Common preparation | 20 fresh clips, five per real/AI × animal/non-animal group: 80 scores. | WaveRep changed by at least 0.10 on 9/10 generated clips. AEGIS had no changes that large. |
| Compression brackets | Original files and CRF 18/23/28/35 on four selected clips: 40 scores. | WaveRep crossed below 0.5 at CRF 23–28 for an AI elephant and 18–23 for an AI sunset scene. |
| Fixed-frame check | Separate resize, crop, encoding and frame-selection controls on one real clip: 36 scores. | Crop alone changed AEGIS from 0.005 to 1.000; resize alone changed WaveRep from 0.151 to 0.677. |

The last check explains a supporting failure case: both detectors gave a real
kitten high scores after common preparation. Holding the same 16 source frames
fixed showed which edits could trigger the change. It describes that clip;
repeatability across other clips is still open.

## Reports and original commands

| Study | Report and selection | Original command |
|---|---|---|
| Initial panel | [Summary](../reports/summary.md) · [Scores](../reports/comparison.md) · [Selection](../configs/selection.md) | `run.py fetch`, then `run.py run` |
| Diagnostics | [Report](../reports/diagnostics/report.md) · [Selection](../configs/diagnostics-selection.md) | `run.py diagnose` |
| Two detectors | [Report](../reports/two-detectors/report.md) · [Selection](../configs/two-detectors-selection.md) | `run.py compare` |
| Common preparation | [Chart and scores](../reports/controlled/report.md) · [Selection](../configs/controlled-selection.md) · [Content audit](../configs/controlled-candidate-audit.json) | `run.py controlled` |
| Compression brackets | [Report](../reports/failure-followup/report.md) · [Selection](../configs/failure-followup-selection.md) | `run.py followup` |
| Fixed-frame check | [Report](../reports/kitten-isolation/report.md) · [Controls](../configs/kitten-isolation-selection.md) | `run.py isolate` |

Run these with `uv run python` after `uv sync --locked`. The old commands remain
available from `src/vidrobust/legacy/` to reproduce the published studies. The new compression config
extends the common-preparation panel to resize and crop: 160 scores on the same 20 clips.
The [original shared-runner outputs](../reports/archive/compression-v1/report.md) are preserved.

Each report keeps its full numerical outputs and validation. See
[methodology](methodology.md) for sampling, preprocessing and measurement limits.
Earlier four-clip discovery results remain in `reports/milestone1/` and `reports/milestone2/`.
