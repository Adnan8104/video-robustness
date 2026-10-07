"""WaveRep adapter; native preprocessing/aggregation adapted from GRIP-UNINA.

Corvi et al., NeurIPS 2025. See vendor/waverep/LICENSE.md and ORIGIN.md.
Sparse temporal sampling is our explicit CPU-budget adaptation.
"""
import math
from pathlib import Path
import sys
from ..media import read_exact_rgb
from ..registry import register

WEIGHTS_HASH = "50d639049d928986ba7d69861a4fe4f3e7afbba1843e3e089cdf6b4748f53d5b"
WEIGHTS_URL = "https://www.grip.unina.it/download/prog/WaveRep_SynthVideoDet/weights_dinov2_G4.ckpt"


def aggregate_frame_logits(logits):
    """The original demo applies sigmoid AFTER averaging the frame logits."""
    if len(logits) != 16 or not all(math.isfinite(v) for v in logits):
        raise ValueError("Expected 16 finite frame logits")
    mean = sum(logits) / len(logits)
    score = 1 / (1 + math.exp(-mean)) if mean >= 0 else math.exp(mean) / (1 + math.exp(mean))
    return mean, score




@register("waverep")
class WaveRepDetector:
    name = "waverep-G4-sparse16"
    checkpoint = dict(path="models/weights_dinov2_G4.ckpt", sha256=WEIGHTS_HASH, url=WEIGHTS_URL,
        revision="0fd6010759c14b572b7842a28fa9f85fe1ddd2fd")
    preprocessing = "16 RGB frames; 504×504 center crop with zero padding for smaller inputs; ImageNet normalization; sigmoid of mean frame logits; batch size 2"

    def __init__(self, root):
        import torch
        import timm
        from torchvision import transforms
        from ..artifacts import sha
        path = root / "models/weights_dinov2_G4.ckpt"
        if sha(path) != WEIGHTS_HASH:
            raise ValueError("WaveRep checkpoint checksum mismatch")
        sys.path.insert(0, str(root / "vendor/aegis"))
        from video_io import check_video_quality, window_sample
        self.check_quality = check_video_quality
        self.window_sample = window_sample
        torch.manual_seed(0)
        torch.set_num_threads(4)
        torch.use_deterministic_algorithms(True)
        # The full released checkpoint supplies the backbone and trained head.
        self.model = timm.create_model("vit_base_patch14_reg4_dinov2.lvd142m",
                                      num_classes=1, pretrained=False, img_size=504)
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        state = checkpoint.get("state_dict", checkpoint)
        if "state_dict" in checkpoint:
            state = {k[6:]: v for k, v in state.items() if k.startswith("model.")}
        self.model.load_state_dict(state, strict=True)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.CenterCrop((504, 504)), transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    def score(self, path):
        return self.score_details(path)["ai_score"]

    def prepare_frames(self, frames):
        import torch
        from PIL import Image
        return torch.stack([self.transform(Image.fromarray(frame)) for frame in frames])

    def predict(self, tensor):
        logits = []
        for start in range(0, 16, 2):
            logits.extend(self.model(tensor[start:start+2]).reshape(-1).tolist())
        mean, score = aggregate_frame_logits(logits)
        return dict(ai_score=score, fusion_logit=mean, frame_logits=logits)

    def score_details(self, path):
        import torch
        from PIL import Image
        meta = self.check_quality(str(path), min_resolution=1)
        indices = self.window_sample(meta["total_frames"], 16, meta["fps"],
                                     target_dur=4.0, random_start=False).tolist()
        frames = read_exact_rgb(path, indices)
        logits = []
        with torch.inference_mode():
            for start in range(0, 16, 2):
                batch = torch.stack([self.transform(Image.fromarray(f)) for f in frames[start:start+2]])
                logits.extend(self.model(batch).reshape(-1).tolist())
        mean, score = aggregate_frame_logits(logits)
        return dict(ai_score=score, fusion_logit=mean, frame_logits=logits,
                    sampled_frame_indices=indices)
