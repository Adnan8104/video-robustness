"""Measure false flags for the released and original trained heads on real clips."""
from collections import Counter
import csv
import json
import math
from pathlib import Path

import numpy as np

if __package__:
    from .train_head import ROOT, VARIANTS, environment, extract, file_map, write
else:
    from train_head import ROOT, VARIANTS, environment, extract, file_map, write
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, load_config
from vidrobust.registry import get_adapter


def count_false_flags(rows, column):
    cases = {(r['video_id'], r['variant']): r for r in rows}
    sources = {r['video_id'] for r in rows}
    variants = ('baseline', 'compression')
    if (not sources or len(cases) != len(rows)
            or set(cases) != {(s,v) for s in sources for v in variants}
            or any(r['label'] != 'real' or not math.isfinite(float(r[column])) for r in rows)):
        raise ValueError('Expected complete, finite paired results on real footage')
    category = {s: cases[s, 'baseline']['cell'] for s in sources}
    if any(r['cell'] != category[r['video_id']] or r['cell'] == 'all' for r in rows):
        raise ValueError('Recording category must be fixed across encodes')
    result = {}
    for key in ('all', *sorted(set(category.values()))):
        members = {s for s in sources if key == 'all' or category[s] == key}
        flags = {v: {s for s in members if float(cases[s,v][column]) >= 0} for v in variants}
        light, heavy = (flags[v] for v in variants)
        result[key] = dict(clips=len(members), baseline_flagged=len(light), compression_flagged=len(heavy),
                           new_flags=sorted(heavy-light), cleared_flags=sorted(light-heavy),
                           flagged_at_both=sorted(light & heavy))
    return result


def main():
    out = ROOT/'reports/false-flags'
    if any((out/p).exists() for p in ('scores.csv', 'summary.json')):
        raise ValueError('This panel has already been scored')
    path, manifest, config, samples = load_config(ROOT, 'configs/experiments/false-flags.json')
    if (Counter((r['label'], r['cell']) for r in samples) != {('real','sports'):20, ('real','vlog'):10}
            or len({r['source_id'] for r in samples}) != 30
            or len({r['author'].casefold() for r in samples}) != 30
            or config['detectors'] != ['waverep'] or config['variants'] != VARIANTS
            or config['baseline'] != 'baseline' or config['preparation'] != 'centered_4s_504_24fps'
            or config.get('sampling', 'centered_4s_16') != 'centered_4s_16'):
        raise ValueError('Unexpected real-footage protocol')
    fit_path = ROOT/'reports/linear-head/fit.json'
    fit = json.loads(fit_path.read_text())
    weights = ROOT/'models/linear-head-policy.npz'
    model_sha = sha(weights)
    if (model_sha != fit['local_weights_sha256'] or environment() != fit['environment']
            or fit['heads'] != ['light_only','both_levels']
            or get_adapter('waverep').adapter.checkpoint['sha256'] != fit['encoder_sha256']):
        raise ValueError('Original model or scoring environment differs')
    original = [ROOT/p for p in fit['fingerprints']]
    if file_map(original) != fit['fingerprints']:
        raise ValueError('Original fit inputs or scoring code changed')
    paths = sorted({*original, path, manifest, fit_path, Path(__file__).resolve(),
                    ROOT/'configs/false-flags-selection.md'})
    revisions = {p.relative_to(ROOT).as_posix(): frozen_revision(ROOT, p) for p in paths}
    fingerprints = file_map(paths)
    with np.load(weights, allow_pickle=False) as data:
        w, b = data['weights'][1], float(data['intercepts'][1])
    features, rows, preparation = extract(config, samples)
    if file_map(paths) != fingerprints or sha(weights) != model_sha:
        raise ValueError('Frozen code, data or weights changed')
    for row, margin in zip(rows, features @ w + b, strict=True):
        row.update(trained_margin=float(margin), sampled_frame_indices=json.dumps(row['sampled_frame_indices']))
    stats = {name: count_false_flags(rows, name+'_margin') for name in ('released','trained')}
    out.mkdir(parents=True, exist_ok=True)
    score_path = out/'scores.csv'
    with score_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    write(out/'summary.json', dict(test=stats, scores_sha256=sha(score_path), preparation=preparation,
        weights_sha256=model_sha, encoder_sha256=fit['encoder_sha256'], environment=fit['environment'],
        frozen_revisions=revisions, fingerprints=fingerprints, cutoff_margin=0,
        reconstructed_released_logits='exact'))
    print(json.dumps(stats, indent=2), flush=True)


if __name__ == '__main__':
    main()
