"""Config-driven preparation, scoring and paired analysis for small experiments."""
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import time

from .registry import detector_names, get_adapter, make_detector
TRANSFORMS = ("identity", "half_resize", "center_crop_80", "center_square", "short_side_504")


def inside(root, value, prefix=None):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or (prefix and not path.is_relative_to((root / prefix).resolve())):
        raise ValueError(f"Path must stay inside {prefix or 'the repository'}: {value}")
    return path


def load_config(root, path):
    path = inside(root, path)
    config = json.loads(path.read_text())
    allowed = {"schema_version", "name", "manifest", "sample_ids", "source_directory", "detectors",
               "preparation", "variants", "baseline", "notes"}
    if set(config) - allowed or config.get("schema_version") != 1:
        raise ValueError("Unknown config field or unsupported schema_version")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", config["name"]):
        raise ValueError("Experiment name must use lowercase letters, numbers and hyphens")
    manifest_path = inside(root, config["manifest"])
    manifest = json.loads(manifest_path.read_text())
    samples = [{**{k: manifest[k] for k in ("dataset", "revision") if k in manifest}, **s}
               for s in manifest["samples"]]
    if "sample_ids" in config:
        ids = config["sample_ids"]
        if not ids or len(ids) != len(set(ids)) or set(ids) - {s["id"] for s in samples}:
            raise ValueError("sample_ids must select unique existing manifest IDs")
        by_id = {s["id"]: s for s in samples}
        samples = [by_id[i] for i in ids]
    if not samples or len({s["id"] for s in samples}) != len(samples) or len({s["sha256"] for s in samples}) != len(samples):
        raise ValueError("Manifest has empty or duplicate inputs")
    for s in samples:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", s["id"]) or s["label"] not in ("real", "ai"):
            raise ValueError("Invalid source ID or label")
        if not re.fullmatch(r"[0-9a-f]{64}", s["sha256"]) or not re.fullmatch(r"[0-9a-f]{40}", s["revision"]):
            raise ValueError("Each source needs a SHA256 and pinned dataset commit")
        if Path(s["remote_path"]).is_absolute() or ".." in Path(s["remote_path"]).parts:
            raise ValueError("Invalid remote path")
    names = config["detectors"]
    available = detector_names()
    if not names or len(set(names)) != len(names) or set(names) - set(available):
        raise ValueError("Choose unique registered detectors from " + ", ".join(available))
    if config["preparation"] not in ("native", "centered_4s_504_24fps"):
        raise ValueError("Unknown preparation profile")
    inside(root, config["source_directory"], "data")
    variants = config["variants"]
    if not variants or len({v["name"] for v in variants}) != len(variants):
        raise ValueError("Variant names must be unique")
    for v in variants:
        if set(v) - {"name", "transform", "encoding", "crf"} or not re.fullmatch(r"[a-z0-9_]+", v["name"]):
            raise ValueError("Invalid variant field or name")
        if v["transform"] not in TRANSFORMS or v["encoding"] not in ("source", "ffv1", "h264"):
            raise ValueError("Unknown transform or encoding")
        if v["encoding"] == "source" and (v["transform"] != "identity" or config["preparation"] != "native"):
            raise ValueError("Source passthrough requires native identity preparation")
        if v["encoding"] == "h264":
            if type(v.get("crf")) is not int or not 0 <= v["crf"] <= 51:
                raise ValueError("H.264 requires integer CRF between 0 and 51")
        elif "crf" in v:
            raise ValueError("CRF only applies to H.264")
    if config["baseline"] not in {v["name"] for v in variants}:
        raise ValueError("Baseline must name a variant")
    return path, manifest_path, config, samples


def frozen_revision(root, path):
    relative = path.relative_to(root).as_posix()
    committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
    if committed != path.read_bytes():
        raise ValueError(f"Commit {relative} before inference")
    return subprocess.check_output(["git", "log", "-1", "--format=%H", "--", relative], cwd=root, text=True).strip()


def experiment_plan(root, path):
    _, _, config, samples = load_config(root, path)
    return dict(name=config["name"], source_clips=len(samples), detectors=config["detectors"],
                variants=[v["name"] for v in config["variants"]], baseline=config["baseline"],
                preparation=config["preparation"], scores=len(samples)*len(config["variants"])*len(config["detectors"]),
                output=f"reports/experiments/{config['name']}")


def analyze(rows, config, samples):
    """Reject missing/mismatched inputs before computing baseline-relative changes."""
    expected = {(s["id"], v["name"], d) for s in samples for v in config["variants"] for d in config["detectors"]}
    indexed = {(r["video_id"], r["variant"], r["detector"]): r for r in rows}
    if len(indexed) != len(rows) or set(indexed) != expected:
        raise ValueError("Incomplete, duplicate or unexpected scores")
    by_id = {s["id"]: s for s in samples}
    for row in rows:
        s = by_id[row["video_id"]]
        if any(row[k] != s.get(k, "") for k in ("label", "cell", "content")):
            raise ValueError("Score labels disagree with manifest")
        if not math.isfinite(row["ai_score"]) or not 0 <= row["ai_score"] <= 1:
            raise ValueError("Invalid score")
        peers = [indexed[(row["video_id"], row["variant"], d)] for d in config["detectors"]]
        for peer in peers:
            for key in ("sha256", "sampled_frame_indices", "sampled_rgb_sha256", "width", "height", "fps", "frames"):
                if row[key] != peer[key]:
                    raise ValueError(f"Paired detector inputs differ: {key}")
        baseline = indexed[(row["video_id"], config["baseline"], row["detector"])]
        if row["sampled_frame_indices"] != baseline["sampled_frame_indices"]:
            raise ValueError("Temporal indices changed across variants")
        row["delta_vs_baseline"] = row["ai_score"] - baseline["ai_score"]
    summary = {}
    for d in config["detectors"]:
        summary[d] = {}
        for v in config["variants"]:
            groups = {}
            for cell in sorted({s.get("cell", s["label"]) for s in samples}):
                selected = [s for s in samples if s.get("cell", s["label"]) == cell]
                group = [indexed[(s["id"], v["name"], d)] for s in selected]
                crossings = []
                for r in group:
                    b = indexed[(r["video_id"], config["baseline"], d)]
                    if (b["ai_score"] >= .5) != (r["ai_score"] >= .5):
                        crossings.append(dict(video_id=r["video_id"], baseline=b["ai_score"], score=r["ai_score"]))
                groups[cell] = dict(n=len(group), median_delta=statistics.median(r["delta_vs_baseline"] for r in group),
                    median_absolute_delta=statistics.median(abs(r["delta_vs_baseline"]) for r in group),
                    changes_at_least_point10=sum(abs(r["delta_vs_baseline"]) >= .1 for r in group),
                    midpoint_conflicts=sum((r["ai_score"] >= .5) != (r["label"] == "ai") for r in group),
                    midpoint_crossings=crossings)
            summary[d][v["name"]] = groups
    return summary


def run_experiment(root, path):
    from .artifacts import sha
    from .frame_scoring import score_frames
    from .media import prepare_cases, read_exact_rgb
    from .experiment_report import write_results
    import imageio_ffmpeg
    config_path, manifest_path, config, samples = load_config(root, path)
    frozen = {p.relative_to(root).as_posix(): frozen_revision(root, p) for p in (config_path, manifest_path)}
    models = {name: get_adapter(name).metadata(root) for name in config["detectors"]}
    code_paths = {str(p.relative_to(root)) for p in (root / "src/vidrobust").rglob("*.py")
                  if "legacy" not in p.relative_to(root / "src/vidrobust").parts}
    code_paths.update(model["code_path"] for model in models.values())
    code_paths.update(str(p.relative_to(root)) for p in (root / "vendor/aegis").glob("*.py"))
    code_hashes = {p: sha(root / p) for p in sorted(code_paths)}
    config_hash, manifest_hash = sha(config_path), sha(manifest_path)
    cases, preparation = prepare_cases(root, config, samples)
    sys.path.insert(0, str(root / "vendor/aegis"))
    from video_io import window_sample
    rows = []
    for name in config["detectors"]:
        detector = make_detector(root, name)
        for index, (path, case) in enumerate(cases, 1):
            indices = window_sample(case["frames"], 16, case["fps"], target_dur=4, random_start=False).tolist()
            start = time.perf_counter()
            details = score_frames(detector, name, read_exact_rgb(path, indices))
            for key, value in list(details.items()):
                if isinstance(value, list):
                    details[key] = json.dumps(value)
            rows.append(case | details | dict(detector=name, elapsed_sec=time.perf_counter()-start,
                        sampled_frame_indices=json.dumps(indices)))
            print(f"{name} {index}/{len(cases)} {case['video_id']} {case['variant']}: {details['ai_score']:.6f}", flush=True)
        del detector
    summary = analyze(rows, config, samples)
    if sha(config_path) != config_hash or sha(manifest_path) != manifest_hash or any(sha(root / p) != h for p, h in code_hashes.items()):
        raise ValueError("Config, manifest or scoring code changed during inference; rerun with a fixed plan")
    metadata = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), config=config,
        config_path=config_path.relative_to(root).as_posix(), models=models,
        config_sha256=config_hash, manifest_sha256=manifest_hash, frozen_commits=frozen,
        code_sha256=code_hashes, python=platform.python_version(),
        packages={p: importlib.metadata.version(p) for p in ("torch", "torchvision", "timm", "numpy", "opencv-python-headless", "imageio-ffmpeg", "matplotlib")},
        model_sha256={name: model["checkpoint"]["sha256"] for name, model in models.items()},
        ffmpeg=imageio_ffmpeg.get_ffmpeg_version(), device="cpu", threads=4,
        seed=0, deterministic_algorithms=True, preparation=preparation)
    validation = dict(source_clips=len(samples), paired_cases=len(cases), model_scores=len(rows),
        source_hashes_and_full_decode="passed", geometry_timing_and_frame_indices="passed",
        complete_case_matrix="passed", identical_bytes_and_RGB_between_detectors="passed",
        config_and_code_unchanged_during_inference="passed")
    out = root / f"reports/experiments/{config['name']}"
    out.mkdir(parents=True, exist_ok=True)
    write_results(root, out, config, samples, rows, summary, metadata, validation)
    print(f"Results: {out.relative_to(root)}/report.md", flush=True)
    return rows
