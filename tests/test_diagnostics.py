"""Guard against assuming monotonicity and changing frames during a paired test."""
import unittest
from vidrobust.diagnostics import curve_metrics, validate_case

class DiagnosticCurveTests(unittest.TestCase):
    def test_non_monotone_curve_retains_multiple_crossings_and_crf_spacing(self):
        rows=[dict(variant=f'crf_{c}',crf=c,ai_score=s) for c,s in zip([18,23,28,32,35],[.9,.2,.8,.7,.1])]
        stats=curve_metrics(rows)
        self.assertTrue(stats['non_monotone'])
        self.assertEqual(stats['midpoint_crossings'],[dict(from_crf=18,to_crf=23),dict(from_crf=23,to_crf=28),dict(from_crf=32,to_crf=35)])
        self.assertEqual(stats['largest_step']['from_crf'],18)
        self.assertAlmostEqual(stats['largest_step']['delta_per_crf'],-.14)
        self.assertAlmostEqual(stats['steps'][-1]['delta_per_crf'],-.2)

    def test_missing_grid_level_is_rejected(self):
        rows=[dict(variant=f'crf_{c}',crf=c,ai_score=.2) for c in [18,23,28,35]]
        with self.assertRaises(ValueError):
            curve_metrics(rows)

    def test_frame_duplication_is_rejected(self):
        source=dict(width=320,height=240,frames=100,fps=25)
        row=dict(video_id='clip',variant='crf_35',width=320,height=240,frames=101,fps=25,ai_score=.4)
        with self.assertRaises(ValueError):
            validate_case(source,row)
