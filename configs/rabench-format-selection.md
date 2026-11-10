# Format-matched compression check

The native RA-Bench test had an aspect-ratio shortcut: all eight real clips
were 16:9 and none of the generated clips were. Test whether compression
still weakens detection on **new pairs** after matching the visible frame
size, frame rate and length. This is not a test of aspect ratio in isolation.

Use the same pinned [RA-Bench releases](rabench-selection.md) and select
one LTX pair and one Kling v3 pair from each of L1-01, L1-02, L1-04 and
L1-07. Eligible pairs have publicly released files with published hashes
and a real anchor marked public-cleared, with a DVIDS source recording
listed as US government public domain by the authors.

Before any scoring, visit categories in the order above and LTX before
Kling. Within a category and generator, sort anchor IDs by the SHA-256 of
`vidrobust-format-v1:` followed by the ID. Consider the first 32 eligible
metadata entries. Exclude parent anchors and DVIDS recording IDs from the
previous RA-Bench pilot and keep each new recording in one pair. Reject
reused file hashes, pairs over 24 MiB and sources that cannot satisfy the
existing common preparation requirements (landscape, shorter side at
least 504, at least four seconds and at least 24 fps). Verify hashes and
full decode counts before freezing the manifest. Record exclusions before
inference. The initial narrower subcategory search was dropped after it
could not fill the first slot; no detector scores were used.

Use one centered lossless 504 × 504 master per source, four seconds at
24 fps. Encode H.264 CRF 18 and 35 independently from it. Score the same
16 positions with AEGIS and WaveRep. Compare AI–real score ordering across
all pairs, ordering within each matched scene, and real flags and AI misses
at the unchanged 0.5 reference. No threshold fitting, training or demo
change. These are small descriptive counts; the comparisons share clips.

Matching the output format removes the exact output aspect-ratio split.
Original camera/generator artifacts can survive the normalization, and
center cropping can omit context. This test does not prove what features
a detector uses or estimate performance on arbitrary uploads.
