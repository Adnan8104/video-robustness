"""Protect native aggregation and byte-identical model comparisons."""
import math
import unittest
from unittest.mock import patch
import numpy as np
from vidrobust.waverep import aggregate_frame_logits, read_exact_rgb
from vidrobust.comparison import pair_rows, summarize


class ComparisonTests(unittest.TestCase):
    def test_wave_averages_logits_before_sigmoid(self):
        values = [4.0] * 8 + [-2.0] * 8
        mean, score = aggregate_frame_logits(values)
        self.assertEqual(mean, 1.0)
        self.assertAlmostEqual(score, 1 / (1 + math.exp(-1)))
        mean_probability = sum(1 / (1 + math.exp(-v)) for v in values) / 16
        self.assertGreater(abs(score - mean_probability), 0.1)

    def test_unpaired_or_different_input_is_rejected(self):
        a = dict(detector='aegis',video_id='clip',variant='original',sha256='a',sampled_frame_indices='[1]',ai_score=.2)
        with self.assertRaises(ValueError):
            pair_rows([a])
        with self.assertRaises(ValueError):
            pair_rows([a, a | dict(detector='waverep',sha256='b')])
        with self.assertRaises(ValueError):
            pair_rows([a, a | dict(detector='waverep',sampled_frame_indices='[2]')])

    def test_missing_selected_frame_is_not_silently_padded(self):
        with patch('cv2.VideoCapture') as factory:
            cap = factory.return_value
            cap.isOpened.return_value = True
            cap.read.side_effect = [(True,np.zeros((2,2,3),dtype=np.uint8)),(False,None)]
            with self.assertRaises(ValueError):
                read_exact_rgb('clip.mp4',[0,2])
            cap.release.assert_called_once()

    def test_opposite_changes_and_fresh_cohort_are_kept_separate(self):
        rows=[]
        for detector in ['aegis','waverep']:
            for cohort,clip in [('previous','old'),('fresh','new')]:
                for variant,score,delta in [('original',.8,0),('encode_control',.5,0),('compression',.8,.3),('resize',.2,-.3),('crop',.5,0)]:
                    rows.append(dict(detector=detector,video_id=clip,cohort=cohort,label='real',variant=variant,
                        sha256=variant,sampled_frame_indices='[1]',ai_score=score,delta_vs_control=delta))
        summary=summarize(rows)
        self.assertEqual(summary['fresh']['aegis']['changes_at_least_point10'],2)
        self.assertEqual(summary['all']['aegis']['changes_at_least_point10'],4)
        self.assertEqual(summary['fresh']['aegis']['real_midpoint_conflicts'],1)
        self.assertEqual(summary['all']['original_midpoint_disagreements'],0)
