"""Retain multiple crossings and keep native originals distinct from preparation."""
import json
import unittest
from vidrobust.legacy.failure_followup import curve_summary, analyze, CRFS, VARIANTS
from vidrobust.legacy.controlled import SAMPLED_INDICES


class FailureFollowupTests(unittest.TestCase):
    def test_multiple_crossings_and_unequal_crf_steps(self):
        points=[dict(crf=c,ai_score=s) for c,s in zip(CRFS,[.9,.2,.8,.1])]
        result=curve_summary(points)
        self.assertTrue(result['non_monotone'])
        self.assertEqual(result['first_tested_below_midpoint_crf'],23)
        self.assertEqual(len(result['midpoint_crossings']),3)
        self.assertAlmostEqual(result['steps'][-1]['delta_per_crf'],-.1)
        self.assertEqual(result['adjacent_changes_at_least_point10'],3)

    def test_incomplete_grid_and_already_below_midpoint(self):
        with self.assertRaises(ValueError):curve_summary([dict(crf=c,ai_score=.9) for c in (18,23,35)])
        result=curve_summary([dict(crf=c,ai_score=s) for c,s in zip(CRFS,[.2,.5,.6,.1])])
        self.assertIsNone(result['first_tested_below_midpoint_crf'])
        self.assertEqual(len(result['midpoint_crossings']),2)

    def test_original_uses_native_metadata_but_crf_cases_require_fixed_frames(self):
        sample=dict(id='clip',label='real',actual_metadata=dict(width=1280,height=720,frames=150,fps=30))
        rows=[]
        for detector in ['aegis','waverep']:
            for variant in VARIANTS:
                meta=sample['actual_metadata'] if variant=='original' else dict(width=504,height=504,frames=96,fps=24)
                rows.append(dict(video_id='clip',label='real',detector=detector,variant=variant,crf=0 if variant=='original' else int(variant[4:]),
                    sha256=variant,sampled_frame_indices=json.dumps([15,134] if variant=='original' else SAMPLED_INDICES),
                    ai_score=.2 if variant=='original' else .8,**meta))
        self.assertTrue(analyze(rows,[sample])['clip']['aegis']['preparation_midpoint_crossing'])
        rows[-1]['frames']=95
        with self.assertRaises(ValueError):analyze(rows,[sample])
