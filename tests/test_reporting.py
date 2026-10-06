"""Guard against cancellation of absolute shifts and discovery-case reuse."""
import json
from pathlib import Path
import tempfile
import unittest
from vidrobust.reporting import write_summary

class PairedSummaryTests(unittest.TestCase):
    def test_opposite_shifts_do_not_cancel_and_new_cohort_excludes_discovery(self):
        config = {"selection": {"retained_discovery_ids": ["old"]},
                  "samples": [{"id": "old", "generator": "MSVD"},
                              {"id": "new", "generator": "MSVD"}]}
        rows = []
        for video_id, baseline, compressed in [("old", 0.3, 0.7), ("new", 0.7, 0.3)]:
            for variant in ["original", "encode_control", "compression", "resize", "crop"]:
                score = compressed if variant == "compression" else baseline
                rows.append(dict(video_id=video_id, generator="MSVD", variant=variant,
                                 ai_score=score, delta=score-baseline, delta_vs_control=score-baseline))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"reports").mkdir()
            write_summary(root, config, rows)
            report = json.loads((root/"reports/summary.json").read_text())
        all_group, new_group = report["groups"]
        self.assertAlmostEqual(all_group["conditions"]["compression"]["median_signed_delta"], 0)
        self.assertAlmostEqual(all_group["conditions"]["compression"]["median_absolute_delta"], 0.4)
        self.assertEqual(all_group["conditions"]["compression"]["sizable_shift_count"], 2)
        self.assertEqual(new_group["clips"], 1)
        self.assertAlmostEqual(new_group["conditions"]["compression"]["median_signed_delta"], -0.4)
        self.assertEqual(report["new_source_clips"], 1)
