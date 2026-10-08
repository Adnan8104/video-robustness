"""One report format for every experiment config."""
import csv
import json
import math
import os


def summarize_decisions(rows, config):
    """Describe fixed-midpoint errors and the coverage cost of model agreement."""
    variants = [v["name"] for v in config["variants"]]
    names = config["detectors"]
    clips = {r["video_id"] for r in rows}
    indexed = {(r["video_id"], r["variant"], r["detector"]): r for r in rows}
    expected = {(clip, variant, name) for clip in clips for variant in variants for name in names}
    if not clips or len(indexed) != len(rows) or set(indexed) != expected:
        raise ValueError("Decision analysis needs a complete, unique paired matrix")
    labels = {}
    for row in rows:
        if row["label"] not in ("real", "ai") or not math.isfinite(row["ai_score"]) or not 0 <= row["ai_score"] <= 1:
            raise ValueError("Invalid decision-analysis label or score")
        if labels.setdefault(row["video_id"], row["label"]) != row["label"]:
            raise ValueError("Paired rows disagree on source label")
    result = {}
    for variant in variants:
        models = {}
        for name in names:
            counts = dict(real_clips=sum(label == "real" for label in labels.values()),
                ai_clips=sum(label == "ai" for label in labels.values()), real_to_ai=0, ai_to_real=0)
            for clip, label in labels.items():
                high = indexed[(clip, variant, name)]["ai_score"] >= .5
                counts["real_to_ai"] += label == "real" and high
                counts["ai_to_real"] += label == "ai" and not high
            models[name] = counts
        agreement = dict(clips=len(clips), agreed_ai=0, agreed_real=0, inconclusive=0,
            real_to_ai=0, ai_to_real=0, correct_agreed=0)
        for clip, label in labels.items():
            high = {indexed[(clip, variant, name)]["ai_score"] >= .5 for name in names}
            if len(high) != 1:
                agreement["inconclusive"] += 1
            else:
                predicted_ai = high.pop()
                agreement["agreed_ai" if predicted_ai else "agreed_real"] += 1
                agreement["real_to_ai"] += label == "real" and predicted_ai
                agreement["ai_to_real"] += label == "ai" and not predicted_ai
                agreement["correct_agreed"] += predicted_ai == (label == "ai")
        agreement["agreed_clips"] = agreement["agreed_ai"] + agreement["agreed_real"]
        result[variant] = dict(models=models, agreement=agreement)
    return result


def write_results(root, out, config, samples, rows, summary, metadata, validation):
    fields = sorted({k for r in rows for k in r})
    with (out / "scores.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for name, value in (("summary", summary), ("run", metadata), ("validation", validation)):
        (out / f"{name}.json").write_text(json.dumps(value, indent=2)+"\n")
    decisions = summarize_decisions(rows, config)
    (out / "decisions.json").write_text(json.dumps(decisions, indent=2)+"\n")
    plot_pairs(root, out, config, samples, rows)
    lines = [f"# {config['name']}", "",
        f"{len(samples)} clips × {len(config['variants'])} variants × {len(config['detectors'])} detectors = {len(rows)} scores.", "",
        f"Baseline: **{config['baseline']}**. Preparation: `{config['preparation']}`.", "",
        "![Detector scores](pairs.png)", "",
        "Higher scores mean more AI-like. Scores are uncalibrated; 0.5 is a fixed reference, not a validated decision threshold.", "",
        "## Both error directions", "",
        "| Variant | Detector | Real scored AI-like / real clips | AI scored real-like / AI clips |",
        "|---|---|---:|---:|"]
    for variant, decision in decisions.items():
        for name, counts in decision["models"].items():
            real = f"{counts['real_to_ai']}/{counts['real_clips']}" if counts["real_clips"] else "—"
            ai = f"{counts['ai_to_real']}/{counts['ai_clips']}" if counts["ai_clips"] else "—"
            lines.append(f"| {variant} | {name} | {real} | {ai} |")
    lines += ["", "## When models agree", "",
        "All scores ≥0.5: AI-like. All scores <0.5: real-like. Mixed sides: inconclusive. "
        "This fixed rule measures a coverage/error tradeoff; agreement does not establish authenticity.", "",
        "| Variant | Agreed clips / all | Correct agreed | Real scored AI-like | AI scored real-like | Inconclusive |",
        "|---|---:|---:|---:|---:|---:|"]
    for variant, decision in decisions.items():
        a = decision["agreement"]
        lines.append(f"| {variant} | {a['agreed_clips']}/{a['clips']} | {a['correct_agreed']} | {a['real_to_ai']} | {a['ai_to_real']} | {a['inconclusive']} |")
    lines += ["", "Inconclusive clips stay in the denominator; they are not counted as correct predictions. "
        "Inspect per-source counts below because source and content can affect these totals.", "",
        "## Changes from baseline", "",
        "| Detector | Variant | Group | Clips | Median change | Median absolute change | Changes ≥0.10 | Scores against label at 0.5 | Crossings |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for d, variants in summary.items():
        for v, groups in variants.items():
            for cell, m in groups.items():
                lines.append(f"| {d} | {v} | {cell} | {m['n']} | {m['median_delta']:+.6f} | {m['median_absolute_delta']:.6f} | {m['changes_at_least_point10']} | {m['midpoint_conflicts']} | {len(m['midpoint_crossings'])} |")
    lines += ["", "## Scores", "", "| Clip | Label | Detector | Variant | Score | Change |",
              "|---|---|---|---|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['video_id']} | {r['label']} | {r['detector']} | {r['variant']} | {r['ai_score']:.6f} | {r['delta_vs_baseline']:+.6f} |")
    lines += ["", "## Run details", "",
        "Every variant starts independently from the source or the common lossless master. "
        "Models receive the same decoded RGB frames, with their own native preprocessing. "
        "Inference runs on CPU with four threads. Configs and source manifests must be committed before scoring.", "",
        "These clips measure score changes, not general detector accuracy. Labels come from the dataset. "
        "Source quality and training overlap are unknown. Common preparation changes geometry and can change sampled physical frames; "
        "comparisons within the prepared variants keep those choices fixed.", ""]
    lines += ["| Adapter | Native preprocessing and aggregation |", "|---|---|"]
    for name, model in metadata["models"].items():
        lines.append(f"| {name} | {model['preprocessing']} |")
    lines.append("")
    if config.get("notes"):
        lines += [config["notes"], ""]
    lines += [f"Reproduce: `uv run python run.py experiment {metadata['config_path']}`.", "",
        "[Scores and logits](scores.csv) · [Summary](summary.json) · [Errors and agreement](decisions.json) · [Config, hashes and preparation commands](run.json) · [Checks](validation.json)", ""]
    (out / "report.md").write_text("\n".join(lines))


def plot_pairs(root, out, config, samples, rows, basename="pairs", compression_hero=True):
    os.environ.setdefault("MPLCONFIGDIR", str(root / "data/.matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cells = sorted({s.get("cell", s["label"]) for s in samples})
    edits = [v["name"] for v in config["variants"] if v["name"] != config["baseline"]]
    indexed = {(r["video_id"], r["variant"], r["detector"]): r for r in rows}
    columns = min(2, len(cells))
    fig, axes = plt.subplots((len(cells)+columns-1)//columns, columns, squeeze=False,
        figsize=(6*columns, 5*((len(cells)+columns-1)//columns)), layout="constrained")
    plt.rcParams["svg.hashsalt"] = "video-robustness"
    palette = ["#2563eb", "#d97706", "#059669", "#9333ea", "#dc2626", "#0891b2"]
    colors = {name: palette[i % len(palette)] for i, name in enumerate(config["detectors"])}
    markers = ["o", "s", "^", "D", "v", "P", "X"]
    for ax, cell in zip(axes.flat, cells):
        group = [s for s in samples if s.get("cell", s["label"]) == cell]
        comparisons = [(d, v) for d in config["detectors"] for v in (edits or [config["baseline"]])]
        for offset, (d, v) in enumerate(comparisons):
            for i, s in enumerate(group):
                a = indexed[(s["id"], config["baseline"], d)]["ai_score"]
                b = indexed[(s["id"], v, d)]["ai_score"]
                y = i + (offset-(len(comparisons)-1)/2)*(.6/max(len(comparisons), 1))
                marker = markers[offset % len(markers)]
                ax.plot([a, b], [y, y], color=colors[d], alpha=.65, lw=1.3)
                ax.scatter(a, y, color=colors[d], marker=marker, s=35)
                if edits:
                    ax.scatter(b, y, facecolors="white", edgecolors=colors[d], marker=marker, s=35,
                               label=f"{d}: {v}" if i == 0 else None)
                elif i == 0:
                    ax.scatter(a, y, color=colors[d], marker=marker, s=35, label=d)
        ax.set_yticks(range(len(group)), [s["id"].rsplit("_", 1)[-1] for s in group])
        ax.invert_yaxis()
        ax.set_xlim(-.03, 1.03)
        ax.axvline(.5, color="#64748b", ls=":", lw=1)
        ax.set_xlabel("AI-like score")
        ax.set_title(f"{cell.replace('_', ' ')} · n={len(group)}")
        ax.grid(axis="x", alpha=.2)
        ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(.5, -.16), ncol=2)
    for ax in list(axes.flat)[len(cells):]:
        ax.set_visible(False)
    caption = f"Filled = {config['baseline']} · hollow = edited" if edits else "Unchanged source scores"
    fig.suptitle(f"{config['name']}\n{caption}", fontweight="bold")
    fig.savefig(out / f"{basename}.png", dpi=180)
    svg = out / f"{basename}.svg"
    fig.savefig(svg, metadata={"Date": None})
    plt.close(fig)
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")

    # Keep a focused compression pair for the README while the full figure covers every edit.
    if compression_hero and "compression" in edits and len(edits) > 1:
        pair_config = config | {"variants": [v for v in config["variants"] if v["name"] in (config["baseline"], "compression")]}
        plot_pairs(root, out, pair_config, samples, rows, basename="compression-pairs", compression_hero=False)
