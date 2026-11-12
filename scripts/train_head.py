"""Fit two frozen-encoder heads, lock them in Git, then score fresh recordings."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, inside, load_config
from vidrobust.frame_scoring import experiment_indices, rgb_digest, tensor_digest
from vidrobust.linear_head import clip_embedding, fit_ridge, metrics, recording_keys
from vidrobust.media import prepare_cases, read_exact_rgb
from vidrobust.registry import get_adapter, make_detector

VARIANTS = [dict(name=name, transform='identity', encoding='h264', crf=crf)
            for name, crf in [('baseline', 18), ('compression', 35)]]
HEADS = ('light_only', 'both_levels')


def file_map(paths):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}


def environment():
    import imageio_ffmpeg
    return dict(python=platform.python_version(), architecture=platform.machine(),
                ffmpeg=imageio_ffmpeg.get_ffmpeg_version(),
                packages={name: importlib.metadata.version(name) for name in
                          ('numpy', 'torch', 'torchvision', 'timm', 'opencv-python-headless')})


def extract(config, samples):
    """Capture the released classifier's actual inputs without replacing it."""
    import torch
    cases, preparation = prepare_cases(ROOT, config, samples)
    detector = make_detector(ROOT, 'waverep')
    head = detector.model.get_classifier()
    features, rows = [], []
    for index, (path, case) in enumerate(cases, 1):
        indices = experiment_indices(case, config)
        if len(set(indices)) != 16:
            raise ValueError('Repeated frame indices')
        frames = read_exact_rgb(path, indices)
        with torch.inference_mode():
            tensor = detector.prepare_frames(frames)
            batches = []
            hook = head.register_forward_pre_hook(lambda _, args: batches.append(args[0].detach()))
            try:
                release = detector.predict(tensor)
            finally:
                hook.remove()
            recovered = [value for batch in batches for value in head(batch).reshape(-1).tolist()]
            if recovered != release['frame_logits']:
                raise ValueError('Captured features did not reconstruct released logits exactly')
            frame_features = torch.cat(batches).cpu().numpy()
            if frame_features.shape != (16, detector.model.num_features):
                raise ValueError('Unexpected feature shape')
        features.append(clip_embedding(frame_features))
        rows.append(case | dict(sampled_frame_indices=indices, sampled_rgb_sha256=rgb_digest(frames),
            model_input_sha256=tensor_digest(tensor), released_margin=release['fusion_logit'],
            released_score=release['ai_score']))
        print(f"{config['name']} {index}/{len(cases)} {case['video_id']} {case['variant']}", flush=True)
    return np.asarray(features), rows, preparation


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['fit', 'test'])
    parser.add_argument('policy')
    args = parser.parse_args()
    policy_path = inside(ROOT, args.policy, 'configs')
    policy = json.loads(policy_path.read_text())
    train = load_config(ROOT, policy['train_config'])
    test = load_config(ROOT, policy['test_config'])
    files = [policy_path, train[0], train[1], test[0], test[1]]
    for item in (train, test):
        _, _, config, samples = item
        if (config['detectors'] != ['waverep'] or config['preparation'] != 'centered_4s_504_24fps'
                or config['variants'] != VARIANTS or config['baseline'] != 'baseline'
                or config.get('sampling', 'centered_4s_16') != 'centered_4s_16'):
            raise ValueError('Expected the same two compression settings and centered WaveRep sampling')
    train_keys, test_keys = recording_keys(train[3]), recording_keys(test[3])
    if any(train_keys[k] & test_keys[k] for k in train_keys):
        raise ValueError('Training and test recordings overlap')
    if (len(train_keys['anchors']), len(test_keys['anchors'])) != (policy['train_pairs'], policy['test_pairs']):
        raise ValueError('Unexpected split sizes')
    code = [Path(__file__).resolve(), *(ROOT / 'src/vidrobust').glob('*.py'),
            ROOT / 'src/vidrobust/adapters/waverep.py', ROOT / 'vendor/aegis/video_io.py']
    frozen = {p.relative_to(ROOT).as_posix(): frozen_revision(ROOT, p) for p in files + code}
    fingerprints = file_map(files + code)
    checkpoint = get_adapter('waverep').adapter.checkpoint
    provenance = dict(frozen_revisions=frozen, fingerprints=fingerprints, environment=environment(),
                      encoder_sha256=checkpoint['sha256'], cpu_threads=4)
    out = inside(ROOT, policy['output'], 'reports')
    out.mkdir(parents=True, exist_ok=True)
    fit_record = out / 'fit.json'
    test_record = out / 'summary.json'
    if test_record.exists() or (out / 'scores.csv').exists():
        raise ValueError('The test has already been scored')
    local_weights = ROOT / 'models' / f'{policy_path.stem}.npz'
    local_weights.parent.mkdir(parents=True, exist_ok=True)

    if args.stage == 'fit':
        if fit_record.exists():
            raise ValueError('The fitted heads are already recorded')
        x, rows, preparation = extract(train[2], train[3])
        y = np.array([1 if r['label'] == 'ai' else -1 for r in rows])
        light = np.array([r['variant'] == 'baseline' for r in rows])
        if file_map(files + code) != fingerprints:
            raise ValueError('Frozen inputs changed during training')
        fitted = [fit_ridge(x[light], y[light], policy['ridge_penalty']),
                  fit_ridge(x, y, policy['ridge_penalty'])]
        np.savez(local_weights, weights=np.stack([w for w, _ in fitted]),
                 intercepts=np.array([b for _, b in fitted]))
        write(fit_record, provenance | dict(
            heads=list(HEADS), ridge_penalty=policy['ridge_penalty'], cutoff_margin=0,
            training_examples=dict(light_only=int(light.sum()), both_levels=len(y)),
            feature_dimensions=x.shape[1], local_weights_sha256=sha(local_weights),
            feature_sha256=hashlib.sha256(x.tobytes()).hexdigest(),
            preparation=preparation, training_inputs=rows, reconstructed_released_logits='exact'))
        print('Heads fitted. Commit fit.json before test inference.', flush=True)
        return

    commit = frozen_revision(ROOT, fit_record)
    saved = json.loads(fit_record.read_text())
    if any(saved[k] != value for k, value in provenance.items()):
        raise ValueError('Fitted heads were produced with different inputs or code')
    if sha(local_weights) != saved['local_weights_sha256']:
        raise ValueError('Local head weights differ from the locked record')
    with np.load(local_weights, allow_pickle=False) as data:
        weights, intercepts = data['weights'], data['intercepts']
    if weights.shape != (2, saved['feature_dimensions']) or intercepts.shape != (2,):
        raise ValueError('Invalid saved head shapes')
    x, rows, preparation = extract(test[2], test[3])
    if file_map(files + code) != fingerprints or sha(local_weights) != saved['local_weights_sha256']:
        raise ValueError('Frozen inputs changed during testing')
    margins = x @ weights.T + intercepts
    for row, scores in zip(rows, margins.tolist(), strict=True):
        row.update({name + '_margin': margin for name, margin in zip(HEADS, scores, strict=True)})
        row['sampled_frame_indices'] = json.dumps(row['sampled_frame_indices'])
    result = {}
    for name in ('released', *HEADS):
        result[name] = {}
        for variant in ('baseline', 'compression'):
            group = [r for r in rows if r['variant'] == variant]
            result[name][variant] = metrics([r['label'] for r in group], [r[name+'_margin'] for r in group])
    path = out / 'scores.csv'
    with path.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    write(test_record, provenance | dict(fit_commit=commit, fit_sha256=sha(fit_record), scores_sha256=sha(path),
          test_pairs=policy['test_pairs'], preparation=preparation, test=result,
          reconstructed_released_logits='exact', disjoint_recordings_and_sources=True))
    for name, variants in result.items():
        for variant, values in variants.items():
            print(name, variant, values)


if __name__ == '__main__':
    main()
