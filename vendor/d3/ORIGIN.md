# D3 author source and lightweight adaptation

Official repository: https://github.com/Zig-HS/D3
Pinned revision: `c798fbc57fe0c4198d63a73732c2c0f9e4b4816c`.
`D3_model.py`, `datasets.py`, `upstream-requirements.txt` and `LICENSE` are unchanged
copies of author files. D3 is MIT-licensed; preserve its copyright and license.

The adapter selects the documented ResNet18 option and L2 discrepancy. The main
paper uses XCLIP. The ImageNet encoder checkpoint is the official torchvision
IMAGENET1K_V1 artifact, https://download.pytorch.org/models/resnet18-f37072fd.pth
(46,830,571 bytes; SHA256 `f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec`).
It is downloaded locally, never committed. The runtime uses the project's locked
torch 2.5.1 / torchvision 0.20.1, rather than the author's newer environment.

The author reads OpenCV **BGR** images and does not convert to RGB before applying
ImageNet channel means. We preserve that ordering, even though our shared media
inputs are RGB. The adapter flips channels before the author's crop/resize/norm.
It trims 10% from both ends of the longer axis and linearly resizes to 224 square.

The author pins Albumentations 2.0.8, which uses albucore 0.0.24 for uint8
normalization. `albucore_functions.py` and `albucore_LICENSE` are unchanged copies
from https://github.com/albumentations-team/albucore/tree/0.0.24 . This MIT-licensed
source is for audit only. The adapter implements its float32 arithmetic using
existing NumPy/OpenCV. No new runtime dependency is installed.

The audit executes unchanged AST nodes for the author forward and crop functions,
and albucore's uint8 normalization LUT. Minimal dependency injection permits these
selected paths to run without Transformers or Albumentations; it does not execute
other model branches. The pretrained ResNet constructor is supplied with the same
strictly loaded local ImageNet checkpoint instead of implicitly downloading it.
Audit outputs record exact source hashes, native-input equality and raw score parity.

Temporal extraction differs: deterministic center windows and directly decoded
source frames replace upstream random-window, 8 fps JPEG extraction. A second
config checks native-like 8 fps timing. Both are explicit adaptations, not full
paper reproduction. `1/(1+temporal_std)` only maps raw real-like discrepancy to a
bounded AI-like **ranking coordinate**. No probability or decision cutoff is supplied.
