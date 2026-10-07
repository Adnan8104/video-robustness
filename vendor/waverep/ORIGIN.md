# WaveRep source and license

Original authors: Riccardo Corvi, Davide Cozzolino, Ekta Prashnani,
Shalini De Mello, Koki Nagano, Luisa Verdoliva.
“Seeing What Matters: Generalizable AI-generated Video Detection with
Forensic-Oriented Augmentation,” NeurIPS 2025.

Source: https://github.com/grip-unina/WaveRep-SyntheticVideoDetection
Pinned revision: `0fd6010759c14b572b7842a28fa9f85fe1ddd2fd`.

`src/vidrobust/adapters/waverep.py` adapts the architecture, torchvision transform and
mean-frame-logit aggregation in `demo/utils.py` and `demo/main_avideo.py`.
It disables the unnecessary backbone download (the full checkpoint supplies it),
uses strict safe checkpoint loading, CPU batches of two, and the same sparse
temporal sampling as AEGIS. It implements a strict selected-frame reader without
silent padding on decode failure. The original demo scores every frame; our
result is explicitly named `waverep-G4-sparse16`.

The original license is retained in LICENSE.md. It permits informational and
nonprofit use and requires attribution when publishing results. This adapter is
for a student research experiment; no model weights or source videos are included.
