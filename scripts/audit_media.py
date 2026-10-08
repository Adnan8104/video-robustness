"""Independently verify source frame counts and sampled presentation timestamps."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from vidrobust.artifacts import sha
from vidrobust.experiment import frozen_revision, load_config
from vidrobust.frame_scoring import experiment_indices
from vidrobust.media import probe


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    args=parser.parse_args()
    config_path, manifest_path, config, samples=load_config(ROOT, args.config)
    if config['preparation']!='native' or config['variants']!=[dict(name='original',transform='identity',encoding='source')]:
        raise ValueError('Source timing audit needs native unchanged-source conditions')
    frozen_revision(ROOT, config_path); frozen_revision(ROOT, manifest_path)
    frozen_revision(ROOT, Path(__file__).resolve())
    import imageio_ffmpeg
    sys.path.insert(0,str(ROOT/'vendor/aegis'))
    out=ROOT/f"reports/experiments/{config['name']}"
    records=[]
    for sample in samples:
        path=ROOT/config['source_directory']/f"{sample['id']}.mp4"
        if sha(path)!=sample['sha256']:
            raise ValueError('Source checksum changed')
        meta=probe(path,full_decode=True)
        if sample.get('actual_metadata',meta)!=meta:
            raise ValueError('Source geometry/timing changed')
        result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','info','-xerror','-i',str(path),
            '-map','0:v:0','-an','-vf','showinfo','-fps_mode','passthrough','-f','null','-'],
            capture_output=True,text=True,check=True)
        pts=[float(v) for v in re.findall(r'\bn:\s*\d+\s+pts:\s*-?\d+\s+pts_time:\s*([-+.eE0-9]+)',result.stderr)]
        if len(pts)!=meta['frames']:
            raise ValueError('Independent FFmpeg/OpenCV counts disagree')
        gaps=[b-a for a,b in zip(pts,pts[1:])]
        if min(gaps)<=0:
            raise ValueError('Nonmonotonic frame timestamps')
        indices=experiment_indices(meta,config)
        selected=[pts[i] for i in indices]
        drift=max(abs((pts[i]-pts[0])-i/meta['fps']) for i in indices)
        if drift>.1:
            raise ValueError('Sampled timestamps differ from nominal timing by >0.1 seconds')
        records.append(dict(video_id=sample['id'], source_sha256=sha(path),
            independent_full_decode_frames=len(pts), opencv_frame_count=meta['frames'],
            header_frame_estimate=sample.get('original_header_frame_estimate',meta['frames']), fps=meta['fps'],
            frame_indices=indices, sampled_pts_seconds=selected, sampled_span_seconds=selected[-1]-selected[0],
            max_sampled_time_drift_from_nominal_seconds=drift,
            min_frame_interval_seconds=min(gaps), max_frame_interval_seconds=max(gaps)))
        print(f"Independent media timing passed: {sample['id']} ({len(pts)} frames)",flush=True)
    audit=dict(config_sha256=sha(config_path),manifest_sha256=sha(manifest_path),
        script_sha256=sha(Path(__file__).resolve()),ffmpeg=imageio_ffmpeg.get_ffmpeg_version(),
        method='Independent full FFmpeg decode/showinfo and OpenCV counts; original presentation timestamps, no resampling',
        clips=records)
    out.mkdir(parents=True,exist_ok=True)
    target=out/'media-timing-audit.json'
    target.write_text(json.dumps(audit,indent=2)+'\n')
    if (out/'run.json').exists():
        run=json.loads((out/'run.json').read_text())
        if run['config_sha256']!=audit['config_sha256'] or run['manifest_sha256']!=audit['manifest_sha256']:
            raise ValueError('Stored run plan differs')
        path=out/'validation.json';validation=json.loads(path.read_text())
        validation['independent_media_timing']=dict(audit=target.name,audit_sha256=sha(target),
            source_clips=len(samples), frame_counts_and_sampled_timestamps='passed')
        path.write_text(json.dumps(validation,indent=2)+'\n')


if __name__=='__main__':
    main()
