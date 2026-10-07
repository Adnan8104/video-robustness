"""Fixed-frame conditional effects and an exact-endpoint preparation path."""
import os


def write_report(root,rows,summary):
    from .kitten_isolation import variant_name
    lookup={(r['detector'],r['variant']):r for r in rows};out=root/'reports/kitten-isolation'
    os.environ.setdefault('MPLCONFIGDIR',str(root/'data/.matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'video-robustness'})
    states=[(0,0,0,'Unedited'),(1,0,0,'Resize'),(0,1,0,'Crop'),(0,0,1,'Encode'),(1,1,0,'Resize + crop'),(1,0,1,'Resize + encode'),(0,1,1,'Crop + encode'),(1,1,1,'All three')]
    fig,axes=plt.subplots(2,2,figsize=(12,8.6),layout='constrained')
    for column,(name,color) in enumerate([('aegis','#2563eb'),('waverep','#d97706')]):
        ax=axes[0,column]
        for offset,sampling,label in [(-.15,'original','Original frames'),(.15,'fps_selected','24-fps-selected frames')]:
            scores=[lookup[(name,variant_name(r,c,e,sampling))]['ai_score'] for r,c,e,_ in states]
            ax.barh([i+offset for i in range(8)],scores,height=.28,color=color,alpha=1 if sampling=='original' else .4,label=label)
        ax.set_yticks(range(8),[s[3] for s in states]);ax.invert_yaxis();ax.set_xlim(0,1.03)
        ax.axvline(.5,color='#64748b',ls=':',lw=1);ax.set_xlabel('AI-like score (uncalibrated)')
        ax.set_title(name.upper() if name=='aegis' else 'WaveRep');ax.grid(axis='x',alpha=.15)
        if column==0:ax.legend(loc='best',fontsize=8)
        path=['r0_c0_e0_original','r0_c0_e0_fps_selected','r1_c0_e0_fps_selected','r1_c1_e0_fps_selected','parent_prepared_encoded']
        ax=axes[1,column];ax.plot(range(5),[lookup[(name,v)]['fusion_logit'] for v in path],marker='o',color=color)
        ax.set_xticks(range(5),['Original','Sample\nswap','Resize','Crop','Parent\nencoding'])
        ax.axhline(0,color='#64748b',ls=':',lw=1);ax.grid(alpha=.15);ax.set_ylabel('Fused raw output (logit)')
        ax.set_title('Path to the exact prepared endpoint')
    fig.suptitle('Real kitten: fixed-frame preparation steps\nTop: conditional edits · bottom: exact-endpoint path (order matters)',fontweight='bold')
    fig.savefig(out/'step-isolation.png',dpi=180);svg=out/'step-isolation.svg';fig.savefig(svg,metadata={'Date':None});plt.close(fig)
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    lines=['# Which preparation steps change the real kitten score?','','One previously observed clip; 36 model scores. '
        'Spatial/encoding interventions use fixed source frames. The alternate frame list is traced from the exact prior 24-fps conversion. '
        'Original and actual prepared endpoints must reproduce the published outputs exactly.','','## Findings','']
    for name in ('aegis','waverep'):
        base=lookup[(name,'r0_c0_e0_original')]
        singles=[(label,lookup[(name,variant_name(r,c,e,'original'))]) for r,c,e,label in states[1:4]]
        crossings=[label.lower() for label,r in singles if base['ai_score']<.5<=r['ai_score']]
        detail=', '.join(f"{label.lower()} {r['ai_score']:.6f}" for label,r in singles)
        lines.append(f"- **{name}:** fixed original-frame reference {base['ai_score']:.6f}; {detail}. Edits sufficient alone to move above the descriptive midpoint in this setting: {', '.join(crossings) if crossings else 'none' }.")
        sampled=lookup[(name,'r0_c0_e0_fps_selected')];metadata=lookup[(name,'metadata_only_24fps')]
        lines.append(f"  Changing only the sampled frame list gives {sampled['ai_score']:.6f}; changing only FPS metadata gives {metadata['ai_score']:.6f}.")
    lines += ['','These are conditional effects on this clip and these input pipelines. A sufficient edit does not reveal a learned biological/texture mechanism, prove a unique cause, or establish population accuracy. '
        'The exact original-to-prepared path below retains possible interactions and the final encoding context.','',
        '![Step isolation and exact preparation path](step-isolation.png)','','## All factorial scores','',
        '| Spatial/encoding edits | AEGIS: original frames | AEGIS: FPS-selected frames | WaveRep: original frames | WaveRep: FPS-selected frames |',
        '|---|---:|---:|---:|---:|']
    for r,c,e,label in states:
        values=[lookup[(name,variant_name(r,c,e,t))]['ai_score'] for name in ('aegis','waverep') for t in ('original','fps_selected')]
        lines.append('| '+label+' | '+' | '.join(f'{v:.6f}' for v in values)+' |')
    lines += ['','## Exact endpoint path','',
        '| Model | Step (all other inputs held fixed) | Score change | Logit change |',
        '|---|---|---:|---:|']
    labels=['Change source-frame list','Resize with alternate frames','Center crop after resize','Encode exact 96-frame/24-fps parent master']
    for name,stats in summary.items():
        for label,step in zip(labels,stats['exact_endpoint_path']):
            lines.append(f"| {name} | {label} | {step['delta_score']:+.6f} | {step['delta_logit']:+.6f} |")
    lines += ['','The logit changes telescope to the actual original-to-prepared difference. '
        'This is a path-dependent decomposition; changing the order or settings can change each contribution. '
        'Do not interpret these numbers as percentages of a unique global cause.','',
        '## Resize/crop interaction without H.264','',
        '| Model | Original frames: logit interaction | FPS-selected frames: logit interaction |',
        '|---|---:|---:|']
    for name,m in summary.items():
        interaction=m['resize_crop_logit_interaction_lossless']
        lines.append(f"| {name} | {interaction['original']:+.6f} | {interaction['fps_selected']:+.6f} |")
    lines += ['','Interaction = z(resize+crop) − z(resize) − z(crop) + z(unedited), on each fixed frame set. '
        'This records non-additivity for these interventions; it is not a significance test. '
        'All conditional single-factor changes are in [summary.json](summary.json).','',
        '## Why the controls matter','',
        '- **Exact frames:** the original list and alternate 24-fps-selected list differ at nine positions. Every resize/crop/encoding pair within a list keeps the same 16 source-frame identities. The alternate list is recovered from unique YUV/plane checksum matches through the actual FPS filter, rather than approximate timestamp rounding.',
        '- **Pixel-exact lossless reference:** native source → FFV1 yuv420p must preserve the sampled decoded RGB pixels exactly. Spatial filters use the same FFmpeg bicubic resize/center crop as the parent recipe. Width, height, all 240 decoded frames and native FPS are checked for each factorial file.',
        '- **Native model preprocessing:** AEGIS keeps its 224-pixel resize and normalization; WaveRep keeps its 504-pixel center crop and normalization, averaging frame logits before sigmoid. Fixed-frame inference injects only the selected RGB frames; it does not change weights, preprocessing or aggregation. Both published endpoint scores, logits and branches must match exactly.',
        '- **Frame rate:** a metadata-only file has 240 unchanged images at 24 fps and the same explicit source indices. Both models consume image tensors, not timestamps. Real FPS conversion affects which images get sampled and can change encoding context; these effects are measured separately.',
        '- **Encoding context:** factorial H.264 conditions encode the full 240-frame native-rate sequence, holding that context fixed across spatial/encoding comparisons. The actual parent baseline encodes a different 96-frame, 24-fps sequence. Its bridge is scored directly. Lossless resized/cropped alternate-frame inputs must match the parent master pixels, permitting an exact final encoding comparison.',
        '- **Model-input hashes:** decoded RGB and final normalized tensor hashes are retained. A crop can remove pixels that a model already ignores through its native center crop; equal tensor hashes identify such no-op conditions. Resize can change the effective field of view or scale after model preprocessing.',
        '- **Scope:** this is a targeted one-clip experiment selected after a failure. Scores and the 0.5 midpoint are uncalibrated. Results depend on codec context, interpolation, sampled frames and intervention order. They explain a pipeline response for this clip without identifying a learned mechanism or general animal-video behavior.', '',
        '## Reproduce and verify','',
        '`uv sync --locked` then `uv run python run.py isolate`. The command recreates local media, verifies exact frame/pixel bridges, runs 36 scores, reloads both models for repeats, and regenerates this report. No new dataset, model or dependency is added. Earlier reports remain unchanged.','',
        '[Frozen specification](../../configs/kitten-isolation-selection.md) · [Exact frame lists](../../configs/kitten-isolation.json) · '
        '[Every score, raw output and input hash](scores.csv) · [Run/commands](run.json) · [Validation and repeats](validation.json) · '
        '[Prior original-file follow-up](../failure-followup/report.md)','',
        'Source frames, transformed videos and weights remain local. WaveRep retains its [authors and informational/nonprofit license](../../vendor/waverep/ORIGIN.md).']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
