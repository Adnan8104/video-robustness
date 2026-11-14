import unittest

from scripts.check_head_cutoff import by_variant, choose_cutoff


def rows(light, heavy):
    return [dict(variant=variant, label=label, both_levels_margin=value)
            for variant, split in [('baseline', light), ('compression', heavy)]
            for label, value in split]


class HeadCutoffTests(unittest.TestCase):
    def test_both_conditions_must_respect_budget(self):
        examples = rows([('real', .5), ('ai', .7)],
                        [('real', .1), ('ai', .6), ('ai', .4)])
        threshold, metrics = choose_cutoff(examples, 0)
        self.assertEqual(threshold, .6)
        self.assertEqual(metrics['compression']['ai_missed'], 1)
        self.assertEqual(metrics['baseline']['real_flagged'], 0)

    def test_all_negative_option_and_equality_rule(self):
        examples = rows([('real', .5), ('ai', .5)], [('real', .5), ('ai', .5)])
        self.assertEqual(by_variant(examples, 'both_levels_margin', .5)['baseline']['ai_missed'], 0)
        threshold, metrics = choose_cutoff(examples, 0)
        self.assertGreater(threshold, .5)
        self.assertEqual(metrics['compression']['real_flagged'], 0)
        self.assertEqual(metrics['compression']['ai_missed'], 1)

    def test_cutoff_does_not_change_ranking_even_with_rounding(self):
        examples = rows([('real', 1e-100), ('ai', 2e-100)],
                        [('real', 1e-100), ('ai', 2e-100)])
        self.assertEqual(by_variant(examples, 'both_levels_margin', .5)['compression']['auc'], 1.)
