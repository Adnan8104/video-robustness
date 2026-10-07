# Two-detector experiment notes

Selection and analysis were frozen in `e61770c` before new model scoring. All 25
previous sources were retained, and ten fresh clips were selected by filename,
file size and deduplication from the pinned dataset listings. No scores were used
to exclude clips. All 187 paired cases completed, yielding 374 model outputs.

WaveRep was chosen after checking the official ReStraV release: no pretrained
classifier head was found there. WaveRep's released G4 weights match both the
authors' MD5 and the recorded SHA-256. The full state loads strictly without an
extra backbone download. Its native transform and mean-logit aggregation are
preserved; using 16 shared sampled frames is our explicit adaptation.

WaveRep scores the two earlier real originals low, so AEGIS's high-score judgments
do not repeat across these two pipelines. AEGIS has a fresh real-panda high-score
case (0.999992), which stays high under compression. It also scores the fresh
generated coastal-road original at 0.309382, rising above 0.98 under resize/crop.

On fresh originals, WaveRep has no source-label conflicts at the descriptive
midpoint; AEGIS has one real and one generated conflict. Under fresh edits,
WaveRep has 9/30 shifts of at least 0.10 relative to CRF 18, compared with AEGIS's
2/30. In particular, fresh generated cats score 0.958810 originally with WaveRep
and 0.000266 after CRF 35. AEGIS remains near one on that clip. Original-condition
agreement does not establish robustness under common editing operations.

Do not declare a universal winner from these counts. Native spatial preprocessing
differs, both models use DINOv2, clips are a convenience sample, labels are
inherited, and training overlap is unknown. The three high-score real-animal AEGIS
cases motivate a future content-controlled check; they do not establish an animal
or texture mechanism. Neither model is validated for deployment by this study.

See validation.json for source decoding, paired input/sampling checks, exact
AEGIS reuse, per-frame aggregation, fresh-model repeats and unit-test results.
Source-frame inspections remain local; only measured charts are published.
