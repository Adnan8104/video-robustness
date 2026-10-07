"""One four-panel diagnostic chart with separate preparation and CRF comparisons."""
import os


def write_report(root, samples, rows, summary):
    from .comparison import pair_rows
    from .failure_followup import CRFS, VARIANTS
    pairs=pair_rows(rows);out=root/'reports/failure-followup'
    os.environ.setdefault('MPLCONFIGDIR',str(root/'data/.matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'video-robustness'})
    fig,axes=plt.subplots(2,2,figsize=(11.8,8.2),layout='constrained')
    for s,ax in zip(samples,axes.flat):
        for name,color,marker,label in [('aegis','#2563eb','o','AEGIS'),('waverep','#d97706','s','WaveRep')]:
            original=pairs[(s['id'],'original')][name]['ai_score']
            values=[pairs[(s['id'],f'crf_{c}')][name]['ai_score'] for c in CRFS]
            ax.plot([11,18],[original,values[0]],linestyle='--',color=color,alpha=.65)
            ax.scatter(11,original,color=color,marker=marker,s=38)
            ax.plot(CRFS,values,color=color,marker=marker,label=label,lw=1.8)
        ax.set_xticks([11,*CRFS],['Original\n(native)',*map(str,CRFS)])
        ax.set_ylim(-.035,1.035);ax.set_xlim(9.5,36.5)
        ax.axhline(.5,color='#64748b',linestyle=':',lw=1)
        ax.axvline(14.5,color='#cbd5e1',lw=1)
        ax.grid(axis='y',alpha=.2);ax.set_ylabel('AI-like score (uncalibrated)')
        ax.set_xlabel('Prepared H.264 CRF (higher = stronger compression)')
        ax.set_title(s['subject']+' ('+s['label']+')')
    axes[0,0].legend(loc='best')
    fig.suptitle('Four selected failure-study clips\nDashed = whole preparation recipe · solid = fixed-preparation CRF curve',fontweight='bold')
    fig.savefig(out/'failure-curves.png',dpi=180)
    svg=out/'failure-curves.svg';fig.savefig(svg,metadata={'Date':None});plt.close(fig)
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    lines=['# Four-clip failure follow-up','','Four existing, deliberately selected clips; 40 model-score rows. '
        'The original-file check tests whether the observed failures already occur before common preparation. '
        'CRF 23 and 28 add two intermediate compression strengths to the prepared CRF 18/35 endpoints.','',
        '## Findings','']
    for s in samples:
        a=summary[s['id']]['aegis'];w=summary[s['id']]['waverep']
        lines.append(f"- **{s['subject']} ({s['label']}):** original → prepared baseline is {a['original_score']:.6f} → {a['baseline_score']:.6f} for AEGIS and {w['original_score']:.6f} → {w['baseline_score']:.6f} for WaveRep.")
        for name,m in [('AEGIS',a),('WaveRep',w)]:
            if m['midpoint_crossings']:
                text='; '.join(f"CRF {c['from_crf']} → {c['to_crf']} (change {c['delta']:+.6f})" for c in m['midpoint_crossings'])
                lines.append(f"  {name} prepared-curve midpoint crossings: {text}.")
    lines += ['', 'A midpoint crossing is descriptive; scores are not calibrated probabilities. '
        'The crossing occurs somewhere between tested settings, and this small grid cannot locate its exact CRF. '
        'If the original and baseline differ, the comparison combines cropping/scaling, frame-rate conversion, '
        'window rounding/frame selection and encoding. It cannot identify a single cause.','',
        '![Original and prepared compression scores](failure-curves.png)','',
        '## All scores','',
        '| Clip | Model | Original | Prepared CRF 18 | CRF 23 | CRF 28 | CRF 35 |',
        '|---|---|---:|---:|---:|---:|---:|']
    for s in samples:
        for name in ['aegis','waverep']:
            values=[pairs[(s['id'],v)][name]['ai_score'] for v in VARIANTS]
            lines.append(f"| {s['subject']} ({s['label']}) | {name} | "+' | '.join(f'{v:.6f}' for v in values)+' |')
    lines += ['','## Preparation and curve steps','',
        '| Clip / model | Baseline − original | Largest adjacent CRF change | Change per CRF unit | Curve direction | First tested below-midpoint CRF* |',
        '|---|---:|---|---:|---|---:|']
    for s in samples:
        for name,m in summary[s['id']].items():
            step=m['largest_step'];first=m['first_tested_below_midpoint_crf']
            lines.append(f"| {s['subject']} / {name} | {m['preparation_delta']:+.6f} | {step['from_crf']} → {step['to_crf']}: {step['delta']:+.6f} | {step['delta_per_crf']:+.6f} | {m['direction']} | {first if first is not None else '—'} |")
    lines += ['','*Only when CRF 18 starts at or above 0.5. All crossings and all adjacent steps, '
        'including positive and negative changes, are retained in [summary.json](summary.json). '
        'Directions ignore changes ≤1e-6. CRF is not a linear perceptual-quality scale.','',
        '## Choices and practical limits','',
        '- **Four targeted clips:** the shared real-kitten error, first low-scoring real horse, and the largest earlier WaveRep drops in each AI content cell. Selection used previous results; these are failure cases and a comparison clip, not a new test set or an accuracy benchmark.',
        '- **Original files:** preserve native 1280×720 resolution and frame rate; both models use their unchanged native spatial preprocessing and the same centered 16 source-frame indices. AEGIS resizes to 224; WaveRep center-crops 504. Prepared variants use 504×504, 24 fps, 96 frames. Original/prepared samples need not be the same physical frames; indices and times remain in the CSV.',
        '- **CRF 23 and 28:** two intermediate levels keep the study small while bracketing large endpoint drops. Each level is encoded independently from the same lossless prepared master with medium preset, yuv420p and no audio. Each master is checked against its parent hash. Endpoints are reused only when hashes, sampled indices, model/preprocessing provenance and package versions agree; otherwise they are rescored and marked in the CSV.',
        '- **Unchanged pretrained inference:** CPU, four threads, seed 0, deterministic algorithms, WaveRep batches of two frames. Strict checkpoints and native aggregation stay unchanged. Full sequential decodes and paired bytes/indices are checked. Raw logits, AEGIS auxiliary heads and all WaveRep frame logits are retained so saturation can be examined.',
        '- **Fresh-model repeats:** reload both models for the kitten original and the newly tested midpoint bracket of each AI curve. If there is no such bracket, repeat CRF 23. Every score, logit, auxiliary output and frame index must match exactly; see [validation.json](validation.json).',
        '- **Interpretation:** the horse shares native size/FPS with the kitten but differs in species, motion, texture and camera history. Original-to-prepared differences do not isolate one transformation. The midpoint is not calibrated; source labels are inherited and possible training overlap is unknown. Four selected clips cannot establish a causal animal effect, population robustness or detector ranking. WaveRep remains a sparse-frame adaptation.', '',
        '## Reproduce','',
        '`uv sync --locked` then `uv run python run.py followup`. The command fetches the four pinned sources and checkpoints if missing, prepares independent encodes, verifies reusable endpoints, scores new cases, reloads both models for repeats, and regenerates this chart/report. No new dataset or dependency is required. Earlier reports stay unchanged.','',
        '[Frozen selection](../../configs/failure-followup-selection.md) · [Manifest](../../configs/failure-followup.json) · '
        '[Scores, branch outputs and sampling](scores.csv) · [Run and commands](run.json) · [Validation](validation.json) · '
        '[Parent balanced panel](../controlled/report.md)','',
        'Only numerical results and measurement charts are published. Videos, source frames, masters and weights stay local. '
        'WaveRep retains its [authors and informational/nonprofit license](../../vendor/waverep/ORIGIN.md).']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
