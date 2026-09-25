# Render Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `render.py`, which compiles every `content/**/*.md` (YAML front matter + Markdown) into `dist/**/*.html` via the existing Jinja2 templates and copies `assets/` into `dist/assets/`.

**Architecture:** One module, `render.py`, with small pure functions plus a thin `main()`. Front matter is parsed with PyYAML, Markdown is converted with Python-Markdown, pages render through `page.html` / `article.html` (which extend `base.html`), and output structure mirrors `content/`.

**Tech Stack:** Python 3.13 (`py` launcher), Jinja2 3.1.6, PyYAML 6.0.3, Markdown 3.11, stdlib `unittest`. Shell is PowerShell 7 on Windows.

**Source of truth:** `docs/superpowers/specs/2026-09-25-render-script-design.md`.

Test commands use `py -m unittest discover -s tests ...` (the `python`/`python3` shims are Windows Store aliases that fail; always use `py`).

---

## File Structure

| File | Responsibility | Status |
|------|----------------|--------|
| `requirements.txt` | Pin runtime dependencies | Create |
| `render.py` | Front matter, Markdown, template selection, rendering, build, CLI | Create |
| `tests/test_render.py` | Unit + integration tests for `render.py` | Create |
| `content/index.md` | Remove duplicated license/footer block | Modify |

`render.py` public contract (as specified):

```
parse_front_matter(text) -> (meta: dict, body: str)
markdown_to_html(body) -> str
select_template(rel_path: Path, meta: dict) -> str
render_document(env, template_name, meta, body_html) -> str
build(content_dir, templates_dir, assets_dir, out_dir) -> list[Path]
main() -> None
```

---

### Task 1: Dependencies and `parse_front_matter`

**Files:**
- Create: `requirements.txt`
- Create: `tests/test_render.py`
- Create: `render.py`

- [ ] **Step 1: Create `requirements.txt`**

```
Jinja2==3.1.6
Markdown==3.11
PyYAML==6.0.3
```

- [ ] **Step 2: Install dependencies**

Run: `py -m pip install -r requirements.txt`
Then verify: `py -c "import markdown; print(markdown.__version__)"`
Expected: `3.11`

- [ ] **Step 3: Write the failing tests**

Create `tests/test_render.py`:

```python
import unittest

from render import parse_front_matter


class ParseFrontMatterTests(unittest.TestCase):
    def test_with_front_matter(self):
        meta, body = parse_front_matter("---\ntitle: Hello\n---\n\n# Body\n")
        self.assertEqual(meta, {"title": "Hello"})
        self.assertIn("# Body", body)
        self.assertNotIn("title: Hello", body)

    def test_without_front_matter(self):
        meta, body = parse_front_matter("# Just markdown\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "# Just markdown\n")

    def test_extra_fields(self):
        meta, body = parse_front_matter(
            "---\ntitle: T\ndate: 2026-01-01\ntemplate: article\n---\nX"
        )
        self.assertEqual(meta["date"], "2026-01-01")
        self.assertEqual(meta["template"], "article")

    def test_empty_block(self):
        meta, body = parse_front_matter("---\n---\nBody")
        self.assertEqual(meta, {})
        self.assertEqual(body, "Body")

    def test_unclosed_raises(self):
        with self.assertRaises(ValueError):
            parse_front_matter("---\ntitle: X\n")

    def test_non_mapping_raises(self):
        with self.assertRaises(ValueError):
            parse_front_matter("---\n- a\n- b\n---\nBody")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k ParseFrontMatterTests`
Expected: ERROR `ModuleNotFoundError: No module named 'render'`.

- [ ] **Step 5: Write the minimal implementation**

Create `render.py`:

```python
import yaml


def parse_front_matter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        raise ValueError("front matter opened with '---' but never closed")

    raw_meta = "\n".join(lines[1:end])
    meta = yaml.safe_load(raw_meta)
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise ValueError("front matter must be a YAML mapping")

    body = "\n".join(lines[end + 1:])
    return meta, body
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k ParseFrontMatterTests`
Expected: PASS (6 tests).

- [ ] **Step 7: Commit**

```bash
git add requirements.txt tests/test_render.py render.py
git commit -m "Add render dependencies and front matter parser"
```

---

### Task 2: `markdown_to_html`

**Files:**
- Modify: `render.py`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

In `tests/test_render.py`, change the import line to:

```python
from render import markdown_to_html, parse_front_matter
```

Append this class at the end of the file (before the `if __name__ == "__main__":` block, or after the existing class):

```python
class MarkdownTests(unittest.TestCase):
    def test_heading(self):
        self.assertIn("<h1>Title</h1>", markdown_to_html("# Title"))

    def test_bold(self):
        self.assertIn("<strong>b</strong>", markdown_to_html("**b**"))

    def test_paragraph(self):
        self.assertIn("<p>text</p>", markdown_to_html("text"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k MarkdownTests`
Expected: ERROR `ImportError: cannot import name 'markdown_to_html' from 'render'`.

- [ ] **Step 3: Write the minimal implementation**

At the top of `render.py`, add the import (above `import yaml`):

```python
import markdown as markdown_lib
```

Append this function to `render.py`:

```python
def markdown_to_html(body):
    return markdown_lib.markdown(body, extensions=["extra"])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k MarkdownTests`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add render.py tests/test_render.py
git commit -m "Add markdown to HTML conversion"
```

---

### Task 3: `select_template`

**Files:**
- Modify: `render.py`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

In `tests/test_render.py`, change the top imports to:

```python
import unittest
from pathlib import Path

from render import markdown_to_html, parse_front_matter, select_template
```

Append this class to the file:

```python
class SelectTemplateTests(unittest.TestCase):
    def test_default_page(self):
        self.assertEqual(select_template(Path("index.md"), {}), "page.html")

    def test_articles_dir(self):
        self.assertEqual(select_template(Path("articles/post.md"), {}), "article.html")

    def test_meta_overrides_dir(self):
        self.assertEqual(
            select_template(Path("articles/post.md"), {"template": "page"}),
            "page.html",
        )

    def test_meta_article_outside_dir(self):
        self.assertEqual(
            select_template(Path("about.md"), {"template": "article"}),
            "article.html",
        )

    def test_invalid_meta_falls_back(self):
        self.assertEqual(
            select_template(Path("articles/post.md"), {"template": "nope"}),
            "article.html",
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k SelectTemplateTests`
Expected: ERROR `ImportError: cannot import name 'select_template' from 'render'`.

- [ ] **Step 3: Write the minimal implementation**

In `render.py`, add the import at the top (top of the import block):

```python
from pathlib import Path
```

Add these constants after the imports and before `parse_front_matter`:

```python
VALID_TEMPLATES = {"page": "page.html", "article": "article.html"}
DEFAULT_TEMPLATE = "page.html"
ARTICLE_DIR = "articles"
```

Append this function to `render.py`:

```python
def select_template(rel_path, meta):
    name = meta.get("template")
    if name in VALID_TEMPLATES:
        return VALID_TEMPLATES[name]
    parts = Path(rel_path).parts
    if parts and parts[0] == ARTICLE_DIR:
        return VALID_TEMPLATES["article"]
    return DEFAULT_TEMPLATE
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k SelectTemplateTests`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add render.py tests/test_render.py
git commit -m "Add template selection logic"
```

---

### Task 4: `render_document`

**Files:**
- Modify: `render.py`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

In `tests/test_render.py`, change the top imports to:

```python
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from render import (
    markdown_to_html,
    parse_front_matter,
    render_document,
    select_template,
)
```

Append this to the file (after the imports, before the first test class):

```python
ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"


def make_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
```

Append this class to the file:

```python
class RenderDocumentTests(unittest.TestCase):
    def test_page_document(self):
        html = render_document(
            make_env(), "page.html", {"title": "About"}, "<h1>About</h1>"
        )
        self.assertIn("<title>About</title>", html)
        self.assertIn("<h1>About</h1>", html)

    def test_article_document(self):
        meta = {"title": "Post", "date": "2026-02-01", "author": "Ann"}
        html = render_document(make_env(), "article.html", meta, "<p>x</p>")
        self.assertIn("<h1>Post</h1>", html)
        self.assertIn('<time datetime="2026-02-01">2026-02-01</time>', html)

    def test_nav_active(self):
        html = render_document(
            make_env(), "page.html", {"nav_active": "principles"}, ""
        )
        self.assertIn('href="/#principles" class="active"', html)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k RenderDocumentTests`
Expected: ERROR `ImportError: cannot import name 'render_document' from 'render'`.

- [ ] **Step 3: Write the minimal implementation**

In `render.py`, add the import at the top:

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape
```

Append this function to `render.py`:

```python
def render_document(env, template_name, meta, body_html):
    template = env.get_template(template_name)
    return template.render(
        page=meta,
        content=body_html,
        nav_active=meta.get("nav_active"),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k RenderDocumentTests`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add render.py tests/test_render.py
git commit -m "Add document rendering"
```

---

### Task 5: `build`

**Files:**
- Modify: `render.py`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

In `tests/test_render.py`, change the top imports to:

```python
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from render import (
    build,
    markdown_to_html,
    parse_front_matter,
    render_document,
    select_template,
)
```

Append this class to the file:

```python
class BuildTests(unittest.TestCase):
    def test_build_pages_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = tmp_path / "content"
            (content / "articles").mkdir(parents=True)
            (content / "index.md").write_text(
                "---\ntitle: Home\n---\n# Home\n", encoding="utf-8"
            )
            (content / "articles" / "post.md").write_text(
                "---\ntitle: Post\ndate: 2026-02-01\nauthor: Ann\n---\nBody\n",
                encoding="utf-8",
            )
            out = tmp_path / "dist"

            written = build(content, ROOT / "templates", ROOT / "assets", out)

            index = out / "index.html"
            post = out / "articles" / "post.html"
            self.assertTrue(index.exists())
            self.assertTrue(post.exists())
            self.assertIn("<title>Home</title>", index.read_text(encoding="utf-8"))
            self.assertIn("<h1>Post</h1>", post.read_text(encoding="utf-8"))
            self.assertTrue((out / "assets" / "css" / "style.css").exists())
            self.assertEqual(written, sorted([index, post]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k BuildTests`
Expected: ERROR `ImportError: cannot import name 'build' from 'render'`.

- [ ] **Step 3: Write the minimal implementation**

In `render.py`, add the import at the top:

```python
import shutil
```

Append this function to `render.py`:

```python
def build(content_dir, templates_dir, assets_dir, out_dir):
    content_dir = Path(content_dir)
    templates_dir = Path(templates_dir)
    assets_dir = Path(assets_dir)
    out_dir = Path(out_dir)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    written = []
    for source in sorted(content_dir.rglob("*.md")):
        rel_path = source.relative_to(content_dir)
        meta, body = parse_front_matter(source.read_text(encoding="utf-8"))
        body_html = markdown_to_html(body)
        template_name = select_template(rel_path, meta)
        html = render_document(env, template_name, meta, body_html)
        target = out_dir / rel_path.with_suffix(".html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        written.append(target)

    shutil.copytree(assets_dir, out_dir / "assets", dirs_exist_ok=True)
    return sorted(written)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_render.py" -v -k BuildTests`
Expected: PASS (1 test).

- [ ] **Step 5: Run the full render test file**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`
Expected: PASS (18 tests).

- [ ] **Step 6: Commit**

```bash
git add render.py tests/test_render.py
git commit -m "Add site build function"
```

---

### Task 6: `main()` and end-to-end build

**Files:**
- Modify: `render.py`

- [ ] **Step 1: Write the CLI entry point**

Append this to `render.py`:

```python
def main():
    written = build("content", "templates", "assets", "dist")
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script end to end**

Run: `py render.py`
Expected: prints `dist\index.html` and exits 0. This regenerates `dist/index.html` (git-ignored build output); the original prototype is fully reproducible from `templates/`, `assets/` and `content/`.

- [ ] **Step 3: Verify the generated page**

Run: `Test-Path "dist\index.html"; Select-String -Path "dist\index.html" -Pattern "<title>Business Model Hub Foundation</title>"`
Expected: `True` and one match.

- [ ] **Step 4: Run the whole test suite**

Run: `py -m unittest discover -s tests -p "test_*.py" -v`
Expected: PASS (all tests: 17 existing + 18 render).

- [ ] **Step 5: Commit**

```bash
git add render.py
git commit -m "Add render script CLI entry point"
```

---

### Task 7: Remove duplicated license block from `content/index.md`

The shared footer in `base.html` already renders the copyright, CC BY 4.0, MIT
and e-mail lines, so the same block at the end of `content/index.md` would be
printed twice.

**Files:**
- Modify: `content/index.md`

- [ ] **Step 1: Remove the trailing block**

In `content/index.md`, delete everything from the `---` separator that precedes
the copyright down to the end of the file, so the file ends after the
`04 · Architecture-Specific Binary Sovereignty` paragraph. The removed text is:

```markdown
---

© 2026 Business Model Hub Foundation.
Except where otherwise noted, content on this site is licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) License.
Open-source runtime components released under the MIT License.

📩 info@businessmodelhub.org
```

- [ ] **Step 2: Rebuild**

Run: `py render.py`
Expected: prints `dist\index.html`, exits 0.

- [ ] **Step 3: Verify the license appears exactly once**

Run: `(Get-Content "dist\index.html" -Raw | Select-String -Pattern "CC BY 4.0" -AllMatches).Matches.Count`
Expected: `1`.

- [ ] **Step 4: Commit**

```bash
git add content/index.md
git commit -m "Remove duplicated license block from homepage content"
```

---

## Self-Review Notes

- **Spec coverage:** `parse_front_matter` (Task 1), `markdown_to_html` (Task 2), `select_template` (Task 3), `render_document` (Task 4), `build` + asset copy + structure preservation (Task 5), `main`/CLI (Task 6), error handling covered by Task 1 tests, dependency pinning (Task 1), duplicate-footer follow-up (Task 7).
- **No placeholders:** every code step contains full function/class bodies and exact commands with expected output.
- **Type consistency:** `parse_front_matter`, `markdown_to_html`, `select_template`, `render_document`, `build`, `main` are used with identical signatures across implementation and tests; constants `VALID_TEMPLATES`, `DEFAULT_TEMPLATE`, `ARTICLE_DIR`, `ROOT`, `TEMPLATES_DIR` are defined once.
- **TDD:** each task writes a failing test, watches it fail, implements, watches it pass, commits. Task 6 is a thin CLI wrapper verified end to end (no new unit behavior).
