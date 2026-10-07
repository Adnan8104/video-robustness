"""Reload models and repeat spatial crossings plus the largest changes per label."""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from vidrobust.artifacts import sha
from vidrobust.experiment import load_config
from vidrobust.frame_scoring import score_frames
from vidrobust.media import read_exact_rgb
from vidrobust.registry import get_adapter, make_detector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    parser.add_argument('--variants', nargs='+', required=True)
    args = parser.parse_args()
    config_path, manifest_path, config, samples = load_config(ROOT, args.config)
    if set(args.variants) - {v['name'] for v in config['variants']} or config['baseline'] in args.variants:
        raise ValueError('Choose existing non-baseline variants')
    out = ROOT / f"reports/experiments/{config['name']}"
    run = json.loads((out / 'run.json').read_text())
    if sha(config_path) != run['config_sha256'] or sha(manifest_path) != run['manifest_sha256']:
        raise ValueError('Config or manifest changed')
    for path, expected in run['code_sha256'].items():
        if sha(ROOT / path) != expected:
            raise ValueError('Scoring code changed: ' + path)
    with (out / 'scores.csv').open() as f:
        rows = list(csv.DictReader(f))
    indexed = {(r['video_id'], r['variant'], r['detector']): r for r in rows}
    repeats = []
    for name in config['detectors']:
        if get_adapter(name).metadata(ROOT) != run['models'][name]:
            raise ValueError('Registered adapter changed')
        if sha(ROOT / run['models'][name]['checkpoint']['path']) != run['model_sha256'][name]:
            raise ValueError('Checkpoint changed')
        edits = [r for r in rows if r['detector'] == name and r['variant'] in args.variants]
        targets = [r for r in edits if
                   (float(r['ai_score']) >= .5) != (float(indexed[(r['video_id'], config['baseline'], name)]['ai_score']) >= .5)]
        for label in sorted({s['label'] for s in samples}):
            group = [r for r in edits if r['label'] == label]
            if group:
                targets.append(max(group, key=lambda r: abs(float(r['delta_vs_baseline']))))
        selected = dict.fromkeys((r['video_id'], v) for r in targets for v in (config['baseline'], r['variant']))
        detector = make_detector(ROOT, name)
        for clip, variant_name in selected:
            row = indexed[(clip, variant_name, name)]
            variant = next(v for v in config['variants'] if v['name'] == variant_name)
            if variant['encoding'] == 'source':
                path = ROOT / config['source_directory'] / f'{clip}.mp4'
            else:
                suffix = 'avi' if variant['encoding'] == 'ffv1' else 'mp4'
                path = ROOT / f"data/experiments/{config['name']}/{clip}_{variant_name}.{suffix}"
            if sha(path) != row['sha256']:
                raise ValueError('Repeat input changed')
            indices = json.loads(row['sampled_frame_indices'])
            details = score_frames(detector, name, read_exact_rgb(path, indices))
            for key, value in details.items():
                expected = json.loads(row[key]) if isinstance(value, list) else row[key] if isinstance(value, str) else float(row[key])
                if value != expected:
                    raise ValueError(f'Repeat differs: {name}/{clip}/{variant_name}/{key}')
            repeats.append(dict(detector=name, video_id=clip, variant=variant_name,
                ai_score=details['ai_score'], all_outputs_and_input_hashes_exact_match=True))
            print(f'Fresh-model repeat passed: {name} {clip} {variant_name}', flush=True)
        del detector
    validation_path = out / 'validation.json'
    validation = json.loads(validation_path.read_text())
    validation['fresh_model_repeat_selection'] = dict(variants=args.variants,
        rule='All selected-variant midpoint crossings plus the largest absolute change per detector and label; baseline included; cases deduplicated')
    validation['fresh_model_repeats'] = repeats
    validation_path.write_text(json.dumps(validation, indent=2)+'\n')
    print(f'Fresh-model repeats passed: {len(repeats)}; two reloads for the current panel')


if __name__ == '__main__':
    main()
