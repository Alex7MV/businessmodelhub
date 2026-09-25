---
name: GigaChat 3.5 Reasoning (432B-A28B)
url: https://huggingface.co/ai-sage/GigaChat3.5-432B-A28B-Reasoning
organization: ai-sage (GigaChat)
params: 432B (MoE)
active_params: 28B
context_length: "262,144 tokens"
license: MIT
tasks: [text-generation]
release: "2026"
languages: [ru, en]
---

# GigaChat 3.5 Reasoning

GigaChat 3.5 Reasoning is the first GigaChat model with full reasoning, trained
with online reinforcement learning. It delivers its largest gains over
GigaChat 3.5 Ultra Instruct in mathematics, code, instruction following, and
structured output.

## Highlights

- **Architecture:** a 432B Mixture-of-Experts model with 28B active parameters,
  combining Multi-head Latent Attention (MLA) with GatedDeltaNet linear-attention
  layers.
- **GatedNorm:** a learned multiplicative gate applied after RMSNorm.
- **Speculative decoding:** three Multi-Token Prediction (MTP) heads.
- **Context and precision:** up to 262K tokens; released as FP8 weights (the model
  was trained natively in FP8 at all stages).
- **Training:** six domain experts (STEM, Code, Code Agent, General Agent,
  Dialogue, Soft Skills) trained independently with online RL and CISPO, then
  combined into one release model via on-policy distillation (OPD).
- **License:** MIT.
