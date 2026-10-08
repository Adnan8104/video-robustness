"""AIGVDet's released RGB branch, not the full RGB + optical-flow detector.

Bai et al., PRCV 2024. Academic research only; see vendor/aigvdet/.
Native spatial preprocessing and mean-of-probabilities aggregation, with the
shared harness's explicit 16-frame sampling instead of all-frame inference.
"""
from ..registry import register

WEIGHTS_HASH = "c2df6f477a590f4b24b14eac9654b868a9f178312795df20749274a502d59bdd"
WEIGHTS_URL = "https://drive.usercontent.google.com/download?id=10EXwX9cXR0VuBmWq7QpMfotnPtIRKIsV&export=download&authuser=0&confirm=t"


def native_transform():
    from torchvision import transforms
    return transforms.Compose([
        transforms.CenterCrop((448, 448)), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def aggregate_frame_logits(logits):
    import torch
    if len(logits) != 16 or not torch.isfinite(torch.tensor(logits)).all():
        raise ValueError("Expected 16 finite frame logits")
    # Author code scores each frame with float32 sigmoid before averaging.
    probabilities = [torch.tensor(value, dtype=torch.float32).sigmoid().item() for value in logits]
    return probabilities, sum(probabilities) / len(probabilities)


@register("aigvdet_rgb")
class AIGVDetRGBDetector:
    name = "AIGVDet-RGB-sparse16"
    checkpoint = dict(path="models/aigvdet_original.pth", sha256=WEIGHTS_HASH,
        url=WEIGHTS_URL, revision="5e0d5dd7c5ecf96040608676a2965502ffed2555")
    preprocessing = "RGB branch only; 16 RGB frames; 448×448 center crop (zero padding if smaller); ImageNet normalization; mean frame sigmoid probabilities; batch size 1"

    def __init__(self, root):
        import torch
        from torchvision.models import resnet50
        from ..artifacts import sha
        path = root / self.checkpoint["path"]
        if sha(path) != WEIGHTS_HASH:
            raise ValueError("AIGVDet RGB checkpoint checksum mismatch")
        torch.manual_seed(0)
        torch.set_num_threads(4)
        torch.use_deterministic_algorithms(True)
        # Native architecture parity checked against the pinned author's ResNet.
        # Strict loading includes the released trained classifier and backbone.
        self.model = resnet50(weights=None, num_classes=1)
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        self.model.load_state_dict(checkpoint.get("model", checkpoint), strict=True)
        self.model.eval()
        self.transform = native_transform()

    def prepare_frames(self, frames):
        import torch
        from PIL import Image
        if len(frames) != 16:
            raise ValueError("Expected 16 RGB frames")
        return torch.stack([self.transform(Image.fromarray(frame)) for frame in frames])

    def predict(self, tensor):
        if tuple(tensor.shape) != (16, 3, 448, 448):
            raise ValueError("Expected 16 normalized 448×448 RGB frames")
        logits = [self.model(frame.unsqueeze(0)).item() for frame in tensor]
        probabilities, score = aggregate_frame_logits(logits)
        return dict(ai_score=score, frame_logits=logits, frame_scores=probabilities)
