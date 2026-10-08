# Registry Index and Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/model-registry/` index page listing all ten models, and make every nav item resolve to a real target.

**Architecture:** A new `collect_registry(content_dir)` in `render.py` reads model front matter, mirroring the existing `collect_articles`. `build()` calls it in the same collection phase and passes the result to `render_document` as `registry`. A new `registry.html` template renders cards that reuse the existing `.article-card` classes, so the registry index and articles index read as one system. Navigation collapses from four items to four live ones, with the `#principles` anchor supplied by `attr_list` in the homepage content.

**Tech Stack:** Python 3, Jinja2 3.1.6, Markdown 3.11 (`extra` — supplies `attr_list` and `fenced_code`), PyYAML 6.0.3, `unittest`, hand-written CSS.

**Design spec:** `docs/superpowers/specs/2026-10-08-registry-index-and-nav-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `render.py` | Add `collect_registry()`, `registry` template name, `registry` parameter on `render_document()`, wiring in `build()`. |
| `templates/registry.html` | Registry index page: card per model. |
| `templates/base.html` | Rewrite nav to four live items. |
| `content/model-registry/index.md` | The registry index; selects `template: registry`. |
| `content/model-registry/*.md` (10 files) | Gain a `summary` field. |
| `content/index.md` | `#principles` anchor on the principles heading. |
| `assets/css/style.css` | `.article-card-meta` flex row; new `.article-card-params`. |
| `tests/test_registry.py` | New: `collect_registry` behaviour + `registry.html` rendering. |
| `tests/test_base.py` | Nav has exactly four items with intended targets. |
| `tests/test_render.py` | `build()` writes the registry index; homepage has `id="principles"`. |
| `tests/test_assets.py` | CSS contains `.article-card-params`. |

## Commands

Use the `py` launcher — `python` and `python3` are broken Windows Store aliases on this machine.

```powershell
py -m unittest discover -s tests -p "test_*.py"
py -m unittest discover -s tests -p "test_registry.py" -v
py render.py
```

## Known data inconsistencies — do not "fix" these

- `release` is not uniform: seven models carry `"2026"`, three carry full dates
  (`"August 25, 2026"`, `"August 11, 2026"`, `"April 2026"`). The card renders
  the value verbatim; normalising it is a separate content decision.
- Front matter coverage across the ten files, counted exactly: `params` 10,
  `active_params` 9, `context_length` 9, `languages` 5, `library` 1. So every
  card always has a params line; `granite-4-2-30b` is the one model with no
  `active_params` (it is dense), and `glm-5-3-flash` the one with no
  `context_length`. Everything except `name`, `organization`, `params`,
  `license`, `release` and `tasks` is optional.
- `context_length`, `languages` and `library` are deliberately not collected for
  cards — they stay on the detail pages so cards do not get noisy.

---

### Task 1: `collect_registry()` — collect and sort model metadata

**Files:**
- Modify: `render.py` (add `REGISTRY_DIR` constant; add `collect_registry` after `collect_articles`)
- Create: `tests/test_registry.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_registry.py`:

```python
import tempfile
import unittest
from pathlib import Path

from render import collect_registry


class CollectRegistryTests(unittest.TestCase):
    def make_content(self, files, tmp_path):
        registry_dir = tmp_path / "content" / "model-registry"
        registry_dir.mkdir(parents=True)
        for name, text in files.items():
            (registry_dir / name).write_text(text, encoding="utf-8")
        return tmp_path / "content"

    def test_extracts_all_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "model.md": "---\n"
                    "name: Test Model\n"
                    "organization: Test Org\n"
                    "params: 70B (MoE)\n"
                    "active_params: 3B\n"
                    "context_length: \"128K tokens\"\n"
                    "license: MIT\n"
                    "tasks: [text-generation]\n"
                    "release: \"2026\"\n"
                    "summary: A test model.\n"
                    "---\n\nBody.\n"
                },
                Path(tmp),
            )
            self.assertEqual(
                collect_registry(content),
                [
                    {
                        "url": "/model-registry/model/",
                        "name": "Test Model",
                        "organization": "Test Org",
                        "params": "70B (MoE)",
                        "active_params": "3B",
                        "context_length": "128K tokens",
                        "license": "MIT",
                        "tasks": ["text-generation"],
                        "release": "2026",
                        "summary": "A test model.",
                    }
                ],
            )

    def test_absent_optional_fields_become_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {"bare.md": "---\nname: Bare\norganization: Org\n---\nBody\n"},
                Path(tmp),
            )
            model = collect_registry(content)[0]
            self.assertEqual(model["params"], "")
            self.assertEqual(model["active_params"], "")
            self.assertEqual(model["summary"], "")
            self.assertEqual(model["tasks"], [])
            self.assertEqual(model["release"], "")

    def test_sorted_by_organization_then_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "a.md": "---\nname: Zed\norganization: Alpha\n---\nB\n",
                    "b.md": "---\nname: Beta\norganization: alpha\n---\nB\n",
                    "c.md": "---\nname: Aaa\norganization: alpha\n---\nB\n",
                },
                Path(tmp),
            )
            order = [(m["organization"], m["name"]) for m in collect_registry(content)]
            self.assertEqual(
                order, [("alpha", "Aaa"), ("alpha", "Beta"), ("Alpha", "Zed")]
            )

    def test_index_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "index.md": "---\nname: Registry\ntemplate: registry\n---\nIntro.\n",
                    "model.md": "---\nname: Model\norganization: Org\n---\nB\n",
                },
                Path(tmp),
            )
            self.assertEqual(
                [m["name"] for m in collect_registry(content)], ["Model"]
            )

    def test_missing_name_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {"bad.md": "---\norganization: Org\n---\nB\n"}, Path(tmp)
            )
            with self.assertRaises(ValueError) as ctx:
                collect_registry(content)
            self.assertIn("bad.md", str(ctx.exception))

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content({}, Path(tmp))
            self.assertEqual(collect_registry(content), [])

    def test_no_registry_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp) / "content"
            content.mkdir()
            self.assertEqual(collect_registry(content), [])


if __name__ == "__main__":
    unittest.main()
```

Note `test_sorted_by_organization_then_name` pins case-insensitive ordering:
`alpha` and `Alpha` must interleave by name, so the sort key lowercases the
organization before comparing.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_registry.py" -v`

Expected: `ImportError: cannot import name 'collect_registry' from 'render'`.

- [ ] **Step 3: Implement `collect_registry`**

In `render.py`, add the constant beside `ARTICLE_INDEX`:

```python
ARTICLE_DIR = "articles"
ARTICLE_INDEX = "index.md"
REGISTRY_DIR = "model-registry"
```

Then insert this immediately after `collect_articles` (before `render_document`):

```python
def collect_registry(content_dir):
    """Model metadata from content/model-registry/*.md, excluding index.md.

    Returns a list of dicts with keys url, name, organization, params,
    active_params, context_length, license, tasks, release and summary,
    sorted by organization then name, both case-insensitive. Absent
    fields become "" or []. A model without a name raises ValueError.
    """
    registry_dir = Path(content_dir) / REGISTRY_DIR
    if not registry_dir.is_dir():
        return []

    collected = []
    for source in sorted(registry_dir.glob("*.md")):
        if source.name == ARTICLE_INDEX:
            continue
        meta, _ = parse_front_matter(source.read_text(encoding="utf-8"))
        name = meta.get("name")
        if not name:
            raise ValueError(
                "model %s has no 'name' in its front matter" % source.name
            )
        collected.append(
            {
                "url": "/%s/%s/" % (REGISTRY_DIR, source.stem),
                "name": name,
                "organization": meta.get("organization") or "",
                "params": meta.get("params") or "",
                "active_params": meta.get("active_params") or "",
                "context_length": meta.get("context_length") or "",
                "license": meta.get("license") or "",
                "tasks": meta.get("tasks") or [],
                "release": meta.get("release") or "",
                "summary": meta.get("summary") or "",
            }
        )

    collected.sort(
        key=lambda item: (item["organization"].lower(), item["name"].lower())
    )
    return collected
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_registry.py" -v`

Expected: `Ran 7 tests ... OK`.

- [ ] **Step 5: Run the full suite**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: all pass, `OK`.

- [ ] **Step 6: Commit**

```powershell
git add render.py tests/test_registry.py
git commit -m "Add collect_registry for model metadata"
```

---

### Task 2: Wire `registry` into the render context and `build()`

**Files:**
- Modify: `render.py` (`VALID_TEMPLATES`, `render_document`, `build`)
- Modify: `tests/test_render.py` (new `BuildTests` test)

- [ ] **Step 1: Write the failing test**

Add this method to `BuildTests` in `tests/test_render.py`:

```python
    def test_registry_index_links_to_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = self.make_content(tmp_path)
            registry = content / "model-registry"
            registry.mkdir()
            (registry / "index.md").write_text(
                "---\ntitle: Registry\ntemplate: registry\n---\nIntro.\n",
                encoding="utf-8",
            )
            (registry / "alpha.md").write_text(
                "---\nname: Alpha\norganization: Org\n"
                "release: \"2026\"\nsummary: The alpha model.\n---\nBody\n",
                encoding="utf-8",
            )
            out = tmp_path / "dist"

            build(content, ROOT / "templates", ROOT / "assets", out)

            index = (out / "model-registry" / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('href="/model-registry/alpha/"', index)
            self.assertIn("Alpha", index)
            self.assertIn("The alpha model.", index)
            self.assertTrue((out / "model-registry" / "alpha" / "index.html").exists())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: FAIL. `template: registry` is not a known template name yet, so the
index falls back to `page.html`, renders no cards, and the
`href="/model-registry/alpha/"` assertion fails.

- [ ] **Step 3: Register the template name**

In `render.py`, replace `VALID_TEMPLATES`:

```python
VALID_TEMPLATES = {
    "page": "page.html",
    "article": "article.html",
    "articles": "articles.html",
    "registry": "registry.html",
}
```

- [ ] **Step 4: Add the `registry` parameter**

Replace `render_document`:

```python
def render_document(env, template_name, meta, body_html, articles=(), registry=()):
    template = env.get_template(template_name)
    return template.render(
        page=meta,
        content=body_html,
        nav_active=meta.get("nav_active"),
        articles=articles,
        registry=registry,
    )
```

- [ ] **Step 5: Collect registry data in `build()`**

Replace the collection phase in `build()`:

```python
    articles = collect_articles(content_dir)
    registry = collect_registry(content_dir)

    written = []
```

And update the render call:

```python
        html = render_document(
            env, template_name, meta, body_html, articles=articles, registry=registry
        )
```

- [ ] **Step 6: Run the test to verify the plumbing works**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: FAIL with `TemplateNotFound: 'registry.html'` — the context plumbing is
in place but the template does not exist yet. That is the expected state.

- [ ] **Step 7: Create a minimal `templates/registry.html` so the task ends green**

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
</main>
{% endblock %}
```

Task 3 replaces this with the card version.

- [ ] **Step 8: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: the Task 2 test now fails on `self.assertIn('href="/model-registry/alpha/"', index)` —
the stub renders no cards. Every other test passes.

- [ ] **Step 9: Commit**

```powershell
git add render.py templates/registry.html tests/test_render.py
git commit -m "Wire registry data into the render context"
```

---

### Task 3: The registry index template and content

**Files:**
- Modify: `templates/registry.html` (replace the stub)
- Create: `content/model-registry/index.md`
- Create: `tests/test_registry.py` (add `RegistryTemplateTests`)

- [ ] **Step 1: Write the failing template tests**

Add to `tests/test_registry.py`, directly above the existing
`if __name__ == "__main__":` guard. First extend the imports at the top of the
file to read:

```python
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from render import collect_registry, render_document

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"


def make_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
```

Then add this class:

```python
class RegistryTemplateTests(unittest.TestCase):
    def make_model(self, **overrides):
        model = {
            "url": "/model-registry/alpha/",
            "name": "Alpha",
            "organization": "Test Org",
            "params": "70B (MoE)",
            "active_params": "3B",
            "context_length": "128K tokens",
            "license": "MIT",
            "tasks": ["text-generation"],
            "release": "2026",
            "summary": "A test model.",
        }
        model.update(overrides)
        return model

    def render_index(self, models):
        return render_document(
            make_env(),
            "registry.html",
            {"title": "Registry", "description": "Verified models."},
            "<p>Intro.</p>",
            registry=models,
        )

    def test_renders_card_per_model(self):
        html = self.render_index([self.make_model()])
        self.assertIn("<h1>Registry</h1>", html)
        self.assertIn('href="/model-registry/alpha/"', html)
        self.assertIn("Alpha", html)
        self.assertIn("Test Org", html)
        self.assertIn("70B (MoE)", html)
        self.assertIn("3B", html)
        self.assertIn("MIT", html)
        self.assertIn("2026", html)
        self.assertIn("A test model.", html)
        self.assertIn("text-generation", html)

    def test_empty_list_renders_no_cards(self):
        html = self.render_index([])
        self.assertIn("<h1>Registry</h1>", html)
        self.assertIn("Intro.", html)
        self.assertNotIn("article-card", html)

    def test_model_without_optional_fields(self):
        html = self.render_index(
            [self.make_model(params="", active_params="", summary="", tasks=[], license="")]
        )
        self.assertIn("Alpha", html)
        self.assertNotIn("article-card-params", html)
        self.assertNotIn("article-tags", html)

    def test_nav_active_registry(self):
        html = render_document(
            make_env(),
            "registry.html",
            {"title": "Registry", "nav_active": "registry"},
            "",
            registry=[],
        )
        self.assertIn('href="/model-registry/" class="active"', html)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_registry.py" -v`

Expected: the four `RegistryTemplateTests` fail against the stub — no card
markup, no params line. `test_nav_active_registry` also fails because the nav
has no Registry item until Task 5.

- [ ] **Step 3: Write the real `templates/registry.html`**

Replace the stub with:

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

{% if registry %}
<ul class="article-list">
    {% for model in registry %}
    <li class="article-card">
        {% if model.organization or model.release or model.license %}
        <div class="article-card-meta">
            {%- if model.organization %}<span>{{ model.organization }}</span>{% endif %}
            {%- if model.release %}<span>{{ model.release }}</span>{% endif %}
            {%- if model.license %}<span>{{ model.license }}</span>{% endif %}
        </div>
        {% endif %}
        <h2><a href="{{ model.url }}">{{ model.name }}</a></h2>
        {% if model.params %}
        <p class="article-card-params">
            {{ model.params }}{% if model.active_params %} &middot; {{ model.active_params }} active{% endif %}
        </p>
        {% endif %}
        {% if model.summary %}<p>{{ model.summary }}</p>{% endif %}
        {% if model.tasks %}
        <p class="article-tags">
            {%- for task in model.tasks %}<span class="article-tag">{{ task }}</span>{% endfor %}
        </p>
        {% endif %}
    </li>
    {% endfor %}
</ul>
{% endif %}
</main>
{% endblock %}
```

- [ ] **Step 4: Create `content/model-registry/index.md`**

```markdown
---
title: Model Registry
description: Upstream open-weight models tracked by the Business Model Hub consortium, with architecture, scale, and licensing details.
template: registry
nav_active: registry
---

Every model in this catalog was ingested from its upstream repository with an
attested SHA-256 digest. Figures below are taken from the upstream model card.
```

- [ ] **Step 5: Run the tests**

Run: `py -m unittest discover -s tests -p "test_registry.py" -v`

Expected: `test_renders_card_per_article`, `test_empty_list_renders_no_cards` and
`test_model_without_optional_fields` pass. `test_nav_active_registry` still fails
until Task 5.

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: `OK` — including the Task 2 build test, which now has a real template.

- [ ] **Step 6: Commit**

```powershell
git add templates/registry.html content/model-registry/index.md tests/test_registry.py
git commit -m "Add model registry index template"
```

---

### Task 4: Card styles and the ten `summary` fields

**Files:**
- Modify: `assets/css/style.css` (`.article-card-meta`, new `.article-card-params`)
- Modify: `tests/test_assets.py`
- Modify: `content/model-registry/*.md` (10 files)

- [ ] **Step 1: Write the failing test**

Add this method to `AssetTests` in `tests/test_assets.py`:

```python
    def test_css_contains_registry_card_styles(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".article-card-params", css)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `py -m unittest discover -s tests -p "test_assets.py" -v`

Expected: FAIL — `.article-card-params` is not in the stylesheet.

- [ ] **Step 3: Add the styles**

In `assets/css/style.css`, replace the existing `.article-card-meta` rule:

```css
.article-card-meta {
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
}
```

The flex row lets the card carry three meta values — organization, release,
license — without separator markup. The articles index has a single `<time>` in
this line, so it renders identically.

Then append after the `.article-tag` rule:

```css
.article-card-params {
    color: var(--muted);
    font-size: 0.85rem;
    margin-bottom: 0.75rem;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `py -m unittest discover -s tests -p "test_assets.py" -v`

Expected: `OK`.

- [ ] **Step 5: Add `summary` to the ten model files**

Each edit inserts a single `summary:` line directly after the `url:` line in that
file's front matter. Every value is quoted, since most contain a colon.

`content/model-registry/deepseek-v4-1-flash.md`:

```yaml
summary: "Multimodal Mixture-of-Experts model with a 552B backbone and a one-million-token context window; processes images and text natively."
```

`content/model-registry/deepseek-v4-flash.md`:

```yaml
summary: "Mixture-of-Experts language model from the DeepSeek-V4 preview series: 284B total parameters, 13B activated per token, one-million-token context."
```

`content/model-registry/gemma-4-26b-a4b-it.md`:

```yaml
summary: "Mixture-of-Experts member of Google's Gemma 4 family of open multimodal models, handling text and image input and generating text."
```

`content/model-registry/gigachat3-5-432b-a28b-reasoning.md`:

```yaml
summary: "First GigaChat model with full reasoning, trained with online reinforcement learning; largest gains in mathematics, code, and structured output."
```

`content/model-registry/glm-5-3-flash.md`:

```yaml
summary: "First natively multimodal model in the GLM-5 series: 320B total parameters with 18B active, at one-tenth the price of GLM-5.2."
```

`content/model-registry/granite-4-2-30b.md`:

```yaml
summary: "IBM's flagship Granite 4.2 reasoning model: a decoder-only dense transformer with 30B parameters, built-in chain-of-thought, and a 512K context window."
```

`content/model-registry/nvidia-nemotron-3-5-lightning-30b-a3b.md`:

```yaml
summary: "General-purpose reasoning and chat model from NVIDIA; this BF16 release is the full-precision reference checkpoint intended for customization and post-training."
```

`content/model-registry/ornith-1-5-35b-a3b-mlx.md`:

```yaml
summary: "Mid-size Mixture-of-Experts member of the Ornith-1.5 family in Apple MLX format, activating roughly 3B parameters per token."
```

`content/model-registry/qwen3-6-35b-a3b.md`:

```yaml
summary: "First open-weight variant of the Qwen3.6 series: a causal language model with a vision encoder, 35B total parameters, and a 262,144-token context extensible to about 1M."
```

`content/model-registry/qwen3-8-flash-next.md`:

```yaml
summary: "Experimental preview of the architecture that will underpin Qwen4, a rethinking of how the core components of modern LLMs interact at scale."
```

Every summary is a compression of the lead paragraph already in that file. None
introduces a claim absent from the existing body text.

- [ ] **Step 6: Verify the front matter still parses**

Run: `py render.py`

Expected: no exception, and `dist\model-registry\` contains an `index.html`
directory entry alongside the ten model directories. A malformed `summary` would
raise from `yaml.load` here.

- [ ] **Step 7: Run the full suite**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: all pass except `test_nav_active_registry` (still pending Task 5).

- [ ] **Step 8: Commit**

```powershell
git add assets/css/style.css tests/test_assets.py content/model-registry
git commit -m "Add model card styles and registry summaries"
```

---

### Task 5: Navigation rewrite and the `#principles` anchor

**Files:**
- Modify: `templates/base.html` (nav block)
- Modify: `content/index.md` (anchor on the principles heading)
- Modify: `tests/test_base.py`
- Modify: `tests/test_render.py` (anchor assertion)

- [ ] **Step 1: Write the failing tests**

In `tests/test_base.py`, replace the two nav tests added earlier
(`test_nav_has_articles_link`, `test_nav_active_marks_articles`) and add the
rest, so the whole nav block reads:

```python
    def test_nav_links(self):
        html = render("base.html")
        for href in ("/#principles", "/model-registry/", "/articles/", "/#contact"):
            self.assertIn('href="%s"' % href, html)

    def test_nav_has_no_dead_verification_link(self):
        html = render("base.html")
        self.assertNotIn("/#verification", html)

    def test_footer_license_lines(self):
        html = render("base.html")
        self.assertIn("CC BY 4.0", html)
        self.assertIn("MIT License", html)

    def test_asset_links(self):
        html = render("base.html")
        self.assertIn('href="/assets/css/style.css"', html)
        self.assertIn('src="/assets/js/main.js"', html)

    def test_nav_active_marks_link(self):
        html = render("base.html", nav_active="principles")
        self.assertIn('href="/#principles" class="active"', html)

    def test_nav_active_marks_registry(self):
        html = render("base.html", nav_active="registry")
        self.assertIn('href="/model-registry/" class="active"', html)

    def test_nav_active_marks_articles(self):
        html = render("base.html", nav_active="articles")
        self.assertIn('href="/articles/" class="active"', html)
```

Note `test_nav_has_no_dead_verification_link` uses `/#contact` and
`/#principles` as live targets while asserting the removed `/#verification`
target is gone.

Add this test to `tests/test_render.py`, in the existing `MarkdownTests` class:

```python
    def test_homepage_principles_heading_carries_anchor(self):
        source = (ROOT / "content" / "index.md").read_text(encoding="utf-8")
        _, body = parse_front_matter(source)
        html = markdown_to_html(body)
        self.assertIn('id="principles"', html)
```

This converts the real homepage body through the real Markdown pipeline and
asserts the anchor survives into HTML, rather than grepping the source for the
literal `{ #principles }`. `parse_front_matter` and `markdown_to_html` are
already imported at the top of `tests/test_render.py`; `ROOT` is defined there
too.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_base.py" -v`

Expected: `test_nav_links` fails on `/#principles`, `test_nav_has_no_dead_verification_link`
fails because `/#verification` is still present, and
`test_nav_active_marks_registry` fails because no Registry link exists.

- [ ] **Step 3: Rewrite the nav**

In `templates/base.html`, replace the whole `nav-links` div with:

```html
        <div class="nav-links">
            <a href="/#principles"{% if nav_active == "principles" %} class="active"{% endif %}>Principles</a>
            <a href="/model-registry/"{% if nav_active == "registry" %} class="active"{% endif %}>Registry</a>
            <a href="/articles/"{% if nav_active == "articles" %} class="active"{% endif %}>Articles</a>
            <a href="/#contact"{% if nav_active == "contact" %} class="active"{% endif %}>Contact</a>
        </div>
```

Also update the logo target in the same file — it currently points at
`/#verification`:

```html
        <a class="logo" href="/#principles">Business Model Hub</a>
```

- [ ] **Step 4: Add the anchor to the homepage**

In `content/index.md`, change:

```markdown
## Core Operational Principles of the Foundation
```

to:

```markdown
## Core Operational Principles of the Foundation { #principles }
```

The `extra` extension is enabled in `render.py`, so `attr_list` supplies the
`id`. Verified: `markdown.markdown("## X { #y }", extensions=["extra"])` yields
`<h2 id="y">X</h2>`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: `OK` — all tests pass, including the previously red
`test_nav_active_registry` and `test_nav_active_articles`.

- [ ] **Step 6: Commit**

```powershell
git add templates/base.html content/index.md tests/test_base.py tests/test_render.py
git commit -m "Fix navigation targets and add principles anchor"
```

---

### Task 6: Full build verification

**Files:** none (verification only)

- [ ] **Step 1: Render from a clean output directory**

Run:

```powershell
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue; py render.py
```

Expected: 15 written paths — `index.html`, `articles\index.html`, two article
directories, `model-registry\index.html`, and ten model directories.

- [ ] **Step 2: Verify every nav target resolves**

Run:

```powershell
$root = (Get-Location).Path + "\dist"
foreach ($u in @("/", "/articles/", "/model-registry/")) {
  "{0,-24} {1}" -f $u, (Test-Path (Join-Path $root $u.TrimEnd("/").Replace("/", "\") | Join-Path -ChildPath "index.html"))
}
```

Expected: `True` for all three.

Then confirm the homepage carries both anchors:

```powershell
Select-String -Path dist\index.html -Pattern 'id="(principles|contact)"' -AllMatches |
  ForEach-Object { $_.Matches.Value }
```

Expected: `id="principles"` and `id="contact"`.

- [ ] **Step 3: Verify no dead links remain**

Run:

```powershell
$root = (Get-Location).Path + "\dist"
$dead = @()
Get-ChildItem -Recurse -File $root -Filter *.html | ForEach-Object {
  $h = Get-Content $_.FullName -Raw -Encoding UTF8
  [regex]::Matches($h, 'href="(/[^"#]*)') | ForEach-Object {
    $u = $_.Groups[1].Value
    $t = if ($u.EndsWith("/")) {
      Join-Path (Join-Path $root $u.TrimEnd("/").Replace("/", "\")) "index.html"
    } else { Join-Path $root $u.TrimStart("/").Replace("/", "\") }
    if (-not (Test-Path $t)) { $dead += "$u (from $($_.Path))" }
  }
}
if ($dead) { $dead } else { "no dead internal links" }
```

Expected: `no dead internal links`. If any appear, fix the source of the link
rather than removing the check.

- [ ] **Step 4: Verify registry cards and sorting**

Run:

```powershell
$h = Get-Content dist\model-registry\index.html -Raw -Encoding UTF8
"cards: " + ([regex]::Matches($h, 'class="article-card"')).Count
[regex]::Matches($h, '<div class="article-card-meta">\s*<span>([^<]*)</span>') |
  ForEach-Object { "  " + $_.Groups[1].Value }
```

Expected: `cards: 10`, and ten organization names in case-insensitive ascending
order — `ai-sage (GigaChat)`, two `DeepSeek-AI`, `Google DeepMind`,
`IBM Granite Team`, `NVIDIA`, `Ornith AI`, two `Qwen`, `Z.ai (zai-org)`.

- [ ] **Step 5: Verify summaries reached the cards**

Run:

```powershell
Select-String -Path dist\model-registry\index.html -Pattern 'article-card-params' |
  Measure-Object | ForEach-Object { "params lines: $($_.Count)" }
```

Expected: `params lines: 10` — every model declares `params`. Nine of them also
append an "active" figure; `granite-4-2-30b` is dense and has no
`active_params`.

- [ ] **Step 6: Run the full test suite**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: `OK`, all tests pass.

- [ ] **Step 7: Confirm dist is not staged**

Run: `git status --short`

Expected: no `dist/` entries.