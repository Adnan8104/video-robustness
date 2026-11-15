# Test the original trained head on another dataset

Use the original two-level head trained only on RA-Bench
(`reports/linear-head/fit.json`). Do not refit or choose another cutoff.
Compare it with released WaveRep on fresh clips from
[ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid), pinned to
`c5093999e799c897c977a8699da95ebbc59cc9cb`. The original training used
LTX and Kling v3; test Veo 3 and real recordings from MSVD. ComGenVid
has been used for earlier baseline studies, but this subset is new to
the project and is not used for fitting the head.

Take 12 real and 12 generated clips. Require native 1280 × 720, at
least four seconds and 24 fps or higher. The native-size requirement
holds resolution and aspect ratio fixed across classes. Sora is
outside these size requirements. Sort eligible metadata rows within
each source by SHA-256 of `vidrobust-head-transfer-v1:` plus the file path.
Consider the first 64 per source, skipping any existing paths, original
MSVD recording IDs or exact hashes from prior manifests. Keep at most one
clip per recording ID. Require a published checksum, max 20 MiB and
verified source geometry and full decode counts. No visual or score
filtering. Freeze the manifest before scoring and save media only locally.

Prepare the same 504 × 504, 24 fps, 96-frame lossless master as in
training. Start the CRF 18 and 35 encodes independently from that
master. Score the identical 16 frames with both heads, and flag at margin
zero. Report clips missed, real clips flagged, and ordering. The
predeclared target is fewer AI misses at CRF 35 without more real flags
than released WaveRep. Report all counts even if it misses that target.

This is an external dataset and generator check for the fitted head,
not a representative estimate. The real and generated scenes are not
paired, original frame rates and acquisition pipelines can differ, and
pretrained encoder training overlap is unknown. Do not update the demo.
