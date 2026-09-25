# Render Script Design — Business Model Hub

Date: 2026-09-25
Status: Approved (design), pending spec review

## Goal

Build a small Python script that compiles Markdown sources in `content/` into
HTML pages in `dist/` using the existing Jinja2 templates, and copies `assets/`
into the build output.

## Context

- `templates/base.html`, `templates/article.html`, `templates/page.html` exist
  with a documented contract (`page`, `content`, `nav_active`).
- `content/index.md` uses YAML front matter (`title`) followed by Markdown.
- `assets/` holds CSS, JS and images, referenced from templates as
  `/assets/...`.
- Installed: Python 3.13 (`py` launcher), Jinja2 3.1.6, PyYAML 6.0.3.
  Not installed: any Markdown library.
- Tests use stdlib `unittest` and run via
  `py -m unittest discover -s tests`.

## Decisions (from brainstorming)

1. Compile **all** `content/**/*.md` into `dist/**/*.html` (structure preserved).
2. Convert Markdown with **Python-Markdown**, pinned in `requirements.txt`.
3. Template selection: front matter `template` field wins; otherwise the
   directory decides (`content/articles/...` → article, else page).
4. Build output is self-contained: `assets/` is copied to `dist/assets/`.

## Architecture

Single module `render.py` at the repository root. It exposes pure, testable
functions and a thin `main()` entry point. No package, no classes.

```
render.py
├── parse_front_matter(text) -> (meta: dict, body: str)
├── markdown_to_html(body) -> str
├── select_template(rel_path: Path, meta: dict) -> str
├── render_document(env, template_name, meta, body_html) -> str
├── build(content_dir, templates_dir, assets_dir, out_dir) -> list[Path]
└── main() -> None
```

`requirements.txt`:

```
markdown==3.11
```

## Function contracts

### `parse_front_matter(text)`

- Split `text` with `str.splitlines()`. If the first line stripped of trailing
  whitespace equals `---`, treat it as an opening delimiter; otherwise return
  `({}, text)` (no front matter).
- Find the next line whose stripped value equals `---` (the closing delimiter).
- Raise `ValueError` if that closing line is missing.
- Parse the lines between the delimiters by joining them with `"\n"` and
  calling `yaml.safe_load`. An empty block (`yaml.safe_load("")` → `None`)
  yields `{}`.
- Raise `ValueError` if the parsed value is neither `None` nor a mapping.
- Return `(meta, body)` where `body` is the remaining lines joined with `"\n"`
  (so the body never includes the front-matter block).

### `markdown_to_html(body)`

- Return `markdown.markdown(body, extensions=["extra"])`.

### `select_template(rel_path, meta)`

- `rel_path` is the content file path relative to `content/` (e.g.
  `index.md`, `articles/chain-of-custody.md`).
- If `meta.get("template")` is `"page"` or `"article"`, return
  `"page.html"` / `"article.html"` respectively.
- Otherwise, if the first path component is `articles`, return
  `"article.html"`; else `"page.html"`.

### `render_document(env, template_name, meta, body_html)`

- Render `env.get_template(template_name)` with:
  - `page = meta`
  - `content = body_html` (marked safe by the templates via `|safe`)
  - `nav_active = meta.get("nav_active")`
- Return the rendered string.

### `build(content_dir, templates_dir, assets_dir, out_dir)`

- Create a Jinja2 `Environment` with `FileSystemLoader(templates_dir)` and
  `select_autoescape(["html", "xml"])`.
- Iterate over `sorted(content_dir.rglob("*.md"))`.
- For each file: read UTF-8 → `parse_front_matter` → `markdown_to_html` →
  `select_template` → `render_document`.
- Output path: `out_dir / rel_path.with_suffix(".html")`; create parent dirs;
  write UTF-8.
- After rendering, copy `assets_dir` to `out_dir / "assets"` with
  `shutil.copytree(..., dirs_exist_ok=True)`.
- Return the list of written HTML paths (sorted).

### `main()`

- Call `build()` with defaults `content/`, `templates/`, `assets/`, `dist/`.
- Print each written path.

## Data flow

```
content/*.md ──parse──> (meta, body) ──markdown──> body_html
                                     └─select_template─> template
meta + body_html + nav_active ──Jinja2──> HTML ──write──> dist/**/*.html
assets/ ──copy──> dist/assets/
```

## Error handling

- Fail fast. Any exception from parsing, Markdown, Jinja2 or I/O aborts the
  build with the original traceback.
- Invalid/front-matter `template` values fall back to the directory rule.

## Testing (TDD)

New test file `tests/test_render.py` (stdlib `unittest`, imports `render`):

- `parse_front_matter`: with metadata; without delimiters; extra fields;
  empty block; unclosed `---` raises `ValueError`; non-mapping YAML raises
  `ValueError`.
- `markdown_to_html`: `# H` → `<h1>`, `**b**` → `<strong>`.
- `select_template`: explicit `page`/`article` override; `articles/` default;
  other directories → page.
- `render_document`: page template includes `title`/body; article template
  includes `<h1>` and `<time>`.
- `build`: `tempfile.TemporaryDirectory` with `index.md` and
  `articles/post.md`; assert `dist/index.html` and `dist/articles/post.html`
  exist with expected content, and `dist/assets/...` was copied.

Tests run with: `py -m unittest discover -s tests -p "test_render.py" -v`.

## Out of scope

- Watching files, incremental builds, minification, sitemap, pagination.
- Cleaning `dist/` before build.
- Changing templates or CSS.
- Deployment.

## Follow-up (not part of this script)

`content/index.md` currently ends with a copyright / CC BY / MIT / e-mail
block. Templates already render this in the shared footer, so rendering the
homepage duplicates it. Recommendation: remove that trailing block from
`content/index.md` as a separate content commit.
