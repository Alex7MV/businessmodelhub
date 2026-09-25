---
name: DeepSeek-V4-Flash
url: https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash
organization: DeepSeek-AI
params: 284B (MoE)
active_params: 13B
context_length: "1,000,000 tokens"
license: MIT
tasks: [text-generation]
release: "2026"
---

# DeepSeek-V4-Flash

DeepSeek-V4-Flash is a Mixture-of-Experts (MoE) language model from the
DeepSeek-V4 preview series, with 284B total parameters, 13B activated per token,
and a one-million-token context window.

## Highlights

- **Hybrid attention:** combines Compressed Sparse Attention (CSA) and Heavily
  Compressed Attention (HCA) for long-context efficiency.
- **mHC:** Manifold-Constrained Hyper-Connections strengthen residual signal
  propagation across layers while preserving model expressivity.
- **Muon optimizer:** used during pre-training for faster convergence and greater
  training stability across more than 32T tokens.
- **Post-training:** a two-stage pipeline — domain experts trained with SFT and
  GRPO reinforcement learning, then consolidated via on-policy distillation.
- **Flash-Max:** a maximum reasoning-effort mode that approaches DeepSeek-V4-Pro
  reasoning performance when given a larger thinking budget.
- **License:** MIT.
