# Fixed expansion sample

The manifest is frozen before expanded detector scoring. It contains 10 real MSVD
clips and 10 generated clips (five Sora, five VEO3), from the same pinned ComGenVid
revision as the initial experiment.

Selection: inspect the first 100 lexicographically ordered file entries in each
source folder. Keep files no larger than 10 MiB and take the first eligible entries
until each quota is reached. For MSVD, keep only one segment per original source
video ID (filename excluding the two trailing time fields). All selected file
hashes must be unique. The download cap keeps the experiment feasible locally;
this is a convenience sample and may favor shorter or more-compressed clips.

The original four clips remain in the panel. Sixteen clips are newly selected.
Results should distinguish the new clips from the already observed cases. No score
or predicted label is used in selection, replacement, or exclusion. Any decoding
or timing failure will be reported explicitly rather than silently dropping a clip.
The detector, frame sampling, and transformation settings remain fixed.

Before scoring, commit this manifest and policy. Use that commit as the selection
reference in the experiment log. Saved previous four-clip reports are in
reports/milestone2/; the initial experiment remains in reports/milestone1/.

Descriptive summary rule fixed before scoring: report signed and absolute score
differences versus control, and count changes of at least 0.10 score units. That
cutoff labels a sizable output change for this report; it is not a calibrated
confidence threshold, a detection operating point, or a significance test.
