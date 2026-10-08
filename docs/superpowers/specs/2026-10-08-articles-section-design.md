# Articles Section — Design

**Date:** 2026-10-08
**Status:** Approved

## Purpose

Add an `/articles/` section for consortium long-form editorial content:
verification methodology, supply-chain incident write-ups, architecture
reviews. The existing model registry stays a separate section.

## Goals

- Author articles as Markdown with YAML front matter in `content/articles/`.
- Generate `/articles/` index automatically from article metadata, newest
  first — no hand-maintained list.
- Reach the section from the site nav and from the homepage.
- Serve every page at a trailing-slash URL so relative links inside an
  article (images, cross-references) resolve correctly on any static host.

## Non-goals

- No pagination, tag-filter UI, search, or RSS feed.
- No build-time validation of model-registry front matter.

## URL layout

`build()` currently maps `content/articles/post.md` to
`dist/articles/post.html`. That flat layout makes trailing-slash URLs
impossible, which in turn breaks relative links inside articles on hosts
without clean-URL rewrites. We switch to directory output.

Single rule applied in `build()`:

```
content/<dir>/<stem>.md  ->  dist/<dir>/index.html          if stem == "index"
content/<dir>/<stem>.md  ->  dist/<dir>/<stem>/index.html   otherwise
```

Resulting URLs:

| Source | Output | URL |
|---|---|---|
| `content/index.md` | `dist/index.html` | `/` |
| `content/articles/index.md` | `dist/articles/index.html` | `/articles/` |
| `content/articles/post.md` | `dist/articles/post/index.html` | `/articles/post/` |
| `content/model-registry/x.md` | `dist/model-registry/x/index.html` | `/model-registry/x/` |

No template links to a `.html` page today, so nothing breaks. `assets/` is
still copied to `dist/assets/` unchanged.

## Renderer changes (`render.py`)

### Template registry

```python
VALID_TEMPLATES = {
    "page": "page.html",
    "article": "article.html",
    "articles": "articles.html",
}
```

The index file selects its own template with `template: articles` in front
matter. `select_template` needs no change: an explicit, valid `template`
value already wins over the directory default (`render.py:55`).

### Article metadata collection

```python
def collect_articles(content_dir):
    """Article metadata from content/articles/*.md, excluding index.md.

    Returns a list of dicts: {url, title, date, summary, tags}, newest
    first. Articles without a date are placed after all dated articles,
    sorted among themselves by title ascending. An article without a title
    raises ValueError.
    """
```

Reads front matter only — bodies are never converted to HTML here, so the
call is cheap and independent of the Markdown pipeline.

- `url` is `/articles/<stem>/`, the same trailing-slash form as rule above.
- `tags` defaults to `[]` when absent or empty.
- Sorting is by `date` descending. `parse_front_matter` already disables the
  YAML timestamp resolver (`render.py:17`), so `date: 2026-01-01` arrives as
  the string `"2026-01-01"` and sorts lexicographically, which matches
  chronological order for `YYYY-MM-DD`.

### Render context

```python
def render_document(env, template_name, meta, body_html, articles=()):
```

The new parameter is optional with an immutable default, and is passed to
the template as `articles`. Every existing call site and test keeps working
unchanged. Templates always receive a real sequence, so `articles.html`
never has to test for `undefined`.

### Two-phase build

`build()` gains a first phase:

1. `articles = collect_articles(content_dir)`
2. Existing render loop, now using the directory-output rule and passing
   `articles` to `render_document`.

## Templates and content

| File | Change |
|---|---|
| `templates/articles.html` | New. Extends `base.html`; `page-head` with title and intro, then a loop over `articles`. |
| `templates/base.html` | Add `Articles` nav item pointing at `/articles/`. |
| `content/articles/index.md` | New. Front matter: `title`, `description`, `template: articles`, `nav_active: articles`. Body: one intro paragraph. |
| `content/articles/joule-exact-engineering.md` | New demo article on JEE, so the section is non-empty in a fresh build. |
| `content/index.md` | Add a block linking to `/articles/`. |
| `assets/css/style.css` | Add `.article-list`, `.article-card`, `.article-card-meta`, `.article-tags`. |

Card styling reuses `.principle` tokens (`--surface`, `--border`, the same
hover border) so the new section does not look bolted on.

### Article front matter

Minimal set, agreed scope:

```yaml
---
title: Joule-Exact Engineering
date: "2026-10-08"
summary: One-sentence description shown on the index page.
tags: [methodology, verification]
---
```

`title` is required (see error handling). `date`, `summary` and `tags` are
optional; the template guards each with `{% if %}`.

## Error handling

`build()` still fails on the first broken source file — unchanged. One new
explicit check:

- An article without `title` raises `ValueError` naming the source path.
  The slug comes from the filename while the card headline comes from
  `title`; silently substituting the filename would establish a hidden
  content convention.

Missing `date`, missing `summary`, and empty `tags` are all valid and handled
by the template.

## Testing

New `tests/test_articles.py`:

- `collect_articles` extracts `url`, `title`, `date`, `summary`, `tags`.
- Sorting puts the newer article first.
- An article without `date` lands last and does not break the build.
- `index.md` is excluded from the article list.
- An article without `title` raises `ValueError`.
- An empty `content/articles/` yields an empty list.

Template rendering of `articles.html`:

- Output contains `<time datetime="...">`, the summary, the article link,
  and the tags.

Empty-section behaviour:

- The index page renders with an empty list; the build does not fail.

`tests/test_render.py`:

- Update the `BuildTests` path expectation from `out / "articles" /
  "post.html"` to `out / "articles" / "post" / "index.html"`.
- End-to-end: `dist/articles/post/index.html` exists and
  `dist/articles/index.html` links to it; `dist/index.html` still present.
- Regression: `select_template(Path("articles/index.md"), {})` still returns
  `article.html` when no explicit template is given.

`tests/test_base.py`: `Articles` nav item is present in the rendered nav.

`tests/test_assets.py`: `style.css` contains `.article-card`.

## Implementation order

TDD, one commit per step:

1. `collect_articles` plus its tests.
2. Directory-output rule in `build()` plus updated build tests.
3. `articles.html`, `content/articles/index.md`, demo article.
4. Nav item, homepage link, CSS.
5. Full build via the `build-project` skill: install, render, test.