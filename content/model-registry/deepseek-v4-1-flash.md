---
name: DeepSeek-V4.1-Flash
url: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash
organization: DeepSeek-AI
params: 552B backbone (MoE)
active_params: 8B prefill / 16B decode
context_length: "1,000,000 tokens"
license: MIT
tasks: [image-text-to-text, text-generation]
release: "2026"
---

# DeepSeek-V4.1-Flash

DeepSeek-V4.1-Flash is a multimodal Mixture-of-Experts (MoE) model with 552B
backbone parameters and support for contexts of up to one million tokens. It
natively processes images and text and generates text autoregressively.

## Highlights

- **Causal Encoder-Decoder (CED):** a 40-layer Transformer split into a 20-layer
  causal encoder and a 20-layer decoder, activating only 8B parameters per token
  during prefill and 16B during decode.
- **KV cache compression:** Compressed Sparse Attention 2 (CSA2) with FP4 main KV
  caching reduces the global KV cache to 890 bytes per token — roughly 1/4 of
  DeepSeek-V4-Flash and about 1/8 of the persistent SWA footprint.
- **Multimodal:** a DeepSeek-ViT vision encoder with 2D-RoPE and a two-layer MLP
  projector fuse images with text from the start of language-model pre-training.
- **Scale:** trained from scratch on a 45T-token multimodal corpus, with context
  extended from 64K to 1M tokens.
- **Controllable reasoning:** a continuous reasoning-effort setting (integer
  1–100) trades inference cost for accuracy.
- **License:** MIT.
