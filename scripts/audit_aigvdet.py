"""Check released RGB-branch parity against pinned author code on fixed clips.

This audits an adapter, not a separate experiment runner. No weights are fetched
implicitly: the registered factory verifies the pinned checkpoint first.
"""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from vidrobust.artifacts import sha
from vidrobust.experiment import load_config, frozen_revision
from vidrobust.frame_scoring import score_frames, tensor_digest
from vidrobust.media import read_exact_rgb
from vidrobust.registry import make_detector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    parser.add_argument('--clips', nargs='+', required=True)
    args = parser.parse_args()
    config_path, manifest_path, config, samples = load_config(ROOT, args.config)
    if 'aigvdet_rgb' not in config['detectors'] or set(args.clips) - {s['id'] for s in samples}:
        raise ValueError('Choose clips in a config with aigvdet_rgb')
    if config['preparation'] != 'native' or config['variants'] != [dict(name='original', transform='identity', encoding='source')]:
        raise ValueError('This native parity audit requires unchanged source bytes')
    frozen_revision(ROOT, config_path)
    frozen_revision(ROOT, manifest_path)
    import torch
    from PIL import Image
    from torchvision import transforms
    from torchvision.transforms import functional as TF
    source = ROOT / 'vendor/aigvdet/resnet.py'
    if sha(source) != 'c7e477dba329434df9ae421e32eae0552b9c2e95db769dbff1050887ca326dc7':
        raise ValueError('Pinned author model source changed')
    spec = importlib.util.spec_from_file_location('aigvdet_author_resnet', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    adapter = make_detector(ROOT, 'aigvdet_rgb')
    native = module.resnet50(num_classes=1)
    state = torch.load(ROOT / adapter.checkpoint['path'], map_location='cpu', weights_only=True)['model']
    native.load_state_dict(state, strict=True)
    native.eval()
    if set(native.state_dict()) != set(adapter.model.state_dict()):
        raise ValueError('Architecture state keys differ')
    sys.path.insert(0, str(ROOT / 'vendor/aegis'))
    from video_io import window_sample
    out = ROOT / f"reports/experiments/{config['name']}"
    references = {}
    if (out / 'scores.csv').exists():
        run = json.loads((out / 'run.json').read_text())
        if sha(config_path) != run['config_sha256'] or sha(manifest_path) != run['manifest_sha256']:
            raise ValueError('Stored run plan changed')
        for path, expected in run['code_sha256'].items():
            if sha(ROOT / path) != expected:
                raise ValueError('Stored scoring code changed')
        with (out / 'scores.csv').open() as f:
            references = {r['video_id']: r for r in csv.DictReader(f) if r['detector'] == 'aigvdet_rgb'}
    if references:
        for row in references.values():
            logits = json.loads(row['frame_logits'])
            probabilities = json.loads(row['frame_scores'])
            native_probs = [torch.tensor(v, dtype=torch.float32).sigmoid().item() for v in logits]
            if len(logits) != 16 or probabilities != native_probs or float(row['ai_score']) != sum(native_probs)/16:
                raise ValueError('Stored RGB score arithmetic differs')
    results = []
    for clip in args.clips:
        sample = next(s for s in samples if s['id'] == clip)
        path = ROOT / config['source_directory'] / f'{clip}.mp4'
        if sha(path) != sample['sha256']:
            raise ValueError('Source bytes differ')
        meta = sample['actual_metadata']
        indices = window_sample(meta['frames'], 16, meta['fps'], target_dur=4, random_start=False).tolist()
        frames = read_exact_rgb(path, indices)
        trans = transforms.Compose([transforms.CenterCrop((448, 448)), transforms.ToTensor()])
        tensor = torch.stack([TF.normalize(trans(Image.fromarray(f)), [.485, .456, .406], [.229, .224, .225]) for f in frames])
        with torch.inference_mode():
            if not torch.equal(tensor, adapter.prepare_frames(frames)):
                raise ValueError('Native preprocessing differs')
            logits, probabilities = [], []
            for image in tensor:
                prediction = native(image.unsqueeze(0))
                logits.append(prediction.item())
                probabilities.append(prediction.sigmoid().item())
            actual = score_frames(adapter, 'aigvdet_rgb', frames)
        if actual['frame_logits'] != logits or actual['frame_scores'] != probabilities or actual['ai_score'] != sum(probabilities)/16:
            raise ValueError('Native logits, probabilities or video aggregation differ')
        if references:
            row = references[clip]
            for key, value in actual.items():
                expected = json.loads(row[key]) if isinstance(value, list) else row[key] if isinstance(value, str) else float(row[key])
                if value != expected:
                    raise ValueError('Fresh native audit differs from stored score: ' + key)
            if json.loads(row['sampled_frame_indices']) != indices:
                raise ValueError('Stored frame indices differ')
        results.append(dict(video_id=clip, ai_score=actual['ai_score'], sha256=sha(path),
            model_input_sha256=tensor_digest(tensor), frame_logits=logits,
            exact_native_preprocessing_logits_probabilities_and_aggregation=True,
            stored_run_exact_match=bool(references)))
        print(f'Native RGB-branch parity passed: {clip} {actual["ai_score"]:.6f}', flush=True)
    audit = dict(checkpoint_sha256=sha(ROOT / adapter.checkpoint['path']), author_model_sha256=sha(source),
        adapter_sha256=sha(ROOT / 'src/vidrobust/adapters/aigvdet_rgb.py'),
        script_sha256=sha(Path(__file__).resolve()), config_sha256=sha(config_path),
        manifest_sha256=sha(manifest_path), state_tensors_loaded_strictly=len(state), clips=results,
        independently_checked_stored_score_arithmetic=len(references),
        scope='RGB branch only; same sparse 16 frames, not full optical-flow detector or all-frame evaluation')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'native-adapter-audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    if references:
        path = out / 'validation.json'
        validation = json.loads(path.read_text())
        validation['native_RGB_branch_parity'] = dict(audit='native-adapter-audit.json',
            audit_sha256=sha(out / 'native-adapter-audit.json'), clips=args.clips, exact_match=True)
        path.write_text(json.dumps(validation, indent=2)+'\n')


if __name__ == '__main__':
    main()
