"""Evaluate the original locked head on fresh ComGenVid recordings."""
from collections import Counter
import csv
import json
from pathlib import Path

import numpy as np

if __package__:
    from .train_head import ROOT, VARIANTS, environment, extract, file_map, write
    from .check_head_cutoff import by_variant
else:
    from train_head import ROOT, VARIANTS, environment, extract, file_map, write
    from check_head_cutoff import by_variant
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, load_config
from vidrobust.registry import get_adapter


def source_key(remote):
    name = Path(remote).stem
    return name.rsplit('_', 2)[0] if '/MSVD/' in remote else name


def check_cohort(samples, previous):
    if Counter((r['label'], r['source']) for r in samples) != {('real', 'MSVD'): 12, ('ai', 'VEO3'): 12}:
        raise ValueError('Expected 12 MSVD and 12 Veo 3 clips')
    keys = set()
    prior_paths = {r.get('remote_path', '') for r in previous}
    prior_hashes = {r.get('sha256') for r in previous}
    prior_groups = {source_key(p) for p in prior_paths if '/MSVD/' in p}
    for row in samples:
        path = row['remote_path']
        key = source_key(path)
        expected_prefix = 'videos/real/MSVD/' if row['label'] == 'real' else 'videos/fake/VEO3/'
        if (not path.startswith(expected_prefix) or row['recording_key'] != key
                or key in keys or path in prior_paths or key in prior_groups
                or row['sha256'] in prior_hashes):
            raise ValueError(f'Unexpected source or reused recording: {path}')
        keys.add(key)


def main():
    output = ROOT / 'reports/head-transfer'
    if (output/'scores.csv').exists() or (output/'summary.json').exists():
        raise ValueError('The transfer panel has already been scored')
    path, manifest, config, samples = load_config(ROOT, 'configs/experiments/head-transfer.json')
    if (config['detectors'] != ['waverep'] or config['preparation'] != 'centered_4s_504_24fps'
            or config['variants'] != VARIANTS or config['baseline'] != 'baseline'
            or config.get('sampling', 'centered_4s_16') != 'centered_4s_16'
            or {r['dataset'] for r in samples} != {'OmerXYZ/comgenvid'}):
        raise ValueError('Unexpected transfer protocol')
    previous = []
    prior_files = []
    for file in sorted((ROOT/'configs').rglob('*.json')):
        if file == manifest:
            continue
        obj = json.loads(file.read_text())
        if isinstance(obj, dict) and obj.get('samples'):
            previous.extend(obj['samples'])
            prior_files.append(file)
    check_cohort(samples, previous)

    fit_path = ROOT/'reports/linear-head/fit.json'
    fit = json.loads(fit_path.read_text())
    model = ROOT/'models/linear-head-policy.npz'
    expected_weights = fit['local_weights_sha256']
    if (sha(model) != expected_weights or fit['environment'] != environment()
            or get_adapter('waverep').adapter.checkpoint['sha256'] != fit['encoder_sha256']
            or fit['heads'] != ['light_only', 'both_levels']):
        raise ValueError('Original model or inference environment changed')
    original = [ROOT/p for p in fit['fingerprints']]
    if file_map(original) != fit['fingerprints']:
        raise ValueError('Original scoring code or fit inputs changed')
    paths = sorted({*original, *prior_files, path, manifest, fit_path, Path(__file__).resolve(),
                    ROOT/'scripts/check_head_cutoff.py', ROOT/'configs/head-transfer-selection.md'})
    revisions = {p.relative_to(ROOT).as_posix(): frozen_revision(ROOT, p) for p in paths}
    fingerprints = file_map(paths)
    with np.load(model, allow_pickle=False) as data:
        weight, intercept = data['weights'][1], float(data['intercepts'][1])

    x, rows, preparation = extract(config, samples)
    if file_map(paths) != fingerprints or sha(model) != expected_weights:
        raise ValueError('Frozen inputs changed during scoring')
    if weight.shape != (x.shape[1],):
        raise ValueError('Unexpected trained head shape')
    for row, margin in zip(rows, x @ weight + intercept, strict=True):
        row.update(trained_margin=float(margin),
                   sampled_frame_indices=json.dumps(row['sampled_frame_indices']))
    results = {name: by_variant(rows, name+'_margin', 0) for name in ('released', 'trained')}
    original_heavy, trained_heavy = (results[k]['compression'] for k in ('released','trained'))
    met_target = (trained_heavy['ai_missed'] < original_heavy['ai_missed']
                  and trained_heavy['real_flagged'] <= original_heavy['real_flagged'])
    output.mkdir(parents=True, exist_ok=True)
    scores = output/'scores.csv'
    with scores.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    write(output/'summary.json', dict(test=results, met_heavy_compression_target=met_target,
          scores_sha256=sha(scores), original_weights_sha256=expected_weights,
          encoder_sha256=fit['encoder_sha256'], environment=fit['environment'],
          frozen_revisions=revisions, fingerprints=fingerprints, preparation=preparation,
          reconstructed_released_logits='exact', cutoff_margin=0))
    print(json.dumps(dict(test=results, met_target=met_target), indent=2))


if __name__ == '__main__':
    main()
