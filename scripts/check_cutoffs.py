"""Choose cutoffs on one frozen split and evaluate them on another."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, inside, load_config

MIDPOINT = 0.5
ALL_NEGATIVE = math.nextafter(1.0, math.inf)


def counts(scores, cutoff):
    real = [score for label, score in scores if label == 'real']
    ai = [score for label, score in scores if label == 'ai']
    return dict(real_clips=len(real), ai_clips=len(ai),
                real_flagged=sum(score >= cutoff for score in real),
                ai_missed=sum(score < cutoff for score in ai))


def choose_cutoff(scores, max_real_flags):
    """Use observed boundaries, the reference point and an all-negative rule."""
    options = {MIDPOINT, ALL_NEGATIVE, *(score for _, score in scores)}
    eligible = [(cutoff, counts(scores, cutoff)) for cutoff in options]
    cutoff, result = min(
        (item for item in eligible if item[1]['real_flagged'] <= max_real_flags),
        key=lambda item: (item[1]['ai_missed'], item[1]['real_flagged'], -item[0]),
    )
    return dict(cutoff=cutoff, **result)


def split_keys(samples, split):
    grouped = defaultdict(list)
    for sample in samples:
        if sample['split'] != split:
            raise ValueError('Sample is in the wrong split')
        grouped[sample['anchor_id']].append(sample)
    sources = set()
    for pair in grouped.values():
        if Counter(s['label'] for s in pair) != {'real': 1, 'ai': 1}:
            raise ValueError('Each anchor needs a real and generated clip')
        urls = {s['original_source_url'] for s in pair}
        if len(urls) != 1 or sources & urls:
            raise ValueError('Expected one distinct recording per pair')
        sources.update(urls)
    return dict(anchor=set(grouped), original_recording=sources,
                digest={s['sha256'] for s in samples}, id={s['id'] for s in samples},
                parent={s['anchor_id'].split('__scene_')[0] for s in samples})


def read_run(path, manifest, config, samples):
    directory = ROOT / 'reports/experiments' / config['name']
    metadata = json.loads((directory / 'run.json').read_text())
    if (metadata['config_sha256'], metadata['manifest_sha256']) != (sha(path), sha(manifest)):
        raise ValueError('Run does not match the frozen config and manifest')
    expected = {(s['id'], d, v['name']): s['label'] for s in samples
                for d in config['detectors'] for v in config['variants']}
    path = directory / 'scores.csv'
    result = {}
    with path.open() as file:
        for row in csv.DictReader(file):
            key = (row['video_id'], row['detector'], row['variant'])
            score = float(row['ai_score'])
            if (key in result or expected.get(key) != row['label']
                    or not math.isfinite(score) or not 0 <= score <= 1):
                raise ValueError('Unexpected or invalid score row')
            result[key] = (row['label'], score)
    if set(result) != set(expected):
        raise ValueError('Incomplete score matrix')
    return metadata, path, result


def variants(config, crfs):
    names = ['baseline', 'compression']
    return (config['preparation'] == 'native' and config['baseline'] == 'baseline'
            and config.get('analysis', 'midpoint') == 'midpoint'
            and config['variants'] == [dict(name=name, transform='identity', encoding='h264', crf=crf)
                                      for name, crf in zip(names, crfs)])


def evaluate(scores, detector, samples, cutoff):
    result = {variant: counts([scores[s['id'], detector, variant] for s in samples], cutoff)
              for variant in ('baseline', 'compression')}
    changes = []
    for sample in samples:
        clip, label = sample['id'], sample['label']
        a, b = [scores[clip, detector, v][1] for v in ('baseline', 'compression')]
        if (a >= cutoff) != (b >= cutoff):
            changes.append(dict(video_id=clip, label=label, baseline=a, compression=b,
                                new_error=(b >= cutoff) != (label == 'ai')))
    return dict(cutoff=cutoff, **result, paired_crossings=changes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['fit', 'score-test', 'evaluate'])
    parser.add_argument('policy', help='Committed policy JSON')
    args = parser.parse_args()
    policy_path = inside(ROOT, args.policy, 'configs')
    policy = json.loads(policy_path.read_text())
    fit = load_config(ROOT, policy['cutoff_config'])
    test = load_config(ROOT, policy['test_config'])
    fp, fm, fc, fs = fit
    tp, tm, tc, ts = test
    for path in (policy_path, fp, fm, tp, tm, Path(__file__).resolve()):
        frozen_revision(ROOT, path)
    a, b = split_keys(fs, 'cutoff'), split_keys(ts, 'test')
    if any(a[k] & b[k] for k in a):
        raise ValueError('The cutoff and test splits share inputs')
    if (not variants(fc, [18]) or not variants(tc, [18, 35])
            or fc['detectors'] != tc['detectors']
            or fc.get('sampling', 'centered_4s_16') != tc.get('sampling', 'centered_4s_16')):
        raise ValueError('Cutoff and test settings disagree')
    expected = {'real': policy['pairs_per_split'], 'ai': policy['pairs_per_split']}
    if any(Counter(s['label'] for s in split) != expected for split in (fs, ts)):
        raise ValueError('Unexpected split size')
    limit = policy['max_cutoff_real_flags']
    if type(limit) is not int or not 0 <= limit < expected['real']:
        raise ValueError('Invalid false-flag budget')
    out = inside(ROOT, policy['output'], 'reports')
    target = out / 'cutoffs.json'
    test_run = ROOT / 'reports/experiments' / tc['name'] / 'run.json'
    if args.stage == 'fit' and test_run.exists():
        raise ValueError('The test run already exists; use the original frozen cutoffs')
    fit_meta, fit_csv, fit_scores = read_run(*fit)
    learned = {}
    for detector in fc['detectors']:
        scores = [fit_scores[s['id'], detector, 'baseline'] for s in fs]
        learned[detector] = choose_cutoff(scores, limit) | {'midpoint': counts(scores, MIDPOINT)}
    record = dict(policy_sha256=sha(policy_path), script_sha256=sha(Path(__file__)),
                  cutoff_config_sha256=sha(fp), cutoff_manifest_sha256=sha(fm),
                  cutoff_scores_sha256=sha(fit_csv), test_config_sha256=sha(tp),
                  test_manifest_sha256=sha(tm), model_sha256=fit_meta['model_sha256'],
                  rule='AI if score >= cutoff; maximize AI caught, then minimize real flags, then choose higher cutoff',
                  max_cutoff_real_flags=limit, cutoffs=learned)
    if args.stage == 'fit':
        out.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps(learned, indent=2))
        return
    commit = frozen_revision(ROOT, target)
    if record != json.loads(target.read_text()):
        raise ValueError('Cutoff record disagrees with its original inputs')
    if args.stage == 'score-test':
        if test_run.exists():
            raise ValueError('The test run already exists; use evaluate to check it')
        from vidrobust.experiment import run_experiment
        run_experiment(ROOT, tp)
    test_meta, test_csv, test_scores = read_run(*test)
    timestamp = subprocess.check_output(['git', 'show', '-s', '--format=%cI', commit],
                                        cwd=ROOT, text=True).strip()
    if datetime.fromisoformat(test_meta['created_at_utc']) < datetime.fromisoformat(timestamp):
        raise ValueError('Test run predates the frozen cutoffs')
    for key in ('model_sha256', 'code_sha256', 'packages', 'ffmpeg'):
        if test_meta[key] != fit_meta[key]:
            raise ValueError(f'Scoring environment changed: {key}')
    results = {d: {'midpoint': evaluate(test_scores, d, ts, MIDPOINT),
                   'frozen': evaluate(test_scores, d, ts, learned[d]['cutoff'])}
               for d in tc['detectors']}
    summary = dict(frozen_cutoff_commit=commit, frozen_cutoff_sha256=sha(target),
                   test_scores_sha256=sha(test_csv), disjoint_inputs_verified=True, test=results)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for d, rules in results.items():
        for name, row in rules.items():
            print(d, name, row['baseline'], row['compression'], 'crossings:', len(row['paired_crossings']))


if __name__ == '__main__':
    main()
