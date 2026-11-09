# RA-Bench cutoff pilot: fixed before inference

Ask whether a cutoff chosen on fresh footage improves on 0.5 on a separate
group, and whether it holds up after compression. Use AEGIS and WaveRep, the
two models in the demo. The pilot does not change the demo.

## Sources and split

[RA-Bench](https://github.com/Shuo-Liang-0111/RA-Bench) provides generated videos
paired to real anchors. Use the [public media release](https://huggingface.co/datasets/liangshuo0111/RA-Bench/tree/5c39eda71afe5eb7f66070f64221ea1c69dcb018)
and its [pinned main and rights tables](https://github.com/Shuo-Liang-0111/RA-Bench/tree/a979505a2703a8304fd69358b71b6988732db850/metadata).

- Use one pair per subcategory a–d in each of L1-01, L1-02, L1-04 and L1-07.
  Subcategories a/b form the cutoff group; c/d form the test group. Use LTX
  for a/c and Kling v3 for b/d. Each group has eight real and eight generated
  clips, with four from each generator.
- Require publicly released real, LTX and Kling files and a real recording
  marked public-cleared in the benchmark's rights table. Visit slots in the
  order above. Within each slot, sort eligible anchor IDs by the SHA-256 of
  `vidrobust-rabench-v1:` followed by the anchor ID, then take the first unused
  parent ID and original source URL. Keep each pair together.
- Match the media release's published file hashes and sizes, with no duplicate
  hashes or exact matches to previous project manifests. The shortlist totals
  251.3 MiB. Videos stay in the ignored data cache. The manifests retain source
  links and the real recordings' rights information.
- Before scoring, require a full decode, even dimensions, 16 distinct samples,
  and frame counts confirmed by FFmpeg and OpenCV. Independently encode the
  planned versions and verify matching geometry, counts and sampled indices.
  Presentation timestamps must stay within 2 ms of source timing after
  normalizing the start time. If a file fails, record the failure and take the
  next eligible pair in its slot before any detector runs.

Pairs control some scene differences. Real and generated videos still differ
in source pipelines, geometry, timing and visual content. This is new footage
for this project; pretrained-model training overlap is unknown.

## Choose, freeze, test

1. Encode the cutoff group as H.264 CRF 18 without spatial transforms and
   score the existing centered four-second, 16-frame window (or the available
   frames for shorter clips). For each model, consider all observed cutoff
   scores, 0.5, and an all-negative cutoff just above 1. Flag AI at score
   greater than or equal to the cutoff. Choose the most AI clips caught with
   at most one of eight real clips flagged. Break ties by fewer real flags,
   then the higher cutoff. Record a zero-catch result if no better rule fits.
2. Commit the two cutoffs and input hashes before starting test inference.
   Encode test clips independently from the same source at CRF 18 and 35.
   Reuse the same frame indices and each detector's existing preprocessing.
3. For both conditions, compare the locked cutoffs and 0.5 on real clips
   flagged and AI clips missed. Show paired errors and recoveries. Call a
   cutoff a clear improvement on this panel only if neither error count
   worsens in either condition and at least one count improves.

The budget of one real flag is an explicit pilot choice, not an estimated
population false-positive rate. Each test clip is one eighth of its class.
Do not tune on the test group, interpret scores as probabilities, or change
the demo based on this small panel.
