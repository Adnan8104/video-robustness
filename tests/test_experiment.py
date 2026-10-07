"""Failure boundaries for the shared runner; real checkpoint runs check parity."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from vidrobust.cli import ROOT
from vidrobust.experiment import analyze, experiment_plan, frozen_revision, inside, load_config
from vidrobust.media import transform_filter


def fixture():
    config = dict(detectors=["aegis", "waverep"], baseline="baseline",
                  variants=[dict(name="baseline"), dict(name="compression")])
    samples = [dict(id="a", label="ai"), dict(id="b", label="ai")]
    rows = []
    for sample in samples:
        for detector in config["detectors"]:
            for variant, score in (("baseline", .5), ("compression", .8 if sample["id"] == "a" else .2)):
                rows.append(dict(video_id=sample["id"], label="ai", cell="", content="", detector=detector,
                    variant=variant, ai_score=score, sha256=sample["id"]+variant,
                    sampled_frame_indices=json.dumps(list(range(16))), sampled_rgb_sha256=sample["id"]+variant,
                    width=504, height=504, frames=96, fps=24))
    return config, samples, rows


class ExperimentTests(unittest.TestCase):
    def test_plan_does_not_download_or_load_model(self):
        with patch("vidrobust.experiment.make_detector") as model, patch("urllib.request.urlretrieve") as network:
            smoke = experiment_plan(ROOT, "configs/experiments/smoke.json")
            compression = experiment_plan(ROOT, "configs/experiments/compression.json")
            self.assertEqual(smoke["scores"], 20)
            self.assertEqual(compression["scores"], 80)
            model.assert_not_called()
            network.assert_not_called()

    def test_reject_invalid_config_before_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = json.loads((ROOT / "configs/experiments/smoke.json").read_text())
            (root / "configs").mkdir()
            (root / "configs/samples.json").write_bytes((ROOT / "configs/samples.json").read_bytes())
            path = root / "config.json"
            for change in (dict(baseline="missing"), dict(detectors=["aegis", "aegis"]),
                           dict(sample_ids=["missing"]), dict(source_directory="../elsewhere"),
                           dict(preparation="typo"), dict(detectros=["aegis"])):
                path.write_text(json.dumps(config | change))
                with self.assertRaises(ValueError):
                    load_config(root, path)
            bad = copy.deepcopy(config)
            bad["variants"][1]["crf"] = True
            path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                load_config(root, path)
            with self.assertRaises(ValueError):
                inside(root, "../escape")

    def test_requires_frozen_config_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "plan.json"
            path.write_bytes(b"changed")
            with patch("subprocess.check_output", return_value=b"committed"):
                with self.assertRaises(ValueError):
                    frozen_revision(root, path)

    def test_reject_incomplete_or_mismatched_pairs_and_labels(self):
        config, samples, rows = fixture()
        for broken in (rows[:-1], rows+[rows[0]]):
            with self.assertRaises(ValueError):
                analyze(broken, config, samples)
        for change in (dict(sampled_rgb_sha256="different"), dict(sampled_frame_indices="[1]"),
                       dict(label="real"), dict(ai_score=float("nan"))):
            broken = copy.deepcopy(rows)
            broken[0].update(change)
            with self.assertRaises(ValueError):
                analyze(broken, config, samples)

    def test_absolute_changes_do_not_cancel_and_single_detector_works(self):
        config, samples, rows = fixture()
        summary = analyze(rows, config, samples)["waverep"]["compression"]["ai"]
        self.assertAlmostEqual(summary["median_delta"], 0)
        self.assertAlmostEqual(summary["median_absolute_delta"], .3)
        self.assertEqual(summary["changes_at_least_point10"], 2)
        self.assertEqual(len(summary["midpoint_crossings"]), 1)
        config["detectors"] = ["aegis"]
        analyze([r for r in rows if r["detector"] == "aegis"], config, samples)

    def test_native_transform_sizes_and_upscaling_boundary(self):
        self.assertEqual(transform_filter("half_resize", 1280, 720)[1], (640, 360))
        self.assertEqual(transform_filter("center_crop_80", 1280, 720)[1], (1024, 576))
        self.assertEqual(transform_filter("center_square", 1280, 720)[1], (720, 720))
        self.assertEqual(transform_filter("short_side_504", 1280, 720)[1], (896, 504))
        self.assertEqual(transform_filter("short_side_504", 720, 1280)[1], (504, 896))
        with self.assertRaises(ValueError):
            transform_filter("short_side_504", 320, 240)

    def test_lossless_native_edits_preserve_identity_pixels_and_frame_count(self):
        import imageio_ffmpeg
        import numpy as np
        from vidrobust.cli import sha
        from vidrobust.media import prepare_cases
        from vidrobust.waverep import read_exact_rgb
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "data/sources"
            cache.mkdir(parents=True)
            source = cache / "clip.mp4"
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                "testsrc2=size=1280x720:rate=24", "-frames:v", "16", "-c:v", "libx264", "-crf", "18",
                "-pix_fmt", "yuv420p", str(source)], check=True)
            config = dict(name="lossless-check", source_directory="data/sources", preparation="native",
                variants=[dict(name=n, transform=t, encoding="ffv1") for n, t in
                          (("baseline", "identity"), ("resize", "short_side_504"), ("crop", "center_square"))])
            sample = dict(id="clip", label="real", dataset="unused", revision="0"*40,
                          remote_path="clip.mp4", sha256=sha(source))
            with patch("urllib.request.urlretrieve") as network:
                cases, _ = prepare_cases(root, config, [sample])
                network.assert_not_called()
            self.assertEqual([(r["width"], r["height"], r["frames"]) for _, r in cases],
                             [(1280, 720, 16), (896, 504, 16), (720, 720, 16)])
            original = read_exact_rgb(source, list(range(16)))
            lossless = read_exact_rgb(cases[0][0], list(range(16)))
            for a, b in zip(original, lossless):
                np.testing.assert_array_equal(a, b)


if __name__ == "__main__":
    unittest.main()
