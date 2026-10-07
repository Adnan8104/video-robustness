# Balanced content panel under common preparation

20 fresh sources: five clips in each real/AI × animal/non-animal cell; 80 model scores. Both detectors see identical bytes and the same 16 frames per condition. Selection and analysis were fixed before inference.

Both models give the real kitten scores above 0.5 in both conditions: AEGIS 0.999967 → 0.904924; WaveRep 0.732082 → 0.688378.

WaveRep has 4/10 generated clips below the midpoint at baseline and 9/10 after compression; 9/10 generated clips change by at least 0.10. AEGIS has 0/20 changes at least 0.10. Matching prepared geometry therefore does not remove these observed failure cases.

These observations concern a frozen convenience panel. Neither a causal animal effect nor a general detector ranking follows from them.

![Paired compression scores](compression-pairs.png)

## Descriptive results

Compression-minus-baseline changes. A conflict is a score on the opposite side of the fixed 0.5 midpoint from the inherited label; this midpoint is not a calibrated decision threshold. Values and counts apply only to these five clips per cell.

| Detector | Cell | Median signed change | Median absolute change | Changes ≥0.10 | Midpoint conflicts baseline → compressed | Midpoint crossings |
|---|---|---:|---:|---:|---:|---:|
| aegis | real_animal | -0.000002 | 0.000371 | 0/5 | 1 → 1 | 0 |
| aegis | real_non_animal | -0.000092 | 0.000092 | 0/5 | 0 → 0 | 0 |
| aegis | ai_animal | -0.000000 | 0.000005 | 0/5 | 0 → 0 | 0 |
| aegis | ai_non_animal | -0.000606 | 0.000606 | 0/5 | 0 → 0 | 0 |
| waverep | real_animal | -0.000443 | 0.000443 | 0/5 | 1 → 1 | 0 |
| waverep | real_non_animal | -0.005177 | 0.005177 | 0/5 | 0 → 0 | 0 |
| waverep | ai_animal | -0.598130 | 0.598130 | 5/5 | 2 → 5 | 3 |
| waverep | ai_non_animal | -0.431239 | 0.431239 | 4/5 | 2 → 4 | 2 |

## Every paired score

| Clip | Subject annotation | AEGIS baseline | Compressed | Change | WaveRep baseline | Compressed | Change |
|---|---|---:|---:|---:|---:|---:|---:|
| controlled_ai_animal_01 | Chimpanzee marching band | 0.999464 | 0.999620 | +0.000156 | 0.151260 | 0.000174 | -0.151086 |
| controlled_ai_animal_02 | Elephant in grassland | 0.999982 | 0.999985 | +0.000003 | 0.996280 | 0.000879 | -0.995401 |
| controlled_ai_animal_03 | Dog with people outdoors | 0.999962 | 0.997467 | -0.002496 | 0.113080 | 0.000288 | -0.112792 |
| controlled_ai_animal_04 | Labrador lying on carpet | 0.999999 | 0.999998 | -0.000000 | 0.971400 | 0.007834 | -0.963566 |
| controlled_ai_animal_05 | Bird flying above human hair | 0.999999 | 0.999994 | -0.000005 | 0.998909 | 0.400779 | -0.598130 |
| controlled_ai_non_animal_01 | People in ruined city | 0.999886 | 0.999280 | -0.000606 | 0.432082 | 0.000843 | -0.431239 |
| controlled_ai_non_animal_02 | Eggplant falling into water | 0.999938 | 0.999651 | -0.000287 | 0.999582 | 0.675879 | -0.323702 |
| controlled_ai_non_animal_03 | People walking at sunset | 0.999909 | 0.931091 | -0.068818 | 0.989897 | 0.002951 | -0.986946 |
| controlled_ai_non_animal_04 | Motorboat and human on water | 0.999884 | 0.983481 | -0.016402 | 0.983940 | 0.000974 | -0.982967 |
| controlled_ai_non_animal_05 | Warehouse workers | 0.999997 | 0.999996 | -0.000001 | 0.092674 | 0.000168 | -0.092506 |
| controlled_real_animal_01 | White kitten close-up | 0.999967 | 0.904924 | -0.095043 | 0.732082 | 0.688378 | -0.043705 |
| controlled_real_animal_02 | Elephants behind zoo fence | 0.000507 | 0.006549 | +0.006042 | 0.000581 | 0.000323 | -0.000258 |
| controlled_real_animal_03 | Tiger playing with human outdoors | 0.000094 | 0.000092 | -0.000002 | 0.001034 | 0.000591 | -0.000443 |
| controlled_real_animal_04 | Gray horse with rider | 0.000034 | 0.000038 | +0.000004 | 0.000123 | 0.000102 | -0.000021 |
| controlled_real_animal_05 | Pinto horse with rider | 0.000501 | 0.000130 | -0.000371 | 0.008413 | 0.001460 | -0.006954 |
| controlled_real_non_animal_01 | Human handling bottle outdoors | 0.000182 | 0.000090 | -0.000092 | 0.000859 | 0.000108 | -0.000751 |
| controlled_real_non_animal_02 | Colorful balls bouncing | 0.000548 | 0.000133 | -0.000415 | 0.006569 | 0.001391 | -0.005177 |
| controlled_real_non_animal_03 | Pouring oil into cooking pan | 0.000044 | 0.000085 | +0.000041 | 0.001167 | 0.000140 | -0.001028 |
| controlled_real_non_animal_04 | Human grooming face | 0.002146 | 0.000784 | -0.001362 | 0.009175 | 0.000246 | -0.008930 |
| controlled_real_non_animal_05 | Greasing baking tray | 0.000175 | 0.000200 | +0.000025 | 0.051373 | 0.009657 | -0.041715 |

## All midpoint crossings

- waverep, controlled_ai_animal_02 (ai_animal): 0.996280 → 0.000879; change -0.995401.
- waverep, controlled_ai_animal_04 (ai_animal): 0.971400 → 0.007834; change -0.963566.
- waverep, controlled_ai_animal_05 (ai_animal): 0.998909 → 0.400779; change -0.598130.
- waverep, controlled_ai_non_animal_03 (ai_non_animal): 0.989897 → 0.002951; change -0.986946.
- waverep, controlled_ai_non_animal_04 (ai_non_animal): 0.983940 → 0.000974; change -0.982967.

## Technical choices and limits

- **One real source and one generator:** pinned MSVD and Veo clips from ComGenVid. This holds source constant within each label while comparing content strata. Sora had too few native-size-eligible clips. The result is specific to this source/generator panel.
- **504×504 without upscaling:** the native shortest side is at least 504. Bicubic downscaling and a central crop supply WaveRep its native image size without zero padding. AEGIS retains its native 224-pixel resize and normalization. Cropping can favor central subjects; embedded letterboxing can remain.
- **Four seconds, 24 fps, 96 frames:** a common duration and frame grid permit identical 16-frame sampling. The centered start is snapped down to a source frame (less than one native frame); timestamps are reset to an exact output grid. Changing native FPS can drop/repeat frames. The preparation itself may remove or add detector cues; these are prepared baselines, not original-file scores.
- **Independent H.264 encodes:** CRF 18 and CRF 35 start from the same lossless FFV1 intermediate. Medium preset, yuv420p, no audio. This avoids applying the compression treatment to an already compressed baseline. FFV1 preserves the prepared pixels, not the original uncompressed camera signal.
- **Frozen manual content audit:** inspect the first ordered eligible candidates, then all 16 sampled frames of selected prepared crops. Keep five per cell before any inference. Animal means a prominent living non-human animal; humans alone and food preparations are non-animal. Ambiguous subjects/styles are excluded. Manual classification is fallible.
- **Pretrained CPU inference:** strict released checkpoints, four threads, seed 0, deterministic algorithms. WaveRep batches two frames and applies sigmoid to the mean frame logit. Its sparse sampling is a budget adaptation rather than reproduction of native all-frame evaluation.
- **Small descriptive panel:** n=5 per cell cannot establish general accuracy, a low false-positive rate, calibration, statistical significance or a mechanism involving animals/texture. Original camera quality, codec history, motion, species, backgrounds, native FPS and possible training overlap remain unmatched. Both models use DINOv2, so they are not independent evidence of every failure.

## Reproduction and evidence

`uv sync --locked` then `uv run python run.py controlled`. The command verifies hashes, downloads the 20 pinned sources and released weights, regenerates both encodes, scores both models, and rebuilds this report. Source downloads total 262.9 MiB; the two model checkpoints total about 764 MiB when absent. Temporary prepared intermediates need additional disk space; they remain ignored by Git.

After scoring, run `uv run python scripts/verify_controlled.py` to reload both models and repeat the kitten pair in both models and the WaveRep pair with the largest absolute compression change. Validation retains the exact comparison of scores, logits, branch outputs and sampled indices.

[Selection policy](../../configs/controlled-selection.md) · [Frozen manifest](../../configs/controlled.json) · [Candidate audit](../../configs/controlled-candidate-audit.json) · [All score/branch outputs](scores.csv) · [Run and preparation commands](run.json) · [Summary](summary.json) · [Validation](validation.json)

Source videos, inspected frames, intermediate media and weights are not redistributed. WaveRep attribution and its informational/nonprofit license remain in [vendor/waverep](../../vendor/waverep/ORIGIN.md). Earlier reports are unchanged.
