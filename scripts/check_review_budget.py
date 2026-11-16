"""Compare fixed WaveRep heads at the same human review budget."""
from collections import Counter
import csv
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

if __package__:
    from .check_head_transfer import source_key
    from .train_head import ROOT, VARIANTS, environment, extract, file_map, write
else:
    from check_head_transfer import source_key
    from train_head import ROOT, VARIANTS, environment, extract, file_map, write
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, load_config
from vidrobust.registry import get_adapter


BUDGET = 10
COHORT = {("real", "MSVD"): 90, ("ai", "VEO3"): 10}
REVISION = "c5093999e799c897c977a8699da95ebbc59cc9cb"


def summarize_queue(rows, column, budget):
    if (not 0 < budget <= len(rows)
            or len({r["source_sha256"] for r in rows}) != len(rows)
            or len({r["video_id"] for r in rows}) != len(rows)
            or any(r["label"] not in ("real", "ai") or not math.isfinite(float(r[column])) for r in rows)):
        raise ValueError("Review ranking requires distinct clips with finite scores and a valid budget")
    ordered = sorted(rows, key=lambda r: (-float(r[column]), r["source_sha256"]))
    queued = ordered[:budget]
    ai_surfaced = sum(r["label"] == "ai" for r in queued)
    return dict(ai_surfaced=ai_surfaced, real_reviewed=budget - ai_surfaced,
                ai_outside=sum(r["label"] == "ai" for r in ordered[budget:]),
                queue=[r["video_id"] for r in queued])


def check_cohort(samples, previous):
    if Counter((r["label"], r["source"]) for r in samples) != COHORT:
        raise ValueError("Expected 90 MSVD clips and 10 Veo 3 clips")
    sizes = Counter((r["label"], r["actual_metadata"]["width"], r["actual_metadata"]["height"])
                    for r in samples)
    if sizes != {("real", 1280, 720): 84, ("real", 1920, 1080): 6, ("ai", 1280, 720): 10}:
        raise ValueError("Unexpected native source resolutions")
    old_hashes = {r.get("sha256") for r in previous}
    old_paths = {r.get("remote_path", "") for r in previous}
    old_recordings = {source_key(p) for p in old_paths if "/MSVD/" in p}
    recordings = set()
    for row in samples:
        path = row["remote_path"]
        key = source_key(path)
        prefix = "videos/real/MSVD/" if row["label"] == "real" else "videos/fake/VEO3/"
        meta = row["actual_metadata"]
        if (row["dataset"] != "OmerXYZ/comgenvid" or row["revision"] != REVISION
                or not path.startswith(prefix) or row["recording_key"] != key
                or key in recordings or key in old_recordings or path in old_paths
                or row["sha256"] in old_hashes or not 0 < row["size_bytes"] <= 128 * 1024**2
                or meta["fps"] < 24
                or meta["frames"] / meta["fps"] < 4):
            raise ValueError(f"Unexpected or reused source: {path}")
        recordings.add(key)


def main():
    out = ROOT / "reports/review-budget"
    if out.exists():
        raise ValueError("The review batch has already been scored")
    path, manifest, config, samples = load_config(ROOT, "configs/experiments/review-budget.json")
    if (config["detectors"] != ["waverep"] or config["variants"] != VARIANTS[1:]
            or config["baseline"] != "compression" or config["analysis"] != "ranking"
            or config["preparation"] != "centered_4s_504_24fps"
            or config.get("sampling", "centered_4s_16") != "centered_4s_16"):
        raise ValueError("Unexpected review protocol")
    prior_files = []
    prior_samples = []
    for file in sorted((ROOT / "configs").rglob("*.json")):
        if file == manifest:
            continue
        data = json.loads(file.read_text())
        if isinstance(data, dict) and data.get("samples"):
            prior_files.append(file)
            prior_samples.extend(data["samples"])
    check_cohort(samples, prior_samples)

    fit_path = ROOT / "reports/linear-head/fit.json"
    fit = json.loads(fit_path.read_text())
    model = ROOT / "models/linear-head-policy.npz"
    model_sha = fit["local_weights_sha256"]
    if (sha(model) != model_sha or environment() != fit["environment"]
            or fit["heads"] != ["light_only", "both_levels"]
            or get_adapter("waverep").adapter.checkpoint["sha256"] != fit["encoder_sha256"]):
        raise ValueError("Original model or scoring environment differs")
    original = [ROOT / p for p in fit["fingerprints"]]
    if file_map(original) != fit["fingerprints"]:
        raise ValueError("Original fit inputs or scoring code changed")
    paths = sorted({*original, *prior_files, fit_path, manifest, path, Path(__file__).resolve(),
                    ROOT / "scripts/check_head_transfer.py", ROOT / "configs/review-budget-selection.md",
                    ROOT / "configs/review-budget-exclusions.json"})
    revisions = {p.relative_to(ROOT).as_posix(): frozen_revision(ROOT, p) for p in paths}
    fingerprints = file_map(paths)
    with np.load(model, allow_pickle=False) as data:
        weight, intercept = data["weights"][1], float(data["intercepts"][1])
    features, rows, preparation = extract(config, samples)
    if file_map(paths) != fingerprints or sha(model) != model_sha:
        raise ValueError("Frozen code, inputs or weights changed")
    expected = {r["id"]: r for r in samples}
    if {r["video_id"] for r in rows} != expected.keys() or len(rows) != len(samples):
        raise ValueError("Scores do not cover the frozen batch")
    for row, margin in zip(rows, features @ weight + intercept, strict=True):
        sample = expected[row["video_id"]]
        if row["label"] != sample["label"]:
            raise ValueError("Score label differs from the frozen manifest")
        row.update(trained_margin=float(margin), source_sha256=sample["sha256"],
                   sampled_frame_indices=json.dumps(row["sampled_frame_indices"]))
    stats = {name: summarize_queue(rows, name + "_margin", BUDGET)
             for name in ("released", "trained")}
    trained_wins = stats["trained"]["ai_surfaced"] > stats["released"]["ai_surfaced"]
    with TemporaryDirectory(prefix=".review-budget-", dir=out.parent) as directory:
        stage = Path(directory)
        scores = stage / "scores.csv"
        with scores.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        write(stage / "summary.json", dict(budget=BUDGET, source_clips=len(samples), test=stats,
              trained_wins=trained_wins, scores_sha256=sha(scores), preparation=preparation,
              weights_sha256=model_sha, encoder_sha256=fit["encoder_sha256"], environment=fit["environment"],
              frozen_revisions=revisions, fingerprints=fingerprints, reconstructed_released_logits="exact"))
        stage.rename(out)
    print(json.dumps(stats, indent=2), flush=True)


if __name__ == "__main__":
    main()
