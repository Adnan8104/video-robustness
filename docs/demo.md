# Local video check

```sh
uv sync --locked --extra demo
uv run --extra demo python run.py demo
```

Open http://127.0.0.1:8501. Choose a video and click **Check video**.
The server listens on this computer only. Stop it with Ctrl+C in the terminal that started it.
The two checkpoints total about 764 MiB and download on first use if missing.

## What you see

- Separate AEGIS and WaveRep scores. Higher is more AI-like; these are not confidence percentages.
- A disagreement notice when their scores fall on opposite sides of the reference midpoint, 0.5.
- Optional **Check beginning, middle and end**: three windows scored separately, with no average verdict.
- An expandable AEGIS table with its appearance, motion and consistency scores.
- A downloadable JSON result with input/checkpoint hashes, sampled frames, raw outputs and source revision.

The main score cards always describe the middle window. Each window uses 16 frames from up to four seconds.
For clips up to four seconds, the three windows are identical and evaluated once. Longer clips under twelve
seconds can have overlapping windows; three windows are not three independent votes. Timing is estimated
from the nominal frame rate, so variable-frame-rate files may have different presentation timestamps.

AEGIS's component scores come from separate learned heads. They do not sum to the final score and do not
prove why a video was flagged. A high motion score, for example, is not evidence of a particular motion defect.
Changing the decision threshold or calibrating scores requires a separate labeled validation set and an
untouched test set. This demo does neither.

## Small scope

Accepted containers: MP4, MOV, MKV, AVI and WebM, if OpenCV can decode them. Use an H.264 MP4 export if a
container cannot be read. Limits are 100 MiB, 30 seconds, 4–60 fps, at least 16 frames, and no more pixels per
frame than 1920 × 1080 (portrait is accepted). The frame-rate floor allows 16 distinct frames in four seconds. The other bounds keep CPU time and memory manageable.
Preview playback also depends on the browser supporting the video's codec.

Uploaded bytes stay in the browser/server session while the page is open. Disk copies use a temporary
directory and are removed on success or failure. Uploads and results are not saved into the repository.
Model weights remain cached locally. This is a local student demo, not a public upload service.

## Technical choices

| Choice | Reason |
|---|---|
| Streamlit as an optional, locked dependency | One Python process runs the upload interface and existing adapters; the experiment runner stays usable without the demo package. |
| `DetectionService` separate from the interface | Upload validation, decoding and inference can be tested without browser widgets. |
| Same adapters and centered sampling as the benchmark | No new model, trained head, resize policy or default decision rule is introduced. |
| One decode pass for selected frames | All models see identical RGB frames; three-section mode reuses overlapping frames. |
| Cached weights and serialized inference | Avoid loading two large models per click; prevent simultaneous sessions from running on shared model state. |
| Session-local results keyed by upload hash and mode | A new video or changed section option clears old scores. Reruns and downloads do not trigger another inference pass. |

AEGIS resizes to 224 × 224. WaveRep center-crops to 504 × 504, padding smaller inputs. WaveRep uses our
16-frame CPU adaptation rather than its official full-video evaluation. Neither model analyzes audio.
Both use DINOv2 backbones, so agreement is not independent confirmation.

[Implementation verification](../reports/demo-validation/report.md) compares pinned source files, native
AEGIS loading/preprocessing, and four previously recorded centered scores. It confirms numerical parity
on those samples; it does not establish accuracy on new uploads or explain a user's false positive.

Framework references: [Streamlit resource caching](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource)
and [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
