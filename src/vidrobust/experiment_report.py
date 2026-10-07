"""One report format for every experiment config."""
import csv
import json
import os


def write_results(root, out, config, samples, rows, summary, metadata, validation):
    fields = sorted({k for r in rows for k in r})
    with (out / "scores.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for name, value in (("summary", summary), ("run", metadata), ("validation", validation)):
        (out / f"{name}.json").write_text(json.dumps(value, indent=2)+"\n")
    plot_pairs(root, out, config, samples, rows)
    lines = [f"# {config['name']}", "",
        f"{len(samples)} clips × {len(config['variants'])} variants × {len(config['detectors'])} detectors = {len(rows)} scores.", "",
        f"Baseline: **{config['baseline']}**. Preparation: `{config['preparation']}`.", "",
        "![Scores before and after each edit](pairs.png)", "",
        "Higher scores mean more AI-like. Scores are uncalibrated; 0.5 is a fixed reference, not a validated decision threshold.", "",
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
        "WaveRep averages 16 frame logits before applying sigmoid; AEGIS uses its released fusion head. "
        "Inference runs on CPU with four threads. Configs and source manifests must be committed before scoring.", "",
        "These clips measure score changes, not general detector accuracy. Labels come from the dataset. "
        "Source quality and training overlap are unknown. Common preparation changes geometry and can change sampled physical frames; "
        "comparisons within the prepared variants keep those choices fixed.", ""]
    if config.get("notes"):
        lines += [config["notes"], ""]
    lines += [f"Reproduce: `uv run python run.py experiment {metadata['config_path']}`.", "",
        "[Scores and logits](scores.csv) · [Summary](summary.json) · [Config, hashes and preparation commands](run.json) · [Checks](validation.json)", ""]
    (out / "report.md").write_text("\n".join(lines))


def plot_pairs(root, out, config, samples, rows):
    os.environ.setdefault("MPLCONFIGDIR", str(root / "data/.matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cells = sorted({s.get("cell", s["label"]) for s in samples})
    edits = [v["name"] for v in config["variants"] if v["name"] != config["baseline"]]
    indexed = {(r["video_id"], r["variant"], r["detector"]): r for r in rows}
    columns = min(2, len(cells))
    fig, axes = plt.subplots((len(cells)+columns-1)//columns, columns, squeeze=False,
        figsize=(6*columns, 3.5*((len(cells)+columns-1)//columns)), layout="constrained")
    plt.rcParams["svg.hashsalt"] = "video-robustness"
    colors = {"aegis": "#2563eb", "waverep": "#d97706"}
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
                ax.scatter(b, y, facecolors="white", edgecolors=colors[d], marker=marker, s=35,
                           label=f"{d}: {v}" if i == 0 else None)
        ax.set_yticks(range(len(group)), [s["id"].rsplit("_", 1)[-1] for s in group])
        ax.invert_yaxis()
        ax.set_xlim(-.03, 1.03)
        ax.axvline(.5, color="#64748b", ls=":", lw=1)
        ax.set_xlabel("AI-like score")
        ax.set_title(f"{cell.replace('_', ' ')} · n={len(group)}")
        ax.grid(axis="x", alpha=.2)
        ax.legend(fontsize=8)
    for ax in list(axes.flat)[len(cells):]:
        ax.set_visible(False)
    fig.suptitle(f"{config['name']}\nFilled = {config['baseline']} · hollow = edited", fontweight="bold")
    fig.savefig(out / "pairs.png", dpi=180)
    svg = out / "pairs.svg"
    fig.savefig(svg, metadata={"Date": None})
    plt.close(fig)
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
