"""Detector boundary: add future VidAudit adapters here, keep experiment logic unchanged."""
from pathlib import Path
from typing import Protocol
import sys
import math

class Detector(Protocol):
    def score(self, path: Path) -> float: ...

class AegisDetector:
    name = "aegis-phase2-epoch7"
    def __init__(self, root: Path):
        import torch
        import timm
        sys.path.insert(0, str(root / "vendor/aegis"))
        import pixel_branch
        # Full checkpoint supplies the backbone. Skip author's machine-specific cache.
        pixel_branch._load_dinov2_224 = lambda: timm.create_model(
            "vit_base_patch14_dinov2", pretrained=False, num_classes=0,
            global_pool="avg", img_size=224)
        from detector_model import VideoForensicsDetector
        from video_io import load_video, check_video_quality
        self.load_video = load_video
        self.check_video_quality = check_video_quality
        torch.manual_seed(0)
        torch.set_num_threads(4)
        torch.use_deterministic_algorithms(True)
        self.model = VideoForensicsDetector(freeze_dino=True)
        checkpoint = torch.load(root / "models/checkpoint_best.pt", map_location="cpu", weights_only=True)
        self.model.load_state_dict(checkpoint["model_state"], strict=True)
        self.model.eval()
        self.epoch = checkpoint.get("epoch")

    def score(self, path: Path) -> float:
        import torch
        # Retain upstream 16-frame/4-second window + ImageNet preprocessing;
        # choose centered window so every variant uses the same temporal region.
        self.check_video_quality(str(path), min_resolution=1)
        bundle = self.load_video(str(path), n_frames=16, n_semantic=8,
                                 sampling="window", target_dur=4.0, random_start=False, quality_filter=False)
        with torch.inference_mode():
            score = self.model(bundle.frames_all.unsqueeze(0))["ai_probability"].item()
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f"Invalid detector score for {path}: {score}")
        return score
