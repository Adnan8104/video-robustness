import unittest

from scripts.check_cutoffs import ALL_NEGATIVE, choose_cutoff, evaluate, split_keys


class CutoffTests(unittest.TestCase):
    def test_budget_and_equality_at_boundary(self):
        scores = [('real', .9), ('real', .6), ('ai', .8), ('ai', .7), ('ai', .55)]
        chosen = choose_cutoff(scores, 1)
        self.assertEqual((chosen['cutoff'], chosen['real_flagged'], chosen['ai_missed']), (.7, 1, 1))

    def test_ties_prefer_fewer_flags_and_then_higher_cutoff(self):
        scores = [('real', .6), ('real', .1), ('ai', .85), ('ai', .8)]
        self.assertEqual(choose_cutoff(scores, 1)['cutoff'], .8)
        disabled = choose_cutoff([('real', 1.0), ('ai', 1.0)], 0)
        self.assertEqual((disabled['cutoff'], disabled['real_flagged'], disabled['ai_missed']),
                         (ALL_NEGATIVE, 0, 1))

    def test_crossings_distinguish_new_errors_and_recoveries(self):
        samples = [{'id': 'x', 'label': 'ai'}, {'id': 'y', 'label': 'real'}]
        scores = {('x','m','baseline'): ('ai', .8), ('x','m','compression'): ('ai', .3),
                  ('y','m','baseline'): ('real', .8), ('y','m','compression'): ('real', .3)}
        result = evaluate(scores, 'm', samples, .5)
        self.assertEqual([r['new_error'] for r in result['paired_crossings']], [True, False])
        self.assertEqual(result['baseline']['real_flagged'], 1)
        self.assertEqual(result['compression']['ai_missed'], 1)

    def test_split_rejects_broken_pairs(self):
        real = dict(id='real', label='real', split='cutoff', anchor_id='anchor',
                    original_source_url='https://example.com/scene', sha256='one')
        fake = dict(real, id='ai', label='ai', sha256='two')
        self.assertEqual(split_keys([real, fake], 'cutoff')['anchor'], {'anchor'})
        with self.assertRaises(ValueError):
            split_keys([real, dict(fake, split='test')], 'cutoff')
        with self.assertRaises(ValueError):
            split_keys([real, fake, dict(fake, id='another')], 'cutoff')
