---
name: Granite-4.2-30B
url: https://huggingface.co/ibm-granite/granite-4.2-30b
organization: IBM Granite Team
params: 30B (dense)
context_length: "128K native, extensible to 512K"
license: Apache-2.0
tasks: [text-generation]
release: "August 25, 2026"
languages: [en, de, es, fr, ja, pt, ar, cs, it, ko, nl, zh]
---

# Granite-4.2-30B

Granite-4.2-30B is the flagship reasoning model in IBM's Granite 4.2 family. It
is a decoder-only dense transformer (GraniteForCausalLM) with 30B parameters,
built-in `<think>...</think>` chain-of-thought, and a 512K context window.

## Highlights

- **Built-in reasoning:** native chain-of-thought that improves performance on
  math, coding, and complex multi-step problems.
- **Flexible thinking modes:** switch between full thinking (default),
  non-thinking, and low-effort modes within a single model.
- **Reasoning-augmented tool calling:** the model reasons about which tools to
  invoke and why, producing more accurate function calls.
- **Architecture:** Grouped Query Attention (GQA) with 32 attention heads and
  8 KV heads, RoPE (θ = 10,000,000), SwiGLU MLP, and RMSNorm.
- **Training:** post-trained from Granite-4.1-30B-Base through multi-stage SFT,
  multi-phase GRPO reinforcement learning, and RLHF.
- **License:** Apache-2.0.
