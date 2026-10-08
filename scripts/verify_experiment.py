"""Check complete run provenance/analysis, with optional published-score parity."""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from vidrobust.artifacts import sha
from vidrobust.experiment import analyze, inside, load_config
from vidrobust.experiment_report import summarize_decisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config")
    parser.add_argument("--variants", nargs="+", help="Compare only these variants with the reference; still validate the complete new run")
    parser.add_argument("--detectors", nargs="+", help="Compare only these detectors with the reference; still validate the complete new run")
    parser.add_argument("reference", nargs="?", help="Optional published scores.csv, relative to the repository root")
    args = parser.parse_args()
    config_path, manifest_path, config, samples = load_config(ROOT, args.config)
    out = ROOT / f"reports/experiments/{config['name']}"
    run = json.loads((out / "run.json").read_text())
    if sha(config_path) != run["config_sha256"] or sha(manifest_path) != run["manifest_sha256"]:
        raise ValueError("Run configuration or source manifest changed")
    for path, expected in run["code_sha256"].items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"Scoring code changed: {path}")
    for name, expected in run["model_sha256"].items():
        path = ROOT / run["models"][name]["checkpoint"]["path"]
        if sha(path) != expected:
            raise ValueError("Checkpoint changed")
    with (out / "scores.csv").open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for key in ("ai_score", "fps"):
            r[key] = float(r[key])
        for key in ("width", "height", "frames"):
            r[key] = int(r[key])
    if analyze(rows, config, samples) != json.loads((out / "summary.json").read_text()):
        raise ValueError("Independent CSV analysis differs from stored summary")
    ranking = config.get('analysis') == 'ranking'
    if ranking and (out / 'decisions.json').exists():
        raise ValueError('Ranking-only runs must not contain midpoint decisions')
    if not ranking and summarize_decisions(rows, config) != json.loads((out / "decisions.json").read_text()):
        raise ValueError("Independent CSV decisions differ from stored error/coverage counts")
    for r in rows:
        variant = next(v for v in config["variants"] if v["name"] == r["variant"])
        if variant["encoding"] == "source":
            path = inside(ROOT, config["source_directory"], "data") / f"{r['video_id']}.mp4"
        else:
            extension = "avi" if variant["encoding"] == "ffv1" else "mp4"
            path = ROOT / f"data/experiments/{config['name']}/{r['video_id']}_{r['variant']}.{extension}"
        if sha(path) != r["sha256"]:
            raise ValueError("Scored media changed")
    if not args.reference:
        if args.variants or args.detectors:
            raise ValueError("Reference subset filters require a reference CSV")
        validation_path = out / "validation.json"
        validation = json.loads(validation_path.read_text())
        validation["independent_run_checks"] = dict(model_scores=len(rows),
            independent_CSV_analysis="passed", independent_error_and_agreement_analysis=("not applicable; ranking-only" if ranking else "passed"),
            scored_media_and_model_and_code_hashes="passed", script_sha256=sha(Path(__file__).resolve()))
        validation_path.write_text(json.dumps(validation, indent=2)+"\n")
        print(f"Independent run verification passed: {len(rows)} scores; inputs, models, code, summaries and error/coverage counts")
        return
    reference_path = inside(ROOT, args.reference, "reports")
    with reference_path.open() as f:
        reference = {(r["video_id"], r["variant"], r["detector"]): r for r in csv.DictReader(f)}
    fields = ["ai_score", "fusion_logit", "pixel_score", "motion_score", "consistency_score"]
    compared_fields = set()
    selected = [r for r in rows if (not args.variants or r["variant"] in args.variants)
                and (not args.detectors or r["detector"] in args.detectors)]
    if not selected or (args.variants and set(args.variants) - {r["variant"] for r in rows}):
        raise ValueError("Reference selection is empty or has unknown variants")
    if args.detectors and set(args.detectors) - set(config["detectors"]):
        raise ValueError("Reference selection has unknown detectors")
    for r in selected:
        key = (r["video_id"], r["variant"], r["detector"])
        old = reference[key]
        for field in ("sha256", "label", "source", "sampled_rgb_sha256", "model_input_sha256"):
            if not old.get(field):
                continue
            if r[field] != old[field]:
                raise ValueError(f"Published {field} differs: {key}")
            compared_fields.add(field)
        for field in ("sampled_frame_indices", "frame_logits", "frame_scores"):
            if old.get(field):
                if json.loads(r[field]) != json.loads(old[field]):
                    raise ValueError(f"Published {field} differs: {key}")
                compared_fields.add(field)
        for field in fields + ["width", "height", "frames", "fps"]:
            if old.get(field):
                if float(r[field]) != float(old[field]):
                    raise ValueError(f"Published {field} differs: {key}")
                compared_fields.add(field)
    validation_path = out / "validation.json"
    validation = json.loads(validation_path.read_text())
    validation["published_reference_parity"] = dict(reference=args.reference, reference_sha256=sha(reference_path),
        matched_scores=len(selected), exact_match=True, compared_fields=sorted(compared_fields),
        independent_CSV_analysis="passed", independent_error_and_agreement_analysis="passed", scored_media_and_model_and_code_hashes="passed")
    validation_path.write_text(json.dumps(validation, indent=2)+"\n")
    print(f"Exact parity: {len(selected)} scores; inputs, available logits and frame lists match {args.reference}")


if __name__ == "__main__":
    main()
