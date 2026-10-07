import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import time
import urllib.request
from urllib.parse import quote
from .detectors import AegisDetector
from .reporting import write_summary

ROOT = Path(__file__).resolve().parents[2]
MODEL_REV = "95b71346cec650165e6ad3fb20ed9e80f4b6702a"
MODEL_HASH = "7df233979f9d3ef340e101d0d635a4d074577d43e6d1591d677cde31f80e44ba"
FILTERS = {
    "encode_control": (None, "18"),
    "compression": (None, "35"),
    "resize": ("scale=trunc(iw/4)*2:trunc(ih/4)*2:flags=bicubic", "18"),
    "crop": ("crop=trunc(iw*0.8/2)*2:trunc(ih*0.8/2)*2", "18"),
}

def validate_rows(rows):
    """Check that paired comparisons retain timing and use intended geometry."""
    for video_id in {r["video_id"] for r in rows}:
        group = {r["variant"]: r for r in rows if r["video_id"] == video_id}
        if len(group) != 1 + len(FILTERS) or len(group) != sum(r["video_id"] == video_id for r in rows):
            raise ValueError(f"Incomplete or duplicate cases for {video_id}")
        source, control = group["original"], group["encode_control"]
        w, h = source["width"], source["height"]
        geometry = {"original": (w, h), "encode_control": (w, h), "compression": (w, h),
                    "resize": (w//4*2, h//4*2), "crop": (int(w*0.8/2)*2, int(h*0.8/2)*2)}
        for variant, row in group.items():
            if row["frames"] != source["frames"] or abs(row["fps"] - source["fps"]) > 0.01:
                raise ValueError(f"Timing changed: {video_id}/{variant}")
            if (row["width"], row["height"]) != geometry[variant]:
                raise ValueError(f"Unexpected dimensions: {video_id}/{variant}")
            row["delta_vs_control"] = row["ai_score"] - control["ai_score"]
    return {"cases": len(rows), "geometry_and_timing_checks": "passed"}

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def download(url, dest, expected):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and sha(dest) == expected:
        return
    tmp = dest.with_suffix(".part")
    print(f"Downloading {dest.name}", flush=True)
    urllib.request.urlretrieve(url, tmp)
    if sha(tmp) != expected:
        tmp.unlink()
        raise ValueError(f"Checksum mismatch: {dest}")
    tmp.replace(dest)

def fetch(root):
    config = json.loads((root / "configs/samples.json").read_text())
    download(f"https://huggingface.co/MusapYildiz/aegis-video-detector/resolve/{MODEL_REV}/checkpoint_best.pt",
             root / "models/checkpoint_best.pt", MODEL_HASH)
    for sample in config["samples"]:
        url = f'https://huggingface.co/datasets/{config["dataset"]}/resolve/{config["revision"]}/{quote(sample["remote_path"], safe="/")}'
        download(url, root / f'data/original/{sample["id"]}.mp4', sample["sha256"])

def run(root):
    import cv2
    import imageio_ffmpeg
    config = json.loads((root / "configs/samples.json").read_text())
    if not (root / "models/checkpoint_best.pt").exists():
        raise FileNotFoundError("Run 'vidrobust fetch' first. Pretrained weights are mandatory.")
    if sha(root / "models/checkpoint_best.pt") != MODEL_HASH:
        raise ValueError("Checkpoint checksum mismatch")
    detector = AegisDetector(root)
    rows, commands = [], []
    for sample in config["samples"]:
        original = root / f'data/original/{sample["id"]}.mp4'
        if sha(original) != sample["sha256"]:
            raise ValueError(f"Source checksum mismatch: {original}")
        baseline = None
        for variant in ["original", *FILTERS]:
            path = original
            if variant != "original":
                path = root / f'data/variants/{sample["id"]}_{variant}.mp4'
                path.parent.mkdir(parents=True, exist_ok=True)
                filt, crf = FILTERS[variant]
                command = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(original), "-map", "0:v:0", "-an"]
                if filt:
                    command += ["-vf", filt]
                command += ["-c:v", "libx264", "-preset", "medium", "-crf", crf, "-pix_fmt", "yuv420p", str(path)]
                subprocess.run(command, check=True)
                commands.append([str(Path(arg).relative_to(root)) if arg.startswith(str(root) + "/") else arg for arg in command[1:]])
            start = time.perf_counter()
            score = detector.score(path)
            elapsed = time.perf_counter()-start
            if baseline is None:
                baseline = score
            cap = cv2.VideoCapture(str(path))
            width, height, frames, fps = [cap.get(k) for k in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FRAME_COUNT, cv2.CAP_PROP_FPS)]
            cap.release()
            rows.append(dict(video_id=sample["id"], label=sample["label"], generator=sample["generator"], variant=variant,
                             ai_score=score, delta=score-baseline, elapsed_sec=elapsed, width=int(width), height=int(height), frames=int(frames), fps=fps, sha256=sha(path)))
            print(f'{sample["id"]} {variant}: {score:.6f} (delta {score-baseline:+.6f})', flush=True)
    validation = validate_rows(rows)
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    with open(reports / "scores.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    metadata = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), detector=detector.name, epoch=detector.epoch, device="cpu", python=platform.python_version(), platform=platform.platform(),
                    model_revision=MODEL_REV, model_sha256=MODEL_HASH, dataset=config, ffmpeg=imageio_ffmpeg.get_ffmpeg_version(),
                    packages={name: importlib.metadata.version(name) for name in ["torch", "torchvision", "timm", "opencv-python-headless", "numpy"]},
                    preprocessing="upstream ImageNet normalization, centered 4s window, 16 frames, 224x224", transformations=commands)
    (reports / "run.json").write_text(json.dumps(metadata, indent=2))
    (reports / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    lines = ["# Robustness experiment with encoding control", "", f"{len(config['samples'])} source clips; paired scores only. Higher scores mean more AI-like according to AEGIS, not calibrated probabilities.", "",
             "| Clip (label) | Original | Encode control (CRF 18) | Compression (CRF 35) | Resize | Crop |", "|---|---:|---:|---:|---:|---:|"]
    for sample in config["samples"]:
        group = [r for r in rows if r["video_id"] == sample["id"]]
        lines.append(f'| {sample["id"]} ({sample["label"]}) | ' + " | ".join(f'{r["ai_score"]:.6f}' for r in group) + " |")
    largest = max((r for r in rows if r["variant"] != "original"), key=lambda r: abs(r["delta"]))
    lines += ["", f'Largest observed shift versus original: {largest["video_id"]} ({largest["label"]}), {largest["variant"]}: {largest["ai_score"]-largest["delta"]:.6f} → {largest["ai_score"]:.6f} (signed delta {largest["delta"]:+.6f}). This is a case to investigate, not an estimate of population robustness.', "",
              "The encode-only control uses exactly the resize/crop codec, CRF 18, preset, pixel format, and audio removal, with no spatial filter. Every variant still starts from the original.", "",
              "| Clip | Control − original | Compression − control | Resize − control | Crop − control |", "|---|---:|---:|---:|---:|"]
    for sample in config["samples"]:
        group = {r["variant"]: r for r in rows if r["video_id"] == sample["id"]}
        shifts = [group["encode_control"]["delta"], *[group[v]["delta_vs_control"] for v in ("compression", "resize", "crop")]]
        lines.append(f'| {sample["id"]} | ' + " | ".join(f"{d:+.6f}" for d in shifts) + " |")
    lines += ["", "See scores.csv for deltas versus both original and control, timings, dimensions, and hashes; run.json records exact inputs and environment. validation.json checks all case geometries and timing. Earlier four-clip experiments are preserved in milestone1/ and milestone2/.", "",
              "Control-relative differences help isolate spatial edits, but are not a causal decomposition: encoding interacts with image content and resolution. Compression versus control compares CRF 35 and CRF 18 encodes. This convenience sample does not establish accuracy, low-FPR performance, calibration, or population robustness. Dataset labels are inherited, not independently audited. Possible training overlap is unknown."]
    (reports / "comparison.md").write_text("\n".join(lines)+"\n")
    write_summary(root, config, rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["fetch", "run", "check", "diagnose", "compare"])
    args = parser.parse_args()
    if args.command == "compare":
        from .comparison import run_comparison
        run_comparison(ROOT)
    elif args.command == "diagnose":
        from .diagnostics import run_diagnostics
        run_diagnostics(ROOT)
    elif args.command == "check":
        import unittest
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
        if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
            raise SystemExit(1)
    else:
        {"fetch": fetch, "run": run}[args.command](ROOT)

if __name__ == "__main__":
    main()
