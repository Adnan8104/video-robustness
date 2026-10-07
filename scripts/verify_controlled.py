"""Repeat the shared kitten failure and the largest WaveRep compression change."""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from vidrobust.cli import sha
from vidrobust.detectors import AegisDetector
from vidrobust.waverep import WaveRepDetector


def main():
    report = ROOT/'reports/controlled'
    with open(report/'scores.csv') as f:
        rows = list(csv.DictReader(f))
    compressed_wave = [r for r in rows if r['detector'] == 'waverep' and r['variant'] == 'compression']
    wave_clip = max(compressed_wave, key=lambda r: abs(float(r['delta_vs_baseline'])))['video_id']
    results = []
    for name, cls, video_ids in [('aegis', AegisDetector, ['controlled_real_animal_01']),
                               ('waverep', WaveRepDetector, list(dict.fromkeys(['controlled_real_animal_01', wave_clip])))]:
        detector = cls(ROOT)
        for video_id, variant in [(v, condition) for v in video_ids for condition in ['baseline', 'compression']]:
            expected = next(r for r in rows if r['detector'] == name and r['video_id'] == video_id and r['variant'] == variant)
            path = ROOT/f'data/controlled/prepared/{video_id}_{variant}.mp4'
            if sha(path) != expected['sha256']:
                raise ValueError('Repeated input checksum differs')
            details = detector.score_details(path)
            differences = {}
            for key, value in details.items():
                if isinstance(value, list):
                    if value != json.loads(expected[key]):
                        raise ValueError(f'Repeated {key} differs')
                else:
                    differences[key] = value - float(expected[key])
                    if differences[key] != 0:
                        raise ValueError(f'Repeated {key} differs: {differences[key]}')
            results.append(dict(detector=name,video_id=video_id,variant=variant,sha256=expected['sha256'],
                ai_score=details['ai_score'],absolute_score_difference=abs(differences['ai_score']),
                all_numeric_outputs_and_indices_exact_match=True))
            print(f'Fresh-model repeat passed: {name} {video_id} {variant}',flush=True)
        del detector
    validation_path = report/'validation.json'
    validation = json.loads(validation_path.read_text())
    validation['fresh_model_repeat_selection'] = 'Kitten pair in both models and WaveRep pair with largest absolute compression change'
    validation['fresh_model_reloads'] = 2
    validation['fresh_model_repeats'] = results
    validation_path.write_text(json.dumps(validation,indent=2)+'\n')


if __name__ == '__main__':
    main()
