"""AEGIS pretrained adapter with its native preprocessing and fusion head."""
from pathlib import Path
import sys
import math
import numpy as np
from ..registry import register

MODEL_REV = "95b71346cec650165e6ad3fb20ed9e80f4b6702a"
MODEL_HASH = "7df233979f9d3ef340e101d0d635a4d074577d43e6d1591d677cde31f80e44ba"


@register("aegis")
class AegisDetector:
    name = "aegis-phase2-epoch7"
    checkpoint = dict(path="models/checkpoint_best.pt", sha256=MODEL_HASH, revision=MODEL_REV,
        url=f"https://huggingface.co/MusapYildiz/aegis-video-detector/resolve/{MODEL_REV}/checkpoint_best.pt")
    preprocessing = "16 RGB frames; linear resize to 224×224; ImageNet normalization; released fusion head"
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
        from video_io import load_video, check_video_quality, window_sample
        self.load_video = load_video
        self.check_video_quality = check_video_quality
        self.window_sample = window_sample
        torch.manual_seed(0)
        torch.set_num_threads(4)
        torch.use_deterministic_algorithms(True)
        self.model = VideoForensicsDetector(freeze_dino=True)
        checkpoint = torch.load(root / "models/checkpoint_best.pt", map_location="cpu", weights_only=True)
        self.model.load_state_dict(checkpoint["model_state"], strict=True)
        self.model.eval()
        self.epoch = checkpoint.get("epoch")

    def score(self, path: Path) -> float:
        return self.score_details(path)["ai_score"]

    def prepare_frames(self, frames):
        from video_io import preprocess_frames
        return preprocess_frames(np.stack(frames), height=224, width=224)

    def predict(self, tensor):
        output = self.model(tensor.unsqueeze(0))
        return dict(ai_score=output["ai_probability"].item(), fusion_logit=output["ai_logit"].item(),
            pixel_score=output["pixel_prob"].item(), motion_score=output["motion_prob"].item(),
            consistency_score=output["consistency_prob"].item())

    def score_details(self, path: Path) -> dict:
        import torch
        # Retain upstream 16-frame/4-second window + ImageNet preprocessing;
        # choose centered window so every variant uses the same temporal region.
        self.check_video_quality(str(path), min_resolution=1)
        bundle = self.load_video(str(path), n_frames=16, n_semantic=8,
                                 sampling="window", target_dur=4.0, random_start=False, quality_filter=False)
        with torch.inference_mode():
            outputs = self.model(bundle.frames_all.unsqueeze(0))
        score = outputs["ai_probability"].item()
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f"Invalid detector score for {path}: {score}")
        details = dict(ai_score=score, fusion_logit=outputs["ai_logit"].item(),
            pixel_score=outputs["pixel_prob"].item(), motion_score=outputs["motion_prob"].item(),
            consistency_score=outputs["consistency_prob"].item(),
            sampled_frame_indices=self.window_sample(bundle.total_frames, 16, bundle.fps,
                target_dur=4.0, random_start=False).tolist())
        if not all(math.isfinite(details[k]) for k in ("fusion_logit", "pixel_score", "motion_score", "consistency_score")):
            raise ValueError(f"Non-finite diagnostic outputs: {path}")
        return details
