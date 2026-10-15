"""D3's XCLIP-16 encoder branch, with the author's eight-frame grouping."""
from ..registry import register
from .d3 import prepare_native_bgr

REVISION = "d6184e3fd8780d04c85d0f1eabe5f94bf44d98f6"
CONFIG_HASH = "43d49d757dc8a3ef3dfd242d7ebe0c2effcfa0404f9343864e50c45245f99d3a"


@register("d3_xclip")
class D3XCLIPDetector:
    name = "D3-XCLIP-16-temporal-ranking"
    ranking_only = True
    runtime_packages = ("transformers", "tokenizers", "safetensors")
    checkpoint = dict(path="models/xclip-base-patch16/model.safetensors",
        sha256="b5db836d57b7e22001cb2bab581719e910b4c571d926fe839b5d07bc0ba2d03e",
        url=f"https://huggingface.co/microsoft/xclip-base-patch16/resolve/{REVISION}/model.safetensors",
        revision=REVISION, config_path="vendor/d3/xclip-config.json", config_sha256=CONFIG_HASH)
    preprocessing = "Author BGR order; trim 10% from each end of long axis; linear 224×224 resize; ImageNet normalization; microsoft/xclip-base-patch16 vision pooler with native num_frames=8, all 16 frames passed together (two groups of eight); sample std of second differences of L2 frame-feature distances. Lower discrepancy is more AI-like; ai_score=1/(1+temporal_std) is ranking only, not a probability or midpoint decision."

    def __init__(self, root):
        import json
        import torch
        try:
            from transformers import XCLIPVisionConfig, XCLIPVisionModel
        except ImportError:
            raise RuntimeError("Install X-CLIP support with: uv sync --locked --extra temporal") from None
        from safetensors import safe_open
        from ..artifacts import sha
        path = root / self.checkpoint['path']
        config_path = root / self.checkpoint['config_path']
        if sha(path) != self.checkpoint['sha256'] or sha(config_path) != CONFIG_HASH:
            raise ValueError('D3 X-CLIP checkpoint or config checksum mismatch')
        config = XCLIPVisionConfig(**json.loads(config_path.read_text())['vision_config'])
        if (config.num_frames, config.patch_size, config.image_size) != (8, 16, 224):
            raise ValueError('Unexpected D3 X-CLIP configuration')
        torch.manual_seed(0)
        torch.set_num_threads(4)
        torch.use_deterministic_algorithms(True)
        self.encoder = XCLIPVisionModel(config)
        # Load only the released vision tensors. No text head or random weights.
        with safe_open(path, framework='pt', device='cpu') as weights:
            state = {key: weights.get_tensor(key) for key in weights.keys() if key.startswith('vision_model.')}
        # Older exports persisted this deterministic index buffer; modern
        # Transformers regenerates it and excludes it from state_dict.
        positions = state.pop('vision_model.embeddings.position_ids', None)
        if positions is None or not torch.equal(positions, self.encoder.vision_model.embeddings.position_ids):
            raise ValueError('Checkpoint position index buffer differs')
        self.encoder.load_state_dict(state, strict=True)
        self.encoder.eval()

    def prepare_frames(self, frames):
        if len(frames) != 16:
            raise ValueError('Expected 16 frames')
        return prepare_native_bgr(frames)

    def predict(self, tensor):
        import torch
        if tuple(tensor.shape) != (16, 3, 224, 224):
            raise ValueError('Expected sixteen normalized 224×224 frames')
        # Do not microbatch, switch to a 16-frame checkpoint, or pool across time.
        # These change the model selected by D3_model's XCLIP-16 branch.
        features = self.encoder(tensor, output_hidden_states=True).pooler_output.reshape(1, 16, -1)
        first = torch.norm(features[:, :-1] - features[:, 1:], p=2, dim=-1)
        second = first[:, 1:] - first[:, :-1]
        std = torch.std(second, dim=1).item()
        return dict(ai_score=1/(1+std), temporal_std=std,
            temporal_mean=torch.mean(second, dim=1).item(),
            first_order_distances=first[0].tolist(), second_order_changes=second[0].tolist())
