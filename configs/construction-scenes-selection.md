# Construction scenes: fixed before scoring

Question: do the existing detector errors persist when real and generated clips
both show cranes/construction activity, with the same broad viewpoint counts?

Six new clips, three per origin. Each origin has two ground-view scenes and one
elevated-view scene, all in daylight. This is a **coarse content/viewpoint match**,
not exact real/generated scene pairs. Use all three unchanged pretrained adapters
on unchanged source bytes, centered four-second/16-frame windows. Eighteen scores.
No threshold, score averaging, sampling or model change.

## Selection

Before any new scores, inspect the Wikimedia Commons crane category and SynthSite
author card/file tree. Working budget: native landscape sources <=1920×1080,
minimum side >=504, 4–120 seconds, 4–60 fps, <=40 MiB per file. Avoid upscaling,
WaveRep padding and stock-media accounts/API keys. Prefer old, author-documented
camera recordings and exclude time-lapse. The earlier 30-second limit is widened
to 120 seconds to allow archived camera sources; each model still sees only the
centered four-second window.

Real sources selected in the reviewed crane-category order: Ambérieux tower crane
(2022), Beynost tower crane (2019), Prague rail crane/site-cabin loading (2015).
Benoît Prieur made the first two at different sites; ŠJů made the third. The authors
identify the footage as their own camera work. Original uploads predate current
video generators. Real labels follow that documented provenance, not model scores.
Commons page revision IDs and original media URLs, author credits, license links,
original-file SHA1 and downloaded-byte SHA256 are recorded. Two WebM header frame
estimates are one larger than actual decoded counts; independent OpenCV and
FFmpeg full decodes must agree on actual frame counts. No re-encoding is introduced.
Beynost has an ending black screen outside the center window; it is retained because
the pre-scoring center-window content review confirmed usable crane footage.

AI sources: first two lexicographic Sora 2 Pro clips and the first daylight Veo 3.1
clip (`veo3.1_0002`) from SynthSite commit
`2904ec01c3dbf2efba09f2cb1b7bdf17841d4d39`. `veo3.1_0001` is excluded before scoring
because it is a night scene without a real night-scene counterpart. SynthSite labels
**all** its media AI-generated; its safe/unsafe hazard labels are not origin labels.
Pinned LFS SHA256 hashes and full decodes must match. Viewpoints are assigned during
visual review, before inference.

Also record considered sources that were not scored: prefabricated-house footage
explicitly described as time-lapse, an inaccessible Pexels download, and a 4K stock
clip outside the pixel budget. These are source/content eligibility decisions,
not model-driven replacements.

Exclude every source hash referenced by configs at project commit
`e157d46c1e213a9a032f6c5ea216c83cdf91e8b7`. All six hashes are new. Review start, middle
and end frames plus the actual sampled window before committing the manifest,
config, this policy and candidate audit. No clip may be replaced after scoring.

## Fixed analysis and verification

Publish all 18 scores and both error directions at the descriptive 0.5 midpoint.
Show ground/elevated groups separately. Report all-model agreement, wrong agreement
and inconclusive counts without counting abstentions as successes. Also report the
existing two-model agreement rule for comparison. No threshold fitting or detector
promotion follows from this pilot.

Check source/model/code/config hashes, full decodes, complete three-model pairing,
shared RGB hashes and unique frame indices. Independently verify sampled presentation
timestamps with `scripts/audit_media.py`; the pre-scoring timestamp record is
`configs/construction-scenes-timing-audit.json`. Recompute summaries and error counts
independently from the CSV. Check native AIGVDet RGB parity on one real control and
one clip from each generator, then repeat representative errors, disagreements and
correct controls after fresh loads for every model. Sources and native image crops
stay local; only provenance, scores and charts are published.

## Limits

Six files cannot establish accuracy or a winner. Real footage has two creators,
AI footage two generators via one curator. The clips are new to this project,
but detector training overlap, prompt lineage and creator independence are unknown.
Ground/elevated grouping is subjective and broad; there are no exact matched
scenes. Machinery types, visible workers/loads, weather, framing, resolutions,
durations, codecs (real WebM versus AI MP4) and processing histories still differ.
Native central crops may omit the crane/activity; the check evaluates each deployed
input pipeline, not an isolated origin signal. Source and codec remain confounded
with origin. A good result would justify a larger, balanced follow-up, not an
authenticity verdict or proof that construction content caused the earlier failures.
