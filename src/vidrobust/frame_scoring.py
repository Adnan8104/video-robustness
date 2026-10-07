"""Fixed RGB-frame inputs with the adapters' unchanged native preprocessing."""
import hashlib
import math
import numpy as np


def rgb_digest(frames):
    if len(frames) != 16:
        raise ValueError('Expected exactly 16 fixed RGB frames')
    digest=hashlib.sha256()
    for frame in frames:
        if frame.dtype!=np.uint8 or frame.ndim!=3 or frame.shape[-1]!=3:
            raise ValueError('Expected uint8 RGB images')
        digest.update(str(frame.shape).encode());digest.update(np.ascontiguousarray(frame).tobytes())
    return digest.hexdigest()


def tensor_digest(tensor):
    values=tensor.detach().cpu().contiguous().numpy()
    return hashlib.sha256(str(values.shape).encode()+str(values.dtype).encode()+values.tobytes()).hexdigest()


def score_frames(detector, name, frames):
    import torch
    from PIL import Image
    from .waverep import aggregate_frame_logits
    rgb_hash=rgb_digest(frames)
    with torch.inference_mode():
        if name=='aegis':
            from video_io import preprocess_frames
            tensor=preprocess_frames(np.stack(frames),height=224,width=224)
            output=detector.model(tensor.unsqueeze(0))
            details=dict(ai_score=output['ai_probability'].item(),fusion_logit=output['ai_logit'].item(),
                pixel_score=output['pixel_prob'].item(),motion_score=output['motion_prob'].item(),
                consistency_score=output['consistency_prob'].item())
        elif name=='waverep':
            tensor=torch.stack([detector.transform(Image.fromarray(f)) for f in frames])
            logits=[]
            for start in range(0,16,2):
                logits.extend(detector.model(tensor[start:start+2]).reshape(-1).tolist())
            mean,score=aggregate_frame_logits(logits)
            details=dict(ai_score=score,fusion_logit=mean,frame_logits=logits)
        else:raise ValueError('Unknown detector')
    if not all(math.isfinite(v) for k,v in details.items() if k!='frame_logits') or not 0<=details['ai_score']<=1:
        raise ValueError('Invalid model outputs')
    return details | dict(sampled_rgb_sha256=rgb_hash,model_input_sha256=tensor_digest(tensor))
