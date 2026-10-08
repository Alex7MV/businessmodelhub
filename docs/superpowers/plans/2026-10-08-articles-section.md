# Articles Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `/articles/` section for consortium long-form content, with an auto-generated index page listing articles newest first, reachable from the site nav and the homepage, served at trailing-slash URLs.

**Architecture:** `build()` becomes two-phase. Phase one calls a new `collect_articles()` which reads only front matter from `content/articles/*.md` and returns sorted metadata dicts. Phase two is the existing render loop, now using a directory-output rule (`stem == "index"` → `<dir>/index.html`, otherwise `<dir>/<stem>/index.html`) and passing the collected list into the Jinja context as `articles`. A new `articles.html` template renders the index via a loop.

**Tech Stack:** Python 3, Jinja2 3.1.6, Markdown 3.11, PyYAML 6.0.3, `unittest` (stdlib), hand-written CSS.

**Design spec:** `docs/superpowers/specs/2026-10-08-articles-section-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `render.py` | Add `collect_articles()`; add `"articles"` to `VALID_TEMPLATES`; add `articles` param to `render_document()`; change output path resolution in `build()`. |
| `templates/articles.html` | Index page: `page-head` + loop over `articles` rendering cards. |
| `templates/base.html` | Add `Articles` nav item → `/articles/`. |
| `content/articles/index.md` | The section index. Selects `template: articles`, sets `nav_active: articles`. |
| `content/articles/joule-exact-engineering.md` | Demo article so a fresh build is non-empty. |
| `content/index.md` | Homepage block linking to `/articles/`. |
| `assets/css/style.css` | `.article-list`, `.article-card`, `.article-card-meta`, `.article-tags`. |
| `tests/test_articles.py` | New: `collect_articles` behaviour + `articles.html` rendering. |
| `tests/test_render.py` | Update one path expectation; add `build()` end-to-end assertions. |
| `tests/test_base.py` | Nav contains `Articles`. |
| `tests/test_assets.py` | CSS contains `.article-card`. |

## Commands

Run everything with the `py` launcher (`python` / `python3` are broken Windows Store aliases on this machine):

```powershell
py -m unittest discover -s tests -p "test_*.py" -v
py -m unittest discover -s tests -p "test_articles.py" -v
py render.py
```

Note: `tests/` imports `render` and `template_env` as top-level modules, and `unittest discover -s tests` puts `tests/` on `sys.path`, so running discovery from the repo root works as-is. This is already the command in the `build-project` skill.

---

### Task 1: `collect_articles()` — extract and sort article metadata

**Files:**
- Modify: `render.py` (add function after `select_template`, before `render_document`)
- Create: `tests/test_articles.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_articles.py`:

```python
import tempfile
import unittest
from pathlib import Path

from render import collect_articles


class CollectArticlesTests(unittest.TestCase):
    def make_content(self, files, tmp_path):
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        for name, text in files.items():
            (articles_dir / name).write_text(text, encoding="utf-8")
        return tmp_path / "content"

    def test_extracts_all_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "post.md": "---\n"
                    "title: A Post\n"
                    "date: 2026-02-01\n"
                    "summary: Short summary.\n"
                    "tags: [methodology, verification]\n"
                    "---\n\nBody text.\n"
                },
                Path(tmp),
            )
            articles = collect_articles(content)
            self.assertEqual(
                articles,
                [
                    {
                        "url": "/articles/post/",
                        "title": "A Post",
                        "date": "2026-02-01",
                        "summary": "Short summary.",
                        "tags": ["methodology", "verification"],
                    }
                ],
            )

    def test_missing_date_summary_and_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {"bare.md": "---\ntitle: Bare\n---\n\nBody.\n"}, Path(tmp)
            )
            articles = collect_articles(content)
            self.assertEqual(articles[0]["date"], "")
            self.assertEqual(articles[0]["summary"], "")
            self.assertEqual(articles[0]["tags"], [])

    def test_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "old.md": "---\ntitle: Old\ndate: 2026-01-01\n---\nB\n",
                    "new.md": "---\ntitle: New\ndate: 2026-03-01\n---\nB\n",
                    "mid.md": "---\ntitle: Mid\ndate: 2026-02-01\n---\nB\n",
                },
                Path(tmp),
            )
            articles = collect_articles(content)
            self.assertEqual(
                [a["title"] for a in articles], ["New", "Mid", "Old"]
            )

    def test_undated_articles_sort_last_by_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "dated.md": "---\ntitle: Dated\ndate: 2026-01-01\n---\nB\n",
                    "zulu.md": "---\ntitle: Zulu\n---\nB\n",
                    "alpha.md": "---\ntitle: Alpha\n---\nB\n",
                },
                Path(tmp),
            )
            articles = collect_articles(content)
            self.assertEqual(
                [a["title"] for a in articles], ["Dated", "Alpha", "Zulu"]
            )

    def test_index_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "index.md": "---\ntitle: Articles\ntemplate: articles\n---\nIntro.\n",
                    "post.md": "---\ntitle: Post\ndate: 2026-02-01\n---\nB\n",
                },
                Path(tmp),
            )
            articles = collect_articles(content)
            self.assertEqual([a["title"] for a in articles], ["Post"])

    def test_missing_title_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {"bad.md": "---\ndate: 2026-02-01\n---\nB\n"}, Path(tmp)
            )
            with self.assertRaises(ValueError) as ctx:
                collect_articles(content)
            self.assertIn("bad.md", str(ctx.exception))

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content({}, Path(tmp))
            self.assertEqual(collect_articles(content), [])

    def test_no_articles_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp) / "content"
            content.mkdir()
            self.assertEqual(collect_articles(content), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_articles.py" -v`

Expected: import error — `ImportError: cannot import name 'collect_articles' from 'render'`.

- [ ] **Step 3: Implement `collect_articles`**

In `render.py`, add `ARTICLE_INDEX = "index.md"` next to the existing constants at the top (after `ARTICLE_DIR = "articles"`), then add this function after `select_template` (i.e. immediately before `render_document`):

```python
def _sort_articles(collected):
    """Newest dated article first; undated last, then by title."""
    dated = [item for item in collected if item["date"]]
    undated = [item for item in collected if not item["date"]]
    dated.sort(key=lambda item: item["date"], reverse=True)
    undated.sort(key=lambda item: item["title"])
    return dated + undated


def collect_articles(content_dir):
    """Article metadata from content/articles/*.md, excluding index.md.

    Returns a list of dicts: {url, title, date, summary, tags}, newest
    first. Articles without a date are placed after all dated articles,
    sorted among themselves by title ascending. An article without a title
    raises ValueError.
    """
    articles_dir = Path(content_dir) / ARTICLE_DIR
    if not articles_dir.is_dir():
        return []

    collected = []
    for source in sorted(articles_dir.glob("*.md")):
        if source.name == ARTICLE_INDEX:
            continue
        meta, _ = parse_front_matter(source.read_text(encoding="utf-8"))
        title = meta.get("title")
        if not title:
            raise ValueError(
                "article %s has no 'title' in its front matter" % source.name
            )
        collected.append(
            {
                "url": "/%s/%s/" % (ARTICLE_DIR, source.stem),
                "title": title,
                "date": meta.get("date") or "",
                "summary": meta.get("summary") or "",
                "tags": meta.get("tags") or [],
            }
        )

    return _sort_articles(collected)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_articles.py" -v`

Expected: `Ran 8 tests ... OK`.

- [ ] **Step 5: Run the full suite to confirm nothing regressed**

Run: `py -m unittest discover -s tests -p "test_*.py" -v`

Expected: all tests pass, `OK`.

- [ ] **Step 6: Commit**

```powershell
git add render.py tests/test_articles.py
git commit -m "Add collect_articles for article metadata"
```

---

### Task 2: Directory-output rule in `build()`

**Files:**
- Modify: `render.py:86-95` (the render loop in `build`)
- Modify: `tests/test_render.py:117-141` (`BuildTests`)

- [ ] **Step 1: Write the failing test**

In `tests/test_render.py`, replace the whole `BuildTests` class body with:

```python
class BuildTests(unittest.TestCase):
    def make_content(self, tmp_path):
        content = tmp_path / "content"
        (content / "articles").mkdir(parents=True)
        (content / "index.md").write_text(
            "---\ntitle: Home\n---\n# Home\n", encoding="utf-8"
        )
        (content / "articles" / "index.md").write_text(
            "---\ntitle: Articles\ntemplate: articles\n---\nIntro.\n",
            encoding="utf-8",
        )
        (content / "articles" / "post.md").write_text(
            "---\ntitle: Post\ndate: 2026-02-01\nsummary: A post.\n---\nBody\n",
            encoding="utf-8",
        )
        return content

    def test_build_pages_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = self.make_content(tmp_path)
            out = tmp_path / "dist"

            written = build(content, ROOT / "templates", ROOT / "assets", out)

            index = out / "index.html"
            articles_index = out / "articles" / "index.html"
            post = out / "articles" / "post" / "index.html"
            self.assertTrue(index.exists())
            self.assertTrue(articles_index.exists())
            self.assertTrue(post.exists())
            self.assertIn("<title>Home</title>", index.read_text(encoding="utf-8"))
            self.assertIn("<title>Post</title>", post.read_text(encoding="utf-8"))
            self.assertTrue((out / "assets" / "css" / "style.css").exists())
            self.assertEqual(
                written, sorted([index, articles_index, post])
            )

    def test_nested_page_outside_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = self.make_content(tmp_path)
            (content / "guides").mkdir()
            (content / "guides" / "start.md").write_text(
                "---\ntitle: Start\n---\nBody\n", encoding="utf-8"
            )
            out = tmp_path / "dist"

            build(content, ROOT / "templates", ROOT / "assets", out)

            self.assertTrue((out / "guides" / "start" / "index.html").exists())
```

Note: the fixture `content/articles/index.md` declares `template: articles`. Until Task 3 Step 5 registers that name in `VALID_TEMPLATES`, `select_template` treats it as invalid and falls back to `article.html` — so this test builds fine and no `articles.html` is needed yet. The stub template appears in Task 3.

- [ ] **Step 2: Run the test to verify it fails**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: `test_build_pages_and_assets` FAILS — `dist/articles/post.html` no longer exists / `dist/articles/post/index.html` missing. Assertion error on `self.assertTrue(post.exists())`.

- [ ] **Step 3: Implement the output rule**

In `render.py`, replace these two lines in `build()` (currently 92-93):

```python
        target = out_dir / rel_path.with_suffix(".html")
        target.parent.mkdir(parents=True, exist_ok=True)
```

with:

```python
        target = output_path(out_dir, rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
```

And add this helper immediately before `build()`:

```python
def output_path(out_dir, rel_path):
    """Map content/<dir>/<stem>.md to its dist index.html location.

    index.md -> <dir>/index.html; anything else -> <dir>/<stem>/index.html.
    """
    if rel_path.stem == "index":
        return out_dir / rel_path.parent / "index.html"
    return out_dir / rel_path.parent / rel_path.stem / "index.html"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: `OK`.

- [ ] **Step 5: Run the full suite**

Run: `py -m unittest discover -s tests -p "test_*.py" -v`

Expected: all pass, `OK`.

- [ ] **Step 6: Commit**

```powershell
git add render.py templates/articles.html tests/test_render.py
git commit -m "Render every page as a directory index"
```

---

### Task 3: Wire `articles` into the render context and build the index template

**Files:**
- Modify: `render.py` (`render_document` signature, `build()` call site, `VALID_TEMPLATES`)
- Modify: `templates/articles.html` (create it; it does not exist until this task)
- Create: `content/articles/index.md`
- Create: `content/articles/joule-exact-engineering.md`
- Modify: `tests/test_articles.py` (add template rendering tests)
- Modify: `tests/test_render.py` (add `articles` to the context assertions)

- [ ] **Step 1: Write the failing template test**

Append to `tests/test_articles.py`, inside the module (above the `if __name__` block). First add these imports at the top of the file, after `from render import collect_articles`:

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

from render import render_document

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"


def make_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
```

Then append this class before the `if __name__ == "__main__":` guard:

```python
class ArticlesTemplateTests(unittest.TestCase):
    def render_index(self, articles):
        return render_document(
            make_env(),
            "articles.html",
            {"title": "Articles", "description": "Long-form articles."},
            "<p>Intro.</p>",
            articles=articles,
        )

    def test_renders_card_per_article(self):
        html = self.render_index(
            [
                {
                    "url": "/articles/post/",
                    "title": "A Post",
                    "date": "2026-02-01",
                    "summary": "Short summary.",
                    "tags": ["methodology", "verification"],
                }
            ]
        )
        self.assertIn("<h1>Articles</h1>", html)
        self.assertIn('href="/articles/post/"', html)
        self.assertIn("A Post", html)
        self.assertIn("Short summary.", html)
        self.assertIn('<time datetime="2026-02-01">2026-02-01</time>', html)
        self.assertIn("methodology", html)
        self.assertIn("verification", html)

    def test_empty_list_renders_no_cards(self):
        html = self.render_index([])
        self.assertIn("<h1>Articles</h1>", html)
        self.assertIn("Intro.", html)
        self.assertNotIn("article-card", html)

    def test_article_without_date_or_summary(self):
        html = self.render_index(
            [
                {
                    "url": "/articles/bare/",
                    "title": "Bare",
                    "date": "",
                    "summary": "",
                    "tags": [],
                }
            ]
        )
        self.assertIn("Bare", html)
        self.assertNotIn("<time", html)

    def test_nav_active_articles(self):
        html = render_document(
            make_env(),
            "articles.html",
            {"title": "Articles", "nav_active": "articles"},
            "",
            articles=[],
        )
        self.assertIn('href="/articles/" class="active"', html)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `py -m unittest discover -s tests -p "test_articles.py" -v`

Expected: `TypeError: render_document() got an unexpected keyword argument 'articles'` for every test in `ArticlesTemplateTests`. The import succeeds — `collect_articles` already exists from Task 1.

- [ ] **Step 3: Add the `articles` parameter to `render_document`**

In `render.py`, replace the existing `render_document` (lines 65-71) with:

```python
def render_document(env, template_name, meta, body_html, articles=()):
    template = env.get_template(template_name)
    return template.render(
        page=meta,
        content=body_html,
        nav_active=meta.get("nav_active"),
        articles=articles,
    )
```

- [ ] **Step 4: Make `build()` two-phase**

In `render.py`, inside `build()`, add the collection pass immediately after `env` is constructed and before `written = []`:

```python
    articles = collect_articles(content_dir)

    written = []
```

Then update the `render_document` call in the render loop to pass it:

```python
        html = render_document(env, template_name, meta, body_html, articles=articles)
```

- [ ] **Step 5: Register the `articles` template name**

In `render.py`, replace `VALID_TEMPLATES` (line 8) with:

```python
VALID_TEMPLATES = {
    "page": "page.html",
    "article": "article.html",
    "articles": "articles.html",
}
```

- [ ] **Step 6: Run the tests to verify the context plumbing works**

Run: `py -m unittest discover -s tests -p "test_articles.py" -v`

Expected: `test_renders_card_per_article`, `test_empty_list_renders_no_cards` and `test_article_without_date_or_summary` still FAIL — the stub `articles.html` renders no cards. `test_nav_active_articles` still FAILS. The point of this step is that the `TypeError` is gone.

- [ ] **Step 7: Write `templates/articles.html`**

Create the file with:

```html
{% extends "base.html" %}

{% block title %}{{ page.title }} — Business Model Hub{% endblock %}
{% block description %}{{ page.description }}{% endblock %}

{% block content %}
<header class="page-head">
    <h1>{{ page.title }}</h1>
</header>

<main class="page-body">
{{ content|safe }}

{% if articles %}
<ul class="article-list">
    {% for article in articles %}
    <li class="article-card">
        <div class="article-card-meta">
            {%- if article.date %}
            <time datetime="{{ article.date }}">{{ article.date }}</time>
            {%- endif %}
        </div>
        <h2><a href="{{ article.url }}">{{ article.title }}</a></h2>
        {% if article.summary %}<p>{{ article.summary }}</p>{% endif %}
        {% if article.tags %}
        <p class="article-tags">
            {%- for tag in article.tags %}<span class="article-tag">{{ tag }}</span>{% endfor %}
        </p>
        {% endif %}
    </li>
    {% endfor %}
</ul>
{% endif %}
</main>
{% endblock %}
```

Note the `{% if articles %}` guard: an empty section must render the page without an empty `<ul>`. This satisfies the `test_empty_list_renders_no_cards` assertion that `article-card` never appears.

- [ ] **Step 8: Create `content/articles/index.md`**

```markdown
---
title: Articles
description: Long-form writing from the Business Model Hub consortium on model verification, supply-chain integrity, and architecture sovereignty.
template: articles
nav_active: articles
---

Long-form material from the consortium: verification methodology, post-mortems of upstream supply-chain events, and reviews of the architectures we validate.
```

- [ ] **Step 9: Create the demo article `content/articles/joule-exact-engineering.md`**

```markdown
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
```

- [ ] **Step 10: Add the end-to-end link assertion to `BuildTests`**

In `tests/test_render.py`, add a new test to `BuildTests`:

```python
    def test_articles_index_links_to_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = self.make_content(tmp_path)
            out = tmp_path / "dist"

            build(content, ROOT / "templates", ROOT / "assets", out)

            articles_index = (out / "articles" / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('href="/articles/post/"', articles_index)
            self.assertIn("A post.", articles_index)
            self.assertNotIn("/articles/index.html", articles_index)
```

- [ ] **Step 11: Run the tests**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: `OK` — all five build tests pass, including the new link assertion.

Run: `py -m unittest discover -s tests -p "test_articles.py" -v`

Expected: all pass except `ArticlesTemplateTests.test_nav_active_articles`, which fails because the `Articles` nav item does not exist until Task 4 Step 3. That single failure is expected and does not block this commit.

- [ ] **Step 12: Commit**

```powershell
git add render.py templates/articles.html content/articles tests/test_articles.py tests/test_render.py
git commit -m "Add articles index template and demo article"
```

---

### Task 4: Navigation, homepage link, and card styles

**Files:**
- Modify: `templates/base.html:18-25` (nav block)
- Modify: `content/index.md`
- Modify: `assets/css/style.css`
- Modify: `tests/test_base.py`, `tests/test_assets.py`

- [ ] **Step 1: Write the failing tests**

In `tests/test_base.py`, add this method to `BaseTemplateTests` (before the `if __name__ == "__main__":` guard):

```python
    def test_nav_has_articles_link(self):
        html = render("base.html")
        self.assertIn('href="/articles/"', html)

    def test_nav_active_marks_articles(self):
        html = render("base.html", nav_active="articles")
        self.assertIn('href="/articles/" class="active"', html)
```

In `tests/test_assets.py`, add this method to `AssetTests`:

```python
    def test_css_contains_article_card_styles(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".article-list", css)
        self.assertIn(".article-card", css)
        self.assertIn(".article-tags", css)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_base.py" -v` and `py -m unittest discover -s tests -p "test_assets.py" -v`

Expected: `test_nav_has_articles_link` and both card-style assertions FAIL.

- [ ] **Step 3: Add the nav item**

In `templates/base.html`, replace the `nav-links` div (lines 20-24) with:

```html
        <div class="nav-links">
            <a href="/#verification"{% if nav_active == "verification" %} class="active"{% endif %}>Verification</a>
            <a href="/#principles"{% if nav_active == "principles" %} class="active"{% endif %}>Principles</a>
            <a href="/articles/"{% if nav_active == "articles" %} class="active"{% endif %}>Articles</a>
            <a href="/#contact"{% if nav_active == "contact" %} class="active"{% endif %}>Contact</a>
        </div>
```

- [ ] **Step 4: Add the homepage link block**

In `content/index.md`, append after the `### 04 · Architecture-Specific Binary Sovereignty` paragraph:

```markdown

## Articles

Long-form material from the consortium — verification methodology, supply-chain post-mortems, and architecture reviews — lives in the [articles section](/articles/).
```

- [ ] **Step 5: Add the card styles**

Append to the end of `assets/css/style.css`:

```css

/* Articles index */
.article-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    margin-top: 2rem;
}

.article-card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 1.75rem;
    transition: border-color 0.3s ease;
}

.article-card:hover {
    border-color: #3a4d6e;
}

.article-card h2 {
    font-family: Georgia, "Times New Roman", serif;
    font-weight: 500;
    font-size: 1.1rem;
    margin: 0.25rem 0 0.75rem;
}

.article-card h2 a {
    color: #f0f4fa;
    text-decoration: none;
}

.article-card h2 a:hover {
    color: var(--accent);
}

.article-card-meta {
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
}

.article-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
}

.article-tag {
    border: 1px solid var(--border);
    padding: 0.2rem 0.6rem;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
}
```

- [ ] **Step 6: Run the full suite**

Run: `py -m unittest discover -s tests -p "test_*.py" -v`

Expected: all tests pass, `OK`. The nav test from Task 3 is now green too.

- [ ] **Step 7: Commit**

```powershell
git add templates/base.html content/index.md assets/css/style.css tests/test_base.py tests/test_assets.py
git commit -m "Link articles section from nav and homepage"
```

---

### Task 5: Full build verification

**Files:** none (verification only)

- [ ] **Step 1: Render the real site**

Run: `py render.py`

Expected output includes these paths:

```
dist\index.html
dist\articles\index.html
dist\articles\joule-exact-engineering\index.html
dist\model-registry\qwen3-8-flash-next\index.html
```

- [ ] **Step 2: Verify the on-disk layout**

Run:

```powershell
Get-ChildItem -Recurse -File dist -Filter *.html | ForEach-Object { $_.FullName.Replace((Get-Location).Path + '\dist\','') }
```

Expected: every model registry page is at `model-registry\<slug>\index.html`; no `.html` file sits directly inside `articles\`.

- [ ] **Step 3: Verify the index links resolve to real files**

Run:

```powershell
Select-String -Path dist\articles\index.html -Pattern 'href="/articles/[a-z0-9-]+/"' -AllMatches | ForEach-Object { $_.Matches.Value }
```

Expected: `href="/articles/joule-exact-engineering/"`. Then confirm `Test-Path dist\articles\joule-exact-engineering\index.html` returns `True`.

- [ ] **Step 4: Verify the article page renders its metadata**

Run:

```powershell
Select-String -Path dist\articles\joule-exact-engineering\index.html -Pattern '<time datetime=' -AllMatches
```

Expected: at least one match, `datetime="2026-10-08"`.

- [ ] **Step 5: Run the full test suite once more**

Run: `py -m unittest discover -s tests -p "test_*.py" -v`

Expected: `OK`.

- [ ] **Step 6: Confirm dist is not staged**

Run: `git status --short`

Expected: no `dist/` entries (it is git-ignored). Working tree clean apart from anything intentionally left uncommitted.