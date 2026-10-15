"""Guard native temporal grouping and ranking semantics without weight downloads."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from vidrobust.adapters.d3_xclip import CONFIG_HASH, D3XCLIPDetector
from vidrobust.artifacts import sha
from vidrobust.experiment import load_config
from vidrobust.registry import get_adapter

ROOT = Path(__file__).resolve().parents[1]


class XCLIPContractTests(unittest.TestCase):
    def test_registered_config_is_native_eight_frame_model(self):
        self.assertEqual(sha(ROOT/'vendor/d3/xclip-config.json'),CONFIG_HASH)
        config=json.loads((ROOT/'vendor/d3/xclip-config.json').read_text())['vision_config']
        self.assertEqual((config['num_frames'],config['patch_size'],config['image_size']),(8,16,224))
        self.assertTrue(get_adapter('d3_xclip').adapter.ranking_only)
        for name in ('xclip-shared','xclip-8fps'):
            with patch('urllib.request.urlretrieve') as network:
                _,_,plan,samples=load_config(ROOT,'configs/experiments/'+name+'.json')
                self.assertEqual(plan['analysis'],'ranking')
                self.assertEqual(len(samples),26)
                network.assert_not_called()

    def test_forward_keeps_all_frames_and_native_raw_arithmetic(self):
        import torch
        from types import SimpleNamespace
        detector=D3XCLIPDetector.__new__(D3XCLIPDetector)
        calls=[]
        features=torch.arange(16,dtype=torch.float32).square().reshape(16,1)
        def encoder(tensor,output_hidden_states):
            calls.append((tuple(tensor.shape),output_hidden_states))
            return SimpleNamespace(pooler_output=features)
        detector.encoder=encoder
        actual=detector.predict(torch.zeros(16,3,224,224))
        first=(features[1:]-features[:-1]).abs().flatten()
        second=first[1:]-first[:-1]
        self.assertEqual(calls,[((16,3,224,224),True)])
        self.assertEqual(actual['first_order_distances'],first.tolist())
        self.assertEqual(actual['second_order_changes'],second.tolist())
        self.assertEqual(actual['temporal_std'],second.std().item())
        self.assertEqual(actual['ai_score'],1/(1+second.std().item()))
        with self.assertRaises(ValueError):
            detector.predict(torch.zeros(8,3,224,224))

    @unittest.skipUnless(importlib.util.find_spec('transformers'),'Install the temporal extra')
    def test_tiny_encoder_has_cross_frame_dependence_within_native_groups(self):
        import torch
        from transformers import XCLIPVisionConfig,XCLIPVisionModel
        torch.manual_seed(0)
        config=XCLIPVisionConfig(hidden_size=16,intermediate_size=32,num_hidden_layers=2,
            num_attention_heads=4,image_size=32,patch_size=16,num_frames=8)
        encoder=XCLIPVisionModel(config).eval()
        frames=torch.randn(16,3,32,32)
        with torch.inference_mode():
            before=encoder(frames).pooler_output
            frames[0]+=4
            after=encoder(frames).pooler_output
        # Temporal context reaches other frames in group 1; group 2 is separate.
        self.assertFalse(torch.equal(before[1],after[1]))
        torch.testing.assert_close(before[8:],after[8:],rtol=0,atol=0)
