import unittest

import numpy as np

from vidrobust.linear_head import clip_embedding, fit_ridge, metrics, recording_keys


class LinearHeadTests(unittest.TestCase):
    def test_dual_fit_matches_the_primal_objective_with_intercept(self):
        x = np.array([[1., 8.], [2., 7.], [4., 9.], [5., 11.]])
        y = np.array([-1, -1, 1, 1])
        penalty = .01
        w, b = fit_ridge(x, y, penalty)
        design = np.column_stack((x, np.ones(len(x))))
        expected = np.linalg.solve(design.T @ design + len(x)*penalty*np.diag([1, 1, 0]),
                                   design.T @ y)
        np.testing.assert_allclose(np.r_[w, b], expected)
        self.assertTrue(np.all(np.sign(x @ w + b) == y))

    def test_embedding_averages_frames_before_unit_normalizing(self):
        frames = [[4., 0.]]*8 + [[0., 3.]]*8
        np.testing.assert_allclose(clip_embedding(frames), [.8, .6])
        with self.assertRaises(ValueError):
            clip_embedding(np.zeros((16, 2)))
        with self.assertRaises(ValueError):
            clip_embedding(frames[:15])

    def test_recording_aliases_are_not_independent_pairs(self):
        def pair(anchor, url):
            return [dict(anchor_id=anchor, label=label, original_source_url=url,
                         sha256=anchor+label) for label in ('real', 'ai')]
        a = pair('a__scene_01', 'https://www.dvidshub.net/video/42/scene')
        b = pair('b__scene_01', 'https://www.dvidshub.net/video/embed/42')
        self.assertEqual(recording_keys(a)['recordings'] & recording_keys(b)['recordings'], {'42'})
        with self.assertRaises(ValueError):
            recording_keys(a+b)

    def test_ordering_counts_ties_and_zero_is_flagged(self):
        summary = metrics(['real','real','ai','ai'], [-.5, 0., 0., .5])
        self.assertEqual((summary['real_flagged'], summary['ai_missed']), (1, 0))
        self.assertEqual((summary['ai_above_real'], summary['ties'], summary['auc']), (3, 1, .875))
