---
title: "Joule-Exact Engineering: What Bit-Exact Inference Actually Requires"
date: "2026-10-08"
summary: Why floating-point drift is a supply-chain problem, and what a bit-exact verification pipeline has to prove at each layer.
tags: [methodology, verification]
---

Consortium members frequently assume that inference is deterministic because the
same weights and the same prompt produce the same answer. That assumption fails
once batching, kernel selection, and reduced-precision paths enter the picture.

## Where drift enters

Drift is introduced at three boundaries: the ingestion of upstream weights, the
compilation step that lowers them to a runtime graph, and the scheduler that
batches requests at serving time. A verification pipeline that only checks the
first boundary will certify artifacts that diverge under load.

## What we require

### Ingestion integrity

Every weight shard is hashed with SHA-256 before compilation, and the hash is
attested at the point of ingest rather than after. A mismatch halts the pipeline;
there is no retry-with-warning path.

### Compilation determinism

The same source graph must produce byte-identical runtime artifacts across
repeated builds. Non-deterministic code generation is a defect, not a warning.

### Runtime reproducibility

Bit-exact token determinism is verified under fixed batch sizes and fixed seed
state. Divergence under these conditions is treated as a release blocker.

## Why this matters for regulated workloads

Quantitative analysis and financial agent workloads inherit model output directly
into downstream calculations. There, a drift of one unit in the last place is a
correctness failure, not a rounding curiosity.