"""Frozen two-model experiment; existing AEGIS results remain untouched."""
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import time
from urllib.parse import quote

VARIANTS = ("original", "encode_control", "compression", "resize", "crop")
MIDPOINT = 0.5


def pair_rows(rows):
    """Require exactly one observation per model on each identical encoded input."""
    paired = {}
    for row in rows:
        key = (row["video_id"], row["variant"])
        group = paired.setdefault(key, {})
        if row["detector"] in group:
            raise ValueError(f"Duplicate model/case: {key}")
        group[row["detector"]] = row
    for key, group in paired.items():
        if set(group) != {"aegis", "waverep"}:
            raise ValueError(f"Unpaired case: {key}")
        a, w = group["aegis"], group["waverep"]
        if a["sha256"] != w["sha256"] or a["sampled_frame_indices"] != w["sampled_frame_indices"]:
            raise ValueError(f"Inputs or temporal sampling differ: {key}")
        for row in group.values():
            if not math.isfinite(row["ai_score"]) or not 0 <= row["ai_score"] <= 1:
                raise ValueError(f"Invalid score: {key}")
    return paired


def summarize(rows):
    pair_rows(rows)
    result = {}
    for cohort in ("all", "fresh"):
        selected = [r for r in rows if cohort == "all" or r["cohort"] == cohort]
        metrics = {}
        for detector in ("aegis", "waverep"):
            subset = [r for r in selected if r["detector"] == detector]
            originals = [r for r in subset if r["variant"] == "original"]
            shifts = [r for r in subset if r["variant"] in ("compression", "resize", "crop")]
            metrics[detector] = dict(source_clips=len(originals),
                real_midpoint_conflicts=sum(r["label"] == "real" and r["ai_score"] >= MIDPOINT for r in originals),
                ai_midpoint_conflicts=sum(r["label"] == "ai" and r["ai_score"] < MIDPOINT for r in originals),
                changes_at_least_point10=sum(abs(r["delta_vs_control"]) >= 0.10 for r in shifts),
                transformed_cases=len(shifts),
                largest_control_relative_change=max(shifts, key=lambda r: abs(r["delta_vs_control"])) if shifts else None)
        pairs = pair_rows(selected)
        originals = [g for (_, v), g in pairs.items() if v == "original"]
        metrics["original_midpoint_disagreements"] = sum(
            (g["aegis"]["ai_score"] >= MIDPOINT) != (g["waverep"]["ai_score"] >= MIDPOINT) for g in originals)
        result[cohort] = metrics
    return result


def read_previous(root):
    from .cli import MODEL_HASH, MODEL_REV
    old = {}
    for directory in (root / "reports", root / "reports/diagnostics"):
        meta = json.loads((directory / "run.json").read_text())
        if meta["model_sha256"] != MODEL_HASH or meta["model_revision"] != MODEL_REV:
            raise ValueError("Published AEGIS provenance differs")
        with open(directory / "scores.csv") as f:
            for row in csv.DictReader(f):
                variant = {"crf_18": "encode_control", "crf_35": "compression"}.get(row["variant"], row["variant"])
                key = (row["video_id"], variant)
                if key in old and (old[key]["sha256"] != row["sha256"] or float(old[key]["ai_score"]) != float(row["ai_score"])):
                    raise ValueError(f"Prior runs disagree: {key}")
                old[key] = dict(row, variant=variant)
    return old


def write_csv(path, rows):
    fields = sorted({key for row in rows for key in row})
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_comparison(root):
    import imageio_ffmpeg
    import torch
    from .cli import download, sha, MODEL_HASH, MODEL_REV, FILTERS
    from .detectors import AegisDetector
    from .diagnostics import probe, validate_case
    from .waverep import WaveRepDetector, WEIGHTS_HASH, WEIGHTS_URL
    config_path = root / "configs/two-detectors.json"
    config = json.loads(config_path.read_text())
    download(WEIGHTS_URL, root / "models/weights_dinov2_G4.ckpt", WEIGHTS_HASH)
    download(f"https://huggingface.co/MusapYildiz/aegis-video-detector/resolve/{MODEL_REV}/checkpoint_best.pt",
             root / "models/checkpoint_best.pt", MODEL_HASH)
    def fetch(sample):
        url = f"https://huggingface.co/datasets/{sample['dataset']}/resolve/{sample['revision']}/{quote(sample['remote_path'], safe='/')}"
        download(url, root / f"data/original/{sample['id']}.mp4", sample["sha256"])
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, config["samples"]))
    previous = read_previous(root)
    case_list, commands, sources = [], [], {}
    # Preserve old files; new encodes live in their own ignored directory.
    for sample in config["samples"]:
        original = root / f"data/original/{sample['id']}.mp4"
        sources[sample["id"]] = probe(original, full_decode=True)
        variants = list(VARIANTS)
        if sample["id"] in config["sweep_ids"]:
            variants += [f"crf_{c}" for c in config["extra_crfs"]]
        for variant in variants:
            path = original
            if variant != "original":
                if variant in FILTERS:
                    filt, crf = FILTERS[variant]
                    path = root / f"data/variants/{sample['id']}_{variant}.mp4"
                    if sample["generator"] == "DAVIS":
                        alias = {"encode_control": "crf_18", "compression": "crf_35"}.get(variant, variant)
                        path = root / f"data/diagnostics/{sample['id']}_{alias}.mp4"
                else:
                    filt, crf = None, variant.split("_")[1]
                    path = root / f"data/diagnostics/{sample['id']}_{variant}.mp4"
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(original), "-map", "0:v:0", "-an"]
                    if filt:
                        cmd += ["-vf", filt]
                    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", str(path)]
                    subprocess.run(cmd, check=True)
                    commands.append([str(Path(a).relative_to(root)) if a.startswith(str(root) + "/") else a for a in cmd[1:]])
            row = dict(video_id=sample["id"], label=sample["label"], source=sample["generator"],
                       cohort=sample["cohort"], variant=variant, sha256=sha(path), **probe(path))
            validate_case(sources[sample["id"]], row | {"ai_score": 0.0})
            case_list.append((path, row))
    if len(case_list) != 187:
        raise ValueError("Frozen case count changed")
    out = root / "reports/two-detectors"
    out.mkdir(parents=True, exist_ok=True)
    signature = dict(config_sha256=sha(config_path), model_sha256=WEIGHTS_HASH,
        adapter_sha256=sha(root / "src/vidrobust/waverep.py"),
        package_versions={p: importlib.metadata.version(p) for p in ("torch", "timm", "opencv-python-headless", "numpy", "torchvision")})
    cache_path = root / "data/waverep-comparison-cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    cached = {(r["video_id"], r["variant"], r["sha256"]): r for r in cache.get("rows", [])} if cache.get("signature") == signature else {}
    wave = WaveRepDetector(root)
    wave_rows = []
    for index, (path, row) in enumerate(case_list, 1):
        key = (row["video_id"], row["variant"], row["sha256"])
        if key in cached:
            scored = cached[key]
        else:
            start = time.perf_counter()
            details = wave.score_details(path)
            scored = row | details | dict(detector="waverep", elapsed_sec=time.perf_counter() - start, reused=False)
            scored["frame_logits"] = json.dumps(scored["frame_logits"])
            scored["sampled_frame_indices"] = json.dumps(scored["sampled_frame_indices"])
        wave_rows.append(scored)
        # Resume after interruption; only matching bytes, adapter and environment qualify.
        temp = cache_path.with_suffix(".part")
        temp.write_text(json.dumps(dict(signature=signature, rows=wave_rows)))
        temp.replace(cache_path)
        print(f"WaveRep {index}/187 {row['video_id']} {row['variant']}: {scored['ai_score']:.6f}", flush=True)
    del wave
    aegis = AegisDetector(root)
    rows, reused_count = list(wave_rows), 0
    for (path, row), wave_row in zip(case_list, wave_rows):
        old = previous.get((row["video_id"], row["variant"]))
        if old and old["sha256"] == row["sha256"]:
            # Legacy root CSV did not store indices; the run records this same sampler.
            indices = aegis.window_sample(row["frames"], 16, row["fps"], target_dur=4.0, random_start=False).tolist()
            details = dict(ai_score=float(old["ai_score"]), sampled_frame_indices=indices)
            for field in ("fusion_logit", "pixel_score", "motion_score", "consistency_score"):
                if field in old:
                    details[field] = float(old[field])
            if old.get("sampled_frame_indices") and json.loads(old["sampled_frame_indices"]) != indices:
                raise ValueError("Recorded AEGIS indices disagree")
            elapsed = float(old["elapsed_sec"])
            reused_count += 1
        else:
            start = time.perf_counter()
            details = aegis.score_details(path)
            elapsed = time.perf_counter() - start
        scored = row | details | dict(detector="aegis", elapsed_sec=elapsed, reused=bool(old and old["sha256"] == row["sha256"]))
        scored["sampled_frame_indices"] = json.dumps(scored["sampled_frame_indices"])
        if scored["sampled_frame_indices"] != wave_row["sampled_frame_indices"]:
            raise ValueError("Models sampled different frames")
        rows.append(scored)
        if not scored["reused"]:
            print(f"AEGIS {row['video_id']} {row['variant']}: {scored['ai_score']:.6f}", flush=True)
    for row in rows:
        control = next(r for r in rows if r["detector"] == row["detector"] and r["video_id"] == row["video_id"] and r["variant"] == "encode_control")
        row["delta_vs_control"] = row["ai_score"] - control["ai_score"]
    pairs = pair_rows(rows)
    write_csv(out / "scores.csv", rows)
    metadata = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), config=config, **signature,
        aegis_model_sha256=MODEL_HASH, aegis_model_revision=MODEL_REV,
        aegis_reused_cases=reused_count, aegis_newly_scored_cases=187-reused_count,
        device="cpu", threads=4, seed=0, deterministic_algorithms=True, batch_size=2,
        python=platform.python_version(), ffmpeg=imageio_ffmpeg.get_ffmpeg_version(),
        sampling="16 frames, centered four-second window, same temporal indices per model",
        prior_runs=["reports/run.json", "reports/diagnostics/run.json"],
        transformations_generated=commands, selection_frozen_commit="e61770c")
    (out / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (out / "validation.json").write_text(json.dumps(dict(source_clips=35, model_scores=len(rows), paired_cases=len(pairs),
        full_source_decode="passed", geometry_timing_input_hashes_and_paired_sampling="passed", source_metadata=sources), indent=2) + "\n")
    summary = summarize(rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    from .comparison_report import write_report, plot_results
    plot_results(root, config, rows)
    write_report(root, config, rows, summary)
    print("Two-detector comparison complete", flush=True)
