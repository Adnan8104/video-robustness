import unittest

import numpy as np

from scripts.train_real_negatives import balanced_ridge
from vidrobust.linear_head import fit_ridge


class BalancedRidgeTests(unittest.TestCase):
    def test_original_balanced_training_is_unchanged(self):
        x = np.array([[1., 3.], [3., 2.], [4., 5.], [7., 4.]])
        y = np.array([-1, -1, 1, 1])
        expected_w, expected_b = fit_ridge(x, y, .01)
        w, b = balanced_ridge(x, y, .01)
        np.testing.assert_allclose(w, expected_w, atol=1e-12)
        self.assertAlmostEqual(b, expected_b)

    def test_duplicating_the_real_class_does_not_shift_the_fit(self):
        x = np.array([[1., 3.], [3., 2.], [4., 5.], [7., 4.]])
        y = np.array([-1, -1, 1, 1])
        expected_w, expected_b = balanced_ridge(x, y, .01)
        w, b = balanced_ridge(np.vstack([x, x[:2]]), np.r_[y, y[:2]], .01)
        np.testing.assert_allclose(w, expected_w, atol=1e-12)
        self.assertAlmostEqual(b, expected_b)
