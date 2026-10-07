"""Upload inference using the benchmark's adapters, frames and score checks."""
import hashlib
import math
from pathlib import Path
import subprocess
import tempfile
import threading

import numpy as np

from .frame_scoring import score_frames
from .media import probe, read_exact_rgb
from .registry import get_adapter, make_detector

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_SECONDS = 30
MAX_PIXELS = 1920 * 1080
MAX_FPS = 60
EXTENSIONS = ("mp4", "mov", "mkv", "avi", "webm")


def centered_indices(meta):
    """Match AEGIS window_sample(..., 16, target_dur=4, random_start=False)."""
    window = max(16, min(int(4 * meta["fps"]), meta["frames"]))
    start = 0 if window >= meta["frames"] else (meta["frames"] - window) // 2
    end = min(start + window, meta["frames"])
    return np.linspace(start, end - 1, 16, dtype=int).tolist()


def section_plan(meta, scan_sections=False):
    """Keep the benchmark's centered window; optionally inspect the two ends."""
    middle = centered_indices(meta)
    if not scan_sections:
        return [("middle", middle)]
    span = min(meta["frames"], max(16, int(4 * meta["fps"])))
    beginning = np.linspace(0, span - 1, 16, dtype=int).tolist()
    end = np.linspace(meta["frames"] - span, meta["frames"] - 1, 16, dtype=int).tolist()
    # Short clips have one window, not three independent observations.
    if beginning == middle == end:
        return [("middle", middle)]
    return [("beginning", beginning), ("middle", middle), ("end", end)]


def validate_metadata(meta):
    if not math.isfinite(meta["fps"]) or not 4 <= meta["fps"] <= MAX_FPS:
        raise ValueError("Use a video with a frame rate between 4 and 60 fps.")
    if meta["frames"] < 16:
        raise ValueError("The video needs at least 16 frames.")
    if meta["frames"] / meta["fps"] > MAX_SECONDS:
        raise ValueError("Trim the video to 30 seconds or less.")
    if min(meta["width"], meta["height"]) < 16 or meta["width"] * meta["height"] > MAX_PIXELS:
        raise ValueError("Use a video up to 1920 × 1080 pixels, or the equivalent in portrait.")


def score_summary(scores):
    """The midpoint describes model output; it is not a calibrated verdict."""
    sides = {score >= 0.5 for score in scores}
    if len(sides) != 1:
        return "Models disagree around 0.5"
    return "Both scores are above 0.5" if True in sides else "Both scores are below 0.5"


class DetectionService:
    """Cache weights only; serialize model loading/inference across sessions."""

    def __init__(self, root):
        self.root = Path(root)
        self.models = {}
        self.lock = threading.Lock()

    def analyze(self, content, filename, names=("aegis", "waverep"), progress=None, *, scan_sections=False):
        suffix = Path(filename).suffix.lower()
        if suffix.lstrip(".") not in EXTENSIONS:
            raise ValueError("Choose an MP4, MOV, MKV, AVI or WebM video.")
        if not content or len(content) > MAX_UPLOAD_BYTES:
            raise ValueError("Choose a nonempty video under 100 MiB.")
        if not names or len(set(names)) != len(names):
            raise ValueError("Choose distinct registered detectors.")
        specs = {name: get_adapter(name) for name in names}
        # Never retain uploads on disk, including when decoding or inference fails.
        with tempfile.TemporaryDirectory(prefix="vidrobust-upload-") as directory:
            source = Path(directory) / ("upload" + suffix)
            source.write_bytes(content)
            try:
                meta = probe(source)
            except ValueError:
                raise ValueError("Could not read this video. Try an H.264 MP4 export.") from None
            validate_metadata(meta)
            plan = section_plan(meta, scan_sections)
            indices = sorted({index for _, selected in plan for index in selected})
            try:
                frames = read_exact_rgb(source, indices)
            except ValueError:
                raise ValueError("The sampled frames could not be decoded. Try an H.264 MP4 export.") from None
            if any(frame.shape != (meta["height"], meta["width"], 3) for frame in frames):
                raise ValueError("Video dimensions changed while decoding. Use a fixed-size export.")
            decoded = dict(zip(indices, frames))
            windows = []
            with self.lock:
                for section, selected in plan:
                    rows = []
                    for name, spec in specs.items():
                        if progress:
                            progress(f"{name} — {section}")
                        if name not in self.models:
                            self.models[name] = make_detector(self.root, name)
                        details = score_frames(self.models[name], name, [decoded[index] for index in selected])
                        rows.append(dict(detector=name, **details,
                            checkpoint_sha256=spec.adapter.checkpoint["sha256"],
                            preprocessing=spec.adapter.preprocessing))
                    windows.append(dict(section=section, sampled_frame_indices=selected,
                        sampled_time_seconds=[i / meta["fps"] for i in selected], detectors=rows))
        middle = next(window for window in windows if window["section"] == "middle")
        warnings = []
        if min(meta["width"], meta["height"]) < 504 and "waverep" in names:
            warnings.append("WaveRep pads smaller frames to 504 × 504. Padding can affect its score.")
        if "waverep" in names:
            warnings.append("WaveRep sees the center 504 × 504 region and uses 16 frames here, rather than its full-video evaluation.")
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
            capture_output=True, text=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=self.root,
            capture_output=True, text=True)
        return dict(schema_version=2, input_sha256=hashlib.sha256(content).hexdigest(),
            input_size_bytes=len(content), metadata=meta, duration_seconds=meta["frames"] / meta["fps"],
            sampled_frame_indices=middle["sampled_frame_indices"], sampled_time_seconds=middle["sampled_time_seconds"],
            sampling=("16 frames per window, up to four seconds each; nominal constant-fps timing. "
                      "Three-section mode adds beginning and end windows, which may overlap on short clips."),
            scan_sections=scan_sections, windows=windows,
            execution="CPU; seed 0; four threads; deterministic algorithms",
            git_revision=revision.stdout.strip() if revision.returncode == 0 else None,
            git_dirty=bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
            warnings=warnings, detectors=middle["detectors"],
            interpretation="Higher means more AI-like; scores are uncalibrated. 0.5 is a reference midpoint, not a validated threshold.")
