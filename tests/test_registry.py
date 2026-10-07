"""Adding a registered adapter must not require edits to the runner or report."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from vidrobust.cli import LEGACY_COMMANDS, ROOT
from vidrobust.experiment import load_config
from vidrobust.frame_scoring import score_frames
from vidrobust.registry import _ADAPTERS, detector_names, make_detector, register


class ToyAdapter:
    checkpoint = dict(path='models/test-only.pt', url='https://example.invalid/test-only.pt', sha256='0'*64)
    preprocessing = 'Test fixture only; no pretrained predictions'

    def __init__(self, root):
        self.root = root

    def prepare_frames(self, frames):
        import torch
        return torch.from_numpy(np.stack(frames)).float()

    def predict(self, tensor):
        return dict(ai_score=.7, fusion_logit=.8472978603872037)


class RegistryTests(unittest.TestCase):
    def test_new_registration_reaches_config_factory_and_scoring(self):
        detector_names()  # Load built-ins before temporarily adding the fixture.
        with patch.dict(_ADAPTERS):
            register('test_adapter')(ToyAdapter)
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / 'configs').mkdir()
                (root / 'configs/samples.json').write_bytes((ROOT / 'configs/samples.json').read_bytes())
                config = json.loads((ROOT / 'configs/experiments/smoke.json').read_text())
                config['detectors'] = ['test_adapter']
                path = root / 'plan.json'
                path.write_text(json.dumps(config))
                load_config(root, path)
                with patch('vidrobust.artifacts.download') as transfer:
                    adapter = make_detector(root, 'test_adapter')
                    transfer.assert_called_once()
                details = score_frames(adapter, 'test_adapter', [np.zeros((2, 4, 3), dtype=np.uint8) for _ in range(16)])
                self.assertEqual(details['ai_score'], .7)
                self.assertEqual(len(details['model_input_sha256']), 64)
                with self.assertRaises(ValueError):
                    register('test_adapter')(ToyAdapter)

    def test_duplicate_and_incomplete_adapters_are_rejected(self):
        detector_names()
        with self.assertRaises(ValueError):
            register('aegis')(ToyAdapter)
        with self.assertRaises(ValueError):
            register('incomplete')(type('Incomplete', (), {}))
        class EscapingAdapter(ToyAdapter):
            checkpoint = ToyAdapter.checkpoint | dict(path='../outside.pt')
        with self.assertRaises(ValueError):
            register('escaping')(EscapingAdapter)

    def test_report_can_plot_a_new_detector_name(self):
        from vidrobust.experiment_report import plot_pairs
        config = dict(name='registry-test', baseline='baseline', detectors=['third_detector'],
                      variants=[dict(name='baseline'), dict(name='compression')])
        samples = [dict(id='clip', label='real')]
        rows = [dict(video_id='clip', variant=v, detector='third_detector', ai_score=s)
                for v, s in [('baseline', .3), ('compression', .7)]]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            plot_pairs(ROOT, out, config, samples, rows)
            self.assertTrue((out / 'pairs.png').exists())
            self.assertTrue((out / 'pairs.svg').exists())

    def test_historical_commands_resolve_after_move(self):
        for module, function in LEGACY_COMMANDS.values():
            study = importlib.import_module(f'vidrobust.legacy.{module}')
            self.assertTrue(callable(getattr(study, function)))


if __name__ == '__main__':
    unittest.main()
