"""Protect conditional interactions, paired case coverage and fixed RGB inputs."""
from itertools import product
import math
import unittest
import numpy as np
from vidrobust.frame_scoring import rgb_digest
from vidrobust.kitten_isolation import factorial_summary,variant_name


def rows_fixture():
    rows=[]
    for name in ('aegis','waverep'):
        for r,c,e in product((0,1),repeat=3):
            for sampling in ('original','fps_selected'):
                z=-4+3*r-c+.5*e+.25*(sampling=='fps_selected')+2*r*c
                rows.append(dict(detector=name,variant=variant_name(r,c,e,sampling),case_type='factorial',
                    ai_score=1/(1+math.exp(-z)),fusion_logit=z,model_input_sha256=f'{r}{c}{e}{sampling}'))
        z=1.2
        rows.append(dict(detector=name,variant='parent_prepared_encoded',case_type='endpoint_bridge',ai_score=1/(1+math.exp(-z)),fusion_logit=z))
    return rows


class KittenIsolationTests(unittest.TestCase):
    def test_conditional_resize_effect_and_nonadditive_crop_interaction(self):
        summary=factorial_summary(rows_fixture())['aegis']
        self.assertEqual(summary['resize_crop_logit_interaction_lossless'],dict(original=2.0,fps_selected=2.0))
        effects=[r for r in summary['conditional_effects'] if r['factor']=='resize' and r['from_variant'] in ('r0_c0_e0_original','r0_c1_e0_original')]
        self.assertEqual([r['delta_logit'] for r in effects],[3.0,5.0])
        self.assertAlmostEqual(sum(r['delta_logit'] for r in summary['exact_endpoint_path']),5.2)

    def test_missing_or_duplicated_factorial_condition_is_rejected(self):
        rows=rows_fixture()
        with self.assertRaises(ValueError):factorial_summary(rows[1:])
        with self.assertRaises(ValueError):factorial_summary(rows+[rows[0]])

    def test_pixel_identity_checks_reject_changed_or_invalid_frames(self):
        frames=[np.full((2,4,3),i,dtype=np.uint8) for i in range(16)]
        digest=rgb_digest(frames)
        self.assertEqual(digest,rgb_digest([f.copy() for f in frames]))
        changed=[f.copy() for f in frames];changed[7][0,0,0]+=1
        self.assertNotEqual(digest,rgb_digest(changed))
        with self.assertRaises(ValueError):rgb_digest(frames[:15])
        with self.assertRaises(ValueError):rgb_digest([f.astype(np.float32) for f in frames])
