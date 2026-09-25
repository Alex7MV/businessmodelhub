---
name: NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16
url: https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16
organization: NVIDIA
params: 30B (MoE)
active_params: 3B
context_length: "up to 1M tokens"
license: OpenMDW-1.1
tasks: [text-generation]
release: "August 11, 2026"
languages: [en, es, fr, de, it, ja]
---

# NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16

Nemotron 3.5 Lightning is a general-purpose reasoning and chat model from
NVIDIA. This BF16 release is the full-precision reference checkpoint, intended
primarily as a starting point for customization and post-training rather than
direct production inference.

## Highlights

- **Hybrid architecture:** interleaves Mamba-2 and Mixture-of-Experts layers with
  select attention layers.
- **Efficient MoE:** 30B total parameters with 3B active per token.
- **Pre-training:** more than 20T tokens using an NVFP4 recipe, with Multi-Token
  Prediction (MTP) layers that predict multiple future tokens.
- **Context:** supports up to 1M tokens (256K for a single-H100 deployment).
- **Customization:** designed for SFT, RL (NeMo RL / NeMo Gym), distillation,
  domain adaptation, and producing quantized variants; an NVFP4 release targets
  deployment.
- **License:** OpenMDW License Agreement, version 1.1.
