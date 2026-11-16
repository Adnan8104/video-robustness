"""Rank a local batch with the head used in the fixed-budget study."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from threading import Lock

import imageio_ffmpeg
import numpy as np

from .artifacts import sha
from .inference import EXTENSIONS, MAX_UPLOAD_BYTES, centered_indices, validate_metadata
from .linear_head import clip_embedding
from .media import probe, read_exact_rgb
from .registry import get_adapter, make_detector

MAX_CLIPS = 20
MAX_BATCH_BYTES = 200 * 1024**2


def prepare_review_frames(source):
    """Use the study's centered, square, CRF 35 input and frame positions."""
    validate_metadata(probe(source))
    meta = probe(source, full_decode=True)
    width, height, fps = meta["width"], meta["height"], meta["fps"]
    if width < height or height < 504 or fps < 24 or meta["frames"] / fps < 4:
        raise ValueError("Use a landscape video at least 504 pixels high, four seconds long and 24 fps.")
    nominal_start = (meta["frames"] / fps - 4) / 2
    start = math.floor(nominal_start * fps) / fps
    master = source.with_name("master.avi")
    encoded = source.with_name("compressed.mp4")
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "warning"]
    common = ["-map", "0:v:0", "-an"]
    output = ["-frames:v", "96", "-pix_fmt", "yuv420p"]
    try:
        subprocess.run(command + ["-ss", f"{start:.9f}", "-i", str(source)] + common + ["-vf",
            "setpts=PTS-STARTPTS,fps=24:start_time=0,scale=-2:504:flags=bicubic,crop=504:504,setsar=1,setpts=N/(24*TB)",
            "-c:v", "ffv1"] + output + [str(master)], check=True, capture_output=True)
        subprocess.run(command + ["-i", str(master)] + common +
            ["-c:v", "libx264", "-preset", "medium", "-crf", "35"] + output + [str(encoded)],
            check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise ValueError("Could not prepare this clip. Try exporting it as a constant-frame-rate MP4.") from None
    prepared = probe(encoded, full_decode=True)
    if prepared != dict(width=504, height=504, frames=96, fps=24.0):
        raise ValueError("Could not prepare exactly four seconds at 24 fps.")
    return read_exact_rgb(encoded, centered_indices(prepared))


class ReviewService:
    def __init__(self, root):
        self.root = Path(root)
        self.detector = None
        self.lock = Lock()

    def rank(self, uploads, progress=None):
        """Return one ordered queue, or reject the batch if an input fails."""
        if not 1 <= len(uploads) <= MAX_CLIPS:
            raise ValueError(f"Choose up to {MAX_CLIPS} videos.")
        if sum(len(content) for _, content in uploads) > MAX_BATCH_BYTES:
            raise ValueError("The batch must be 200 MiB or less.")
        digests = set()
        inputs = []
        for name, content in uploads:
            suffix = Path(name).suffix.lower()
            if suffix.lstrip(".") not in EXTENSIONS or not 0 < len(content) <= MAX_UPLOAD_BYTES:
                raise ValueError(f"{name}: Choose a supported nonempty video up to 100 MiB.")
            digest = hashlib.sha256(content).hexdigest()
            if digest in digests:
                raise ValueError(f"{name}: Remove duplicate clips from the batch.")
            digests.add(digest)
            inputs.append((name, content, suffix, digest))

        model = self.root / "models/linear-head-policy.npz"
        if not model.is_file():
            raise ValueError("The fitted head is missing. Follow the README setup for the review mode.")
        fit = json.loads((self.root / "reports/linear-head/fit.json").read_text())
        if (sha(model) != fit["local_weights_sha256"] or fit["heads"] != ["light_only", "both_levels"]
                or get_adapter("waverep").adapter.checkpoint["sha256"] != fit["encoder_sha256"]):
            raise ValueError("The local model does not match the head used in the benchmark.")
        with np.load(model, allow_pickle=False) as data:
            weight, intercept = data["weights"][1], float(data["intercepts"][1])

        rows = []
        with self.lock:
            for index, (name, content, suffix, digest) in enumerate(inputs, start=1):
                with TemporaryDirectory(prefix="vidrobust-review-") as directory:
                    source = Path(directory) / ("clip" + suffix)
                    source.write_bytes(content)
                    try:
                        frames = prepare_review_frames(source)
                    except ValueError as error:
                        raise ValueError(f"{name}: {error}") from None
                if self.detector is None:
                    self.detector = make_detector(self.root, "waverep")
                margin = self._margin(frames, weight, intercept)
                rows.append(dict(name=name, sha256=digest, margin=margin))
                if progress:
                    progress(index, len(inputs))
        return sorted(rows, key=lambda row: (-row["margin"], row["sha256"]))

    def _margin(self, frames, weight, intercept):
        import torch

        detector = self.detector
        batches = []
        classifier = detector.model.get_classifier()
        with torch.inference_mode():
            tensor = detector.prepare_frames(frames)
            hook = classifier.register_forward_pre_hook(lambda _, args: batches.append(args[0].detach()))
            try:
                detector.predict(tensor)
            finally:
                hook.remove()
            features = torch.cat(batches).cpu().numpy()
        if features.shape != (16, detector.model.num_features):
            raise ValueError("Unexpected WaveRep feature shape.")
        margin = float(clip_embedding(features) @ weight + intercept)
        if not math.isfinite(margin):
            raise ValueError("The fitted head returned an invalid score.")
        return margin
