# Third detector comparison: fixed before inference

Keep the source-panel manifest, labels, source hashes, 20 clips, center-window indices and 0.5 reference unchanged. Add `aigvdet_rgb` through the registry. Rerun AEGIS and WaveRep, require exact parity with their published scores, and compare both error directions. No threshold tuning or removal of difficult clips.

Candidate: the released AIGVDet **RGB branch only**, a ResNet50 convolutional network. This tests a different feature extractor from the current DINOv2-based adapters, using existing CPU dependencies. It omits the full detector's optical-flow branch to keep this first comparison small. This adaptation cannot claim full AIGVDet paper performance. Native spatial preprocessing and probability averaging must match pinned upstream inference; shared temporal sampling remains 16 frames.

Promotion criterion for this regression panel: recover both shared generated-video misses (`panel_wan_04`, `panel_wan_05`) without adding real-footage errors relative to WaveRep (zero here). Report all 20 scores and the changed agreement coverage, including any newly missed generated clips. A candidate that passes still needs separately selected, content-matched confirmation footage before accepting an improvement. Failure means retaining it as an evaluated baseline, without promoting it to the default demo.

Confirm exact architecture/preprocessing/raw-logit parity using the released checkpoint and pinned author code on the two shared misses and one real control. Repeat representative source errors, model disagreements and correct controls after fresh model loads. Weights and source videos stay local.
