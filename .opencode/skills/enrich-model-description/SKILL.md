---
name: enrich-model-description
description: Use when a content/model-registry markdown file only has a url field or needs a fuller LLM model description, or when asked to enrich or fill in a model entry. Pulls facts from the model's Hugging Face card and writes front matter plus an overview.
---

# Enrich Model Description

Fill in or expand a model entry in `content/model-registry/`, using the model's
Hugging Face card as the source of truth.

## When to Use

- A file under `content/model-registry/` contains only `url:` or is missing a description.
- The user asks to enrich, complete, or fill in a model description.
- The Hugging Face card changed and the entry is stale.

Do not use for editing site templates, CSS, or `render.py`.

## Front Matter Schema

| Field | Notes |
|-------|-------|
| `name` | Model display name. |
| `url` | Keep the existing value from the file; never drop it. |
| `organization` | Publisher / lab. |
| `params` | Total parameters, e.g. `284B (MoE)`. |
| `active_params` | Activated per token for MoE; omit for dense models. |
| `context_length` | e.g. `262,144 tokens`; note native vs extensible. |
| `license` | SPDX id or license name. |
| `tasks` | Pipeline tasks, e.g. `[text-generation]`. |
| `release` | Release date/year if stated. |
| `languages` | Optional. |
| `library` | Optional (e.g. `mlx`). |

Body: `# <name>`, one overview paragraph, then a `## Highlights` bullet list.

## Steps

1. Read the target file and copy the existing `url`.
2. Fetch the raw card (the rendered HTML page is bloated): swap the URL to
   `https://huggingface.co/<repo>/raw/main/README.md` and fetch it. When working
   on several models, download all cards to a temp directory first, then grep
   them, so context is not flooded.
3. Extract: total and active parameters, context length, license, pipeline task,
   release date, languages, architecture, and training highlights.
4. Write the file: front matter (schema above), overview, `## Highlights`.
5. Verify with the `build-project` skill (render + tests).

## Rules

- Write in English, matching the rest of `content/`.
- Never invent values. Omit a field when the card does not state it.
- Prefer the card's YAML front matter; if `license` is absent there, check the
  repository's `LICENSE` file.
- Keep the original `url` exactly as provided.

## Common Mistakes

- Fetching the rendered HTML page instead of the raw `README.md`.
- Guessing parameters, context length, or release dates.
- Dropping the `url` field.
- Skipping the build and tests after editing.
