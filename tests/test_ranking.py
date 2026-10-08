"""Prevent arbitrary midpoints and sampling drift in temporal ranking runs."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from vidrobust.cli import ROOT
from vidrobust.experiment import load_config
from vidrobust.experiment_report import summarize_rankings, summarize_decisions, write_results
from vidrobust.frame_scoring import experiment_indices


class RankingTests(unittest.TestCase):
    def test_rank_only_config_rejects_midpoint_before_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'configs').mkdir()
            (root/'configs/temporal-panel.json').write_bytes((ROOT/'configs/temporal-panel.json').read_bytes())
            config = json.loads((ROOT/'configs/experiments/temporal-shared.json').read_text())
            path = root/'plan.json'
            with patch('urllib.request.urlretrieve') as download:
                path.write_text(json.dumps(config))
                load_config(root, path)
                for changes in [dict(analysis='midpoint'), dict(analysis='typo'), dict(sampling='typo')]:
                    path.write_text(json.dumps(config | changes))
                    with self.assertRaises(ValueError):
                        load_config(root, path)
                download.assert_not_called()

    def test_auc_ties_and_single_origin_have_defined_behavior(self):
        config = dict(analysis='ranking', detectors=['candidate'], variants=[dict(name='original')])
        rows = [dict(video_id=str(i), label=label, detector='candidate', variant='original', source='mixed', ai_score=s)
                for i,(label,s) in enumerate([('real',.2),('real',.8),('ai',.2),('ai',.9)])]
        m = summarize_rankings(rows,config)['candidate']['original']['all']
        self.assertEqual((m['pairs'],m['ai_above_real'],m['ties'],m['pairwise_auc']), (4,2,1,.625))
        self.assertIsNone(summarize_rankings(rows[:2],config)['candidate']['original']['all']['pairwise_auc'])
        with self.assertRaises(ValueError):
            summarize_decisions(rows,config)

    def test_eight_fps_positions_have_correct_duration_and_no_duplicates(self):
        config=dict(sampling='centered_2s_8fps')
        for fps,frames in [(24,240),(30,300),(25,250)]:
            indices=experiment_indices(dict(fps=fps,frames=frames),config)
            self.assertEqual(len(set(indices)),16)
            self.assertEqual(indices[0],(frames-round(fps*2))//2)
            self.assertLessEqual(abs((indices[-1]-indices[0])/fps - 1.875),1/fps)
        for meta in [dict(fps=7,frames=100),dict(fps=30,frames=59)]:
            with self.assertRaises(ValueError):
                experiment_indices(meta,config)

    def test_ranking_report_removes_stale_decisions_and_has_no_error_claims(self):
        config=dict(name='ranking-test',analysis='ranking',detectors=['candidate'],baseline='original',
                    preparation='native',variants=[dict(name='original')])
        rows=[dict(video_id='clip',label='real',detector='candidate',variant='original',source='source',
                   ai_score=.8,temporal_std=.25,delta_vs_baseline=0)]
        metadata=dict(config_path='test.json',models={'candidate':dict(preprocessing='Ranking only')})
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            (out/'decisions.json').write_text('stale')
            with patch('vidrobust.experiment_report.plot_pairs'):
                write_results(ROOT,out,config,[dict(id='clip',label='real')],rows,
                              summarize_rankings(rows,config),metadata,{})
            self.assertFalse((out/'decisions.json').exists())
            report=(out/'report.md').read_text()
            self.assertIn('no decision cutoff',report)
            self.assertNotIn('Both error directions',report)


if __name__=='__main__':
    unittest.main()
