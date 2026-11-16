import unittest

from scripts.check_false_flags import count_false_flags


def fixture():
    return [
        dict(video_id=clip, variant=variant, cell=category, label='real', margin=margin)
        for clip, category, values in [('new','sports',[-1,0]), ('cleared','sports',[1,-1]),
                                       ('both','vlog',[1,1]), ('clear','vlog',[-1,-1])]
        for variant,margin in zip(('baseline','compression'),values)
    ]


class FalseFlagTests(unittest.TestCase):
    def test_equal_totals_can_hide_changes_on_individual_recordings(self):
        r = count_false_flags(fixture(), 'margin')
        self.assertEqual((r['all']['baseline_flagged'], r['all']['compression_flagged']), (2,2))
        self.assertEqual(r['all']['new_flags'], ['new'])
        self.assertEqual(r['all']['cleared_flags'], ['cleared'])
        self.assertEqual(r['vlog']['flagged_at_both'], ['both'])

    def test_rejects_incomplete_pairs_and_generated_inputs(self):
        rows = fixture()
        with self.assertRaises(ValueError):
            count_false_flags(rows[1:], 'margin')
        rows[0]['label'] = 'ai'
        with self.assertRaises(ValueError):
            count_false_flags(rows, 'margin')
