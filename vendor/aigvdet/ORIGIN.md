# AIGVDet RGB branch

Bai et al., *AI-Generated Video Detection*, PRCV 2024.
Official repository: https://github.com/multimediaFor/AIGVDet
Pinned commit: `5e0d5dd7c5ecf96040608676a2965502ffed2555`.

`resnet.py` is an unchanged copy of `networks/resnet.py` for native parity auditing. SHA256: `c7e477dba329434df9ae421e32eae0552b9c2e95db769dbff1050887ca326dc7`. The adapter uses torchvision's structurally equivalent ResNet50, loads every released backbone/head parameter strictly, and checks exact outputs against this file. Author inference is in `demo.py` and `test.py` at the same commit.

Released `original.pth` is the trained RGB branch checkpoint, from the README's Google Drive folder. File ID `10EXwX9cXR0VuBmWq7QpMfotnPtIRKIsV`; 282,581,704 bytes; SHA256 `c2df6f477a590f4b24b14eac9654b868a9f178312795df20749274a502d59bdd`. The original artifact includes optimizer state; only the model is loaded.

Native transform: 448×448 center crop, RGB tensor in [0,1], ImageNet normalization. Each frame is scored with sigmoid, then those probabilities are averaged. Higher means generated. The full paper detector averages this branch with a separate optical-flow branch. **We evaluate only the RGB branch**, using the harness's shared centered 16 frames rather than all frames. Smaller inputs receive the same CenterCrop zero padding. No new parameters or thresholds are fitted.

See [the authors' academic-only restriction](LICENSE.md). No model weights or dataset videos are committed.
