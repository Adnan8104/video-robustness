"""Verify source provenance, native AEGIS parity and existing score regression."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
REV = "d86a774fd971954a023e1cd00ed7ff5b2575e0d1"
from vidrobust.artifacts import sha
from vidrobust.frame_scoring import tensor_digest
from vidrobust.inference import DetectionService
from vidrobust.registry import get_adapter

source_checks = []
for filename in ("detector_model.py", "pixel_branch.py", "motion_branch.py", "consistency_branch.py", "video_io.py"):
    remote_path = f"src/{'utils' if filename == 'video_io.py' else 'branches'}/{filename}"
    url = f"https://raw.githubusercontent.com/MusapYildiz/ai_video_detection_benchmark/{REV}/{remote_path}"
    remote = urllib.request.urlopen(url, timeout=30).read()
    local = (ROOT / "vendor/aegis" / filename).read_bytes()
    assert local == remote, filename
    source_checks.append(dict(path=f"vendor/aegis/{filename}", sha256=hashlib.sha256(local).hexdigest(), matches_pinned_upstream=True))
print("All five vendored source files exactly match pinned upstream.", flush=True)

service = DetectionService(ROOT)
reference = list(csv.DictReader((ROOT / "reports/experiments/smoke/scores.csv").open()))
checks = []
for video_id in ("real_01", "ai_01"):
    source = ROOT / "data/original" / (video_id + ".mp4")
    result = service.analyze(source.read_bytes(), source.name, scan_sections=True,
                             progress=lambda stage: print(video_id, stage, flush=True))
    adapter = service.models["aegis"]
    import torch
    bundle = adapter.load_video(str(source), n_frames=16, n_semantic=8,
        sampling="window", target_dur=4., random_start=False, quality_filter=False)
    aegis = next(row for row in result["detectors"] if row["detector"] == "aegis")
    assert tensor_digest(bundle.frames_all) == aegis["model_input_sha256"]
    with torch.inference_mode():
        output = adapter.model(bundle.frames_all.unsqueeze(0))
    for target, upstream in (("ai_score", "ai_probability"), ("fusion_logit", "ai_logit"),
                             ("pixel_score", "pixel_prob"), ("motion_score", "motion_prob"),
                             ("consistency_score", "consistency_prob")):
        assert aegis[target] == output[upstream].item(), (video_id, target)
    for row in result["detectors"]:
        old = next(r for r in reference if r["video_id"] == video_id and r["variant"] == "original" and r["detector"] == row["detector"])
        assert result["input_sha256"] == old["sha256"]
        for key in ("ai_score", "fusion_logit"):
            assert row[key] == float(old[key]), (video_id, key)
        for key in ("sampled_rgb_sha256", "model_input_sha256"):
            assert row[key] == old[key], (video_id, key)
        assert result["sampled_frame_indices"] == json.loads(old["sampled_frame_indices"])
    checks.append(dict(video_id=video_id, label="real" if video_id.startswith("real") else "ai",
        input_sha256=result["input_sha256"], metadata=result["metadata"],
        centered_tensor_and_all_five_aegis_outputs_match_native_loader=True,
        both_centered_scores_logits_and_input_hashes_match_previous_smoke=True,
        windows=result["windows"]))

models = {}
for name in ("aegis", "waverep"):
    spec = get_adapter(name)
    actual = sha(ROOT / spec.adapter.checkpoint["path"])
    assert actual == spec.adapter.checkpoint["sha256"]
    models[name] = dict(sha256=actual, verified=True, preprocessing=spec.adapter.preprocessing)
paths = sorted((ROOT / "src/vidrobust").glob("*.py")) + sorted((ROOT / "src/vidrobust/adapters").glob("*.py"))
paths += [ROOT / "demo.py", ROOT / "run.py", ROOT / "pyproject.toml", ROOT / "uv.lock", Path(__file__).resolve()]
report = dict(aegis_upstream_revision=REV, source_checks=source_checks, models=models, checks=checks,
    code_sha256={str(path.relative_to(ROOT)): sha(path) for path in paths},
    limits="Two previously scored public clips. Confirms implementation parity, not detection accuracy or an explanation of the user's uploaded clip.")
out = ROOT / "reports/demo-validation"
out.mkdir(exist_ok=True)
(out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
print("Native-loader parity and four centered benchmark scores match exactly.", flush=True)
