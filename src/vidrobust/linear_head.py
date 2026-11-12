"""Small deterministic linear heads for a frozen video encoder."""
from collections import Counter, defaultdict
import math
import re

import numpy as np


def fit_ridge(features, labels, penalty):
    """Fit +/-1 targets with mean squared loss, L2 penalty, and a free intercept."""
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)
    if (x.ndim != 2 or x.shape[1] == 0 or y.shape != (len(x),)
            or not np.isfinite(x).all() or set(y) != {-1, 1}
            or not math.isfinite(penalty) or penalty <= 0):
        raise ValueError('Expected finite features, both labels and positive regularization')
    center, mean = x.mean(axis=0), y.mean()
    z = x - center
    # Solve in sample space; there are fewer clips than feature dimensions.
    dual = np.linalg.solve(z @ z.T + penalty * len(x) * np.eye(len(x)), y - mean)
    weights = z.T @ dual
    return weights, float(mean - center @ weights)


def clip_embedding(frame_features):
    x = np.asarray(frame_features, dtype=np.float64)
    if x.ndim != 2 or len(x) != 16 or not np.isfinite(x).all():
        raise ValueError('Expected sixteen finite feature vectors')
    mean = x.mean(axis=0)
    norm = np.linalg.norm(mean)
    if not math.isfinite(norm) or norm <= 0:
        raise ValueError('Invalid embedding norm')
    return mean / norm


def recording_keys(samples):
    """Validate matched pairs and retain grouping keys for leakage checks."""
    pairs = defaultdict(list)
    for sample in samples:
        pairs[sample['anchor_id']].append(sample)
    recordings = set()
    for pair in pairs.values():
        if Counter(s['label'] for s in pair) != {'real': 1, 'ai': 1}:
            raise ValueError('Every anchor needs one real and one generated clip')
        ids = {re.fullmatch(r'https://www\.dvidshub\.net/video/(?:embed/)?(\d+)(?:/[^?#]*)?',
                            s['original_source_url']) for s in pair}
        if None in ids:
            raise ValueError('Need attributed DVIDS recordings')
        keys = {m.group(1) for m in ids}
        if len(keys) != 1 or recordings & keys:
            raise ValueError('Expected a distinct recording for every pair')
        recordings.update(keys)
    return dict(anchors=set(pairs), recordings=recordings,
                parents={a.split('__scene_')[0] for a in pairs},
                digests={s['sha256'] for s in samples})


def metrics(labels, margins):
    real = [v for y, v in zip(labels, margins, strict=True) if y == 'real']
    ai = [v for y, v in zip(labels, margins, strict=True) if y == 'ai']
    if (not real or not ai or len(real) + len(ai) != len(labels)
            or not all(math.isfinite(v) for v in real + ai)):
        raise ValueError('Expected finite margins for both classes')
    wins = sum(a > r for a in ai for r in real)
    ties = sum(a == r for a in ai for r in real)
    return dict(real_clips=len(real), ai_clips=len(ai), real_flagged=sum(r >= 0 for r in real),
                ai_missed=sum(a < 0 for a in ai), ai_above_real=wins, ties=ties,
                comparisons=len(real)*len(ai), auc=(wins+.5*ties)/(len(real)*len(ai)))
