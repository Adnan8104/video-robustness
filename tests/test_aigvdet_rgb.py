"""Guard native probability aggregation and RGB spatial preprocessing."""
import math
import unittest
import numpy as np
from PIL import Image
from vidrobust.adapters.aigvdet_rgb import aggregate_frame_logits, native_transform, AIGVDetRGBDetector
from vidrobust.registry import detector_names


class AIGVDetRGBTests(unittest.TestCase):
    def test_probabilities_are_averaged_after_sigmoid(self):
        import torch
        logits = [-8.0] * 12 + [4.0] * 4
        probabilities, score = aggregate_frame_logits(logits)
        expected = [torch.tensor(v).sigmoid().item() for v in logits]
        self.assertEqual(probabilities, expected)
        self.assertEqual(score, sum(expected) / 16)
        self.assertGreater(abs(score - 1 / (1 + math.exp(-sum(logits) / 16))), .2)
        for invalid in (logits[:15], [float('nan')] * 16, [float('inf')] * 16):
            with self.assertRaises(ValueError):
                aggregate_frame_logits(invalid)

    def test_native_crop_keeps_rgb_and_has_no_resize(self):
        import torch
        frame = np.zeros((504, 720, 3), dtype=np.uint8)
        frame[28:476, 136:584] = [255, 128, 0]
        actual = native_transform()(Image.fromarray(frame))
        self.assertEqual(tuple(actual.shape), (3, 448, 448))
        expected = (torch.tensor([1., 128/255., 0.]) - torch.tensor([.485, .456, .406])) / torch.tensor([.229, .224, .225])
        self.assertTrue(torch.equal(actual, expected[:, None, None].expand_as(actual)))
        padded = native_transform()(Image.fromarray(np.full((224, 224, 3), 255, dtype=np.uint8)))
        black = (torch.zeros(3) - torch.tensor([.485, .456, .406])) / torch.tensor([.229, .224, .225])
        self.assertTrue(torch.equal(padded[:, 0, 0], black))
        self.assertTrue(torch.equal(padded[:, 224, 224], (torch.ones(3) - torch.tensor([.485, .456, .406])) / torch.tensor([.229, .224, .225])))

    def test_registry_and_input_contract_without_loading_weights(self):
        self.assertIn('aigvdet_rgb', detector_names())
        adapter = AIGVDetRGBDetector.__new__(AIGVDetRGBDetector)
        with self.assertRaises(ValueError):
            adapter.prepare_frames([])
        import torch
        with self.assertRaises(ValueError):
            adapter.predict(torch.zeros(16, 3, 224, 224))
