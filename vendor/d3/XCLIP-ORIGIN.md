# D3 X-CLIP encoder follow-up

The unchanged `D3_model.py` at D3 revision
`c798fbc57fe0c4198d63a73732c2c0f9e4b4816c` requests
`XCLIPVisionModel.from_pretrained("microsoft/xclip-base-patch16")` for its
`XCLIP-16` branch. The number 16 is the spatial patch size; the native encoder
configuration has **eight frames**. Sixteen input frames form two eight-frame
groups inside cross-frame attention. The adapter preserves this behavior and
uses the per-frame vision pooler, without X-CLIP's text head or video pooling.

Official encoder: https://huggingface.co/microsoft/xclip-base-patch16
Pinned model revision: `d6184e3fd8780d04c85d0f1eabe5f94bf44d98f6`.
`xclip-config.json` is an unchanged copy of its `config.json` (SHA256
`43d49d757dc8a3ef3dfd242d7ebe0c2effcfa0404f9343864e50c45245f99d3a`).
The official `model.safetensors` is 779,789,644 bytes; SHA256
`b5db836d57b7e22001cb2bab581719e910b4c571d926fe839b5d07bc0ba2d03e`.
It stays under ignored `models/`. Every vision tensor is loaded strictly; the
unused text, projection, prompt and integration weights remain unused.
The old export also stores a deterministic `position_ids` buffer. The adapter
checks it exactly against the generated index tensor, then omits it from strict
state loading because this library version marks that buffer nonpersistent.

X-CLIP authors: Bolin Ni, Houwen Peng, Minghao Chen, Songyang Zhang, Gaofeng Meng,
Jianlong Fu, Shiming Xiang, Haibin Ling. The official model card declares MIT;
the [Microsoft VideoX license](https://github.com/microsoft/VideoX/blob/master/LICENSE)
is retained unchanged as `xclip-LICENSE`. The Transformers implementation is a
locked package dependency, under its own Apache-2.0 license.

The adapter uses Transformers 4.57.6, a fixed patch release of the author's 4.57
series. Version 4.57.0 was yanked for setup errors. Existing torch 2.5.1 and
torchvision 0.20.1 stay fixed. No package upgrade is made to the other detectors.
The encoder config and weights are verified by hash; model creation needs no
remote code, tokenizer, external cache or pickle weight loading.

Preprocessing/discrepancy follow [the earlier D3 audit](ORIGIN.md), including its
BGR order. Direct decoded frames and deterministic windows still differ from
upstream random-window JPEG extraction. This tests the main encoder branch on
our sampling profiles; it does not reproduce the full paper benchmark.

The shared `audit_d3.py` executes the unchanged author forward and crop functions.
For X-CLIP its constructor is supplied with the library's independent local
`from_pretrained` loader. Native and adapter state tensors must be exactly equal,
as must normalized images, discrepancy outputs and saved benchmark scores.
