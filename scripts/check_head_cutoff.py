"""Lock a single trained-head margin on development clips, then test fresh pairs."""
import argparse
import csv
import json
import math
from pathlib import Path

if __package__:
    from .train_head import ROOT, VARIANTS, environment, extract, write
else:
    from train_head import ROOT, VARIANTS, environment, extract, write
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, inside, load_config
from vidrobust.linear_head import metrics, recording_keys
from vidrobust.registry import get_adapter

import numpy as np

VARIANT_NAMES = ('baseline', 'compression')
REPORT = ROOT / 'reports/head-cutoff'
FIT = ROOT / 'reports/linear-head/fit.json'
DEV = ROOT / 'reports/linear-head/scores.csv'
DEV_SUMMARY = ROOT / 'reports/linear-head/summary.json'
WEIGHTS = ROOT / 'models/linear-head-policy.npz'
TEST = ROOT / 'configs/experiments/head-cutoff-test.json'
POLICY = ROOT / 'configs/head-cutoff-selection.md'
PRIOR = ('rabench-pilot', 'rabench-format', 'linear-head-train', 'linear-head-test')


def by_variant(rows, column, cutoff):
    result = {}
    for variant in VARIANT_NAMES:
        group = [r for r in rows if r['variant'] == variant]
        margins = [float(r[column]) for r in group]
        result[variant] = metrics([r['label'] for r in group], margins)
        result[variant].update(
            real_flagged=sum(r['label'] == 'real' and v >= cutoff for r, v in zip(group, margins)),
            ai_missed=sum(r['label'] == 'ai' and v < cutoff for r, v in zip(group, margins)))
    return result


def choose_cutoff(rows, budget):
    """Maximize heavy catches, then light catches, within both false-flag caps."""
    scores = [float(r['both_levels_margin']) for r in rows]
    if not scores or not all(map(math.isfinite, scores)) or budget < 0:
        raise ValueError('Expected finite margins and a nonnegative budget')
    candidates = {0., *(v for v in scores if v > 0),
                  math.nextafter(max(0., *scores), math.inf)}
    best = None
    for cutoff in sorted(candidates):
        result = by_variant(rows, 'both_levels_margin', cutoff)
        light, heavy = [result[v] for v in VARIANT_NAMES]
        flags = light['real_flagged'] + heavy['real_flagged']
        if max(light['real_flagged'], heavy['real_flagged']) > budget:
            continue
        key = heavy['ai_missed'], light['ai_missed'], flags, -cutoff
        if best is None or key < best[0]:
            best = key, cutoff, result
    _, cutoff, counts = best
    return cutoff, counts


def read_development(samples):
    expected = {(row['id'], v): row['label'] for row in samples for v in VARIANT_NAMES}
    with DEV.open() as stream:
        rows = list(csv.DictReader(stream))
    actual = {(r['video_id'], r['variant']): r['label'] for r in rows}
    if len(actual) != len(rows) or actual != expected:
        raise ValueError('Incomplete or unexpected development scores')
    return rows


def lock_record():
    path, manifest, config, samples = load_config(ROOT, TEST)
    keys = recording_keys(samples)
    if (len(keys['anchors']) != 8 or len(keys['parents']) != 8
            or config['detectors'] != ['waverep']
            or config['variants'] != VARIANTS or config['baseline'] != 'baseline'
            or config['preparation'] != 'centered_4s_504_24fps'
            or config.get('sampling', 'centered_4s_16') != 'centered_4s_16'):
        raise ValueError('Unexpected test cohort or preparation')
    prior_paths = [ROOT / f'configs/{name}.json' for name in PRIOR]
    for prior_path in prior_paths:
        previous = json.loads(prior_path.read_text())['samples']
        prior_keys = recording_keys(previous)
        if any(keys[k] & prior_keys[k] for k in keys):
            raise ValueError(f'Test recordings overlap {prior_path.name}')
    fit, dev_summary = [json.loads(p.read_text()) for p in (FIT, DEV_SUMMARY)]
    if dev_summary['fit_sha256'] != sha(FIT) or dev_summary['scores_sha256'] != sha(DEV):
        raise ValueError('Development results do not match the published fit')
    if fit['heads'] != ['light_only', 'both_levels'] or fit['local_weights_sha256'] != sha(WEIGHTS):
        raise ValueError('Local trained head does not match its original fit')
    if (fit['encoder_sha256'] != get_adapter('waverep').adapter.checkpoint['sha256']
            or fit['environment'] != environment()):
        raise ValueError('Encoder or scoring environment changed')
    original = [ROOT / p for p in fit['fingerprints']]
    if any(sha(p) != fit['fingerprints'][p.relative_to(ROOT).as_posix()] for p in original):
        raise ValueError('Original fit inputs or code changed')
    paths = sorted({*original, *prior_paths, path, manifest, POLICY, FIT, DEV, DEV_SUMMARY,
                    Path(__file__).resolve()})
    frozen = {p.relative_to(ROOT).as_posix(): frozen_revision(ROOT, p) for p in paths}
    dev = read_development(json.loads(prior_paths[-1].read_text())['samples'])
    cutoff, counts = choose_cutoff(dev, 1)
    record = dict(cutoff=cutoff, max_dev_real_flags_per_condition=1,
                  development=dict(zero=by_variant(dev, 'both_levels_margin', 0), stricter=counts),
                  weights_sha256=sha(WEIGHTS), encoder_sha256=fit['encoder_sha256'],
                  fingerprints={p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
                  frozen_revisions=frozen, environment=fit['environment'], test_pairs=8)
    return record, config, samples, fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['lock', 'test'])
    args = parser.parse_args()
    record, config, samples, fit = lock_record()
    REPORT.mkdir(parents=True, exist_ok=True)
    locked = REPORT / 'cutoff.json'
    scores = REPORT / 'scores.csv'
    summary = REPORT / 'summary.json'
    if scores.exists() or summary.exists():
        raise ValueError('The fresh test set has already been scored')
    if args.stage == 'lock':
        if locked.exists():
            raise ValueError('The cutoff record already exists')
        write(locked, record)
        print(json.dumps({k: record[k] for k in ('cutoff', 'development')}, indent=2))
        return
    commit = frozen_revision(ROOT, locked)
    if record != json.loads(locked.read_text()):
        raise ValueError('The committed cutoff does not match development inputs')
    with np.load(WEIGHTS, allow_pickle=False) as data:
        weights, intercepts = data['weights'], data['intercepts']
    if weights.shape != (2, fit['feature_dimensions']) or intercepts.shape != (2,):
        raise ValueError('Unexpected fitted weights')
    features, rows, preparation = extract(config, samples)
    if (sha(WEIGHTS) != record['weights_sha256']
            or json.loads(locked.read_text()) != record
            or any(sha(ROOT / p) != digest for p, digest in record['fingerprints'].items())):
        raise ValueError('Inputs changed during scoring')
    margins = features @ weights[1] + intercepts[1]
    for row, margin in zip(rows, margins.tolist(), strict=True):
        row.update(both_levels_margin=margin, sampled_frame_indices=json.dumps(row['sampled_frame_indices']))
    results = dict(released=by_variant(rows, 'released_margin', 0),
                   zero=by_variant(rows, 'both_levels_margin', 0),
                   stricter=by_variant(rows, 'both_levels_margin', record['cutoff']))
    with scores.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    write(summary, dict(cutoff_commit=commit, cutoff_sha256=sha(locked), scores_sha256=sha(scores),
                        reconstructed_released_logits='exact', preparation=preparation, test=results))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
