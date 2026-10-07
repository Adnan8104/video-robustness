"""Frozen content strata with common geometry and independent CRF encodes."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import time
from urllib.parse import quote

CELLS = ("real_animal", "real_non_animal", "ai_animal", "ai_non_animal")
VARIANTS = ("baseline", "compression")
SAMPLED_INDICES = [0, 6, 12, 19, 25, 31, 38, 44, 50, 57, 63, 69, 76, 82, 88, 95]


def validate_panel(samples, previous_samples):
    """Reject reused source identities, duplicate media, or an unbalanced panel."""
    if len(samples) != 20 or Counter(s['cell'] for s in samples) != Counter({c: 5 for c in CELLS}):
        raise ValueError("Expected exactly five unique sources in each of four cells")
    for key in ('id', 'sha256'):
        if len({s[key] for s in samples}) != 20:
            raise ValueError(f"Duplicate source {key}")
    prior_hashes = {s['sha256'] for s in previous_samples}
    prior_ids = {s['source_id'] for s in previous_samples if s.get('source') == 'MSVD' or s.get('generator') == 'MSVD'}
    real_ids = [s['source_id'] for s in samples if s['label'] == 'real']
    if len(real_ids) != len(set(real_ids)) or set(real_ids) & prior_ids:
        raise ValueError("Reused MSVD source identity")
    for s in samples:
        if s['sha256'] in prior_hashes:
            raise ValueError("Reused prior source media")
        if s['cell'] != f"{s['label']}_{s['content']}" or s['source'] != ('MSVD' if s['label'] == 'real' else 'VEO3'):
            raise ValueError("Source, label or content cell disagrees")
        if not s.get('crop_review_passed'):
            raise ValueError("Selected crop has not been reviewed")


def validate_prepared(meta):
    if (meta['width'], meta['height'], meta['frames']) != (504, 504, 96) or abs(meta['fps'] - 24) > 1e-6:
        raise ValueError("Prepared media must be 504x504, 24 fps, exactly 96 frames")


def prepare_panel(root, config):
    import imageio_ffmpeg
    from ..artifacts import download, sha
    from .diagnostics import probe
    def fetch(s):
        path = root / f"data/controlled/sources/{s['id']}.mp4"
        url = f"https://huggingface.co/datasets/{s['dataset']}/resolve/{s['revision']}/{quote(s['remote_path'], safe='/')}"
        # The screening cache may supply verified bytes; the public reproduction downloads them.
        screened = root / f"data/controlled-candidates/{s['candidate_id']}.mp4"
        if not path.exists() and screened.exists() and sha(screened) == s['sha256']:
            import shutil
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(screened, path)
        download(url, path, s['sha256'])
        return path
    with ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(fetch, config['samples']))
    cases, records = [], []
    for sample, source in zip(config['samples'], sources):
        meta = probe(source, full_decode=True)
        if meta != sample['actual_metadata']:
            raise ValueError(f"Frozen source metadata changed: {sample['id']}")
        if min(meta['width'], meta['height']) < 504 or meta['width']/meta['height'] < 1.4 or meta['fps'] < 24 or meta['frames']/meta['fps'] < 4:
            raise ValueError("Source fails native eligibility")
        nominal_start = (meta['frames']/meta['fps'] - 4)/2
        start = math.floor(nominal_start * meta['fps']) / meta['fps']
        directory = root / 'data/controlled/prepared'
        directory.mkdir(parents=True, exist_ok=True)
        master = directory / f"{sample['id']}_master.avi"
        commands = [[imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'warning', '-ss', f'{start:.9f}', '-i', str(source),
            '-map', '0:v:0', '-an', '-vf', 'setpts=PTS-STARTPTS,fps=24:start_time=0,scale=-2:504:flags=bicubic,crop=504:504,setsar=1,setpts=N/(24*TB)',
            '-frames:v', '96', '-c:v', 'ffv1', '-pix_fmt', 'yuv420p', str(master)]]
        paths = {v: directory / f"{sample['id']}_{v}.mp4" for v in VARIANTS}
        for variant, crf in zip(VARIANTS, (18, 35)):
            commands.append([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'warning', '-i', str(master),
                '-map', '0:v:0', '-an', '-frames:v', '96', '-c:v', 'libx264', '-preset', 'medium',
                '-crf', str(crf), '-pix_fmt', 'yuv420p', str(paths[variant])])
        logs = []
        for command in commands:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logs.append(result.stderr.strip().replace(str(root) + '/', ''))
        master_meta = probe(master, full_decode=True)
        validate_prepared(master_meta)
        record = dict(video_id=sample['id'], source_metadata=meta, nominal_center_start_seconds=nominal_start, start_seconds=start,
            master_sha256=sha(master), master_metadata=master_meta,
            commands=[[str(Path(a).relative_to(root)) if a.startswith(str(root)+'/') else a for a in cmd[1:]] for cmd in commands],
            warnings=logs)
        for variant, path in paths.items():
            info = probe(path, full_decode=True)
            validate_prepared(info)
            cases.append((path, dict(video_id=sample['id'], label=sample['label'], cell=sample['cell'],
                source=sample['source'], content=sample['content'], variant=variant, sha256=sha(path), **info)))
        records.append(record)
        print(f"Prepared {sample['id']}: both 96-frame conditions", flush=True)
    return cases, records


def analyze(rows, samples):
    from .comparison import pair_rows
    pairs = pair_rows(rows)
    expected = {(s['id'], v) for s in samples for v in VARIANTS}
    if set(pairs) != expected:
        raise ValueError("Missing or unexpected cases in frozen panel")
    sample_by_id = {s['id']: s for s in samples}
    result = {}
    for row in rows:
        sample = sample_by_id[row['video_id']]
        if any(row[key] != sample[key] for key in ('label', 'cell', 'content', 'source')):
            raise ValueError("Score row disagrees with frozen content labels")
        validate_prepared(row)
        if json.loads(row['sampled_frame_indices']) != SAMPLED_INDICES:
            raise ValueError('Sampling differs from the native 16-frame centered window')
    for detector in ('aegis', 'waverep'):
        cells = {}
        for cell in CELLS:
            group = [s for s in samples if s['cell'] == cell]
            changes, crossings = [], []
            conflicts = {v: 0 for v in VARIANTS}
            for s in group:
                a = pairs[(s['id'], 'baseline')][detector]['ai_score']
                b = pairs[(s['id'], 'compression')][detector]['ai_score']
                changes.append(b-a)
                if (a >= .5) != (b >= .5):
                    crossings.append(dict(video_id=s['id'], baseline=a, compression=b, delta=b-a))
                for variant, score in zip(VARIANTS, (a, b)):
                    conflicts[variant] += (score >= .5) != (s['label'] == 'ai')
            cells[cell] = dict(n=len(group), median_delta=statistics.median(changes),
                median_absolute_delta=statistics.median(abs(d) for d in changes),
                changes_at_least_point10=sum(abs(d) >= .1 for d in changes),
                midpoint_conflicts=conflicts, midpoint_crossings=crossings)
        result[detector] = cells
    return result


def run_controlled(root):
    import imageio_ffmpeg
    from ..artifacts import download, sha
    from ..adapters.aegis import MODEL_HASH, MODEL_REV
    from ..adapters.aegis import AegisDetector
    from ..adapters.waverep import WaveRepDetector, WEIGHTS_HASH, WEIGHTS_URL
    from .comparison import write_csv
    config_path = root / 'configs/controlled.json'
    config = json.loads(config_path.read_text())
    previous = json.loads((root/'configs/two-detectors.json').read_text())['samples']
    validate_panel(config['samples'], previous)
    # Require a committed manifest so the run cannot precede the reviewed selection.
    frozen = subprocess.check_output(['git', 'show', 'HEAD:configs/controlled.json'], cwd=root)
    if frozen != config_path.read_bytes():
        raise ValueError("Commit the reviewed manifest before inference")
    frozen_commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', 'configs/controlled.json'], cwd=root, text=True).strip()
    download(WEIGHTS_URL, root/'models/weights_dinov2_G4.ckpt', WEIGHTS_HASH)
    download(f'https://huggingface.co/MusapYildiz/aegis-video-detector/resolve/{MODEL_REV}/checkpoint_best.pt', root/'models/checkpoint_best.pt', MODEL_HASH)
    cases, preparation = prepare_panel(root, config)
    out = root/'reports/controlled'
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, cls in (('aegis', AegisDetector), ('waverep', WaveRepDetector)):
        detector = cls(root)
        for i, (path, row) in enumerate(cases, 1):
            start = time.perf_counter()
            details = detector.score_details(path)
            for field in ('sampled_frame_indices', 'frame_logits'):
                if field in details:
                    details[field] = json.dumps(details[field])
            scored = row | details | dict(detector=name, elapsed_sec=time.perf_counter()-start)
            rows.append(scored)
            print(f"{name} {i}/40 {row['video_id']} {row['variant']}: {details['ai_score']:.6f}", flush=True)
        del detector
    for row in rows:
        baseline = next(r for r in rows if r['detector'] == row['detector'] and r['video_id'] == row['video_id'] and r['variant'] == 'baseline')
        row['delta_vs_baseline'] = row['ai_score'] - baseline['ai_score']
    summary = analyze(rows, config['samples'])
    write_csv(out/'scores.csv', rows)
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    packages = {p: importlib.metadata.version(p) for p in ('torch', 'timm', 'numpy', 'torchvision', 'opencv-python-headless', 'imageio-ffmpeg', 'matplotlib')}
    module_paths = ['src/vidrobust/legacy/controlled.py','src/vidrobust/adapters/aegis.py','src/vidrobust/adapters/waverep.py','vendor/aegis/video_io.py']
    metadata = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), selection_frozen_commit=frozen_commit,
        config_sha256=sha(config_path), config=config, package_versions=packages,
        code_sha256={p: sha(root/p) for p in module_paths}, python=platform.python_version(),
        aegis_model_sha256=MODEL_HASH, aegis_model_revision=MODEL_REV, waverep_model_sha256=WEIGHTS_HASH,
        ffmpeg=imageio_ffmpeg.get_ffmpeg_version(), device='cpu', threads=4, seed=0,
        deterministic_algorithms=True, waverep_frame_batch=2,
        sampling='shared 16 indices in each 96-frame centered interval', preparation=preparation)
    (out/'run.json').write_text(json.dumps(metadata, indent=2)+'\n')
    (out/'validation.json').write_text(json.dumps(dict(source_clips=20, encoded_cases=40, model_scores=len(rows),
        full_source_master_and_prepared_decode='passed', exact_prepared_geometry='504x504 / 24 fps / 96 frames',
        source_hashes_and_fresh_identities='passed', five_per_cell='passed', paired_input_hashes_and_sampling='passed'), indent=2)+'\n')
    from .controlled_report import write_report
    write_report(root, config, rows, summary)
    print('Controlled content comparison complete', flush=True)
