"""Targeted original-file check and four-level fixed-preparation CRF curves."""
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
import platform
import subprocess
import time

CRFS = (18, 23, 28, 35)
VARIANTS = ('original', 'crf_18', 'crf_23', 'crf_28', 'crf_35')


def curve_summary(points):
    ordered = sorted(points, key=lambda r: r['crf'])
    if tuple(r['crf'] for r in ordered) != CRFS:
        raise ValueError('Expected four unique frozen CRF levels')
    steps = [dict(from_crf=a['crf'], to_crf=b['crf'], delta=b['ai_score']-a['ai_score'],
                  delta_per_crf=(b['ai_score']-a['ai_score'])/(b['crf']-a['crf'])) for a, b in zip(ordered, ordered[1:])]
    crossings = [step for step, a, b in zip(steps, ordered, ordered[1:])
                 if (a['ai_score'] >= .5) != (b['ai_score'] >= .5)]
    positive = any(s['delta'] > 1e-6 for s in steps)
    negative = any(s['delta'] < -1e-6 for s in steps)
    return dict(steps=steps, largest_step=max(steps, key=lambda s: abs(s['delta'])),
        midpoint_crossings=crossings, non_monotone=positive and negative,
        direction='mixed' if positive and negative else 'decreasing' if negative else 'increasing' if positive else 'flat',
        first_tested_below_midpoint_crf=next((p['crf'] for p in ordered[1:] if p['ai_score'] < .5), None) if ordered[0]['ai_score'] >= .5 else None,
        adjacent_changes_at_least_point10=sum(abs(s['delta']) >= .1 for s in steps))


def analyze(rows, samples):
    from .comparison import pair_rows
    from .controlled import validate_prepared, SAMPLED_INDICES
    pairs = pair_rows(rows)
    if set(pairs) != {(s['id'], v) for s in samples for v in VARIANTS}:
        raise ValueError('Incomplete or unexpected follow-up cases')
    result = {}
    for sample in samples:
        clip = {}
        for name in ('aegis', 'waverep'):
            group = {v: pairs[(sample['id'], v)][name] for v in VARIANTS}
            for variant, row in group.items():
                if row['label'] != sample['label']:
                    raise ValueError('Source label changed')
                if variant != 'original':
                    validate_prepared(row)
                    if json.loads(row['sampled_frame_indices']) != SAMPLED_INDICES:
                        raise ValueError('Prepared temporal sampling changed')
                elif any(row[key] != sample['actual_metadata'][key] for key in ('width', 'height', 'fps', 'frames')):
                    raise ValueError('Original geometry changed')
            stats = curve_summary([group[f'crf_{c}'] for c in CRFS])
            stats.update(original_score=group['original']['ai_score'], baseline_score=group['crf_18']['ai_score'],
                preparation_delta=group['crf_18']['ai_score']-group['original']['ai_score'],
                preparation_midpoint_crossing=(group['original']['ai_score'] >= .5) != (group['crf_18']['ai_score'] >= .5))
            clip[name] = stats
        result[sample['id']] = clip
    return result


def run_followup(root):
    import imageio_ffmpeg
    from .cli import sha, download, MODEL_HASH, MODEL_REV
    from .controlled import prepare_panel
    from .diagnostics import probe
    from .comparison import write_csv
    from .detectors import AegisDetector
    from .waverep import WaveRepDetector, WEIGHTS_HASH, WEIGHTS_URL, aggregate_frame_logits
    from .failure_report import write_report
    cfg_path = root/'configs/failure-followup.json'
    config = json.loads(cfg_path.read_text())
    if tuple(config['crfs']) != CRFS:
        raise ValueError('Frozen CRF grid changed')
    if subprocess.check_output(['git','show','HEAD:configs/failure-followup.json'],cwd=root) != cfg_path.read_bytes():
        raise ValueError('Commit the follow-up manifest before inference')
    frozen_commit = subprocess.check_output(['git','log','-1','--format=%H','--','configs/failure-followup.json'],cwd=root,text=True).strip()
    for key, path in [('parent_manifest','configs/controlled.json'),('parent_run','reports/controlled/run.json'),('parent_scores','reports/controlled/scores.csv')]:
        if sha(root/path) != config[key+'_sha256']:
            raise ValueError('Parent evidence changed: '+path)
    parent = json.loads((root/'reports/controlled/run.json').read_text())
    manifest = json.loads((root/'configs/controlled.json').read_text())
    samples = [next(s for s in manifest['samples'] if s['id'] == c['id']) for c in config['clips']]
    packages = {p: importlib.metadata.version(p) for p in parent['package_versions']}
    inference_paths = ['src/vidrobust/detectors.py','src/vidrobust/waverep.py','vendor/aegis/video_io.py']
    inference_matches = packages == parent['package_versions'] and all(sha(root/p) == parent['code_sha256'][p] for p in inference_paths)
    inference_matches &= parent['aegis_model_sha256'] == MODEL_HASH and parent['waverep_model_sha256'] == WEIGHTS_HASH and parent['aegis_model_revision'] == MODEL_REV
    download(WEIGHTS_URL, root/'models/weights_dinov2_G4.ckpt', WEIGHTS_HASH)
    download(f'https://huggingface.co/MusapYildiz/aegis-video-detector/resolve/{MODEL_REV}/checkpoint_best.pt',root/'models/checkpoint_best.pt',MODEL_HASH)
    with open(root/'reports/controlled/scores.csv') as f:
        prior = {(r['video_id'],r['variant'],r['detector']):r for r in csv.DictReader(f)}
    prepared, preparation = prepare_panel(root, dict(samples=samples))
    prepared_by_key = {(row['video_id'],row['variant']):(path,row) for path,row in prepared}
    parent_masters = {r['video_id']:r['master_sha256'] for r in parent['preparation']}
    master_matches = {r['video_id']:r['master_sha256']==parent_masters[r['video_id']] for r in preparation}
    directory = root/'data/failure-followup'
    directory.mkdir(parents=True,exist_ok=True)
    cases, commands = [], []
    for s in samples:
        source = root/f"data/controlled/sources/{s['id']}.mp4"
        info = probe(source,full_decode=True)
        cases.append((source,dict(video_id=s['id'],label=s['label'],subject=s['subject'],variant='original',crf=0,sha256=sha(source),**info)))
        master = root/f"data/controlled/prepared/{s['id']}_master.avi"
        for crf in CRFS:
            if crf in (18,35):
                path, row = prepared_by_key[(s['id'],'baseline' if crf==18 else 'compression')]
                row = row | dict(variant=f'crf_{crf}',crf=crf,subject=s['subject'])
            else:
                path = directory/f"{s['id']}_crf_{crf}.mp4"
                command = [imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','warning','-i',str(master),'-map','0:v:0','-an','-frames:v','96',
                           '-c:v','libx264','-preset','medium','-crf',str(crf),'-pix_fmt','yuv420p',str(path)]
                output = subprocess.run(command,check=True,capture_output=True,text=True)
                commands.append(dict(args=[a.replace(str(root)+'/', '') for a in command[1:]],warnings=output.stderr.strip().replace(str(root)+'/', '')))
                row = dict(video_id=s['id'],label=s['label'],subject=s['subject'],variant=f'crf_{crf}',crf=crf,sha256=sha(path),**probe(path,full_decode=True))
            cases.append((path,row))
    rows = []
    for name, cls in [('aegis',AegisDetector),('waverep',WaveRepDetector)]:
        detector = cls(root)
        for i,(path,row) in enumerate(cases,1):
            indices = detector.window_sample(row['frames'],16,row['fps'],target_dur=4.0,random_start=False).tolist()
            parent_variant = config['prior_endpoints'].get(row['variant'])
            old = prior.get((row['video_id'],parent_variant,name))
            reused = bool(inference_matches and master_matches[row['video_id']] and old and old['sha256']==row['sha256'] and json.loads(old['sampled_frame_indices'])==indices)
            if reused:
                details = {k:float(old[k]) for k in ['ai_score','fusion_logit','pixel_score','motion_score','consistency_score'] if old.get(k)}
                details['sampled_frame_indices'] = old['sampled_frame_indices']
                if old.get('frame_logits'):details['frame_logits']=old['frame_logits']
                elapsed = float(old['elapsed_sec'])
            else:
                start = time.perf_counter();details=detector.score_details(path);elapsed=time.perf_counter()-start
                for key in ['sampled_frame_indices','frame_logits']:
                    if key in details:details[key]=json.dumps(details[key])
            if json.loads(details['sampled_frame_indices']) != indices:
                raise ValueError('Unexpected native sampling')
            rows.append(row | details | dict(detector=name,reused=reused,elapsed_sec=elapsed,
                sampled_seconds=json.dumps([i/row['fps'] for i in indices])))
            print(f"{name} {i}/20 {row['video_id']} {row['variant']}: {details['ai_score']:.6f}"+(' (reused)' if reused else ''),flush=True)
        del detector
    for r in rows:
        original = next(o for o in rows if o['video_id']==r['video_id'] and o['detector']==r['detector'] and o['variant']=='original')
        baseline = next(o for o in rows if o['video_id']==r['video_id'] and o['detector']==r['detector'] and o['variant']=='crf_18')
        r.update(delta_vs_original=r['ai_score']-original['ai_score'],delta_vs_baseline=r['ai_score']-baseline['ai_score'])
        if r['detector']=='waverep':
            logit,score=aggregate_frame_logits(json.loads(r['frame_logits']))
            if logit != r['fusion_logit'] or score != r['ai_score']:raise ValueError('Native WaveRep aggregation changed')
    summary = analyze(rows,samples)
    out = root/'reports/failure-followup';out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'scores.csv',rows)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    metadata=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),config=config,selection_frozen_commit=frozen_commit,
        config_sha256=sha(cfg_path),package_versions=packages,python=platform.python_version(),ffmpeg=imageio_ffmpeg.get_ffmpeg_version(),
        device='cpu',threads=4,seed=0,deterministic_algorithms=True,waverep_frame_batch=2,
        aegis_model_sha256=MODEL_HASH,aegis_model_revision=MODEL_REV,waverep_model_sha256=WEIGHTS_HASH,
        code_sha256={p:sha(root/p) for p in inference_paths+['src/vidrobust/failure_followup.py','src/vidrobust/failure_report.py','src/vidrobust/controlled.py']},
        newly_scored_cases=sum(not r['reused'] for r in rows),reused_cases=sum(r['reused'] for r in rows),
        preparation=preparation,medium_crf_commands=commands,parent_master_hash_matches=master_matches)
    (out/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    validation=dict(source_clips=4,model_scores=len(rows),paired_cases=20,full_source_master_and_prepared_decodes='passed',
        native_metadata_and_same_input_bytes_per_model='passed',paired_sampling='passed',native_waverep_aggregation='passed',
        parent_evidence_hashes='passed',parent_master_hash_matches=master_matches)
    # Fresh reloads protect the surprising original kitten and newly measured AI brackets.
    repeats=[]
    for name,cls in [('aegis',AegisDetector),('waverep',WaveRepDetector)]:
        detector=cls(root)
        selected=[(samples[0]['id'],'original')]
        for s in samples:
            if s['label']!='ai':continue
            crossings=summary[s['id']][name]['midpoint_crossings']
            targets={c for step in crossings for c in (step['from_crf'],step['to_crf']) if c in (23,28)} or {23}
            selected += [(s['id'],f'crf_{c}') for c in sorted(targets)]
        for clip,variant in selected:
            path=next(p for p,r in cases if r['video_id']==clip and r['variant']==variant)
            expected=next(r for r in rows if r['video_id']==clip and r['variant']==variant and r['detector']==name)
            details=detector.score_details(path)
            if sha(path)!=expected['sha256']:raise ValueError('Repeat input changed')
            for key,value in details.items():
                recorded=json.loads(expected[key]) if isinstance(value,list) else expected[key]
                if value!=recorded:raise ValueError(f'Fresh repeat mismatch: {name}/{clip}/{variant}/{key}')
            repeats.append(dict(detector=name,video_id=clip,variant=variant,ai_score=details['ai_score'],all_outputs_exact_match=True))
            print(f'Fresh repeat passed: {name} {clip} {variant}',flush=True)
        del detector
    validation['fresh_model_repeats']=repeats
    (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    write_report(root,samples,rows,summary)
    print('Four-clip follow-up complete',flush=True)
