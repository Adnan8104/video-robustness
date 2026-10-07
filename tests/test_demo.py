"""Exercise actual upload, submit and stale-result behavior without weights."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Install the demo extra for UI tests")
class DemoTests(unittest.TestCase):
    def setUp(self):
        from streamlit.testing.v1 import AppTest
        # The first table imports pandas/Arrow; allow cold-start time in CI.
        self.app = AppTest.from_file(str(ROOT / "demo.py"), default_timeout=20).run()

    def test_empty_page_does_not_load_weights(self):
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.button[0].disabled)
        self.assertEqual(self.app.title[0].value, "Check a video")

    def test_upload_submit_and_change_clear_stale_result(self):
        result = dict(detectors=[dict(detector="aegis", ai_score=.2, preprocessing="test"),
            dict(detector="waverep", ai_score=.8, preprocessing="test")],
            metadata=dict(width=640, height=360), duration_seconds=4., warnings=[], sampling="test")
        service = Mock()
        service.analyze.return_value = result
        with patch("vidrobust.demo.get_service", return_value=service):
            self.app.file_uploader[0].set_value(("clip.mp4", b"fixture", "video/mp4")).run()
            self.app.button[0].click().run()
            self.assertFalse(self.app.exception)
            service.analyze.assert_called_once()
            self.assertEqual(self.app.subheader[0].value, "Models disagree around 0.5")
            self.assertEqual([metric.value for metric in self.app.metric], ["0.2000", "0.8000"])
            # A rerun leaves results visible without doing inference again.
            self.app.run()
            service.analyze.assert_called_once()
            self.app.checkbox[0].check().run()
            self.assertFalse(self.app.metric)
            self.assertNotIn("result", self.app.session_state)
            self.app.file_uploader[0].set_value(("other.mp4", b"new-video", "video/mp4")).run()
            self.assertFalse(self.app.metric)
            self.assertNotIn("result", self.app.session_state)

    def test_failed_recheck_removes_previous_result(self):
        service = Mock()
        service.analyze.side_effect = ValueError("Could not read this video.")
        with patch("vidrobust.demo.get_service", return_value=service):
            self.app.file_uploader[0].set_value(("bad.mp4", b"broken", "video/mp4")).run()
            self.app.session_state["result"] = {"old": "result"}
            self.app.button[0].click().run()
            self.assertFalse(self.app.exception)
            self.assertEqual(self.app.error[0].value, "Could not read this video.")
            self.assertNotIn("result", self.app.session_state)
            self.app.file_uploader[0].clear().run()
            self.assertFalse(self.app.error)

    def test_three_section_and_branch_tables_are_rendered(self):
        windows = []
        for section, score in (("beginning", .1), ("middle", .6), ("end", .9)):
            windows.append(dict(section=section, sampled_time_seconds=[0., 3.9], detectors=[
                dict(detector="aegis", ai_score=score, pixel_score=.2, motion_score=.4,
                     consistency_score=.9, preprocessing="test"),
                dict(detector="waverep", ai_score=.1, preprocessing="test")]))
        service = Mock()
        service.analyze.return_value = dict(windows=windows, detectors=windows[1]["detectors"],
            metadata=dict(width=640, height=360), duration_seconds=12., warnings=[],
            sampling="test", scan_sections=True)
        with patch("vidrobust.demo.get_service", return_value=service):
            self.app.file_uploader[0].set_value(("clip.mp4", b"fixture", "video/mp4")).run()
            self.app.checkbox[0].check().run()
            self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertTrue(service.analyze.call_args.kwargs["scan_sections"])
        self.assertEqual(self.app.table[0].value["AEGIS"].tolist(), ["0.1000", "0.6000", "0.9000"])
        self.assertEqual(self.app.table[1].value["Consistency"].tolist(), ["0.9000"] * 3)
