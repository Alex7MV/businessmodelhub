# Jinja2 Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate the empty Jinja2 templates `templates/base.html`, `templates/article.html`, `templates/page.html` so they reproduce the design of `dist/index.html`, and extract its inline CSS/JS into `assets/`.

**Architecture:** Jinja2 template inheritance. `base.html` holds the whole document frame (`<head>`, `<nav>`, `<footer>`, script includes) and exposes blocks; `article.html` and `page.html` extend it and override blocks. All styles move verbatim to `assets/css/style.css`; the e-mail de-obfuscation script moves verbatim to `assets/js/main.js`.

**Tech Stack:** Python 3.13 (`py` launcher), Jinja2 3.1.6 (already installed), stdlib `unittest` (no third-party test dependency). Shell is PowerShell 7 on Windows.

**Source of truth:** `dist/index.html` (iframe-free single page), `content/index.md`, `docs/superpowers/specs/2026-09-25-jinja2-templates-design.md`.

---

## File Structure

| File | Responsibility | Status |
|------|----------------|--------|
| `tests/template_env.py` | Shared Jinja2 `render()` helper for tests | Create |
| `tests/test_assets.py` | Assert CSS/JS assets exist and contain expected tokens | Create |
| `tests/test_base.py` | Assert `base.html` frame contract | Create |
| `tests/test_article.py` | Assert `article.html` article contract | Create |
| `tests/test_page.py` | Assert `page.html` page contract | Create |
| `assets/css/style.css` | Styles moved from inline `<style>` | Create |
| `assets/js/main.js` | E-mail de-obfuscation script | Create |
| `templates/base.html` | Document frame + blocks | Modify (currently empty) |
| `templates/article.html` | `extends base`; structured article | Modify (currently empty) |
| `templates/page.html` | `extends base`; hero block + free body | Modify (currently empty) |

Test commands use `py -m unittest discover -s tests ...` (the `python`/`python3` shims on this machine are Windows Store aliases that fail; always use `py`).

---

### Task 1: Test harness + asset extraction

**Files:**
- Create: `tests/template_env.py`
- Create: `tests/test_assets.py`
- Create: `assets/css/style.css`
- Create: `assets/js/main.js`

- [ ] **Step 1: Write the shared test helper**

Create `tests/template_env.py`:

```python
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"


def render(template_name, **context):
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template(template_name).render(**context)
```

- [ ] **Step 2: Write the failing asset tests**

Create `tests/test_assets.py`:

```python
import unittest

from template_env import ROOT


class AssetTests(unittest.TestCase):
    def test_css_contains_theme_tokens(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("--accent: #e8d9a8;", css)
        self.assertIn(".principles-grid", css)

    def test_js_contains_email_deobfuscation(self):
        js = (ROOT / "assets" / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn('querySelector(".footer-email")', js)
        self.assertIn('"mailto:"', js)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_assets.py" -v`
Expected: FAIL with `FileNotFoundError` for `assets\css\style.css`.

- [ ] **Step 4: Create `assets/css/style.css`**

Copy verbatim the CSS between `<style>` and `</style>` in `dist/index.html` (lines 9-249), then append these new rules at the end of the file:

```css
        /* Article / page prose */
        .page-head,
        .article-body,
        .page-body {
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
            padding: 2.5rem 2rem 0;
        }

        .article-meta {
            font-size: 0.8rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 1rem;
        }

        .article-body,
        .page-body {
            padding-top: 1.5rem;
            padding-bottom: 4rem;
            font-size: 0.95rem;
            color: #aab6c8;
        }

        .article-body h2,
        .page-body h2 {
            font-family: Georgia, "Times New Roman", serif;
            font-weight: 500;
            color: #f0f4fa;
            margin: 2rem 0 0.75rem;
        }

        .article-body h3,
        .page-body h3 {
            font-family: Georgia, "Times New Roman", serif;
            font-weight: 500;
            color: var(--accent);
            margin: 1.5rem 0 0.5rem;
        }

        .article-body p,
        .page-body p {
            margin-bottom: 1rem;
        }

        .article-body a,
        .page-body a {
            color: var(--accent);
        }

        .nav-links a.active {
            color: var(--accent);
        }

        @media (max-width: 600px) {
            .page-head,
            .article-body,
            .page-body {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
```

Do not edit any rule copied from `dist/index.html`; only append.

- [ ] **Step 5: Create `assets/js/main.js`**

Copy verbatim the JavaScript between `<script>` and `</script>` in `dist/index.html` (lines 316-324):

```javascript
(function () {
    var link = document.querySelector(".footer-email");
    if (!link) return;
    link.addEventListener("click", function (event) {
        event.preventDefault();
        var reversed = link.querySelector(".rev").textContent.trim();
        window.location.href = "mailto:" + reversed.split("").reverse().join("");
    });
})();
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_assets.py" -v`
Expected: PASS (2 tests).

- [ ] **Step 7: Commit**

```bash
git add tests/template_env.py tests/test_assets.py assets/css/style.css assets/js/main.js
git commit -m "Add CSS/JS assets and test harness"
```

---

### Task 2: `base.html`

**Files:**
- Create: `tests/test_base.py`
- Modify: `templates/base.html` (currently empty)

- [ ] **Step 1: Write the failing base tests**

Create `tests/test_base.py`:

```python
import unittest

from template_env import render


class BaseTemplateTests(unittest.TestCase):
    def test_default_title(self):
        html = render("base.html")
        self.assertIn("<title>Business Model Hub Foundation</title>", html)

    def test_nav_links(self):
        html = render("base.html")
        for href in ("/#verification", "/#principles", "/#contact"):
            self.assertIn('href="%s"' % href, html)

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_base.py" -v`
Expected: FAIL (all 5 tests — empty template).

- [ ] **Step 3: Write `templates/base.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Business Model Hub Foundation{% endblock %}</title>
    <meta name="description" content="{% block description %}{% endblock %}">

    <link rel="apple-touch-icon" sizes="180x180" href="/assets/images/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/assets/images/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/assets/images/favicon-16x16.png">
    <link rel="manifest" href="/assets/images/site.webmanifest">
    <link rel="stylesheet" href="/assets/css/style.css">

    {% block head_extra %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
    <nav>
        <a class="logo" href="/#verification">Business Model Hub</a>
        <div class="nav-links">
            <a href="/#verification"{% if nav_active == "verification" %} class="active"{% endif %}>Verification</a>
            <a href="/#principles"{% if nav_active == "principles" %} class="active"{% endif %}>Principles</a>
            <a href="/#contact"{% if nav_active == "contact" %} class="active"{% endif %}>Contact</a>
        </div>
    </nav>

    {% block content %}{% endblock %}

    <footer id="contact">
        <div class="footer-inner">
            <div class="footer-row">
                <span>&copy; 2026 Business Model Hub Foundation.</span>
                <span class="footer-sep" aria-hidden="true">&middot;</span>
                <a class="footer-email" href="#" aria-label="Send email"><span class="rev" aria-hidden="true">gro.buhledomssenisub@ofni</span></a>
            </div>
            <span class="footer-license">Except where otherwise noted, content on this site is licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) License. Open-source runtime components released under the MIT License.</span>
        </div>
    </footer>

    <script src="/assets/js/main.js" defer></script>
    {% block scripts_extra %}{% endblock %}
</body>
</html>
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_base.py" -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/test_base.py templates/base.html
git commit -m "Add base Jinja2 template frame"
```

---

### Task 3: `article.html`

**Files:**
- Create: `tests/test_article.py`
- Modify: `templates/article.html` (currently empty)

- [ ] **Step 1: Write the failing article tests**

Create `tests/test_article.py`:

```python
import unittest

from template_env import render

PAGE = {
    "title": "Chain of Custody",
    "author": "BMH Team",
    "date": "2026-02-01",
    "description": "How BMH verifies upstream artifacts.",
}


class ArticleTemplateTests(unittest.TestCase):
    def _render(self, **overrides):
        page = dict(PAGE)
        page.update(overrides.pop("page", {}))
        return render("article.html", page=page, content="<p>Body text</p>", **overrides)

    def test_title_tag(self):
        html = self._render()
        self.assertIn("<title>Chain of Custody — Business Model Hub</title>", html)

    def test_heading(self):
        html = self._render()
        self.assertIn("<h1>Chain of Custody</h1>", html)

    def test_meta_line(self):
        html = self._render()
        self.assertIn("BMH Team", html)
        self.assertIn('<time datetime="2026-02-01">2026-02-01</time>', html)

    def test_body_and_base(self):
        html = self._render()
        self.assertIn("<p>Body text</p>", html)
        self.assertIn("CC BY 4.0", html)

    def test_no_meta_when_author_and_date_absent(self):
        html = self._render(page={"author": None, "date": None})
        self.assertNotIn("article-meta", html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_article.py" -v`
Expected: FAIL (all 5 tests — empty template).

- [ ] **Step 3: Write `templates/article.html`**

```html
{% extends "base.html" %}

{% block title %}{{ page.title }} — Business Model Hub{% endblock %}
{% block description %}{{ page.description }}{% endblock %}

{% block content %}
<header class="page-head">
    {% if page.overline %}<div class="overline">{{ page.overline }}</div>{% endif %}
    <h1>{{ page.title }}</h1>
    {% if page.author or page.date %}
    <p class="article-meta">
        {%- if page.author %}{{ page.author }}{% endif -%}
        {%- if page.author and page.date %} &middot; {% endif -%}
        {%- if page.date %}<time datetime="{{ page.date }}">{{ page.date }}</time>{% endif -%}
    </p>
    {% endif %}
</header>

<main class="article-body">
{{ content|safe }}
</main>
{% endblock %}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_article.py" -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/test_article.py templates/article.html
git commit -m "Add article Jinja2 template"
```

---

### Task 4: `page.html`

**Files:**
- Create: `tests/test_page.py`
- Modify: `templates/page.html` (currently empty)

- [ ] **Step 1: Write the failing page tests**

Create `tests/test_page.py`:

```python
import unittest

from template_env import render


class PageTemplateTests(unittest.TestCase):
    def test_content_rendered(self):
        html = render("page.html", page={}, content="<h1>About BMH</h1>")
        self.assertIn("<h1>About BMH</h1>", html)

    def test_no_automatic_heading(self):
        html = render("page.html", page={"title": "About"}, content="<p>x</p>")
        self.assertNotIn("<h1>About</h1>", html)

    def test_title_uses_page_title(self):
        html = render("page.html", page={"title": "About"}, content="")
        self.assertIn("<title>About</title>", html)

    def test_title_falls_back_to_default(self):
        html = render("page.html", page={}, content="")
        self.assertIn("<title>Business Model Hub Foundation</title>", html)

    def test_extends_base(self):
        html = render("page.html", page={}, content="")
        self.assertIn("CC BY 4.0", html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_page.py" -v`
Expected: FAIL (all 5 tests — empty template).

- [ ] **Step 3: Write `templates/page.html`**

```html
{% extends "base.html" %}

{% block title %}{% if page.title %}{{ page.title }}{% else %}{{ super() }}{% endif %}{% endblock %}
{% block description %}{{ page.description }}{% endblock %}

{% block content %}
{% block hero %}{% endblock %}

<main class="page-body">
{{ content|safe }}
</main>
{% endblock %}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_page.py" -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/test_page.py templates/page.html
git commit -m "Add simple page Jinja2 template"
```

---

### Task 5: Full-suite verification and manual preview

**Files:**
- No source changes; verification only.

- [ ] **Step 1: Run the entire test suite**

Run: `py -m unittest discover -s tests -p "test_*.py" -v`
Expected: PASS (17 tests: 2 assets + 5 base + 5 article + 5 page).

- [ ] **Step 2: Render a preview page and inspect it**

Run:

```powershell
py -c "import sys; sys.path.insert(0, 'tests'); from template_env import render; from pathlib import Path; Path('dist/preview.html').write_text(render('page.html', page={'title': 'Business Model Hub Foundation'}, content='<h1>Independent Upstream Artifact Verification</h1><p>Preview body</p>'), encoding='utf-8')"
```

Expected: no traceback; `dist/preview.html` created (git-ignored). Open it in a browser and confirm nav, footer (license lines, e-mail link) and body styling match `dist/index.html`.

- [ ] **Step 3: Confirm no stray files are staged**

Run: `git status --short`
Expected: only `docs/` changes if any remain; `dist/` is ignored and must not appear.

---

## Self-Review Notes

- **Spec coverage:** base blocks (Task 2), article contract (Task 3), page contract + hero block (Task 4), asset extraction (Task 1), path normalization to `/assets/images/…` (Task 2), verification (Task 5). All spec sections covered.
- **No placeholders:** every code step contains full file content or an exact verbatim source range.
- **Type consistency:** `page.title`, `page.description`, `page.overline`, `page.date`, `page.author`, `content`, `nav_active` are used identically across tests and templates. Test helper is always `render(template_name, **context)` from `template_env`.
