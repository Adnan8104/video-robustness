# Sources and credits

The project uses released models and author code. Their original notices,
licenses and weight provenance are kept under `vendor/`. Videos and trained
weights are downloaded locally and aren't redistributed.

## Models

| Model | Authors / project | Use here | License and provenance |
|---|---|---|---|
| [AEGIS](https://huggingface.co/MusapYildiz/aegis-video-detector) | Musap Yıldız | Released detector | [MIT license](../vendor/aegis/LICENSE) |
| [WaveRep](https://github.com/grip-unina/WaveRep-SyntheticVideoDetection) | Riccardo Corvi, Davide Cozzolino, Ekta Prashnani, Shalini De Mello, Koki Nagano, Luisa Verdoliva; GRIP-UNINA | Sparse-frame inference | [Informational/nonprofit license](../vendor/waverep/LICENSE.md) |
| [AIGVDet](https://github.com/multimediaFor/AIGVDet) | Jianfa Bai, Man Lin, Gang Cao, Zijie Lou | RGB branch only, sampled frames | [Academic-only restriction](../vendor/aigvdet/LICENSE.md), [provenance](../vendor/aigvdet/ORIGIN.md) |
| [D3](https://github.com/Zig-HS/D3) | Chende Zheng and coauthors | ResNet18 temporal ranking option | [MIT license](../vendor/d3/LICENSE), [provenance](../vendor/d3/ORIGIN.md) |

D3's normalization audit also uses unchanged albucore source, with its
[MIT license](../vendor/d3/albucore_LICENSE) retained. These adaptations don't
establish performance of the full paper methods.

## Datasets

- [ComGenVid](https://huggingface.co/datasets/OmerXYZ/comgenvid): real and generated footage for the original robustness work.
- [VLM4D](https://huggingface.co/datasets/shijiezhou/VLM4D): the source panel's Ego4D and YouTube-VOS clips; inherited source rights apply.
- [GovTech SynthSite](https://huggingface.co/datasets/govtech/SynthSite): generated construction footage. All its videos are generated; hazard labels are separate from origin labels. The pinned author card and license terms are recorded in the manifests.

The source manifests record pinned versions, file hashes and selection notes.

## Wikimedia construction recordings

| Recording | Camera author | Documented date | License |
|---|---|---|---|
| [Ambérieux construction crane](https://commons.wikimedia.org/w/index.php?oldid=805766832) | Benoît Prieur | 2022-01-04 | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) |
| [Beynost sports-site crane](https://commons.wikimedia.org/w/index.php?oldid=1032231965) | Benoît Prieur | 2019-08-04 | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) |
| [Prague rail crane loading a site cabin](https://commons.wikimedia.org/w/index.php?oldid=836118434) | ŠJů, Wikimedia Commons | 2015-01-10 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

These files retain their original WebM bytes. The generated comparison uses two
Sora 2 Pro clips and one Veo 3.1 clip from the pinned SynthSite source.
