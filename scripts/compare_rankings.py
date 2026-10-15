"""Compare ranking runs on identical sources, retaining every real control."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from vidrobust.artifacts import sha
from vidrobust.experiment import inside, load_config


def evaluate(rows, targets):
    if not targets or len(set(targets)) != len(targets):
        raise ValueError('Choose unique targets')
    if not rows or len({r['video_id'] for r in rows}) != len(rows):
        raise ValueError('Expected exactly one score per source')
    real = [r for r in rows if r['label'] == 'real']
    ai = [r for r in rows if r['label'] == 'ai']
    if not real or not ai or any(r['label'] not in ('real','ai') or not math.isfinite(float(r['ai_score']))
                                or not 0<=float(r['ai_score'])<=1 for r in rows):
        raise ValueError('Expected finite scores for both labels')
    wins = sum(float(a['ai_score']) > float(b['ai_score']) for a in ai for b in real)
    ties = sum(float(a['ai_score']) == float(b['ai_score']) for a in ai for b in real)
    indexed = {r['video_id']:r for r in rows}
    if any(t not in indexed or indexed[t]['label'] != 'ai' for t in targets):
        raise ValueError('Every target must be an existing AI source')
    checks = []
    for target in targets:
        row = indexed[target]
        blockers = [dict(video_id=r['video_id'], ai_score=float(r['ai_score']),
                        temporal_std=float(r['temporal_std']))
                    for r in real if float(r['ai_score']) >= float(row['ai_score'])]
        checks.append(dict(video_id=target, ai_score=float(row['ai_score']),
            temporal_std=float(row['temporal_std']), blocking_controls=blockers,
            strictly_ahead_of_all_real=not blockers))
    return dict(real_clips=len(real), ai_clips=len(ai), pairs=len(real)*len(ai),
        ai_above_real=wins, ties=ties, auc=(wins+.5*ties)/(len(real)*len(ai)),
        targets=checks, all_targets_strictly_ahead_of_all_real=all(not t['blocking_controls'] for t in checks))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('configs',nargs='+')
    parser.add_argument('--targets',nargs='+',required=True)
    parser.add_argument('--output',required=True,help='Directory under reports/')
    args=parser.parse_args()
    if len(set(args.targets))!=len(args.targets):
        raise ValueError('Targets must be unique')
    out=inside(ROOT,args.output,'reports')
    runs=[]
    reference=None
    inputs_by_profile={}
    for config in args.configs:
        config_path,manifest_path,plan,samples=load_config(ROOT,config)
        if plan.get('analysis')!='ranking' or len(plan['detectors'])!=1 or len(plan['variants'])!=1:
            raise ValueError('Choose single-model, single-variant ranking runs')
        directory=ROOT/'reports/experiments'/plan['name']
        metadata=json.loads((directory/'run.json').read_text())
        if sha(config_path)!=metadata['config_sha256'] or sha(manifest_path)!=metadata['manifest_sha256']:
            raise ValueError('Stored input plan changed')
        rows=list(csv.DictReader((directory/'scores.csv').open()))
        selected={s['id']:s for s in samples}
        if set(r['video_id'] for r in rows)!=set(selected):
            raise ValueError('Incomplete score matrix')
        sources={r['video_id']:(r['sha256'],r['label']) for r in rows}
        for clip,(digest,label) in sources.items():
            if (digest,label)!=(selected[clip]['sha256'],selected[clip]['label']):
                raise ValueError('Stored source or label differs from manifest')
        if reference is not None and sources!=reference:
            raise ValueError('Ranking runs must use identical sources and labels')
        reference=sources
        if any(r['detector']!=plan['detectors'][0] or r['variant']!=plan['variants'][0]['name'] for r in rows):
            raise ValueError('Stored detector or variant differs')
        sampling=plan.get('sampling','centered_4s_16')
        inputs={r['video_id']:(r['sampled_frame_indices'],r['sampled_rgb_sha256'],r['model_input_sha256']) for r in rows}
        if sampling in inputs_by_profile and inputs!=inputs_by_profile[sampling]:
            raise ValueError('Inputs differ within a sampling profile')
        inputs_by_profile[sampling]=inputs
        metrics=evaluate(rows,args.targets)
        stored=json.loads((directory/'summary.json').read_text())[plan['detectors'][0]][plan['variants'][0]['name']]['all']
        if (stored['pairwise_auc'],stored['ai_above_real'],stored['ties'],stored['pairs'])!=(metrics['auc'],metrics['ai_above_real'],metrics['ties'],metrics['pairs']):
            raise ValueError('Independent ranking counts differ')
        runs.append(dict(experiment=plan['name'],detector=plan['detectors'][0],sampling=sampling,
            scores_path=str((directory/'scores.csv').relative_to(ROOT)),scores_sha256=sha(directory/'scores.csv'),
            config_sha256=sha(config_path),manifest_sha256=sha(manifest_path),**metrics))
    result=dict(script_sha256=sha(Path(__file__).resolve()),criterion='Every target strictly ahead of every real control; no cutoff fitted',
        identical_source_hashes_and_labels=True,identical_frame_indices_RGB_and_normalized_tensors_within_sampling_profiles=True,runs=runs)
    out.mkdir(parents=True,exist_ok=True)
    (out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Temporal encoder comparison','',f"All runs use the same {runs[0]['real_clips']} real and {runs[0]['ai_clips']} AI source files. "
        'These are previously examined clips; AUC measures ordering, not detection accuracy. No cutoff is fitted.','',
        '| Run | Correctly ordered pairs / total | AUC | All targets strictly ahead of every real control |',
        '|---|---:|---:|---|']
    for run in runs:
        lines.append(f"| {run['experiment']} | {run['ai_above_real']}/{run['pairs']} | {run['auc']:.3f} | {'Yes' if run['all_targets_strictly_ahead_of_all_real'] else 'No'} |")
    lines+=['','## Shared misses','','A blocking control has an equal or more AI-like ranking coordinate than the AI target. '
        'Any blocker prevents a single cutoff from recovering that target without a real-video error on these data.','',
        '| Run | Target | Blocking controls / real clips | Control IDs |','|---|---|---:|---|']
    for run in runs:
        for target in run['targets']:
            controls=target['blocking_controls']
            lines.append(f"| {run['experiment']} | {target['video_id']} | {len(controls)}/{run['real_clips']} | {', '.join(r['video_id'] for r in controls) or 'None'} |")
    lines+=['','Sources, score hashes and exact target/control values: [comparison.json](comparison.json).','']
    (out/'report.md').write_text('\n'.join(lines))
    print(json.dumps([{k:r[k] for k in ('experiment','auc','all_targets_strictly_ahead_of_all_real')} for r in runs],indent=2))


if __name__=='__main__':
    main()
