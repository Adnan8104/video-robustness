"""Fixed RGB-frame inputs with the adapters' unchanged native preprocessing."""
import hashlib
import math
import numpy as np


def experiment_indices(meta, config):
    """Keep historical sampling or select sixteen nominal 8 fps positions."""
    if config.get('sampling', 'centered_4s_16') == 'centered_4s_16':
        from video_io import window_sample
        return window_sample(meta['frames'], 16, meta['fps'], target_dur=4, random_start=False).tolist()
    if config['sampling'] != 'centered_2s_8fps':
        raise ValueError('Unknown sampling profile')
    duration = int(round(meta['fps'] * 2))
    if meta['fps'] < 8 or meta['frames'] < duration:
        raise ValueError('8 fps sampling requires at least two seconds and native fps >=8')
    start = (meta['frames'] - duration) // 2
    indices = (start + np.floor(np.arange(16) * meta['fps'] / 8)).astype(int).tolist()
    if len(set(indices)) != 16 or indices[-1] >= meta['frames']:
        raise ValueError('Invalid 8 fps sample indices')
    return indices


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
    rgb_hash=rgb_digest(frames)
    with torch.inference_mode():
        tensor = detector.prepare_frames(frames)
        details = detector.predict(tensor)
    numeric = [v for value in details.values() for v in (value if isinstance(value, list) else [value])]
    if not all(math.isfinite(v) for v in numeric) or not 0<=details['ai_score']<=1:
        raise ValueError('Invalid model outputs')
    return details | dict(sampled_rgb_sha256=rgb_hash,model_input_sha256=tensor_digest(tensor))
