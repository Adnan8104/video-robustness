"""Audit D3's lightweight path against pinned native code and raw arithmetic."""
import argparse
import ast
import csv
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'vendor/aegis'))
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, load_config
from vidrobust.frame_scoring import experiment_indices, score_frames, tensor_digest
from vidrobust.media import probe, read_exact_rgb
from vidrobust.registry import make_detector


def native_node(path, name, namespace):
    """Execute an unchanged selected AST node, with explicit dependencies only."""
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future,node],type_ignores=[]))
    exec(compile(module,str(path),'exec'),namespace)
    return namespace[name]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    parser.add_argument('--clips',nargs='+',required=True)
    args=parser.parse_args()
    config_path,manifest_path,config,samples=load_config(ROOT,args.config)
    if config.get('analysis') != 'ranking' or config['detectors'] != ['d3_resnet18']:
        raise ValueError('Choose a D3-only ranking config')
    if config['preparation'] != 'native' or config['variants'] != [dict(name='original',transform='identity',encoding='source')]:
        raise ValueError('Audit requires unchanged source bytes')
    if len(args.clips) != len(set(args.clips)) or set(args.clips)-{s['id'] for s in samples}:
        raise ValueError('Choose unique configured clips')
    for path in (config_path,manifest_path,Path(__file__).resolve()):
        frozen_revision(ROOT,path)
    vendor=ROOT/'vendor/d3'
    hashes=json.loads((vendor/'source-hashes.json').read_text())
    for file,expected in hashes.items():
        if sha(vendor/file) != expected:
            raise ValueError('Pinned native source changed: '+file)
    import cv2
    import numpy as np
    import torch
    import torchvision.models as models
    adapter=make_detector(ROOT,'d3_resnet18')
    state=torch.load(ROOT/adapter.checkpoint['path'],map_location='cpu',weights_only=True)
    def local_resnet18(pretrained):
        if pretrained is not True:
            raise ValueError('Native encoder must request pretrained weights')
        encoder=models.resnet18(weights=None)
        encoder.load_state_dict(state,strict=True)
        return encoder
    namespace=dict(torch=torch,nn=torch.nn,F=torch.nn.functional,
                   models=SimpleNamespace(resnet18=local_resnet18),Transformers=[])
    native=native_node(vendor/'D3_model.py','D3_model',namespace)(encoder_type='ResNet-18',loss_type='l2').eval()
    crop=native_node(vendor/'datasets.py','crop_center_by_percentage',{})
    normalize=native_node(vendor/'albucore_functions.py','normalize_lut',dict(
        np=np,cv2=cv2,preserve_channel_dim=lambda f:f,
        MAX_VALUES_BY_DTYPE={np.dtype('uint8'):255},get_num_channels=lambda image:image.shape[-1]))
    if set(native.encoder.state_dict()) != set(adapter.encoder.state_dict()):
        raise ValueError('Native architecture keys differ')
    out=ROOT/f"reports/experiments/{config['name']}"
    run=json.loads((out/'run.json').read_text())
    if sha(config_path) != run['config_sha256'] or sha(manifest_path) != run['manifest_sha256']:
        raise ValueError('Stored plan changed')
    for path,expected in run['code_sha256'].items():
        if sha(ROOT/path) != expected:
            raise ValueError('Stored scoring code changed')
    rows=list(csv.DictReader((out/'scores.csv').open()))
    if len(rows) != len(samples):
        raise ValueError('Incomplete score matrix')
    for row in rows:
        first=json.loads(row['first_order_distances']); second=json.loads(row['second_order_changes'])
        if len(first) != 15 or len(second) != 14 or min(first) < 0:
            raise ValueError('Invalid temporal distance arrays')
        expected=(np.array(first,dtype=np.float32)[1:] - np.array(first,dtype=np.float32)[:-1]).tolist()
        if second != expected:
            raise ValueError('Second differences disagree')
        mean=sum(second)/14
        std=math.sqrt(sum((x-mean)**2 for x in second)/13)
        if not math.isclose(std,float(row['temporal_std']),rel_tol=1e-6,abs_tol=1e-7):
            raise ValueError('Raw std arithmetic disagrees')
        if not math.isclose(mean,float(row['temporal_mean']),rel_tol=1e-6,abs_tol=1e-7):
            raise ValueError('Raw mean arithmetic disagrees')
        if 1/(1+float(row['temporal_std'])) != float(row['ai_score']):
            raise ValueError('Bounded coordinate arithmetic disagrees')
    real=[float(r['temporal_std']) for r in rows if r['label']=='real']
    ai=[float(r['temporal_std']) for r in rows if r['label']=='ai']
    wins=sum(a<b for a in ai for b in real); ties=sum(a==b for a in ai for b in real)
    summary=json.loads((out/'summary.json').read_text())['d3_resnet18']['original']['all']
    if (summary['pairs'],summary['ai_above_real'],summary['ties'],summary['pairwise_auc']) != (len(ai)*len(real),wins,ties,(wins+.5*ties)/(len(ai)*len(real))):
        raise ValueError('Raw discrepancy rank counts disagree')
    indexed={r['video_id']:r for r in rows}
    results=[]
    mean=np.array([.485,.456,.406],dtype=np.float32)*255
    denominator=np.reciprocal(np.array([.229,.224,.225],dtype=np.float32)*255)
    for clip in args.clips:
        sample=next(s for s in samples if s['id']==clip)
        path=ROOT/config['source_directory']/f'{clip}.mp4'
        if sha(path) != sample['sha256']:
            raise ValueError('Source hash changed')
        meta=probe(path,full_decode=True)
        if meta != sample['actual_metadata']:
            raise ValueError('Source metadata changed')
        indices=experiment_indices(meta,config)
        frames=read_exact_rgb(path,indices)
        native_images=[]
        for frame in frames:
            image=crop(cv2.cvtColor(frame,cv2.COLOR_RGB2BGR),.1)
            image=cv2.resize(image,(224,224),interpolation=cv2.INTER_LINEAR)
            image=normalize(image,mean,denominator)
            native_images.append(torch.from_numpy(image.transpose(2,0,1).copy()))
        tensor=torch.stack(native_images)
        if not torch.equal(tensor,adapter.prepare_frames(frames)):
            raise ValueError('Native preprocessing differs')
        with torch.inference_mode():
            _,native_mean,native_std=native(tensor.unsqueeze(0))
            actual=score_frames(adapter,'d3_resnet18',frames)
        if actual['temporal_std'] != native_std.item() or actual['temporal_mean'] != native_mean.item():
            raise ValueError('Native forward differs')
        row=indexed[clip]
        for key,value in actual.items():
            expected=json.loads(row[key]) if isinstance(value,list) else row[key] if isinstance(value,str) else float(row[key])
            if value != expected:
                raise ValueError('Stored output differs: '+key)
        if json.loads(row['sampled_frame_indices']) != indices:
            raise ValueError('Stored temporal indices differ')
        results.append(dict(video_id=clip,frame_indices=indices,source_sha256=sample['sha256'],
            native_input_sha256=tensor_digest(tensor),temporal_std=actual['temporal_std'],
            native_preprocessing_and_forward_and_stored_outputs_exact=True))
        print('D3 native parity passed: '+clip,flush=True)
    audit=dict(script_sha256=sha(Path(__file__).resolve()),native_source_sha256=hashes,
        checkpoint_sha256=sha(ROOT/adapter.checkpoint['path']),sampling=config.get('sampling','centered_4s_16'),
        arithmetic_rows=len(rows),arithmetic_tolerance='std/mean: rel 1e-6, abs 1e-7; second differences and bounded coordinate exact',
        raw_rank_counts_exact=True,clips=results)
    (out/'native-adapter-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    validation=json.loads((out/'validation.json').read_text())
    validation['native_temporal_parity']=dict(audit='native-adapter-audit.json',
        audit_sha256=sha(out/'native-adapter-audit.json'),clips=args.clips,exact_match=True,
        independent_arithmetic_rows=len(rows),independent_raw_rank_counts='passed')
    (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(f'D3 audit passed: {len(results)} native clips; {len(rows)} independent score checks',flush=True)


if __name__=='__main__':
    main()
