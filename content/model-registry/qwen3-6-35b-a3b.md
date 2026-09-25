---
name: Qwen3.6-35B-A3B
url: https://huggingface.co/Qwen/Qwen3.6-35B-A3B
organization: Qwen
params: 35B (MoE)
active_params: 3B
context_length: "262,144 native, extensible to 1,010,000"
license: Apache-2.0
tasks: [image-text-to-text]
release: "April 2026"
---

# Qwen3.6-35B-A3B

Qwen3.6-35B-A3B is the first open-weight variant of the Qwen3.6 series: a causal
language model with a vision encoder, 35B total parameters, 3B activated per
token, and a 262,144-token native context extensible to about 1M tokens.

## Highlights

- **Agentic coding:** handles frontend workflows and repository-level reasoning
  with greater fluency and precision.
- **Thinking preservation:** retains reasoning context from historical messages,
  streamlining iterative development and reducing redundant token usage.
- **Architecture:** 40 layers in a
  `10 × (3 × (Gated DeltaNet → MoE) → 1 × (Gated Attention → MoE))` layout, with
  256 experts and 8 routed + 1 shared active per token.
- **Multimodal:** processes text, images, and video and generates text.
- **Context:** 262,144 tokens natively, extensible up to 1,010,000 tokens with
  YaRN.
- **License:** Apache-2.0.
