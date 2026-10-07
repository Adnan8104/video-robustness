"""Measured outputs only: concise comparison, paired plots and explicit limits."""
import os
import json
from .comparison import VARIANTS, pair_rows
from .diagnostics import curve_metrics


def compression_metrics(config, pairs):
    result = {}
    levels = [(18, "encode_control"), (23, "crf_23"), (28, "crf_28"), (32, "crf_32"), (35, "compression")]
    for clip in config["sweep_ids"]:
        result[clip] = {}
        for detector in ("aegis", "waverep"):
            points = [pairs[clip, variant][detector] | dict(crf=crf, variant=f"crf_{crf}") for crf, variant in levels]
            result[clip][detector] = curve_metrics(points)
    return result


def plot_results(root, config, rows):
    os.environ.setdefault("MPLCONFIGDIR", str(root / "data/.matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "svg.hashsalt": "video-robustness"})
    out = root / "reports/two-detectors"
    pairs = pair_rows(rows)
    colors = {"aegis": "#2563eb", "waverep": "#ea580c"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), layout="constrained")
    panels = [("real_01", ["encode_control", "crf_23", "crf_28", "crf_32", "compression"],
               ["18", "23", "28", "32", "35"], "MSVD rodent: compression sweep", "CRF (higher = stronger compression)"),
              ("davis_04", VARIANTS, ["Original", "CRF 18", "CRF 35", "Resize", "Crop"],
               "DAVIS bear: five conditions", "Condition")]
    for ax, (clip, variants, labels, title, xlabel) in zip(axes, panels):
        for detector in ("aegis", "waverep"):
            positions = [18, 23, 28, 32, 35] if clip == "real_01" else list(range(len(variants)))
            ax.plot(positions, [pairs[clip, v][detector]["ai_score"] for v in variants],
                    marker="o", label=detector.upper() if detector == "aegis" else "WaveRep (sparse16)", color=colors[detector])
        ax.set_xticks(positions, labels)
        ax.set_ylim(-.03, 1.03)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.axhline(.5, color="#64748b", linestyle=":", linewidth=1)
        ax.grid(alpha=.2)
    axes[0].set_ylabel("Model-specific AI-like score")
    axes[1].legend(fontsize=8, loc="best")
    fig.suptitle("Two source-labeled real clips: models disagree", fontweight="bold")
    save(fig, out, "known-cases")
    plt.close(fig)

    fresh = [s for s in config["samples"] if s["cohort"] == "fresh"]
    fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
    for i, sample in enumerate(fresh):
        group = pairs[sample["id"], "original"]
        values = [group[d]["ai_score"] for d in ("aegis", "waverep")]
        ax.plot(values, [i, i], color="#cbd5e1", linewidth=1.5, zorder=1)
        for detector, value in zip(("aegis", "waverep"), values):
            ax.scatter(value, i, color=colors[detector], s=38, zorder=2,
                       label=("AEGIS" if detector == "aegis" else "WaveRep (sparse16)") if i == 0 else None)
    ax.set_yticks(range(len(fresh)), [f"{s['id']} ({s['generator']}; {s['label']})" for s in fresh])
    ax.invert_yaxis()
    ax.set_xlim(-.03, 1.03)
    ax.set_xlabel("Model-specific AI-like score (uncalibrated)")
    ax.set_title("Ten fresh clips: original-condition scores")
    ax.axvline(.5, color="#64748b", linestyle=":", linewidth=1)
    ax.grid(axis="x", alpha=.2)
    ax.legend(fontsize=8, loc="best")
    save(fig, out, "fresh-scores")
    plt.close(fig)


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=180)
    path = out / f"{name}.svg"
    fig.savefig(path, metadata={"Date": None})
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def write_report(root, config, rows, summary):
    out = root / "reports/two-detectors"
    pairs = pair_rows(rows)
    curves = compression_metrics(config, pairs)
    (out / "curve-summary.json").write_text(json.dumps(curves, indent=2) + "\n")
    high_wave_known = sum(pairs[clip, "original"]["waverep"]["ai_score"] >= .5 for clip in ("real_01", "davis_04"))
    a_fresh, w_fresh = summary["fresh"]["aegis"], summary["fresh"]["waverep"]
    lines = ["# AEGIS and WaveRep: paired robustness comparison", "",
        "35 source clips: 25 previous and ten fresh. Five standard conditions plus retained compression-sweep points produce 187 paired cases (374 model scores). 137 published AEGIS cases are reused after byte/hash and provenance checks; 50 new AEGIS and all 187 WaveRep cases are scored.", "",
        "[Frozen selection](../../configs/two-detectors-selection.md) · [Input manifest](../../configs/two-detectors.json)", "",
        "## Findings", "",
        f"WaveRep gives scores above the descriptive midpoint on {high_wave_known}/2 known real originals that AEGIS scores highly. On the rodent, original scores are AEGIS {pairs['real_01','original']['aegis']['ai_score']:.6f} and WaveRep {pairs['real_01','original']['waverep']['ai_score']:.6f}; on the bear they are {pairs['davis_04','original']['aegis']['ai_score']:.6f} and {pairs['davis_04','original']['waverep']['ai_score']:.6f}, respectively.", "",
        f"On ten fresh originals, AEGIS has {a_fresh['real_midpoint_conflicts']} real-label and {a_fresh['ai_midpoint_conflicts']} AI-label midpoint conflicts; WaveRep has {w_fresh['real_midpoint_conflicts']} and {w_fresh['ai_midpoint_conflicts']}. The models disagree across the midpoint on {summary['fresh']['original_midpoint_disagreements']}/10 originals. These are descriptive small-panel counts, not an accuracy ranking.", "",
        f"The fresh real panda clip (`fresh_real_05`) scores {pairs['fresh_real_05','original']['aegis']['ai_score']:.6f} with AEGIS and {pairs['fresh_real_05','original']['waverep']['ai_score']:.6f} with WaveRep. AEGIS remains at {pairs['fresh_real_05','compression']['aegis']['ai_score']:.6f} after strong compression. This adds another high-score real-animal case, but the earlier compression drop does not repeat on it. Animal content alone is not a controlled explanation.", "",
        f"The fresh generated coastal-road clip (`fresh_sora_03`) scores {pairs['fresh_sora_03','original']['aegis']['ai_score']:.6f} with AEGIS; resizing raises it to {pairs['fresh_sora_03','resize']['aegis']['ai_score']:.6f}, and cropping to {pairs['fresh_sora_03','crop']['aegis']['ai_score']:.6f}. WaveRep's original score is {pairs['fresh_sora_03','original']['waverep']['ai_score']:.6f}, falling to {pairs['fresh_sora_03','compression']['waverep']['ai_score']:.6f} after strong compression. The fresh panel contains both original-label conflicts and edit-sensitive decisions.", "",
        f"For fresh compression/resize/crop conditions, AEGIS has {a_fresh['changes_at_least_point10']}/30 changes of at least 0.10 relative to the encode-only control; WaveRep has {w_fresh['changes_at_least_point10']}/30. A correct-looking original score does not establish transformation stability.", "",
        "## Known real cases", "", "![Known cases](known-cases.png)", "",
        "| Case | Model | Original | CRF 18 | CRF 35 | Resize | Crop | Compression − control |",
        "|---|---|---:|---:|---:|---:|---:|---:|"]
    for clip in ("real_01", "davis_04"):
        for detector in ("aegis", "waverep"):
            values = [pairs[clip, v][detector]["ai_score"] for v in VARIANTS]
            delta = pairs[clip, "compression"][detector]["delta_vs_control"]
            lines.append(f"| {clip} | {detector} | " + " | ".join(f"{v:.6f}" for v in values) + f" | {delta:+.6f} |")
    lines += ["", "Scores are model-specific and uncalibrated. Agreement or disagreement on these exact cases does not identify a shared learned mechanism or establish general superiority.", "",
        "| Sweep clip | Model | Largest CRF step | Signed change | Midpoint crossings | Non-monotone? |",
        "|---|---|---|---:|---|---|"]
    for clip, models in curves.items():
        for detector, metric in models.items():
            step = metric["largest_step"]
            crossings = ", ".join(f"{p['from_crf']}–{p['to_crf']}" for p in metric["midpoint_crossings"]) or "none"
            lines.append(f"| {clip} | {detector} | {step['from_crf']}–{step['to_crf']} | {step['delta']:+.6f} | {crossings} | {'yes' if metric['non_monotone'] else 'no'} |")
    lines += ["", "All five sampled levels and signed steps per CRF are retained in [curve metrics](curve-summary.json). The sparse grid and CRF's non-linear quality scale limit transition interpretation.", "",
        "## Fresh clips", "", "![Fresh original scores](fresh-scores.png)", "",
        "| Clip | Source label | AEGIS original | WaveRep original | Midpoint disagreement? |",
        "|---|---|---:|---:|---|"]
    for sample in config["samples"]:
        if sample["cohort"] != "fresh":
            continue
        group = pairs[sample["id"], "original"]
        a, w = group["aegis"]["ai_score"], group["waverep"]["ai_score"]
        lines.append(f"| {sample['id']} | {sample['label']} ({sample['generator']}) | {a:.6f} | {w:.6f} | {'yes' if (a >= .5) != (w >= .5) else 'no'} |")
    lines += ["", "## Descriptive summary", "",
        "Conflicts use the fixed score midpoint 0.5 only; this is not an operating-threshold or false-positive-rate evaluation. Each original source contributes once. Large changes count each compression/resize/crop condition relative to CRF 18, with absolute magnitude at least 0.10; opposite signs do not cancel.", "",
        "| Panel | Model | Original real conflicts | Original AI conflicts | Large paired changes |",
        "|---|---|---:|---:|---:|"]
    for cohort in ("all", "fresh"):
        sources = [s for s in config["samples"] if cohort == "all" or s["cohort"] == cohort]
        real = sum(s["label"] == "real" for s in sources)
        ai = len(sources) - real
        for detector in ("aegis", "waverep"):
            m = summary[cohort][detector]
            lines.append(f"| {cohort} | {detector} | {m['real_midpoint_conflicts']}/{real} | {m['ai_midpoint_conflicts']}/{ai} | {m['changes_at_least_point10']}/{m['transformed_cases']} |")
    lines += ["", "| Panel | Original model midpoint disagreements |", "|---|---:|"]
    for cohort in ("all", "fresh"):
        n = summary[cohort]["aegis"]["source_clips"]
        lines.append(f"| {cohort} | {summary[cohort]['original_midpoint_disagreements']}/{n} |")
    lines += ["", "## Scope and technical choices", "",
        "WaveRep G4 uses released trained weights, strict full-state loading and the native 504-pixel center crop/pad plus ImageNet normalization. The native demo averages frame logits before sigmoid; this adapter retains that rule. It uses the same 16 temporal indices as AEGIS over a centered four-second window, rather than every frame as in the WaveRep demo. This keeps CPU cost manageable and controls temporal selection, but is explicitly a sparse-frame adaptation, not reproduction of the paper's evaluation.", "",
        "The native spatial preprocessing differs: AEGIS resizes to 224; WaveRep crops/pads to 504. Resizing can therefore add more zero padding for WaveRep, and this experiment measures the complete input pipeline. No raw score magnitude is treated as comparable calibrated confidence. Full per-frame WaveRep logits and sampling indices are retained in the CSV.", "",
        "The fresh clips are ten filename-selected cases from the existing ComGenVid dataset, not a representative or declared training holdout. Training overlap is unknown; content and source encoding differ by class. Both models use DINOv2 backbones, so they do not cover independent backbone families. Five fresh real and five fresh generated clips cannot support a low-FPR claim, a deployment recommendation, or a robust accuracy ranking. No model or threshold was trained/tuned on these clips.", "",
        "## Sources and reproducibility", "",
        "WaveRep: Riccardo Corvi, Davide Cozzolino, Ekta Prashnani, Shalini De Mello, Koki Nagano, Luisa Verdoliva, ‘Seeing What Matters: Generalizable AI-generated Video Detection with Forensic-Oriented Augmentation,’ NeurIPS 2025. [Official code](https://github.com/grip-unina/WaveRep-SyntheticVideoDetection), [retained license and adapter notes](../../vendor/waverep/ORIGIN.md). Informational/nonprofit research use; weights are not redistributed.", "",
        "AEGIS: [published checkpoint](https://huggingface.co/MusapYildiz/aegis-video-detector). Inputs: [ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid), [DAVIS via VLM4D](https://huggingface.co/datasets/shijiezhou/VLM4D). Media and extracted frames remain local.", "",
        "Reproduce with `uv sync --locked` then `uv run python run.py compare`. WaveRep adds a ~331 MiB checkpoint and the fresh inputs add ~42 MiB. All existing dependencies suffice. Interrupted WaveRep extraction can resume only when input, model, adapter and environment signatures match.", "",
        "[All scores and frame logits](scores.csv) · [Summary JSON](summary.json) · [Run metadata](run.json) · [Validation](validation.json) · [Experiment notes](experiment-log.md)"]
    (out / "report.md").write_text("\n".join(lines) + "\n")
