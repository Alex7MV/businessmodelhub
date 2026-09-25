# Jinja2 Templates Design — Business Model Hub

Date: 2026-09-25
Status: Approved (design), pending spec review

## Goal

Refactor the static `dist/index.html` into reusable Jinja2 templates so that
article pages and simple pages (Contacts, About) share one common frame
(head, nav, footer) without duplicating markup.

## Context

- Repository has no build system yet; `dist/index.html` is a single
  self-contained page.
- Content source lives in `content/` (e.g. `content/index.md`).
- Assets live in `assets/images/`.
- `dist/` is git-ignored.

## Decisions (from brainstorming)

1. Templating engine: **Jinja2** (Python).
2. CSS and JS are extracted from inline code into external assets.
3. The homepage (hero + principles grid) is rendered by `page.html`; a
   `hero` block is available for future overrides.
4. `article.html` shows title + date/author + body.

## Architecture

Template inheritance (approach A):

```
templates/base.html        # frame: <head>, <nav>, content slot, <footer>, scripts
templates/article.html     # extends base; structured article header + body
templates/page.html        # extends base; optional hero block + free-form body
assets/css/style.css       # all styles moved verbatim from dist/index.html
assets/js/main.js          # e-mail de-obfuscation IIFE moved verbatim
```

`base.html` provides the whole document skeleton. Child templates override
blocks only.

## Template contract

Context variables passed by the renderer:

| Variable      | Type   | Used by        | Purpose                                   |
|---------------|--------|----------------|-------------------------------------------|
| `page`        | object | article, page  | page metadata (see below)                 |
| `page.title`  | str    | article, page  | `<title>` and article heading             |
| `page.description` | str | article, page | meta description                          |
| `page.overline` | str  | article, page  | small uppercase label above heading       |
| `page.date`   | str (ISO) | article     | article publication date                  |
| `page.author` | str    | article        | article author                            |
| `content`     | str (safe HTML) | article, page | rendered body                 |
| `nav_active`  | str    | base           | marks active nav link                     |

## base.html

Blocks:

- `title` — default `Business Model Hub Foundation`.
- `description` — meta description (default empty).
- `head_extra` — extra `<head>` markup (default empty).
- `body_class` — class on `<body>` (default empty).
- `content` — main region between nav and footer.
- `scripts_extra` — extra scripts after `main.js` (default empty).

Structure:

- `<head>`: charset, viewport, title, description, favicon/manifest links
  normalized to `/assets/images/…`, stylesheet `/assets/css/style.css`.
- `<nav>`: logo link + Verification / Principles / Contact links; active
  link derived from `nav_active`.
- `{% block content %}`.
- `<footer>`: © 2026 Business Model Hub Foundation. line, CC BY 4.0 content
  license line, MIT runtime line, obfuscated e-mail link.
- `<script src="/assets/js/main.js" defer>` + `{% block scripts_extra %}`.

## article.html

Extends `base.html`.

- `title` block: `{{ page.title }} — Business Model Hub`.
- `content` block:
  - optional overline (`page.overline`);
  - `<h1>{{ page.title }}</h1>`;
  - meta line: author and `<time datetime="{{ page.date }}">{{ page.date }}</time>`
    separated by `·` when both present;
  - `<main class="article-body">{{ content|safe }}</main>`.
- Article body must not repeat the title.

## page.html

Extends `base.html`.

- `title` block: `{{ page.title }} — Business Model Hub`.
- `content` block:
  - `{% block hero %}{% endblock %}` (empty by default);
  - `<main class="page-body">{{ content|safe }}</main>`.
- No automatic heading: the heading is part of `content`, so `content/index.md`
  keeps its own `h1`/`h2` without duplication.

## Assets

- `assets/css/style.css`: copy of the inline `<style>` from `dist/index.html`.
  Add rules reusing existing tokens (`--muted`, `--accent`, `--border`) for:
  - `.page-head` — spacing around a page/article heading block;
  - `.article-meta` — small muted line for author/date;
  - `.article-body` / `.page-body` — readable max-width for prose text.
  Existing visual output for the homepage must remain unchanged.
- `assets/js/main.js`: the e-mail de-obfuscation IIFE from `dist/index.html`.

## Path normalization

`dist/index.html` references icons from the web root (`/favicon-32x32.png`,
etc.) while files live in `assets/images/`. Templates point to
`/assets/images/favicon-32x32.png`, `/assets/images/apple-touch-icon.png`,
`/assets/images/site.webmanifest`, etc.

## Out of scope

- Building a static site generator or render script.
- Migrating all existing content beyond `content/index.md`.
- Visual redesign; styling stays byte-identical to the current page.
- Deployment changes.

## Verification

- Render `content/index.md` via `page.html` and confirm the output matches
  `dist/index.html` visually.
- Render a sample article via `article.html` and confirm title/date/author
  and body appear once.
- Confirm `nav_active` highlights the correct link.
