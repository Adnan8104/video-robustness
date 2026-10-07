"""One numerical figure and a small-panel descriptive report."""
import os


def write_report(root, config, rows, summary):
    from .controlled import CELLS
    from .comparison import pair_rows
    pairs = pair_rows(rows)
    out = root/'reports/controlled'
    os.environ.setdefault('MPLCONFIGDIR', str(root/'data/.matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'svg.hashsalt': 'video-robustness'})
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout='constrained')
    for cell, ax in zip(CELLS, axes.flat):
        samples = [s for s in config['samples'] if s['cell'] == cell]
        for name, color, marker in [('aegis', '#2563eb', 'o'), ('waverep', '#d97706', 's')]:
            for i, s in enumerate(samples):
                a = pairs[(s['id'], 'baseline')][name]['ai_score']
                b = pairs[(s['id'], 'compression')][name]['ai_score']
                y = i + (-.12 if name == 'aegis' else .12)
                ax.plot([a, b], [y, y], color=color, alpha=.7, lw=1.6)
                ax.scatter(a, y, color=color, marker=marker, s=48, label=f'{name.upper()} baseline' if i == 0 else None)
                ax.scatter(b, y, facecolors='white', edgecolors=color, marker=marker, s=48,
                           label=f'{name.upper()} compressed' if i == 0 else None)
        ax.set_yticks(range(5), [s['id'].rsplit('_', 1)[-1] for s in samples])
        ax.invert_yaxis(); ax.set_xlim(-.03, 1.03)
        ax.axvline(.5, color='#64748b', ls=':', lw=1)
        ax.set_xlabel('AI-like score (uncalibrated)'); ax.set_ylabel('Clip in cell')
        ax.set_title(cell.replace('_', ' ').title() + ' · n=5'); ax.grid(axis='x', alpha=.2)
    axes[0, 0].legend(fontsize=8, loc='upper center', bbox_to_anchor=(.5, 1.02))
    fig.suptitle('Matched preparation: compression response\nFilled = CRF 18 baseline · hollow = CRF 35 compressed', fontweight='bold')
    fig.savefig(out/'compression-pairs.png', dpi=180)
    svg = out/'compression-pairs.svg'
    fig.savefig(svg, metadata={'Date': None}); plt.close(fig)
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    kitten = 'controlled_real_animal_01'
    kitten_scores = {name: [pairs[(kitten, v)][name]['ai_score'] for v in ('baseline', 'compression')] for name in ('aegis', 'waverep')}
    wave_conflicts = {v: sum(summary['waverep'][cell]['midpoint_conflicts'][v] for cell in ('ai_animal', 'ai_non_animal')) for v in ('baseline', 'compression')}
    wave_large_ai = sum(summary['waverep'][cell]['changes_at_least_point10'] for cell in ('ai_animal', 'ai_non_animal'))
    aegis_large = sum(m['changes_at_least_point10'] for m in summary['aegis'].values())
    lines = ['# Balanced content panel under common preparation', '',
        '20 fresh sources: five clips in each real/AI × animal/non-animal cell; 80 model scores. '
        'Both detectors see identical bytes and the same 16 frames per condition. Selection and analysis were fixed before inference.', '',
        f"Both models give the real kitten scores above 0.5 in both conditions: AEGIS {kitten_scores['aegis'][0]:.6f} → {kitten_scores['aegis'][1]:.6f}; WaveRep {kitten_scores['waverep'][0]:.6f} → {kitten_scores['waverep'][1]:.6f}.", '',
        f"WaveRep has {wave_conflicts['baseline']}/10 generated clips below the midpoint at baseline and {wave_conflicts['compression']}/10 after compression; {wave_large_ai}/10 generated clips change by at least 0.10. AEGIS has {aegis_large}/20 changes at least 0.10. Matching prepared geometry therefore does not remove these observed failure cases.", '',
        'These observations concern a frozen convenience panel. Neither a causal animal effect nor a general detector ranking follows from them.', '',
        '![Paired compression scores](compression-pairs.png)', '',
        '## Descriptive results', '',
        'Compression-minus-baseline changes. A conflict is a score on the opposite side of the fixed 0.5 midpoint from the inherited label; '
        'this midpoint is not a calibrated decision threshold. Values and counts apply only to these five clips per cell.', '',
        '| Detector | Cell | Median signed change | Median absolute change | Changes ≥0.10 | Midpoint conflicts baseline → compressed | Midpoint crossings |',
        '|---|---|---:|---:|---:|---:|---:|']
    for detector, cells in summary.items():
        for cell, m in cells.items():
            conflicts = m['midpoint_conflicts']
            lines.append(f"| {detector} | {cell} | {m['median_delta']:+.6f} | {m['median_absolute_delta']:.6f} | {m['changes_at_least_point10']}/5 | {conflicts['baseline']} → {conflicts['compression']} | {len(m['midpoint_crossings'])} |")
    lines += ['', '## Every paired score', '', '| Clip | Subject annotation | AEGIS baseline | Compressed | Change | WaveRep baseline | Compressed | Change |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for s in config['samples']:
        values = []
        for detector in ('aegis', 'waverep'):
            a = pairs[(s['id'], 'baseline')][detector]['ai_score']
            b = pairs[(s['id'], 'compression')][detector]['ai_score']
            values += [f'{a:.6f}', f'{b:.6f}', f'{b-a:+.6f}']
        lines.append(f"| {s['id']} | {s['subject']} | " + ' | '.join(values) + ' |')
    lines += ['', '## All midpoint crossings', '']
    crossings = [(name, cell, c) for name, cells in summary.items() for cell, m in cells.items() for c in m['midpoint_crossings']]
    if not crossings:
        lines.append('None in this panel.')
    for name, cell, c in crossings:
        lines.append(f"- {name}, {c['video_id']} ({cell}): {c['baseline']:.6f} → {c['compression']:.6f}; change {c['delta']:+.6f}.")
    lines += ['', '## Technical choices and limits', '',
        '- **One real source and one generator:** pinned MSVD and Veo clips from ComGenVid. This holds source constant within each label while comparing content strata. Sora had too few native-size-eligible clips. The result is specific to this source/generator panel.',
        '- **504×504 without upscaling:** the native shortest side is at least 504. Bicubic downscaling and a central crop supply WaveRep its native image size without zero padding. AEGIS retains its native 224-pixel resize and normalization. Cropping can favor central subjects; embedded letterboxing can remain.',
        '- **Four seconds, 24 fps, 96 frames:** a common duration and frame grid permit identical 16-frame sampling. The centered start is snapped down to a source frame (less than one native frame); timestamps are reset to an exact output grid. Changing native FPS can drop/repeat frames. The preparation itself may remove or add detector cues; these are prepared baselines, not original-file scores.',
        '- **Independent H.264 encodes:** CRF 18 and CRF 35 start from the same lossless FFV1 intermediate. Medium preset, yuv420p, no audio. This avoids applying the compression treatment to an already compressed baseline. FFV1 preserves the prepared pixels, not the original uncompressed camera signal.',
        '- **Frozen manual content audit:** inspect the first ordered eligible candidates, then all 16 sampled frames of selected prepared crops. Keep five per cell before any inference. Animal means a prominent living non-human animal; humans alone and food preparations are non-animal. Ambiguous subjects/styles are excluded. Manual classification is fallible.',
        '- **Pretrained CPU inference:** strict released checkpoints, four threads, seed 0, deterministic algorithms. WaveRep batches two frames and applies sigmoid to the mean frame logit. Its sparse sampling is a budget adaptation rather than reproduction of native all-frame evaluation.',
        '- **Small descriptive panel:** n=5 per cell cannot establish general accuracy, a low false-positive rate, calibration, statistical significance or a mechanism involving animals/texture. Original camera quality, codec history, motion, species, backgrounds, native FPS and possible training overlap remain unmatched. Both models use DINOv2, so they are not independent evidence of every failure.', '',
        '## Reproduction and evidence', '',
        '`uv sync --locked` then `uv run python run.py controlled`. '
        'The command verifies hashes, downloads the 20 pinned sources and released weights, regenerates both encodes, scores both models, and rebuilds this report. '
        f"Source downloads total {sum(s['bytes'] for s in config['samples'])/(1024*1024):.1f} MiB; the two model checkpoints total about 764 MiB when absent. "
        'Temporary prepared intermediates need additional disk space; they remain ignored by Git.', '',
        'After scoring, run `uv run python scripts/verify_controlled.py` to reload both models and repeat the kitten pair in both models and the WaveRep pair with the largest absolute compression change. Validation retains the exact comparison of scores, logits, branch outputs and sampled indices.', '',
        '[Selection policy](../../configs/controlled-selection.md) · [Frozen manifest](../../configs/controlled.json) · '
        '[Candidate audit](../../configs/controlled-candidate-audit.json) · [All score/branch outputs](scores.csv) · '
        '[Run and preparation commands](run.json) · [Summary](summary.json) · [Validation](validation.json)', '',
        'Source videos, inspected frames, intermediate media and weights are not redistributed. '
        'WaveRep attribution and its informational/nonprofit license remain in [vendor/waverep](../../vendor/waverep/ORIGIN.md). '
        'Earlier reports are unchanged.']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
