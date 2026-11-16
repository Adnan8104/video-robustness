# Ten review slots for 100 clips

Compare released WaveRep and the original two-level head fitted on
RA-Bench. Neither model is updated. Set aside ten manual review slots
for one test batch containing 90 real clips and ten Veo 3 clips.

Both classes come from [ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid)
at revision `c5093999e799c897c977a8699da95ebbc59cc9cb`. Require at
least four seconds and 24 fps. Use the pinned dataset's `metadata.jsonl`
with SHA-256 in the manifest. Remove paths and MSVD recording IDs used
by earlier manifests. Scan 1280 × 720 sources first. Within each
class and resolution, sort by SHA-256 of `vidrobust-review-budget-v1:`
plus the dataset path. Consider the first 64 Veo 3 metadata entries or
as many as needed to fill the quota. Require a published file checksum,
a file size at most 128 MiB, and a full decode that verifies geometry,
duration and frame count. Skip repeated recording IDs and hashes.

The initial 20 MiB cap yielded only 19 real clips. At the higher cap,
84 of the 105 remaining 720p MSVD entries passed preflight. Fill the last
six real slots from the 22 remaining 1920 × 1080 MSVD metadata entries
using the same ordering and checks. These adjustments were made before
any detector ran. Selection used no visual or score filtering.

Each clip supplies a centered four-second lossless master at
504 × 504 and 24 fps. Encode it at CRF 35 with H.264 and give
both heads the same 16 frames. Rank by descending raw margin,
using ascending source SHA-256 to break ties. Take exactly ten per
model. Report generated clips surfaced, real clips sent to review
and generated clips left outside. The trained head meets the
target only if it surfaces more generated clips in those ten slots.

The 10% generated mix is a test setting. This panel covers one
generator and one real-video collection. Six real sources have higher
native resolution. Scenes and acquisition pipelines can also differ
by label, and pretraining overlap is unknown.
