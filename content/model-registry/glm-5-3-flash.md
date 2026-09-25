---
name: GLM-5.3-Flash
url: https://huggingface.co/zai-org/GLM-5.3-Flash
organization: Z.ai (zai-org)
params: 320B (MoE)
active_params: 18B
license: MIT
tasks: [image-text-to-text]
release: "2026"
languages: [en, zh]
---

# GLM-5.3-Flash

GLM-5.3-Flash is the first natively multimodal model in the GLM-5 series. With
320B total parameters and just 18B active parameters, it outperforms GLM-5.2
across benchmarks at one-tenth the price while approaching Claude Opus 4.8 on
coding and agentic benchmarks.

## Highlights

- **Hybrid attention:** a first for the GLM series, combining sparse and linear
  attention to sharply reduce long-context serving cost while preserving precise
  long-context capability.
- **mHC:** Manifold-Constrained Hyper-Connections further improve scaling
  efficiency.
- **Multimodal pre-training:** trained on a 30T-token multimodal corpus.
- **Reasoning control:** thinking budget is controlled through `reasoning_effort`
  with `low`, `high`, and `max` levels (defaults to `max`).
- **Deployment:** supported by SGLang, vLLM, TokenSpeed, Transformers,
  KTransformers, and Unsloth.
- **License:** MIT.
