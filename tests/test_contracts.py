"""Small failure-boundary tests; actual pretrained run is the integration check."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from vidrobust.cli import download, sha

class ProvenanceTests(unittest.TestCase):
    def test_bad_download_never_becomes_input(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "clip.mp4"
            def fake_transfer(url, path):
                Path(path).write_bytes(b"wrong content")
            with patch("urllib.request.urlretrieve", side_effect=fake_transfer):
                with self.assertRaises(ValueError):
                    download("https://example.invalid/clip", dest, "0"*64)
            self.assertFalse(dest.exists())
            self.assertFalse(dest.with_suffix(".part").exists())

    def test_verified_file_is_reused_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "clip.mp4"
            dest.write_bytes(b"verified input")
            expected = hashlib.sha256(b"verified input").hexdigest()
            with patch("urllib.request.urlretrieve") as transfer:
                download("https://example.invalid/clip", dest, expected)
                transfer.assert_not_called()
            self.assertEqual(sha(dest), expected)


class FrameSamplingTests(unittest.TestCase):
    def test_centered_window_is_repeatable_and_inside_video(self):
        import sys
        from vidrobust.cli import ROOT
        sys.path.insert(0, str(ROOT / "vendor/aegis"))
        from video_io import window_sample
        import numpy as np
        first = window_sample(300, 16, 30, target_dur=4, random_start=False)
        second = window_sample(300, 16, 30, target_dur=4, random_start=False)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first[0], 90)
        self.assertEqual(first[-1], 209)

if __name__ == "__main__":
    unittest.main()
