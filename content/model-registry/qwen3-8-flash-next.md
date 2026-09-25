---
name: Qwen3.8-Flash-Next
url: https://huggingface.co/Qwen/Qwen3.8-Flash-Next
organization: Qwen
params: 125B (+51B n-gram embedding, +4B MTP)
active_params: 6B
context_length: "262,144 native, extensible to 1,000,000"
license: qwen-community-1.0
tasks: [image-text-to-text]
release: "2026"
---

# Qwen3.8-Flash-Next

Qwen3.8-Flash-Next is an experimental preview of the architecture that will
underpin Qwen4 — a fundamental rethinking of how the core components of modern
LLMs interact at scale. It is a causal language model with a vision encoder.

## Highlights

- **Hybrid attention with QSA:** the Gated DeltaNet and Gated Attention pairing is
  reworked into Gated DeltaNet and Qwen Sparse Attention (QSA), which selects at
  the micro-block level to cut long-context latency.
- **Gated Residual:** modulates information flowing through widened residual
  streams via a data-dependent read gate and a per-branch scalar write gate,
  preserving training stability with low inference overhead.
- **N-gram Embedding:** short n-grams index a large embedding table (20M
  bigrams/trigrams) for parameter scaling that is cheaper and easier to offload
  than MoE.
- **Tailored training recipe:** Muon and AdamW are applied to specific weight
  categories, with scaling-law-guided batch sizing and no batch-size warmup.
- **Scale:** 125B parameters with 6B activated, plus a 51B n-gram embedding and
  4B MTP; 262,144-token context natively, extensible to 1,000,000 tokens.
- **License:** Qwen Community License 1.0.
