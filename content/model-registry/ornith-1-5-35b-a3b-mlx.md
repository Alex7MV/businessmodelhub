---
name: Ornith-1.5-35B-A3B (MLX)
url: https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-MLX
organization: Ornith AI
params: ~35B (MoE)
active_params: ~3B
context_length: "262,144 native, extensible to ~1M via YaRN"
license: MIT
tasks: [text-generation]
release: "2026"
library: mlx
---

# Ornith-1.5-35B-A3B (MLX)

Ornith-1.5-35B-A3B is the mid-size mixture-of-experts member of the Ornith-1.5
family, distributed here in Apple MLX format. It activates only ~3B parameters
per token yet significantly outperforms its similar-sized peer Qwen3.6-35B
across coding and agentic benchmarks.

## Highlights

- **Self-improvement:** Ornith-1.5 expands the self-improvement loop from scaffold
  and rollout optimization to jointly optimizing task generation, scaffold
  construction, and solution rollouts, improving the policy with reinforcement
  learning.
- **Efficient MoE:** ~35B total parameters with ~3B activated per token (roughly
  70 GB in bf16).
- **Long context:** handles up to 262,144 tokens natively; RoPE/YaRN scaling with
  factor 4.0 extends the usable window to roughly 1M tokens.
- **Format:** MLX build for Apple silicon; the reference repository is
  `ornith-ai/Ornith-1.5-35B-A3B`.
- **License:** MIT.
