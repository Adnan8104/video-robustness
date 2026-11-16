"""Exercise the review queue without downloading model weights."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from vidrobust.review import ReviewService

ROOT = Path(__file__).resolve().parents[1]


class ReviewServiceTest(unittest.TestCase):
    def test_invalid_batch_is_rejected_before_model_load(self):
        service = ReviewService(ROOT)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            service.rank([("a.mp4", b"clip"), ("b.mp4", b"clip")])
        self.assertIsNone(service.detector)

    def test_missing_head_has_setup_message(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "fitted head is missing"):
                ReviewService(directory).rank([("a.mp4", b"clip")])


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Install the demo extra for UI tests")
class ReviewDemoTest(unittest.TestCase):
    def test_rank_then_edit_budget_and_clear_stale_queue(self):
        from streamlit.testing.v1 import AppTest

        service = Mock()
        service.rank.return_value = [dict(name="b.mp4", margin=0.2), dict(name="a.mp4", margin=-0.5)]
        app = AppTest.from_file(str(ROOT / "demo.py"), default_timeout=20).run()
        app.sidebar.radio[0].set_value("Prioritize for review").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.button[0].disabled)
        with patch("vidrobust.review_demo.get_service", return_value=service):
            app.file_uploader[0].set_value([("a.mp4", b"a", "video/mp4"), ("b.mp4", b"b", "video/mp4")]).run()
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.table[0].value["Video"].tolist(), ["b.mp4", "a.mp4"])
            app.number_input[0].set_value(1).run()
            self.assertEqual(app.table[0].value["Video"].tolist(), ["b.mp4"])
            service.rank.assert_called_once()
            app.file_uploader[0].clear().run()
            self.assertFalse(app.table)
