"""D3 temporal ranking with its released lightweight ResNet18 encoder option.

No fitted classifier or decision threshold. See vendor/d3/ORIGIN.md for the
author's BGR preprocessing and the explicit temporal/encoding adaptations.
"""
from ..registry import register

WEIGHTS_HASH = "f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec"


def prepare_native_bgr(frames):
    import cv2
    import numpy as np
    import torch
    mean = np.array([.485, .456, .406], dtype=np.float32) * 255
    denominator = np.reciprocal(np.array([.229, .224, .225], dtype=np.float32) * 255)
    images = []
    for frame in frames:
        # The author passes cv2.imread BGR to Albumentations without RGB conversion.
        image = np.ascontiguousarray(frame[..., ::-1])
        height, width = image.shape[:2]
        if width > height:
            margin = int(width * .1)
            image = image[:, margin:width-margin]
        else:
            margin = int(height * .1)
            image = image[margin:height-margin, :]
        if image.size == 0:
            raise ValueError('D3 crop is empty')
        image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_LINEAR).astype(np.float32)
        image = (image - mean) * denominator
        images.append(torch.from_numpy(image.transpose(2, 0, 1).copy()))
    return torch.stack(images)


@register("d3_resnet18")
class D3ResNet18Detector:
    name = "D3-ResNet18-temporal-ranking"
    ranking_only = True
    checkpoint = dict(path="models/resnet18-f37072fd.pth", sha256=WEIGHTS_HASH,
        url="https://download.pytorch.org/models/resnet18-f37072fd.pth",
        revision="torchvision-0.20.1-ResNet18-IMAGENET1K_V1")
    preprocessing = "Author BGR order; trim 10% from each end of long axis; OpenCV linear 224×224 resize; ImageNet normalization; ResNet18 pooled features; sample std of second differences of L2 frame-feature distances; lower discrepancy is more AI-like. ai_score=1/(1+temporal_std) is a bounded ranking coordinate, never a probability or midpoint decision."

    def __init__(self, root):
        import torch
        from torchvision.models import resnet18
        from ..artifacts import sha
        path = root / self.checkpoint['path']
        if sha(path) != WEIGHTS_HASH:
            raise ValueError('D3 encoder checkpoint checksum mismatch')
        torch.manual_seed(0)
        torch.set_num_threads(4)
        torch.use_deterministic_algorithms(True)
        encoder = resnet18(weights=None)
        encoder.load_state_dict(torch.load(path, map_location='cpu', weights_only=True), strict=True)
        self.encoder = torch.nn.Sequential(*list(encoder.children())[:-1]).eval()

    def prepare_frames(self, frames):
        if len(frames) != 16:
            raise ValueError('Expected 16 frames')
        return prepare_native_bgr(frames)

    def predict(self, tensor):
        import torch
        if tuple(tensor.shape) != (16, 3, 224, 224):
            raise ValueError('Expected sixteen normalized 224×224 frames')
        features = self.encoder(tensor).reshape(1, 16, -1)
        first = torch.norm(features[:, :-1] - features[:, 1:], p=2, dim=-1)
        second = first[:, 1:] - first[:, :-1]
        std = torch.std(second, dim=1).item()
        return dict(ai_score=1/(1+std), temporal_std=std,
            temporal_mean=torch.mean(second, dim=1).item(),
            first_order_distances=first[0].tolist(), second_order_changes=second[0].tolist())
