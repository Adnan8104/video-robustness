"""Reproduce a native config, then check its clips through the demo service."""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, inside, load_config, run_experiment
from vidrobust.inference import DetectionService
from vidrobust.registry import get_adapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="Committed native config with one unchanged-source variant")
    args = parser.parse_args()
    config_path, manifest_path, config, samples = load_config(ROOT, args.config)
    if config["preparation"] != "native" or len(config["variants"]) != 1 or config["variants"][0] != {
        "name": config["baseline"], "transform": "identity", "encoding": "source"
    }:
        parser.error("Section checks require native preparation and one unchanged-source variant")
    if any(sample["label"] != "real" for sample in samples):
        parser.error("This follow-up summarizes real-only configs")
    manifest = json.loads(manifest_path.read_text())
    paths = [config_path, manifest_path, Path(__file__).resolve()]
    if manifest.get("selection_policy"):
        paths.append(inside(ROOT, manifest["selection_policy"]))
    frozen = {str(p.relative_to(ROOT)): frozen_revision(ROOT, p) for p in paths}
    paths += [p for p in (ROOT / "src/vidrobust").rglob("*.py") if "legacy" not in p.parts]
    paths += list((ROOT / "vendor/aegis").glob("*.py"))
    code_hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    # The shared runner verifies source downloads/full decodes and records runtime versions.
    reference = run_experiment(ROOT, args.config)
    service = DetectionService(ROOT)
    checks, flat = [], []
    for sample in samples:
        source = inside(ROOT, config["source_directory"], "data") / (sample["id"] + ".mp4")
        assert sha(source) == sample["sha256"], sample["id"]
        result = service.analyze(source.read_bytes(), source.name, names=tuple(config["detectors"]),
            scan_sections=True, progress=lambda stage: print(sample["id"], stage, flush=True))
        assert result["input_sha256"] == sample["sha256"]
        assert result["metadata"] == sample["actual_metadata"]
        assert len({tuple(w["sampled_frame_indices"]) for w in result["windows"]}) == len(result["windows"])
        for window in result["windows"]:
            assert len(window["sampled_frame_indices"]) == len(set(window["sampled_frame_indices"])) == 16
            assert len({r["sampled_rgb_sha256"] for r in window["detectors"]}) == 1
            for row in window["detectors"]:
                if window["section"] == "middle":
                    previous = next(r for r in reference if r["video_id"] == sample["id"] and r["detector"] == row["detector"])
                    for key in ("ai_score", "fusion_logit", "sampled_rgb_sha256", "model_input_sha256"):
                        assert previous[key] == row[key], (sample["id"], key)
                    assert json.loads(previous["sampled_frame_indices"]) == window["sampled_frame_indices"]
                flat.append(dict(video_id=sample["id"], cell=sample["cell"], content=sample["content"],
                    section=window["section"], start_seconds=window["sampled_time_seconds"][0],
                    end_seconds=window["sampled_time_seconds"][-1], detector=row["detector"], ai_score=row["ai_score"]))
        checks.append(dict(video_id=sample["id"], cell=sample["cell"], content=sample["content"], result=result))
    for name in config["detectors"]:
        checkpoint = get_adapter(name).adapter.checkpoint
        assert sha(ROOT / checkpoint["path"]) == checkpoint["sha256"]
    assert all(sha(ROOT / path) == digest for path, digest in code_hashes.items())
    summary = {}
    for name in config["detectors"]:
        summary[name] = {}
        for cell in sorted({s["cell"] for s in samples} | {"all"}):
            selected = [r for r in flat if r["detector"] == name and (cell == "all" or r["cell"] == cell)]
            middle = [r for r in selected if r["section"] == "middle"]
            summary[name][cell] = dict(clips=len(middle), windows=len(selected),
                middle_at_or_above_point5=sum(r["ai_score"] >= .5 for r in middle),
                any_section_at_or_above_point5=len({r["video_id"] for r in selected if r["ai_score"] >= .5}),
                windows_at_or_above_point5=sum(r["ai_score"] >= .5 for r in selected))
    out = ROOT / "reports/experiments" / config["name"]
    report = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), frozen_commits=frozen,
        config_path=args.config, code_sha256=code_hashes, checks=checks, summary=summary,
        validation=dict(source_and_checkpoint_hashes="passed", centered_scores_logits_and_inputs_match_runner="passed",
            shared_RGB_and_unique_indices="passed", frozen_code_and_config="passed"))
    (out / "sections.json").write_text(json.dumps(report, indent=2) + "\n")
    with (out / "sections.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(flat)
    plot_sections(out, config, samples, flat)
    lines = [f"# {config['name']}: real footage by section", "",
        f"{len(samples)} archived real clips; {len(flat)//len(config['detectors'])} distinct sampled windows per detector. "
        "Each model receives the same 16 RGB frames in each window.", "",
        "![Section scores](sections.png)", "",
        "| Detector | Group | Clips | Middle ≥0.5 | Any section ≥0.5 | Windows ≥0.5 / sampled |",
        "|---|---|---:|---:|---:|---:|"]
    for name, groups in summary.items():
        for group, s in groups.items():
            lines.append(f"| {name} | {group} | {s['clips']} | {s['middle_at_or_above_point5']} | {s['any_section_at_or_above_point5']} | {s['windows_at_or_above_point5']}/{s['windows']} |")
    lines += ["", "0.5 is an uncalibrated reference midpoint. A high score conflicts with the real source label; "
        "it does not establish that a video is AI-generated. Any-section counts give more opportunities for a high score than middle-only counts.", "",
        "## Every score", "",
        "| Clip | Content | Section | Sampled seconds | " + " | ".join(config["detectors"]) + " |",
        "|---|---|---|---|" + "---:|" * len(config["detectors"])]
    for check in checks:
        for window in check["result"]["windows"]:
            scores = {r["detector"]: r["ai_score"] for r in window["detectors"]}
            times = window["sampled_time_seconds"]
            values = " | ".join(f"{scores[name]:.6f}" for name in config["detectors"])
            lines.append(f"| {check['video_id']} | {check['content']} | {window['section']} | {times[0]:.2f}–{times[-1]:.2f} | {values} |")
    lines += ["", "## What this test establishes", "",
        f"Source dataset: `{manifest.get('dataset', 'see manifest')}`. "
        "Selection and source labels were fixed before inference. " + config.get("notes", ""), "",
        f"[Frozen source manifest](../../../{config['manifest']})" +
        (f" · [Selection policy](../../../{manifest['selection_policy']})" if manifest.get("selection_policy") else ""), "",
        "Source bytes are unchanged. No resizing, cropping or re-encoding is added by this check; "
        "each detector still uses its own native preprocessing. All shortest sides are at least 504 pixels, "
        "so WaveRep adds no padding. WaveRep evaluates only its central 504×504 region with 16 frames, "
        "rather than the upstream full-video evaluation.", "",
        "Beginning/middle/end windows can overlap on clips shorter than 12 seconds. Identical windows are "
        "deduplicated. These are not independent videos or a population false-positive rate. "
        "A real-only panel cannot measure AI-detection recall or identify the better model overall. "
        "Training overlap, source quality and the exact visual trigger remain unknown.", "",
        "Checks passed: full source decodes, source/checkpoint hashes, identical RGB inputs between models, "
        "and exact middle-window score/logit/input-hash reproduction against the config runner. "
        "The models and thresholds were not changed.", "",
        f"Reproduce: `uv run python scripts/check_sections.py {args.config}`.", "",
        "[Raw section scores and hashes](sections.json) · [CSV](sections.csv) · [Runtime provenance](run.json)", ""]
    (out / "sections.md").write_text("\n".join(lines))
    print(json.dumps(summary, indent=2), flush=True)


def plot_sections(out, config, samples, rows):
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data/.matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(config["detectors"]), figsize=(5.5*len(config["detectors"]), 6),
        sharey=True, squeeze=False, layout="constrained")
    axes = axes[0]
    colors = {"beginning": "#2563eb", "middle": "#d97706", "end": "#059669"}
    offsets = {"beginning": -.2, "middle": 0, "end": .2}
    for axis, name in zip(axes, config["detectors"]):
        for section in colors:
            selected = [r for r in rows if r["detector"] == name and r["section"] == section]
            axis.scatter([r["ai_score"] for r in selected],
                [next(i for i, s in enumerate(samples) if s["id"] == r["video_id"]) + offsets[section] for r in selected],
                color=colors[section], marker={"beginning": "o", "middle": "s", "end": "^"}[section], label=section, s=45)
        axis.set_xlim(-.03, 1.03); axis.axvline(.5, color="#64748b", ls=":")
        axis.set_title(name.upper()); axis.set_xlabel("AI-like score (uncalibrated)"); axis.grid(axis="x", alpha=.2)
        axis.legend(loc="lower right")
    axes[0].set_yticks(range(len(samples)), [s["content"] for s in samples]); axes[0].invert_yaxis()
    fig.suptitle("Archived real footage: scores by section", fontweight="bold")
    fig.savefig(out / "sections.png", dpi=180); plt.close(fig)


if __name__ == "__main__":
    main()
