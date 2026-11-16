import unittest

from scripts.check_review_budget import summarize_queue


class ReviewBudgetTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            dict(video_id="ai_a", label="ai", source_sha256="c", score=0.6),
            dict(video_id="real_a", label="real", source_sha256="b", score=0.6),
            dict(video_id="ai_b", label="ai", source_sha256="a", score=0.9),
        ]

    def test_ties_break_by_hash_and_count_review_slots(self):
        expected = dict(ai_surfaced=1, real_reviewed=1, ai_outside=1,
                        queue=["ai_b", "real_a"])
        self.assertEqual(summarize_queue(self.rows, "score", 2), expected)
        self.assertEqual(summarize_queue(self.rows[::-1], "score", 2), expected)

    def test_reject_duplicate_clips_and_nonfinite_scores(self):
        with self.assertRaises(ValueError):
            summarize_queue(self.rows + self.rows[:1], "score", 2)
        self.rows[0]["score"] = float("nan")
        with self.assertRaises(ValueError):
            summarize_queue(self.rows, "score", 2)
