# Real-footage check: selection fixed before scoring

Question: do high AI-like scores recur on archived real kitchen footage, beyond the user's upload?
Select six kitchen-action clips and two music clips as a small comparison group.
This is a targeted convenience sample, not a population false-positive estimate.

Source: MSVD clips from ComGenVid commit `c5093999e799c897c977a8699da95ebbc59cc9cb`.
The original MSVD authors collected the corpus in July–September 2010:
https://www.cs.utexas.edu/~ml/clamp/videoDescription/ .
Use their recovered English captions, `AllVideoDescriptions.txt`, to identify actions.
ComGenVid labels this subset real; modern mirror encoding may differ from the original archive.
Videos remain local and are not redistributed. Cite Chen & Dolan, ACL 2011.

Exclude all MSVD source IDs referenced by project configs at commit
`a3e38f4cdf36233b77a90d637e7477911845d221`, including the prior
candidate audit. Order filenames lexicographically; at most one segment per source ID.
Require metadata duration 4–30 seconds, 4–60 fps, shortest side at least 504 pixels,
at most 1920×1080 total pixels, and file size at most 30 MiB. A 10 MiB size limit left
no eligible clips in these content groups; it was increased before downloading or scoring.
The size cap keeps the download small; the minimum side avoids WaveRep padding.

Kitchen candidates have at least three captions matching these whole words/stems:
cook/cooking/cooks, kitchen, pour/pouring/pours, chop/chopping/chops,
slice/slices/sliced/slicing, stir/stirring/stirs, peel/peeling/peels,
knead/kneading/kneads. Music candidates have at least three captions mentioning
piano or guitar and do not qualify as kitchen candidates. Take the first six kitchen
and first two music sources meeting these rules. Inspect beginning, middle and end
frames for visibly photographic content and the assigned action. Document exclusions
and take the next eligible candidate if decode or content fails; never replace by score.

Freeze source hashes, actual decoded metadata, captions and config before model inference.
Run the existing runner on unchanged source bytes and both models, then inspect the
beginning/middle/end with the same upload service used in the demo. Each window samples
16 frames over up to four seconds; short windows overlap, and identical windows are
counted once. Record source hashes, shared RGB hashes, exact indices and checkpoint hashes.
Require centered scores and input hashes to reproduce the config runner exactly.

Report every score and count real-label conflicts at the fixed reference midpoint 0.5,
separately for the middle window and for any scanned section. Do not tune a threshold,
combine scores into a verdict, or claim overall accuracy from a real-only panel.
Source-domain and pretrained training overlap are unknown; new to this project does
not mean unseen during pretraining. Timing uses nominal constant-fps frame indices.

Visual review excluded `_6OTzzK7t9Y_158_170.mp4`: its mirror footage showed piano
playing despite cooking captions. The next eligible kitchen candidate,
`cUW_bXll6YM_390_395.mp4`, showed oil being poured over tomatoes and was retained.
Music captions identified guitar/piano, but visual review found electric bass and
violin; both satisfy the broader music-performance comparison group. The vanilla
clip's captions mention several different liquids; annotation follows the visible
vanilla label. These discrepancies are recorded rather than treated as exact captions.
