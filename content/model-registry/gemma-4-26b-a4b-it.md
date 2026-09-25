---
name: Gemma 4 26B A4B IT
url: https://huggingface.co/google/gemma-4-26B-A4B-it
organization: Google DeepMind
params: 25.2B (MoE)
active_params: 3.8B
context_length: "256K tokens"
license: Apache-2.0 (Gemma Terms of Use)
tasks: [image-text-to-text]
release: "2026"
languages: 140+ languages (multilingual)
---

# Gemma 4 26B A4B IT

Gemma 4 26B A4B is the Mixture-of-Experts member of Google DeepMind's Gemma 4
family of open multimodal models, handling text and image input and generating
text output.

## Highlights

- **Efficient MoE:** 25.2B total parameters with only 3.8B active per token
  (8 active / 128 total experts plus 1 shared), running almost as fast as a 4B
  dense model.
- **Hybrid attention:** interleaves local sliding-window attention with global
  attention, using unified Keys/Values and Proportional RoPE (p-RoPE) on global
  layers.
- **Multimodal:** text and image input with variable aspect ratio and resolution
  support, using a ~550M-parameter vision encoder.
- **Reasoning:** designed as a capable reasoner with configurable thinking modes.
- **Context and vocabulary:** a 256K-token context window and a 262K-token
  vocabulary.
- **License:** Apache-2.0 under the Gemma Terms of Use.
