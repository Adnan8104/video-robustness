# The 20-clip panel across all three edits

20 selected clips, two detectors, four conditions: **160 scores**. The sources are the same as the earlier compression panel; resize and crop are added follow-ups.

- **A real clip gained an AI-like score after resize.** For the real elephant clip, AEGIS moved from 0.000507 to 0.838585.
- **AI scores also dropped after spatial edits.** WaveRep’s AI sunset score moved from 0.989897 to 0.190008 after resize and 0.475689 after crop.
- **An edit can remove an existing high score too.** On the prepared real kitten, the 80% crop moved AEGIS from 0.999967 to 0.002365, and WaveRep from 0.732082 to 0.033672.

![Every edit compared with baseline](../reports/experiments/compression/pairs.png)

## Counts on this panel

0.5 is a fixed reference point. “Real ≥0.5” and “AI <0.5” count scores on the opposite side of that reference from the inherited label.

| Detector | Condition | Real ≥0.5 /10 | AI <0.5 /10 | Absolute changes ≥0.10 /20 | Midpoint crossings vs baseline |
|---|---|---:|---:|---:|---:|
| aegis | baseline | 1 | 0 | 0 | 0 |
| aegis | compression | 1 | 0 | 0 | 0 |
| aegis | half_resize | 2 | 0 | 1 | 1 |
| aegis | center_crop_80 | 0 | 0 | 1 | 1 |
| waverep | baseline | 1 | 4 | 0 | 0 |
| waverep | compression | 1 | 9 | 9 | 5 |
| waverep | half_resize | 0 | 6 | 8 | 3 |
| waverep | center_crop_80 | 0 | 5 | 5 | 2 |

## Why the crop results differ from the native kitten check

The earlier [kitten study](../reports/kitten-isolation/report.md) held native source frames fixed and compared a square crop with the full landscape image. The added panel crop removes 20% per dimension from an already prepared 504×504 square, then encodes it at CRF 18. These are different inputs and edits. One crop can raise a score while another lowers it.

Resize produces 252×252 inputs and crop produces 402×402 inputs. WaveRep zero-pads both to 504×504; AEGIS resizes each to 224×224. The observed response includes native preprocessing and encoding. It does not isolate a learned visual mechanism or show which detector is generally more accurate.

[Full report and scores](../reports/experiments/compression/report.md) · [Frozen config](../configs/experiments/compression.json) · [Run provenance](../reports/experiments/compression/run.json) · [Validation](../reports/experiments/compression/validation.json)
