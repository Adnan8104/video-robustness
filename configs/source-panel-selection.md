# Source panel: plan fixed before inference

Question: how often do the two existing detectors disagree with real/generated source
labels on additional sources, and what happens if model disagreement is left unresolved?

Twenty new clips, five per source group: real Ego4D and real YouTube-VOS via VLM4D;
generated Cosmos via VLM4D; generated Wan 2.2-14B via GovTech SynthSite. VLM4D commit
`9562dc8608cf9715f979ed0c6a5409a11b3978ca`; SynthSite commit
`2904ec01c3dbf2efba09f2cb1b7bdf17841d4d39`. The author cards identify real and generated
origins. SynthSite's True_Positive/False_Positive hazard annotations are not real/AI
labels: every SynthSite video is generated. See the pinned source cards in the manifest.

Exclude all source paths and hashes referenced by configs at project commit
`d0b0a62302bc301611166f8e2767324a6a91d00f`. Within each source directory, inspect the first
40 filenames in lexicographic order, limited to files at most 10 MiB. Download and verify
pinned tree SHA256, full-decode, and retain the first five eligible files: 4–30 seconds,
4–60 fps, at least 16 frames, shortest side at least 504 pixels, and at most 1920×1080
pixels. The common minimum side avoids WaveRep padding. Confirm photographic-style
content and annotate depicted activity from start/middle/end frames before inference.
Exclude rendered/cartoon-style or mismatched/ambiguous candidates before scoring;
record every downloaded candidate and reason. Do not replace a clip based on a score.

Use unchanged source bytes and the existing native centered four-second/16-frame
sampling. Both models receive the same decoded RGB frames and their own native
preprocessing. No model, threshold, sampling setting or input edit is tuned here.
Freeze manifest, visual notes, config and this plan before inference. Forty scores.

Fixed analysis: report every score, and at the descriptive 0.5 reference midpoint
count real-to-AI and AI-to-real errors separately for each detector and source group.
Also count agreement on AI, agreement on real and disagreement. Evaluate a fixed
three-outcome rule: report AI-like only if both scores are >=0.5, real-like only if
both are <0.5, and otherwise inconclusive. Record errors among agreed cases plus how
many clips become inconclusive. This is a tradeoff check, not a validated authenticity
verdict. Do not tune thresholds or average incomparable scores. Keep all disagreements.

This is a source-diverse convenience pilot, not a declared training holdout or a
population accuracy estimate. Real/source and AI/generator groups are confounded with
content, native encoding and camera viewpoint; original long-video/creator grouping
and detector training membership are unknown. Distinct files are not proof of
independent source footage. In particular, the Wan group is construction-themed.
We cannot attribute errors solely to generator shift or claim an overall winner.
No threshold calibration or deployment change follows from this twenty-clip panel.

Save source/weights/code hashes, frame indices, RGB/model input hashes and runtime
versions. Check the complete matrix, full decodes, pairing and score arithmetic.
Repeat representative errors/disagreements with fresh model instances. Videos,
frames and weights remain local. Publish only sources, numerical results and charts.

Visual review retained all geometry-eligible candidates. Cosmos clips depict generated
robotics scenes, with origin established by the VLM4D author card. Apparent shared
setups are recorded in `visual_cluster`: Ego4D clips 1–2 share a painting room and
3–5 share a kitchen; Wan clips 1–3 share a steel-beam construction scene. These are
repeated scene snippets, not five independent original sources within each group.
Ten downloaded YouTube-VOS candidates failed geometry/timing and remain in the audit.
