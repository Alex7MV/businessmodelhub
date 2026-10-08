# Registry Index and Navigation — Design

**Date:** 2026-10-08
**Status:** Approved

## Purpose

Two production-readiness gaps found in the articles-section audit:

1. Two of four nav items point at anchors that do not exist. The homepage
   contains a single `id`, `contact`; `#verification` and `#principles` resolve
   to nothing, giving 28 dead clicks across 14 pages.
2. The ten model-registry pages are built but orphaned — no link anywhere on
   the site points at `/model-registry/*`.

Both are closed by this design.

## Goals

- A registry index page at `/model-registry/` listing all ten models, reachable
  from the nav and from the homepage.
- Every nav item resolves to a real target.
- Registry cards reuse existing article-card styling; new CSS is minimal.
- Model descriptions live in explicit `summary` front matter, not derived at
  build time.

## Non-goals

- No verification status badge. See "Deliberate omissions" below.
- No filtering, search, or pagination on the registry index.
- No model-registry front-matter validation beyond what this index needs.
- No changes to the existing model detail pages.

## Navigation

Four items, all resolving:

| Item | Target | Source |
|---|---|---|
| Principles | `/#principles` | anchor on the homepage |
| Registry | `/model-registry/` | new index page |
| Articles | `/articles/` | existing |
| Contact | `/#contact` | anchor on the existing footer |

`Verification` is removed. No content on the site backs that promise, and a
nav item that cannot be honoured is worse than no item.

`nav_active` values: `registry` for the registry index, `articles` for the
articles index (existing), and nothing for the two anchor links — an anchor
does not correspond to a page.

### The `#principles` anchor

Set in `content/index.md` on the `Core Operational Principles` heading using
`attr_list` (`## Core Operational Principles of the Foundation { #principles }`).
The `extra` extension is already enabled in `render.py`, so no renderer change
is needed and the anchor stays a property of the content rather than a hardcoded
string in a template.

Verified against the rendered output: `##` headings in markdown `extra` accept
`{ #id }` and emit `<h2 id="principles">`.

## Registry index

### Collection

```python
def collect_registry(content_dir):
    """Model metadata from content/model-registry/*.md, excluding index.md.

    Returns dicts {url, name, organization, params, active_params,
    context_length, license, tasks, release, summary}, sorted by
    organization then name. Absent fields become "" or [].
    """
```

Symmetric with the existing `collect_articles`. Reads front matter only.

- `url` is `/model-registry/<stem>/`, matching the trailing-slash output rule
  in `output_path`.
- Sorting is `organization` ascending, then `name` ascending, both
  case-insensitive so `DeepSeek-AI` and `NVIDIA` interleave predictably.
- A model without `name` raises `ValueError` naming the source file, matching
  the existing behaviour in `collect_articles`.
- `index.md` in `model-registry/` is excluded.

Front matter is heterogeneous across the ten files: `params` is present in 8,
`active_params` in 4, `context_length` in 7, `languages` in 5, `library` in 1.
Every field except `name` and `organization` is therefore optional, and the
template guards each with `{% if %}`.

### Template registration

```python
VALID_TEMPLATES = {
    "page": "page.html",
    "article": "article.html",
    "articles": "articles.html",
    "registry": "registry.html",
}
```

The index file selects it via `template: registry` in front matter. Note that
`content/model-registry/*.md` without an explicit `template` currently falls
back to `page.html` (they are not under `articles/`); the index file sets it
explicitly, so detail pages are unaffected.

### Build

`build()` already calls `collect_articles` in its collection phase. Add
`collect_registry(content_dir)` beside it and pass the result to
`render_document` as `registry=`.

`render_document` gains a third optional parameter:

```python
def render_document(env, template_name, meta, body_html, articles=(), registry=()):
```

Both defaults are immutable. Every page receives both keys, so no template
needs an `is defined` check.

## Registry template

`templates/registry.html` extends `base.html` and reuses the article-index
structure: `page-head`, intro from the index file's own body, then a
`.article-list` of `.article-card` items.

Per card:

- meta line — release year, then license, both only when present
- `h2` — model `name` linking to its page
- a params line — `params`, with `active_params` appended as
  "8B active" style text when present
- `summary`
- `.article-tags` from `tasks`

Reusing `.article-card` means the registry index and the articles index look
like one system. `context_length`, `languages` and `library` stay on the detail
pages; the card would get noisy with all of them.

New CSS: exactly one rule, `.article-card-params` — `color: var(--muted)`,
`font-size: 0.85rem`, `margin-bottom: 0.75rem`. The meta and tags lines reuse
`.article-card-meta` and `.article-tag` unchanged. The params line gets its own
class rather than borrowing `.article-card-meta`'s uppercase tracking, which
would render values like `552B backbone (MoE)` in the wrong style.

## Content

Add a one-sentence `summary` to each of the ten model files, taken from the
lead paragraph already present in each file's body. This is deliberate content
work, not derivation at build time: a card summary derived by parsing the first
paragraph breaks silently the moment someone edits that paragraph.

`summary` values must be quoted where they contain a colon, matching the rule
already noted for `title` in the SelfCheck article.

## Deliberate omissions

**No verification badge.** The homepage states that a model "enters the
verified BMH registry" after passing the test suite, but no field in any
registry file records whether verification happened. Rendering a `Verified`
badge would assert work that the data does not contain. If verification is
actually performed, a `verified: true` field should be added explicitly and
the badge derived from it — that is a content and process question, not a
rendering one.

**No 404 page, sitemap, or robots.txt.** Raised during the readiness audit,
deferred: not required for the site to function.

**No mobile nav.** `.nav-links` is hidden below 600px, so mobile visitors have
only the logo. Pre-existing and unchanged by this design.

## Testing

New `tests/test_registry.py`:

- `collect_registry` extracts every field correctly
- sorting is by organization, then name
- absent optional fields yield `""` / `[]` and do not raise
- `index.md` is excluded from the list
- a model without `name` raises `ValueError`
- an empty or missing `model-registry/` directory returns `[]`

Template rendering:

- `registry.html` renders a card per model with its link, release year,
  license, params, summary, and tasks
- an empty list renders the page with no cards and no `article-card` markup
- `nav_active: registry` marks the Registry nav link

`tests/test_render.py`:

- `build()` writes `dist/model-registry/index.html`
- that index links to every built model page
- the homepage contains `id="principles"` in the rendered output

`tests/test_base.py`:

- nav contains exactly `Principles`, `Registry`, `Articles`, `Contact`
- `Verification` is gone
- all four hrefs are the intended targets

## Implementation order

TDD, one commit per step:

1. `collect_registry` plus its tests.
2. `registry` in `VALID_TEMPLATES`, `render_document` parameter, `build()`
   wiring plus tests.
3. `content/model-registry/index.md` and `templates/registry.html`.
4. `summary` in the ten model files.
5. Nav rewrite in `templates/base.html` and the `#principles` anchor in
   `content/index.md`.
6. Full build via the `build-project` skill.