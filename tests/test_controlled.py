"""Protect stratification, timing, freshness and compression sign reporting."""
import copy
import json
import unittest
from vidrobust.controlled import CELLS, SAMPLED_INDICES, analyze, validate_panel, validate_prepared


def fixture():
    samples, rows = [], []
    for cell in CELLS:
        label = cell.split('_', 1)[0]
        content = cell.split('_', 1)[1]
        for i in range(5):
            sample = dict(id=f'{cell}_{i}', cell=cell, label=label, content=content,
                source='MSVD' if label == 'real' else 'VEO3', source_id=f'{cell}_{i}',
                sha256=f'source_{cell}_{i}', crop_review_passed=True)
            samples.append(sample)
            for detector in ('aegis', 'waverep'):
                for variant, score in [('baseline', .5), ('compression', .8 if i%2 == 0 else .2)]:
                    rows.append({k: sample[k] for k in ('label', 'content', 'source', 'cell')} | dict(
                        video_id=sample['id'], detector=detector, variant=variant, sha256=f"{sample['id']}_{variant}",
                        sampled_frame_indices=json.dumps(SAMPLED_INDICES), width=504, height=504, fps=24, frames=96, ai_score=score))
    return samples, rows


class ControlledTests(unittest.TestCase):
    def test_reject_unbalanced_panel_and_reused_source_id(self):
        samples, _ = fixture()
        validate_panel(samples, [])
        broken = copy.deepcopy(samples); broken[0]['cell'] = 'real_non_animal'
        with self.assertRaises(ValueError): validate_panel(broken, [])
        with self.assertRaises(ValueError):
            validate_panel(samples, [dict(generator='MSVD',source_id=samples[0]['source_id'],sha256='other')])
        with self.assertRaises(ValueError):
            validate_panel(samples, [dict(generator='VEO3',source_id='other',sha256=samples[0]['sha256'])])

    def test_reject_short_or_wrong_fps_preparation(self):
        m = dict(width=504,height=504,frames=96,fps=24)
        validate_prepared(m)
        for change in (dict(frames=95),dict(fps=25),dict(width=502)):
            with self.assertRaises(ValueError): validate_prepared(m|change)

    def test_opposite_changes_do_not_cancel_in_absolute_metric(self):
        samples, rows = fixture()
        result = analyze(rows, samples)['aegis']['real_animal']
        self.assertAlmostEqual(result['median_absolute_delta'], .3)
        self.assertEqual(result['changes_at_least_point10'], 5)
        self.assertEqual(len(result['midpoint_crossings']), 2)
        self.assertEqual(result['midpoint_conflicts']['baseline'], 5)
        self.assertEqual(result['midpoint_conflicts']['compression'], 3)
        with self.assertRaises(ValueError): analyze(rows[:-2], samples)
        broken = copy.deepcopy(rows); broken[0]['cell'] = 'ai_animal'
        with self.assertRaises(ValueError): analyze(broken, samples)
