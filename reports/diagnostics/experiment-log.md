# Diagnostic experiment notes

Selection and analysis policy were committed as `dfcb346` before the new scores.
The four sweep cases were chosen from the preceding experiment; they are discovery
cases, not independent confirmation. Five DAVIS files were selected by filename
and size from a pinned VLM4D revision. No clip was removed after scoring.

All 49 cases completed. Nine source clips decoded fully. Frame counts, FPS,
dimensions, and the actual sampled indices passed paired checks. Twelve cases
overlapping the preceding run match both scores and encoded video hashes. Five
key cases were rescored after loading a fresh model and reproduced exactly.
Local frame inspection of the DAVIS bear at original, CRF 18, and CRF 35 confirmed
the same scene and no blank-frame decoding failure. Source frames are not published.

The original rodent-in-cage case stays near 0.98 through CRF 28, then drops at 32
and 35. The largest sampled step is 32–35. A slight 18–23 increase makes its curve
technically non-monotone; calling it a perfectly monotone response would be wrong.
The Sora case also changes direction materially. The Veo raw output falls even
while its score remains close to one, illustrating sigmoid saturation.

The DAVIS bear is a new source-labeled real case with a large compression response:
0.994 original, 0.993 CRF 18 control, and 0.237 CRF 35. Its compression-minus-control
change is −0.756. The other four DAVIS cases stay below 0.01 across all conditions.
The earlier absence of a similar large shift in 16 new ComGenVid clips therefore
does not establish that the original failure was isolated.

Both prominent real cases contain animals, but that observation is not a
content-controlled explanation. Backgrounds, source encodings, resolution, and
possible training overlap differ. Compression alone changes several statistics.
This experiment establishes a reproducible score response, not its learned cause.
