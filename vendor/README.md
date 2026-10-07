AEGIS source copied unchanged from https://github.com/MusapYildiz/ai_video_detection_benchmark
commit d86a774fd971954a023e1cd00ed7ff5b2575e0d1. MIT license in aegis/LICENSE.
Only five inference-related source files are included. Training scripts are omitted.
Our adapter constructs DINOv2 without the author's absolute-path cache, then strictly
loads the complete detector checkpoint (including backbone). No architecture change.
OpenCV fallback replaces optional Decord on macOS. The quality check permits spatial
variants below 128 pixels, since rejecting them would hide a robustness failure.

WaveRep's original license and source/author attribution are in waverep/.
The adapter in src/vidrobust/adapters/waverep.py preserves its native spatial transform
and score aggregation, with explicit sparse temporal sampling for this experiment.
No trained weights are redistributed.
