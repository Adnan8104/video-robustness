# Real-footage audit for both fixed heads

Use the [2019 YouTube UGC research dataset](https://research.google/pubs/youtube-ugc-dataset-for-video-compression-research/)
to check real footage from outside the earlier RA-Bench and ComGenVid
panels. Take 20 sports and 10 vlog clips from the published 720p VP9 VOD
release. They are already compressed before our experiment. Compare the
released WaveRep head and the original RA-Bench trained head at margin
zero with no new fit or cutoff choice.

From the public bucket listings for the two categories, take the
`_vod.webm` files up to 12 MiB with CC BY 4.0 credits in the
[upstream attribution file](https://storage.googleapis.com/ugc-dataset/ATTRIBUTION).
Sort within category by SHA-256 of `vidrobust-false-flags-v1:` plus the
object path. Preflight the first 28 sports entries and all 15 vlog
entries. Retain the first eligible entries in that order, sports first,
with one clip per credited creator across both categories. Exclude prior
file hashes, unsuitable geometry or timing, and windows not dominated by
camera footage after reviewing three frames around the center. Include
ordinary overlays and edits if the reviewed frames show camera footage.
No detector scores are used for selection. Keep media and review frames local.

Pin the storage generation, source checksums, author credits and decode
metadata in the manifest. Each source supplies the same four-second
504 × 504, 24 fps master used in the training tests. Encode CRF 18 and 35
from that master and score the same 16 frames. Report counts at both
levels, per-category counts, and which recordings cross the cutoff.

This measures false flags only. The selected camera clips are new to the
project, but the two categories are not a representative sample of all
uploads. Some videos may have had earlier processing and pretrained
encoder overlap is unknown. The two encodes of each recording are paired,
so 60 encodes do not make 60 independent recordings. No demo change.
