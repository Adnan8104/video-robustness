"""Upload boundaries, cleanup and parity with the benchmark's frame sampler."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import imageio_ffmpeg

from vidrobust.inference import DetectionService, centered_indices, section_plan, score_summary, validate_metadata

ROOT = Path(__file__).resolve().parents[1]


class FakeDetector:
    def __init__(self, score):
        self.score = score

    def prepare_frames(self, frames):
        import torch
        return torch.zeros((len(frames), 3, 4, 4))

    def predict(self, tensor):
        return dict(ai_score=self.score)


class InferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        path = Path(cls.directory.name) / "fixture.mp4"
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=240x144:rate=24", "-frames:v", "24",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
        cls.content = path.read_bytes()
        long_path = Path(cls.directory.name) / "long.mp4"
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=240x144:rate=24", "-frames:v", "288",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(long_path)], check=True)
        cls.long_content = long_path.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_centered_frames_match_pinned_upstream(self):
        sys.path.insert(0, str(ROOT / "vendor/aegis"))
        from video_io import window_sample
        for count, fps in ((16, 24), (240, 30000 / 1001), (301, 24), (100, 60), (200, 1)):
            with self.subTest(count=count, fps=fps):
                expected = window_sample(count, 16, fps, target_dur=4, random_start=False).tolist()
                self.assertEqual(centered_indices(dict(frames=count, fps=fps)), expected)

    def test_resource_limits_before_inference(self):
        meta = dict(width=1920, height=1080, frames=720, fps=24)
        validate_metadata(meta)
        validate_metadata(dict(meta, width=1080, height=1920))
        validate_metadata(dict(meta, frames=16, fps=4))
        for change in (dict(fps=float("nan")), dict(fps=61), dict(fps=3.9), dict(fps=0), dict(frames=721),
                       dict(frames=15), dict(width=3840), dict(height=1)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_metadata(meta | change)

    def test_three_sections_keep_middle_parity_and_short_clips_deduplicate(self):
        meta = dict(frames=720, fps=24)
        plan = section_plan(meta, True)
        self.assertEqual([name for name, _ in plan], ["beginning", "middle", "end"])
        self.assertEqual(plan[1][1], centered_indices(meta))
        self.assertEqual((plan[0][1][0], plan[-1][1][-1]), (0, 719))
        self.assertTrue(all(len(set(selected)) == 16 for _, selected in plan))
        self.assertEqual(section_plan(dict(frames=24, fps=24), True),
                         section_plan(dict(frames=24, fps=24), False))
        # Just over four seconds: beginning and middle can sample identical frames.
        short = dict(frames=97, fps=24)
        short_plan = section_plan(short, True)
        self.assertEqual([name for name, _ in short_plan], ["middle", "end"])
        self.assertEqual(short_plan[0][1], centered_indices(short))
        self.assertEqual(len({tuple(indices) for _, indices in short_plan}), len(short_plan))

    def test_three_sections_share_decoded_frames_and_do_not_average_scores(self):
        first, second = FakeDetector(.2), FakeDetector(.8)
        seen = []

        def inspect_frames(frames):
            seen.append(frames)
            return FakeDetector.prepare_frames(first, frames)

        first.prepare_frames = inspect_frames
        with patch("vidrobust.inference.make_detector", side_effect=[first, second]):
            result = DetectionService(ROOT).analyze(self.long_content, "clip.mp4", scan_sections=True)
        self.assertEqual(len(result["windows"]), 3)
        self.assertEqual(result["detectors"], result["windows"][1]["detectors"])
        self.assertEqual(result["sampled_frame_indices"], result["windows"][1]["sampled_frame_indices"])
        self.assertEqual(len(seen), 3)
        self.assertNotEqual(seen[0][0].tobytes(), seen[-1][0].tobytes())
        for window in result["windows"]:
            self.assertEqual(window["detectors"][0]["sampled_rgb_sha256"], window["detectors"][1]["sampled_rgb_sha256"])

    def test_midpoint_disagreement_is_not_a_verdict(self):
        self.assertEqual(score_summary([.2, .8]), "Models disagree around 0.5")
        self.assertEqual(score_summary([.1, .4]), "Both scores are below 0.5")
        self.assertEqual(score_summary([.5, .9]), "Both scores are above 0.5")

    def test_real_decode_shared_frames_cached_models_and_cleanup(self):
        directories = []
        temporary = tempfile.TemporaryDirectory

        def tracked(**kwargs):
            directory = temporary(**kwargs)
            directories.append(Path(directory.name))
            return directory

        service = DetectionService(ROOT)
        with patch("vidrobust.inference.tempfile.TemporaryDirectory", side_effect=tracked), \
             patch("vidrobust.inference.make_detector", side_effect=[FakeDetector(.2), FakeDetector(.8)]) as factory:
            result = service.analyze(self.content, "../../private/clip.mp4")
            repeat = service.analyze(self.content, "different-name.mp4")
            self.assertEqual(factory.call_count, 2)
        self.assertEqual(result, repeat)
        self.assertEqual(result["input_sha256"], hashlib.sha256(self.content).hexdigest())
        self.assertEqual(result["metadata"]["frames"], 24)
        self.assertEqual(len(result["sampled_frame_indices"]), 16)
        self.assertEqual(result["detectors"][0]["sampled_rgb_sha256"], result["detectors"][1]["sampled_rgb_sha256"])
        self.assertEqual(len(result["warnings"]), 2)
        self.assertNotIn("private", str(result))
        self.assertTrue(all(not directory.exists() for directory in directories))

    def test_cleanup_after_model_failure(self):
        from vidrobust import inference
        paths = []
        original_probe = inference.probe

        def tracked_probe(path):
            paths.append(path)
            return original_probe(path)

        with patch("vidrobust.inference.probe", side_effect=tracked_probe), \
             patch("vidrobust.inference.make_detector", side_effect=RuntimeError("model failed")):
            with self.assertRaisesRegex(RuntimeError, "model failed"):
                DetectionService(ROOT).analyze(self.content, "clip.mp4")
        self.assertEqual(len(paths), 1)
        self.assertFalse(paths[0].parent.exists())

    def test_invalid_uploads_never_load_models(self):
        with patch("vidrobust.inference.make_detector") as factory:
            for content, name in ((b"", "clip.mp4"), (b"text", "clip.txt"), (b"broken", "clip.mp4")):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    DetectionService(ROOT).analyze(content, name)
            with patch("vidrobust.inference.MAX_UPLOAD_BYTES", 1), self.assertRaises(ValueError):
                DetectionService(ROOT).analyze(self.content, "clip.mp4")
            factory.assert_not_called()
