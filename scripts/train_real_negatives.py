"""Check whether extra real footage helps the fixed-encoder classifier."""
import argparse
import csv
import hashlib
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
from vidrobust.linear_head import recording_keys
from vidrobust.registry import get_adapter

OUT = ROOT / 'reports/real-negatives'
ORIGINAL = ROOT / 'models/linear-head-policy.npz'
LOCAL = ROOT / 'models/real-negatives.npz'
PRIOR = ('rabench-pilot', 'rabench-format', 'linear-head-train',
         'linear-head-test', 'head-cutoff-test')


def balanced_ridge(x, y, penalty):
    """Give each class half the loss, leaving the intercept unpenalized."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if (x.ndim != 2 or y.shape != (len(x),) or set(y) != {-1, 1}
            or not np.isfinite(x).all() or not np.isfinite(penalty) or penalty <= 0):
        raise ValueError('Expected finite features, both labels and a positive penalty')
    mass = np.array([.5 / np.count_nonzero(y == k) for k in y])
    mean = mass @ x
    mean_y = mass @ y
    scale = np.sqrt(mass)
    z = (x - mean) * scale[:, None]
    a = np.linalg.solve(z @ z.T + penalty * np.eye(len(x)), (y - mean_y) * scale)
    w = z.T @ a
    return w, float(mean_y - mean @ w)


def setup():
    original_plan = load_config(ROOT, 'configs/experiments/linear-head-train.json')
    extra = load_config(ROOT, 'configs/experiments/real-negatives-train.json')
    test = load_config(ROOT, 'configs/experiments/real-negatives-test.json')
    extra_sources = extra[3]
    fresh = recording_keys(test[3])
    if len(fresh['anchors']) != 8 or len(fresh['parents']) != 8:
        raise ValueError('Expected eight separate test recordings')
    prior_files = [ROOT / f'configs/{name}.json' for name in PRIOR]
    for path in prior_files:
        seen = recording_keys(json.loads(path.read_text())['samples'])
        if any(fresh[key] & seen[key] for key in fresh):
            raise ValueError(f'Test overlap with {path.name}')
    manifests = [json.loads(path.read_text()) for path in prior_files[-2:]]
    eligible = {s['sha256']: {'revision': m['revision'], **s}
                for m in manifests for s in m['samples'] if s['label'] == 'real'}
    if (len(extra_sources) != 16 or {s['sha256'] for s in extra_sources} != set(eligible)
            or any(s['label'] != 'real' or any(s[k] != eligible[s['sha256']][k]
                   for k in ('anchor_id','original_source_url','remote_path','revision','actual_metadata'))
                   for s in extra_sources)):
        raise ValueError('Extra training must include every real recording from both prior tests')
    for _, _, config, _ in (original_plan, extra, test):
        if (config['detectors'] != ['waverep'] or config['variants'] != VARIANTS
                or config['baseline'] != 'baseline'
                or config['preparation'] != 'centered_4s_504_24fps'
                or config.get('sampling', 'centered_4s_16') != 'centered_4s_16'):
            raise ValueError('Unexpected model or preparation')
    fit_path = ROOT / 'reports/linear-head/fit.json'
    fit = json.loads(fit_path.read_text())
    checkpoint = get_adapter('waverep').adapter.checkpoint
    if (fit['local_weights_sha256'] != sha(ORIGINAL) or fit['environment'] != environment()
            or fit['encoder_sha256'] != checkpoint['sha256']):
        raise ValueError('Original weights or environment changed')
    original_code = [ROOT / p for p in fit['fingerprints']]
    if file_map(original_code) != fit['fingerprints']:
        raise ValueError('Original scoring path has changed')
    paths = {*original_code, fit_path, *prior_files, *extra[:2], *test[:2],
             Path(__file__).resolve(), ROOT / 'scripts/check_head_cutoff.py',
             ROOT / 'configs/real-negatives-selection.md'}
    provenance = dict(fingerprints=file_map(sorted(paths)),
                      revisions={p.relative_to(ROOT).as_posix(): frozen_revision(ROOT, p)
                                 for p in sorted(paths)},
                      original_weights_sha256=fit['local_weights_sha256'],
                      encoder_sha256=checkpoint['sha256'], environment=fit['environment'])
    return original_plan, extra, test, fit, provenance


def verify_inputs(provenance):
    if (sha(ORIGINAL) != provenance['original_weights_sha256']
            or any(sha(ROOT / p) != h for p, h in provenance['fingerprints'].items())):
        raise ValueError('Frozen inputs changed during the run')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('fit', 'test'))
    args = parser.parse_args()
    original_plan, extra, test, fit, provenance = setup()
    with np.load(ORIGINAL, allow_pickle=False) as data:
        orig_w, orig_b = data['weights'][1], float(data['intercepts'][1])
    OUT.mkdir(parents=True, exist_ok=True)
    fit_path, score_path, summary_path = [OUT / p for p in ('fit.json','scores.csv','summary.json')]
    if score_path.exists() or summary_path.exists():
        raise ValueError('Test results already exist')
    if args.stage == 'fit':
        if fit_path.exists():
            raise ValueError('Fit already exists')
        base, base_rows, _ = extract(original_plan[2], original_plan[3])
        if (hashlib.sha256(base.tobytes()).hexdigest() != fit['feature_sha256']
                or base_rows != fit['training_inputs']):
            raise ValueError('Original features or video inputs do not reproduce')
        y = np.array([1 if r['label'] == 'ai' else -1 for r in base_rows])
        w, b = balanced_ridge(base, y, fit['ridge_penalty'])
        if not (np.allclose(w, orig_w, atol=1e-10, rtol=0)
                and np.isclose(b, orig_b, atol=1e-10, rtol=0)):
            raise ValueError('Balanced objective did not reproduce the original head')
        negatives, extra_rows, preparation = extract(extra[2], extra[3])
        features = np.concatenate([base, negatives])
        labels = np.concatenate([y, np.full(len(negatives), -1)])
        w, b = balanced_ridge(features, labels, fit['ridge_penalty'])
        verify_inputs(provenance)
        np.savez(LOCAL, weights=w, intercept=b)
        np.savez(ROOT/'models/real-negatives-features.npz', base=base, extra=negatives, labels=labels)
        write(fit_path, provenance | dict(
            weights_sha256=sha(LOCAL), original_feature_sha256=fit['feature_sha256'],
            added_feature_sha256=hashlib.sha256(negatives.tobytes()).hexdigest(),
            original_examples=len(base), added_examples=len(negatives), ridge_penalty=fit['ridge_penalty'],
            extra_inputs=extra_rows, extra_preparation=preparation, recreated_original_head=True))
        print('Fit complete; commit fit.json before testing.', flush=True)
        return

    commit = frozen_revision(ROOT, fit_path)
    record = json.loads(fit_path.read_text())
    if (any(record[k] != value for k, value in provenance.items())
            or sha(LOCAL) != record['weights_sha256']):
        raise ValueError('Local fit differs from the locked record')
    with np.load(LOCAL, allow_pickle=False) as data:
        w, b = data['weights'], float(data['intercept'])
    features, rows, preparation = extract(test[2], test[3])
    verify_inputs(provenance)
    if sha(LOCAL) != record['weights_sha256'] or frozen_revision(ROOT, fit_path) != commit:
        raise ValueError('Locked fit changed during scoring')
    for row, old, new in zip(rows, features @ orig_w + orig_b, features @ w + b, strict=True):
        row.update(original_margin=float(old), extra_real_margin=float(new),
                   sampled_frame_indices=json.dumps(row['sampled_frame_indices']))
    results = {k: by_variant(rows, k + '_margin', 0) for k in ('released','original','extra_real')}
    old, new = (results[k]['compression'] for k in ('original','extra_real'))
    met_target = (new['real_flagged'] < old['real_flagged'] and new['ai_missed'] <= old['ai_missed']
                  and new['ai_missed'] < new['ai_clips'])
    with score_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    write(summary_path, dict(fit_commit=commit, fit_sha256=sha(fit_path),
          scores_sha256=sha(score_path), preparation=preparation, test=results,
          met_heavy_compression_target=met_target))
    print(json.dumps(dict(test=results, met_target=met_target), indent=2), flush=True)


if __name__ == '__main__':
    main()
