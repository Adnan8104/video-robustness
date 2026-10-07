"""Native-frame factorial with pixel-exact original/prepared endpoint bridges."""
import csv
from datetime import datetime,timezone
import importlib.metadata
from itertools import product
import json
import platform
import re
import subprocess
import time


def variant_name(resize,crop,encode,sampling):
    return f'r{resize}_c{crop}_e{encode}_{sampling}'


def factorial_summary(rows):
    expected={(name,variant_name(r,c,e,t)) for name in ('aegis','waverep') for r,c,e in product((0,1),repeat=3) for t in ('original','fps_selected')}
    factorial=[r for r in rows if r['case_type']=='factorial']
    keyed={(r['detector'],r['variant']):r for r in factorial}
    if set(keyed)!=expected or len(factorial)!=len(expected):raise ValueError('Incomplete/duplicate factorial')
    result={}
    for name in ('aegis','waverep'):
        conditional=[]
        for axis,index in [('resize',0),('crop',1),('encoding',2)]:
            for other in product((0,1),repeat=2):
                bits=list(other);bits.insert(index,0);off=tuple(bits);bits[index]=1;on=tuple(bits)
                for sampling in ('original','fps_selected'):
                    a=keyed[(name,variant_name(*off,sampling))];b=keyed[(name,variant_name(*on,sampling))]
                    conditional.append(dict(factor=axis,from_variant=a['variant'],to_variant=b['variant'],delta_score=b['ai_score']-a['ai_score'],delta_logit=b['fusion_logit']-a['fusion_logit'],midpoint_crossing=(a['ai_score']>=.5)!=(b['ai_score']>=.5),identical_model_input=a['model_input_sha256']==b['model_input_sha256']))
        for bits in product((0,1),repeat=3):
            a=keyed[(name,variant_name(*bits,'original'))];b=keyed[(name,variant_name(*bits,'fps_selected'))]
            conditional.append(dict(factor='sampled_frames',from_variant=a['variant'],to_variant=b['variant'],delta_score=b['ai_score']-a['ai_score'],delta_logit=b['fusion_logit']-a['fusion_logit'],midpoint_crossing=(a['ai_score']>=.5)!=(b['ai_score']>=.5),identical_model_input=a['model_input_sha256']==b['model_input_sha256']))
        interactions={}
        for t in ('original','fps_selected'):
            z={(r,c):keyed[(name,variant_name(r,c,0,t))]['fusion_logit'] for r,c in product((0,1),repeat=2)}
            interactions[t]=z[(1,1)]-z[(1,0)]-z[(0,1)]+z[(0,0)]
        path=[variant_name(0,0,0,'original'),variant_name(0,0,0,'fps_selected'),variant_name(1,0,0,'fps_selected'),variant_name(1,1,0,'fps_selected'),'parent_prepared_encoded']
        lookup={r['variant']:r for r in rows if r['detector']==name}
        steps=[dict(from_variant=a,to_variant=b,delta_score=lookup[b]['ai_score']-lookup[a]['ai_score'],delta_logit=lookup[b]['fusion_logit']-lookup[a]['fusion_logit']) for a,b in zip(path,path[1:])]
        if abs(sum(s['delta_logit'] for s in steps)-(lookup[path[-1]]['fusion_logit']-lookup[path[0]]['fusion_logit']))>1e-10:raise ValueError('Path deltas do not telescope')
        result[name]=dict(conditional_effects=conditional,resize_crop_logit_interaction_lossless=interactions,exact_endpoint_path=steps)
    return result


def run_isolation(root):
    import imageio_ffmpeg
    from ..artifacts import sha, download
    from ..adapters.aegis import MODEL_HASH, MODEL_REV
    from .comparison import write_csv
    from .controlled import SAMPLED_INDICES
    from ..adapters.aegis import AegisDetector
    from .diagnostics import probe
    from ..adapters.waverep import WaveRepDetector,WEIGHTS_HASH,WEIGHTS_URL,read_exact_rgb
    from ..frame_scoring import rgb_digest,score_frames
    from .kitten_report import write_report
    cfg_path=root/'configs/kitten-isolation.json';config=json.loads(cfg_path.read_text())
    if subprocess.check_output(['git','show','HEAD:configs/kitten-isolation.json'],cwd=root)!=cfg_path.read_bytes():raise ValueError('Commit the specification before inference')
    for p,digest in config['evidence_sha256'].items():
        if sha(root/p)!=digest:raise ValueError('Parent evidence changed: '+p)
    sample=next(s for s in json.loads((root/'configs/controlled.json').read_text())['samples'] if s['id']==config['video_id'])
    source=root/f"data/controlled/sources/{sample['id']}.mp4"
    from urllib.parse import quote
    download(f"https://huggingface.co/datasets/{sample['dataset']}/resolve/{sample['revision']}/{quote(sample['remote_path'],safe='/')}",source,config['source_sha256'])
    download(WEIGHTS_URL,root/'models/weights_dinov2_G4.ckpt',WEIGHTS_HASH)
    download(f'https://huggingface.co/MusapYildiz/aegis-video-detector/resolve/{MODEL_REV}/checkpoint_best.pt',root/'models/checkpoint_best.pt',MODEL_HASH)
    parent_run=json.loads((root/'reports/controlled/run.json').read_text());prep=next(p for p in parent_run['preparation'] if p['video_id']==sample['id'])
    with open(root/'reports/failure-followup/scores.csv') as f:parent_rows=[r for r in csv.DictReader(f) if r['video_id']==sample['id']]
    directory=root/'data/kitten-isolation';directory.mkdir(parents=True,exist_ok=True)
    ff=imageio_ffmpeg.get_ffmpeg_exe();commands=[]
    def execute(cmd):
        result=subprocess.run(cmd,capture_output=True,text=True,check=True)
        commands.append([a.replace(str(root)+'/', '') for a in cmd[1:]])
        return result.stderr
    original_meta=probe(source,full_decode=True)
    if original_meta!=sample['actual_metadata']:raise ValueError('Original metadata changed')
    paths={}
    for r,c in product((0,1),repeat=2):
        path=directory/f'r{r}_c{c}_lossless.avi'
        filters=['setpts=N/((30000/1001)*TB)']
        if r:filters.append('scale=-2:504:flags=bicubic')
        if c:filters.append(r'crop=min(iw\,ih):min(iw\,ih)')
        filters.append('setsar=1')
        execute([ff,'-y','-loglevel','warning','-i',str(source),'-map','0:v:0','-an','-vf',','.join(filters),'-r',config['native_rate'],'-frames:v','240','-c:v','ffv1','-pix_fmt','yuv420p',str(path)])
        paths[(r,c,0)]=path
        encoded=directory/f'r{r}_c{c}_crf18.mp4'
        execute([ff,'-y','-loglevel','warning','-i',str(path),'-map','0:v:0','-an','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',str(encoded)])
        paths[(r,c,1)]=encoded
    metadata_path=directory/'metadata_only_24fps.avi'
    execute([ff,'-y','-loglevel','warning','-i',str(paths[(0,0,0)]),'-map','0:v:0','-an','-vf','setpts=N/(24*TB)','-r','24','-frames:v','240','-c:v','ffv1','-pix_fmt','yuv420p',str(metadata_path)])
    # Recreate exact parent encodes only if absent; never touch parent reports.
    master=root/f"data/controlled/prepared/{sample['id']}_master.avi"
    prepared=root/f"data/controlled/prepared/{sample['id']}_baseline.mp4"
    if not master.exists() or not prepared.exists():
        from .controlled import prepare_panel
        prepare_panel(root,dict(samples=[sample]))
    if sha(master)!=prep['master_sha256']:raise ValueError('Parent master changed')
    if sha(prepared)!=next(r['sha256'] for r in parent_rows if r['variant']=='crf_18'):raise ValueError('Parent encoded baseline changed')
    # Recover actual FPS-selected source-frame identities with raw YUV checksums.
    pattern=re.compile(r'n:\s*(\d+).*?checksum:([0-9A-F]+)\s+plane_checksum:\[([0-9A-F ]+)\]')
    def parse(log,tag):
        found={}
        for line in log.splitlines():
            if tag in line:
                m=pattern.search(line)
                if m:found[int(m[1])]=m[2]+':'+m[3]
        return found
    native=parse(execute([ff,'-hide_banner','-i',str(source),'-an','-vf','showinfo@source','-f','null','-']),'showinfo@source')
    trace=parse(execute([ff,'-y','-hide_banner','-ss',f"{prep['start_seconds']:.9f}",'-i',str(source),'-an','-vf',
        'setpts=PTS-STARTPTS,fps=24:start_time=0,showinfo@sampled,scale=-2:504:flags=bicubic,crop=504:504,setsar=1,setpts=N/(24*TB)',
        '-frames:v','96','-c:v','ffv1','-pix_fmt','yuv420p',str(directory/'trace_master.avi')]),'showinfo@sampled')
    mapping=[]
    for i in SAMPLED_INDICES:
        candidates=[n for n,v in native.items() if v==trace[i]]
        if len(candidates)!=1:raise ValueError('Ambiguous frame identity trace')
        mapping.append(candidates[0])
    if mapping!=config['fps_selected_source_indices']:raise ValueError('Frozen FPS mapping changed')
    original_frames=read_exact_rgb(source,config['original_source_indices']);original_hash=rgb_digest(original_frames)
    if rgb_digest(read_exact_rgb(paths[(0,0,0)],config['original_source_indices']))!=original_hash:raise ValueError('Identity round-trip changed pixels')
    if rgb_digest(read_exact_rgb(metadata_path,config['original_source_indices']))!=original_hash:raise ValueError('Metadata-only control changed pixels')
    prepared_master_hash=rgb_digest(read_exact_rgb(master,SAMPLED_INDICES))
    if rgb_digest(read_exact_rgb(paths[(1,1,0)],mapping))!=prepared_master_hash:raise ValueError('Isolated lossless spatial inputs do not match parent master')
    cases=[]
    for r,c,e in product((0,1),repeat=3):
        path=paths[(r,c,e)];meta=probe(path,full_decode=True)
        expected=(896 if r else 1280,504 if r else 720)
        if c:expected=(expected[1],expected[1])
        if (meta['width'],meta['height'])!=expected or meta['frames']!=240 or abs(meta['fps']-original_meta['fps'])>1e-8:raise ValueError('Factorial geometry/timing changed')
        for sampling,indices in [('original',config['original_source_indices']),('fps_selected',mapping)]:
            cases.append((path,indices,dict(variant=variant_name(r,c,e,sampling),resize=r,crop=c,encoding=e,sampling=sampling,case_type='factorial',**meta)))
    for path,indices,variant,kind in [(metadata_path,config['original_source_indices'],'metadata_only_24fps','metadata_control'),(prepared,SAMPLED_INDICES,'parent_prepared_encoded','endpoint_bridge')]:
        cases.append((path,indices,dict(variant=variant,case_type=kind,resize=0 if kind=='metadata_control' else 1,crop=0 if kind=='metadata_control' else 1,encoding=0 if kind=='metadata_control' else 1,sampling='original' if kind=='metadata_control' else 'fps_selected',**probe(path,full_decode=True))))
    rows=[]
    for name,cls in [('aegis',AegisDetector),('waverep',WaveRepDetector)]:
        detector=cls(root)
        for i,(path,indices,case) in enumerate(cases,1):
            frames=read_exact_rgb(path,indices);start=time.perf_counter();details=score_frames(detector,name,frames)
            if 'frame_logits' in details:details['frame_logits']=json.dumps(details['frame_logits'])
            row=case|details|dict(video_id=sample['id'],label='real',detector=name,sha256=sha(path),sampled_frame_indices=json.dumps(indices),elapsed_sec=time.perf_counter()-start)
            rows.append(row);print(f"{name} {i}/18 {case['variant']}: {row['ai_score']:.6f}",flush=True)
        # Native-frame injection must reproduce the published original AND encoded endpoint.
        for variant,parent_variant in [('r0_c0_e0_original','original'),('parent_prepared_encoded','crf_18')]:
            row=next(r for r in rows if r['detector']==name and r['variant']==variant);old=next(r for r in parent_rows if r['detector']==name and r['variant']==parent_variant)
            for key in ('ai_score','fusion_logit','pixel_score','motion_score','consistency_score'):
                if old.get(key) and row[key]!=float(old[key]):raise ValueError('Direct-frame endpoint differs: '+key)
            if old.get('frame_logits') and json.loads(old['frame_logits'])!=json.loads(row['frame_logits']):raise ValueError('Direct-frame endpoint logits differ')
        del detector
    if len(rows)!=config['expected_model_scores']:raise ValueError('Case count changed')
    summary=factorial_summary(rows);out=root/'reports/kitten-isolation';out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'scores.csv',rows);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    repeats=[]
    for name,cls in [('aegis',AegisDetector),('waverep',WaveRepDetector)]:
        detector=cls(root)
        largest=max((r for r in rows if r['detector']==name and r['case_type']=='factorial' and r['encoding']==0 and r['sampling']=='original'),key=lambda r:r['ai_score'])
        for variant in dict.fromkeys(['r0_c0_e0_original',largest['variant'],'parent_prepared_encoded']):
            path,indices,_=next(c for c in cases if c[2]['variant']==variant);details=score_frames(detector,name,read_exact_rgb(path,indices));old=next(r for r in rows if r['detector']==name and r['variant']==variant)
            for key,value in details.items():
                expected=json.loads(old[key]) if isinstance(value,list) else old[key]
                if value!=expected:raise ValueError(f'Fresh repeat mismatch: {name}/{variant}/{key}')
            repeats.append(dict(detector=name,variant=variant,ai_score=details['ai_score'],all_outputs_and_input_hashes_exact_match=True))
        del detector
    code_paths=['src/vidrobust/legacy/kitten_isolation.py','src/vidrobust/legacy/kitten_report.py','src/vidrobust/frame_scoring.py','src/vidrobust/adapters/aegis.py','src/vidrobust/adapters/waverep.py','vendor/aegis/video_io.py']
    (out/'run.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),config=config,config_sha256=sha(cfg_path),selection_frozen_commit=subprocess.check_output(['git','log','-1','--format=%H','--','configs/kitten-isolation.json'],cwd=root,text=True).strip(),code_sha256={p:sha(root/p) for p in code_paths},package_versions={p:importlib.metadata.version(p) for p in parent_run['package_versions']},python=platform.python_version(),ffmpeg=imageio_ffmpeg.get_ffmpeg_version(),device='cpu',threads=4,seed=0,waverep_frame_batch=2,aegis_model_sha256=MODEL_HASH,waverep_model_sha256=WEIGHTS_HASH,commands=commands),indent=2)+'\n')
    (out/'validation.json').write_text(json.dumps(dict(model_scores=36,identity_rgb_exact_match=True,metadata_only_rgb_exact_match=True,fps_mapping_unique_and_matches_frozen_indices=True,lossless_spatial_inputs_equal_parent_master=True,both_direct_frame_endpoints_equal_published_outputs=True,full_decode_geometry_and_fixed_frame_checks='passed',fresh_model_repeats=repeats),indent=2)+'\n')
    write_report(root,rows,summary)
    print('Kitten step isolation complete',flush=True)
