"""Descriptive paired summaries; no population accuracy or significance estimates."""
from pathlib import Path
from statistics import median
import json

SHIFT_CUTOFF = 0.10

def write_summary(root: Path, config: dict, rows: list[dict]):
    old_ids = set(config.get("selection", {}).get("retained_discovery_ids", []))
    source_order = list(dict.fromkeys(s["generator"] for s in config["samples"]))
    metrics = []
    for cohort, ids in [("all", {s["id"] for s in config["samples"]}),
                        ("new", {s["id"] for s in config["samples"]} - old_ids)]:
        for source in source_order:
            subset = [r for r in rows if r["video_id"] in ids and r["generator"] == source]
            originals = [r["ai_score"] for r in subset if r["variant"] == "original"]
            if not originals:
                continue
            conditions = {}
            for variant in ("encode_control", "compression", "resize", "crop"):
                values = [r["delta"] if variant == "encode_control" else r["delta_vs_control"]
                          for r in subset if r["variant"] == variant]
                conditions[variant] = dict(median_signed_delta=median(values),
                    median_absolute_delta=median(abs(v) for v in values),
                    sizable_shift_count=sum(abs(v) >= SHIFT_CUTOFF for v in values),
                    minimum_delta=min(values), maximum_delta=max(values))
            metrics.append(dict(cohort=cohort, source=source, clips=len(originals),
                                median_original_score=median(originals), conditions=conditions))
    largest_per_clip = []
    for sample in config["samples"]:
        candidates = [r for r in rows if r["video_id"] == sample["id"]
                      and r["variant"] in ("compression", "resize", "crop")]
        r = max(candidates, key=lambda r: abs(r["delta_vs_control"]))
        largest_per_clip.append(dict(video_id=r["video_id"],source=r["generator"],
            new_clip=r["video_id"] not in old_ids,variant=r["variant"],
            control_score=r["ai_score"]-r["delta_vs_control"],score=r["ai_score"],delta=r["delta_vs_control"]))
    largest_per_clip.sort(key=lambda r: abs(r["delta"]), reverse=True)
    result = dict(source_clips=len(config["samples"]),scored_cases=len(rows),
        new_source_clips=len(config["samples"])-len(old_ids),shift_cutoff=SHIFT_CUTOFF,
        cutoff_meaning="Descriptive score-change cutoff, not confidence or a detection threshold.",
        groups=metrics,largest_shift_per_clip=largest_per_clip)
    (root/"reports/summary.json").write_text(json.dumps(result,indent=2)+"\n")
    lines = ["# Expanded paired score experiment", "",
             f"{result['source_clips']} source clips, {result['scored_cases']} scored cases, {result['new_source_clips']} newly selected clips. The original four discovery clips remain in the panel.", "",
             "The manifest and descriptive rule were committed before expanded scoring; see [selection policy](../configs/selection.md). Score changes of at least 0.10 are counted as sizable output shifts for this report. This cutoff is not a confidence threshold or a significance test."]
    for cohort, title in [("all","All selected clips"),("new","Newly selected clips only")]:
        lines += ["",f"## {title}","",
            "| Source | Clips | Median original score | Encode shift ≥0.10 | Compression shift ≥0.10 | Resize shift ≥0.10 | Crop shift ≥0.10 |",
            "|---|---:|---:|---:|---:|---:|---:|"]
        for m in metrics:
            if m["cohort"] != cohort:
                continue
            counts = [m["conditions"][v]["sizable_shift_count"] for v in ("encode_control","compression","resize","crop")]
            lines.append(f"| {m['source']} | {m['clips']} | {m['median_original_score']:.6f} | " + " | ".join(str(n) for n in counts) + " |")
    lines += ["","## Median absolute score changes (all clips)","",
        "| Source | Encode control − original | Compression − control | Resize − control | Crop − control |",
        "|---|---:|---:|---:|---:|"]
    for m in metrics:
        if m["cohort"] == "all":
            values = [m["conditions"][v]["median_absolute_delta"] for v in ("encode_control","compression","resize","crop")]
            lines.append(f"| {m['source']} | " + " | ".join(f"{v:.6f}" for v in values) + " |")
    lines += ["","## Largest change per clip (top five)","",
              "| Clip | Source | Newly selected? | Condition | Control score | Variant score | Signed change |",
              "|---|---|---|---|---:|---:|---:|"]
    for r in largest_per_clip[:5]:
        lines.append(f"| {r['video_id']} | {r['source']} | {'yes' if r['new_clip'] else 'no'} | {r['variant']} | {r['control_score']:.6f} | {r['score']:.6f} | {r['delta']:+.6f} |")
    lines += ["", "[All paired scores](comparison.md) · [Raw scores](scores.csv) · [Run metadata](run.json)", "",
        "The size cap, filename ordering, one real-video dataset, and five clips per generator make this a convenience sample. Existing discovery cases are not independent confirmation. Low shifts can also reflect saturated scores near zero or one. Labels are inherited, training overlap is unknown, and re-encoding interacts with spatial edits. These results do not estimate population robustness, accuracy, calibration, or low-FPR performance. All variants of a clip are paired observations, not independent samples."]
    (root/"reports/summary.md").write_text("\n".join(lines)+"\n")
