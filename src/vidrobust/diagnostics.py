"""Fixed compression sweep and an independent-source convenience panel."""
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import time
from urllib.parse import quote

CRFS = (18, 23, 28, 32, 35)

def curve_metrics(rows):
    points = sorted((r for r in rows if r["variant"].startswith("crf_")), key=lambda r: r["crf"])
    if len(points) != 5 or tuple(r["crf"] for r in points) != CRFS:
        raise ValueError("Compression curve must have all five unique frozen CRF levels")
    steps = [dict(from_crf=a["crf"], to_crf=b["crf"], delta=b["ai_score"]-a["ai_score"],
                  delta_per_crf=(b["ai_score"]-a["ai_score"])/(b["crf"]-a["crf"]))
             for a,b in zip(points, points[1:])]
    crossings = [dict(from_crf=a["crf"],to_crf=b["crf"]) for a,b in zip(points,points[1:])
                 if (a["ai_score"]-0.5)*(b["ai_score"]-0.5) < 0]
    deltas = [s["delta"] for s in steps]
    return dict(score_range=max(r["ai_score"] for r in points)-min(r["ai_score"] for r in points),
        largest_step=max(steps,key=lambda s: abs(s["delta"])),steps=steps,midpoint_crossings=crossings,
        non_monotone=any(d>1e-6 for d in deltas) and any(d < -1e-6 for d in deltas))

def probe(path, full_decode=False):
    import cv2
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Cannot decode video: {path.name}")
    meta = dict(width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),fps=cap.get(cv2.CAP_PROP_FPS))
    try:
        if min(meta["width"],meta["height"]) < 1 or meta["frames"] < 8 or meta["fps"] <= 0:
            raise ValueError(f"Invalid source geometry/timing: {path.name}")
        if full_decode:
            count=0
            while cap.read()[0]:
                count+=1
            if count!=meta["frames"]:
                raise ValueError(f"Partial decode: {path.name} ({count}/{meta['frames']})")
    finally:
        cap.release()
    return meta

def validate_case(source, row):
    if row["frames"]!=source["frames"] or abs(row["fps"]-source["fps"]) > 0.01:
        raise ValueError(f"Timing changed: {row['video_id']}/{row['variant']}")
    w,h=source["width"],source["height"]
    expected = (w//4*2,h//4*2) if row["variant"]=="resize" else (int(w*0.8/2)*2,int(h*0.8/2)*2) if row["variant"]=="crop" else (w,h)
    if (row["width"],row["height"])!=expected:
        raise ValueError(f"Geometry changed: {row['video_id']}/{row['variant']}")
    if not math.isfinite(row["ai_score"]) or not 0<=row["ai_score"]<=1:
        raise ValueError("Invalid score")

def plot_results(root, config, rows):
    os.environ.setdefault("MPLCONFIGDIR",str(root/"data/.matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out=root/"reports/diagnostics"
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,"svg.hashsalt":"video-robustness"})
    colors=["#dc2626","#2563eb","#059669","#9333ea"]
    fig,axes=plt.subplots(1,2,figsize=(12,4.7),layout="constrained")
    for sample,color in zip(config["sweep"],colors):
        points=sorted([r for r in rows if r["video_id"]==sample["id"] and r["crf"]],key=lambda r:r["crf"])
        label=f"{sample['id']} ({sample['generator']})"
        for ax,key in zip(axes,["ai_score","fusion_logit"]):
            ax.plot([r["crf"] for r in points],[r[key] for r in points],marker="o",color=color,label=label)
            ax.set_xticks(CRFS);ax.set_xlabel("CRF (higher = stronger compression)");ax.grid(alpha=.2)
    axes[0].set_ylim(-.03,1.03);axes[0].set_ylabel("AI-like score");axes[0].set_title("Score response")
    axes[0].axhline(.5,color="#64748b",linestyle=":",linewidth=1)
    axes[1].set_ylabel("Fused raw output (logit)");axes[1].set_title("Raw output response")
    axes[1].axhline(0,color="#64748b",linestyle=":",linewidth=1)
    axes[1].legend(loc="best",fontsize=8)
    fig.suptitle("Compression sweep: four diagnostic clips",fontweight="bold")
    fig.savefig(out/"compression-curves.png",dpi=180);fig.savefig(out/"compression-curves.svg",metadata={"Date":None});plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.6),layout="constrained")
    variants=["original","crf_18","crf_35","resize","crop"]
    for sample in config["second_source"]:
        scores={r["variant"]:r["ai_score"] for r in rows if r["video_id"]==sample["id"]}
        ax.plot(range(5),[scores[v] for v in variants],marker="o",label=sample["source_id"])
    ax.set_xticks(range(5),["Original","Encode CRF 18","Compress CRF 35","Half-size","Center crop"])
    ax.set_ylim(-.03,1.03);ax.set_ylabel("AI-like score");ax.set_title("Second real source: five DAVIS clips")
    ax.axhline(.5,color="#64748b",linestyle=":",linewidth=1);ax.grid(alpha=.2);ax.legend(fontsize=8,loc="best")
    fig.savefig(out/"second-source.png",dpi=180);fig.savefig(out/"second-source.svg",metadata={"Date":None});plt.close(fig)
    for name in ("compression-curves.svg", "second-source.svg"):
        path=out/name
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")

def write_report(root, config, rows):
    out=root/"reports/diagnostics"
    curves={s["id"]:curve_metrics([r for r in rows if r["video_id"]==s["id"]]) for s in config["sweep"]}
    by_case={(r["video_id"],r["variant"]):r for r in rows}
    def score(clip, variant):
        return by_case[clip,variant]["ai_score"]
    failure_step=curves["real_01"]["largest_step"]
    other_real_max=max(r["ai_score"] for r in rows if r["cohort"]=="second_source" and r["video_id"]!="davis_04")
    (out/"curve-summary.json").write_text(json.dumps(curves,indent=2)+"\n")
    lines=["# Compression sweep and second-source check","",
        "Nine source clips, 49 scored cases. Four deliberately selected diagnostic clips use an original plus five CRF encodes. Five freshly selected DAVIS clips use the original and four standard conditions.","",
        "Selection was frozen before scoring; see [manifest](../../configs/diagnostics.json) and [policy](../../configs/diagnostics-selection.md). Diagnostic controls were chosen from prior results and are not a holdout.","",
        "## Findings","",
        f"The original MSVD failure scores {score('real_01','crf_18'):.3f} at CRF 18 and {score('real_01','crf_28'):.3f} at 28, then {score('real_01','crf_32'):.3f} at 32 and {score('real_01','crf_35'):.3f} at 35. Its largest sampled step is {failure_step['from_crf']}–{failure_step['to_crf']} ({failure_step['delta']:+.3f}); the five-point grid brackets the change without identifying an exact transition or a cause.","",
        f"The second real source contains another large compression response: DAVIS `bear` scores {score('davis_04','original'):.3f} on the original, {score('davis_04','crf_18'):.3f} on the CRF 18 control, and {score('davis_04','crf_35'):.3f} at CRF 35. The other four DAVIS clips have a maximum score of {other_real_max:.6f} across all five conditions. This repeats the qualitative pattern on one new source clip, not an estimate of its frequency.","",
        f"The Sora diagnostic curve falls to {score('ai_03','crf_28'):.3f} at CRF 28, then rises to {score('ai_03','crf_32'):.3f} at 32 and {score('ai_03','crf_35'):.3f} at 35. The Veo score stays high, while its fused raw output falls from {by_case['ai_06','crf_18']['fusion_logit']:.3f} at CRF 18 to {by_case['ai_06','crf_35']['fusion_logit']:.3f} at CRF 35. Saturated scores can hide substantial internal output changes.","",
        "## Compression curves","","![Compression curves](compression-curves.png)","",
        "| Clip | Original | CRF 18 | CRF 23 | CRF 28 | CRF 32 | CRF 35 |","|---|---:|---:|---:|---:|---:|---:|"]
    for sample in config["sweep"]:
        group={r["variant"]:r for r in rows if r["video_id"]==sample["id"]}
        values=[group[v]["ai_score"] for v in ["original",*[f"crf_{c}" for c in CRFS]]]
        lines.append(f"| {sample['id']} | "+" | ".join(f"{v:.6f}" for v in values)+" |")
    lines += ["","| Clip | Largest sampled step | Signed score change | Change per CRF unit | Midpoint crossings | Non-monotone? |","|---|---|---:|---:|---|---|"]
    for id,m in curves.items():
        step=m["largest_step"];crossings=", ".join(f"{p['from_crf']}–{p['to_crf']}" for p in m["midpoint_crossings"]) or "none"
        lines.append(f"| {id} | {step['from_crf']}–{step['to_crf']} | {step['delta']:+.6f} | {step['delta_per_crf']:+.6f} | {crossings} | {'yes' if m['non_monotone'] else 'no'} |")
    lines += ["","The largest adjacent step describes where the measured change concentrates on this five-point grid. Uneven CRF spacing and non-linear encoding quality limit interpretation. A crossing of score 0.5 (raw output 0) is a descriptive midpoint, not a validated operating threshold. This coarse grid cannot locate an exact transition or identify the responsible features.","",
        "## Second real source","","![Second-source results](second-source.png)","",
        "| Clip (DAVIS source) | Original | CRF 18 | CRF 35 | Resize | Crop | Compression − control |","|---|---:|---:|---:|---:|---:|---:|"]
    for sample in config["second_source"]:
        group={r["variant"]:r for r in rows if r["video_id"]==sample["id"]}
        values=[group[v]["ai_score"] for v in ["original","crf_18","crf_35","resize","crop"]]
        delta=group["crf_35"]["ai_score"]-group["crf_18"]["ai_score"]
        lines.append(f"| {sample['source_id']} | "+" | ".join(f"{v:.6f}" for v in values)+f" | {delta:+.6f} |")
    lines += ["","[VLM4D's source card](https://huggingface.co/datasets/shijiezhou/VLM4D) identifies DAVIS as real third-person footage. Its published MP4s can reflect source conversion/encoding; they are not matched in content or resolution to the MSVD failure. Dataset and clip labels are inherited, and training overlap is unknown.","",
        "## Interpretation limits","",
        "Scores are not calibrated authenticity probabilities. Raw logits expose changes hidden by saturated outputs. Pixel, motion, and consistency scores in the CSV are auxiliary trained-head outputs, not an attribution of the fused decision. Compression changes many image statistics simultaneously; curves alone cannot establish a texture/frequency mechanism. Five new real clips cannot estimate a false-positive rate or establish general robustness.","",
        "[Raw outputs and hashes](scores.csv) · [Run metadata](run.json) · [Validation](validation.json) · [Curve metrics](curve-summary.json) · [Experiment notes](experiment-log.md)","",
        "All source media remain local and are excluded from Git. Plots contain only experiment measurements, not frames."]
    (out/"report.md").write_text("\n".join(lines)+"\n")

def run_diagnostics(root):
    import imageio_ffmpeg
    from .cli import download, sha, MODEL_HASH, MODEL_REV, FILTERS
    from .detectors import AegisDetector
    config=json.loads((root/"configs/diagnostics.json").read_text())
    if tuple(config["crfs"])!=CRFS:
        raise ValueError("CRF grid differs from the frozen experiment")
    samples=config["sweep"]+config["second_source"]
    download(f"https://huggingface.co/MusapYildiz/aegis-video-detector/resolve/{MODEL_REV}/checkpoint_best.pt",root/"models/checkpoint_best.pt",MODEL_HASH)
    def fetch(sample):
        url=f"https://huggingface.co/datasets/{sample['dataset']}/resolve/{sample['revision']}/{quote(sample['remote_path'],safe='/')}"
        download(url,root/f"data/original/{sample['id']}.mp4",sample["sha256"])
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch,samples))
    out=root/"reports/diagnostics";out.mkdir(parents=True,exist_ok=True)
    preflight={s["id"]:probe(root/f"data/original/{s['id']}.mp4",full_decode=True) for s in samples}
    model=AegisDetector(root);rows=[];commands=[]
    for sample in samples:
        original=root/f"data/original/{sample['id']}.mp4"
        levels=CRFS if sample["cohort"]=="diagnostic_sweep" else (18,35)
        variants=[("original",None,None),*[(f"crf_{c}",c,None) for c in levels]]
        if sample["cohort"]=="second_source":
            variants += [(v,18,FILTERS[v][0]) for v in ("resize","crop")]
        baseline=None
        for variant,crf,filt in variants:
            path=original
            if variant!="original":
                path=root/f"data/diagnostics/{sample['id']}_{variant}.mp4";path.parent.mkdir(parents=True,exist_ok=True)
                cmd=[imageio_ffmpeg.get_ffmpeg_exe(),"-y","-loglevel","error","-i",str(original),"-map","0:v:0","-an"]
                if filt:
                    cmd += ["-vf",filt]
                cmd += ["-c:v","libx264","-preset","medium","-crf",str(crf),"-pix_fmt","yuv420p",str(path)]
                subprocess.run(cmd,check=True)
                commands.append([str(Path(a).relative_to(root)) if a.startswith(str(root)+"/") else a for a in cmd[1:]])
            start=time.perf_counter();details=model.score_details(path);elapsed=time.perf_counter()-start
            if baseline is None:
                baseline=details["ai_score"]
            row=dict(video_id=sample["id"],source=sample["generator"],source_id=sample["source_id"],label=sample["label"],cohort=sample["cohort"],variant=variant,crf=crf,
                **details,delta_vs_original=details["ai_score"]-baseline,elapsed_sec=elapsed,**probe(path),sha256=sha(path))
            row["sampled_frame_indices"]=json.dumps(row["sampled_frame_indices"])
            validate_case(preflight[sample["id"]],row)
            if variant!="original":
                first=next(r for r in rows if r["video_id"]==sample["id"] and r["variant"]=="original")
                if row["sampled_frame_indices"]!=first["sampled_frame_indices"]:
                    raise ValueError("Sampled frames changed across paired variants")
            rows.append(row)
            print(f"{sample['id']} {variant}: {details['ai_score']:.6f}, raw {details['fusion_logit']:+.3f}",flush=True)
    if len(rows)!=49:
        raise ValueError("Incomplete diagnostic experiment")
    with open(out/"scores.csv","w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(rows)
    import importlib.metadata
    metadata=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),model_revision=MODEL_REV,model_sha256=MODEL_HASH,device="cpu",threads=4,seed=0,deterministic_algorithms=True,sampling="16 frames, centered four-second window",python=platform.python_version(),config=config,
        packages={p:importlib.metadata.version(p) for p in ("torch","timm","opencv-python-headless","imageio-ffmpeg","matplotlib")},ffmpeg=imageio_ffmpeg.get_ffmpeg_version(),transformations=commands)
    (out/"run.json").write_text(json.dumps(metadata,indent=2)+"\n")
    (out/"validation.json").write_text(json.dumps(dict(source_clips=9,scored_cases=49,full_source_decode='passed',geometry_timing_and_sampled_indices='passed',preflight=preflight),indent=2)+"\n")
    plot_results(root,config,rows);write_report(root,config,rows)
