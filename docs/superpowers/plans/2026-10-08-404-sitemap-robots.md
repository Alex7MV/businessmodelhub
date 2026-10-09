# 404, Sitemap and Robots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a root `404.html`, a generated `sitemap.xml`, and a root `robots.txt` for a site deployed at `https://businessmodelhub.org`.

**Architecture:** `SITE_URL` is a single constant in `render.py`. `output_path` gains a `404` case so the error page lands at the site root where hosts look for it. `build()` emits `sitemap.xml` and `robots.txt` alongside the pages, deriving every URL from the paths it just wrote so the map cannot disagree with the output layout.

**Tech Stack:** Python 3 stdlib only for this work — Jinja2, Markdown and PyYAML are already used for pages. No new dependencies, no new templates, no CSS or JS changes.

**Design spec:** `docs/superpowers/specs/2026-10-08-404-sitemap-robots-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `render.py` | `SITE_URL`, `404` case in `output_path`, `url_for_output`, `write_sitemap`, `write_robots`, calls in `build()`. |
| `content/404.md` | The not-found page, rendered by the existing `page.html`. |
| `tests/test_render.py` | Output-path case, sitemap and robots contents, 404 links. |

## Commands

Use the `py` launcher — `python` and `python3` are broken Windows Store aliases here.

```powershell
py -m unittest discover -s tests -p "test_render.py" -v
py -m unittest discover -s tests -p "test_*.py"
py render.py
```

## The trap this plan exists to close

`output_path` maps every non-`index` stem to `<dir>/<stem>/index.html`. Without
the new case, `404.md` becomes `dist/404/index.html` — verified against the
current code. Hosts serve a custom not-found page from `404.html` at the site
root, so the page would be built, listed as written, and never used. The build
would look clean and the site would still be broken.

## Current output count

The build writes 15 pages today. After this plan it writes 17 entries: 16 HTML
pages (15 existing plus `404.html`) plus the two generated text files are
written separately and are not part of the `written` list returned by `build()`.

---

### Task 1: `SITE_URL` and the `404` output-path case

**Files:**
- Modify: `render.py:8-12` (constants) and `render.py:170-177` (`output_path`)
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

Add a new test class to `tests/test_render.py`, below the `MarkdownTests` class
and above `if __name__ == "__main__":`:

```python
class OutputPathTests(unittest.TestCase):
    def test_index_stem_maps_to_directory_index(self):
        out = Path("dist")
        self.assertEqual(
            output_path(out, Path("index.md")), out / "index.html"
        )
        self.assertEqual(
            output_path(out, Path("articles/index.md")),
            out / "articles" / "index.html",
        )

    def test_other_stems_map_to_their_own_directory(self):
        out = Path("dist")
        self.assertEqual(
            output_path(out, Path("articles/post.md")),
            out / "articles" / "post" / "index.html",
        )

    def test_404_stem_maps_to_root_file(self):
        out = Path("dist")
        self.assertEqual(
            output_path(out, Path("404.md")), out / "404.html"
        )

    def test_site_url_has_no_trailing_slash(self):
        self.assertFalse(SITE_URL.endswith("/"))
        self.assertTrue(SITE_URL.startswith("https://"))
```

Add `SITE_URL` to the import list at the top of `tests/test_render.py`. The
file currently imports:

```python
from render import (
    build,
    markdown_to_html,
    parse_front_matter,
    select_template,
)
```

Change it to:

```python
from render import (
    SITE_URL,
    build,
    markdown_to_html,
    output_path,
    parse_front_matter,
    select_template,
)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: collection fails with
`ImportError: cannot import name 'SITE_URL' from 'render'`. That is the
expected failure for this step.

- [ ] **Step 3: Add the constant and the output-path case**

In `render.py`, replace the constants block:

```python
ARTICLE_DIR = "articles"
ARTICLE_INDEX = "index.md"
REGISTRY_DIR = "model-registry"
```

with:

```python
ARTICLE_DIR = "articles"
ARTICLE_INDEX = "index.md"
REGISTRY_DIR = "model-registry"
ERROR_STEM = "404"
SITE_URL = "https://businessmodelhub.org"
```

Then replace `output_path`:

```python
def output_path(out_dir, rel_path):
    """Map a content source path to its dist location.

    index.md -> <dir>/index.html; 404.md -> <dir>/404.html;
    anything else -> <dir>/<stem>/index.html.
    """
    if rel_path.stem == "index":
        return out_dir / rel_path.parent / "index.html"
    if rel_path.stem == ERROR_STEM:
        return out_dir / rel_path.parent / (ERROR_STEM + ".html")
    return out_dir / rel_path.parent / rel_path.stem / "index.html"
```

Hosts look for `404.html` at the site root, not in a subdirectory, which is why
this case exists.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: `OK`. `test_other_stems_map_to_their_own_directory` guards the
regression — the new branch must not disturb any other stem.

- [ ] **Step 5: Commit**

```powershell
git add render.py tests/test_render.py
git commit -m "Map 404 source to a root error page"
```

---

### Task 2: URL derivation and the sitemap

**Files:**
- Modify: `render.py` (add `url_for_output` and `write_sitemap`; call from `build()`)
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

Add these methods to `OutputPathTests`:

```python
    def test_url_for_output_uses_trailing_slash_for_index(self):
        out = Path("dist")
        self.assertEqual(url_for_output(out, out / "index.html"), "/")
        self.assertEqual(
            url_for_output(out, out / "articles" / "index.html"), "/articles/"
        )
        self.assertEqual(
            url_for_output(out, out / "articles" / "post" / "index.html"),
            "/articles/post/",
        )

    def test_url_for_output_keeps_non_index_files(self):
        out = Path("dist")
        self.assertEqual(url_for_output(out, out / "404.html"), "/404.html")
```

And add a new test class below `OutputPathTests`:

```python
class SitemapTests(unittest.TestCase):
    def build_site(self, tmp_path):
        content = tmp_path / "content"
        (content / "articles").mkdir(parents=True)
        (content / "index.md").write_text(
            "---\ntitle: Home\n---\n# Home\n", encoding="utf-8"
        )
        (content / "404.md").write_text(
            "---\ntitle: Not found\n---\nBody\n", encoding="utf-8"
        )
        (content / "articles" / "index.md").write_text(
            "---\ntitle: Articles\ntemplate: articles\n---\nIntro.\n",
            encoding="utf-8",
        )
        (content / "articles" / "post.md").write_text(
            "---\ntitle: Post\n---\nBody\n", encoding="utf-8"
        )
        out = tmp_path / "dist"
        build(content, ROOT / "templates", ROOT / "assets", out)
        return out

    def test_sitemap_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_site(Path(tmp))
            self.assertTrue((out / "sitemap.xml").exists())

    def test_sitemap_urls_are_absolute_and_end_in_slash(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_site(Path(tmp))
            xml = (out / "sitemap.xml").read_text(encoding="utf-8")
            for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
                self.assertTrue(loc.startswith(SITE_URL + "/"))
                self.assertTrue(loc.endswith("/"))

    def test_sitemap_lists_every_page_except_404(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_site(Path(tmp))
            xml = (out / "sitemap.xml").read_text(encoding="utf-8")
            locs = re.findall(r"<loc>([^<]+)</loc>", xml)
            self.assertEqual(
                sorted(locs),
                sorted([SITE_URL + "/", SITE_URL + "/articles/",
                        SITE_URL + "/articles/post/"]),
            )
            self.assertNotIn("404", xml)
```

The fixture deliberately includes `404.md`, so the exclusion is asserted rather
than assumed: three pages are built, the error page is among them, and the map
must still list exactly the three real URLs.

Add `url_for_output` and `re` to the imports of `tests/test_render.py`.
`re` is not currently imported there.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: `ImportError: cannot import name 'url_for_output' from 'render'`.

- [ ] **Step 3: Implement `url_for_output` and `write_sitemap`**

In `render.py`, add these two functions after `output_path`:

```python
def url_for_output(out_dir, path):
    """Turn a written output path into its site-root-relative URL path."""
    rel = Path(path).relative_to(out_dir).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("/index.html")] + "/"
    return "/" + rel


def write_sitemap(out_dir, written):
    """Write sitemap.xml from the pages that were actually built."""
    entries = []
    for path in written:
        if path.name == "404.html":
            continue
        url = SITE_URL + url_for_output(out_dir, path)
        entries.append(
            "  <url><loc>%s</loc></url>" % url.replace("&", "&amp;")
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    (out_dir / "sitemap.xml").write_text(xml, encoding="utf-8")
```

- [ ] **Step 4: Call `write_sitemap` from `build()`**

In `build()`, replace the final two lines:

```python
    shutil.copytree(assets_dir, out_dir / "assets", dirs_exist_ok=True)
    return sorted(written)
```

with:

```python
    shutil.copytree(assets_dir, out_dir / "assets", dirs_exist_ok=True)
    write_sitemap(out_dir, written)
    return sorted(written)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: `OK`. The fixture builds four pages — home, articles index, one
article, and the error page — so the sitemap must contain exactly three
`<loc>` entries.

- [ ] **Step 6: Inspect the real sitemap**

Run: `py render.py | Out-Null; Get-Content dist\sitemap.xml`

Expected: 15 `<url>` entries with no trailing blank line issue, starting with
`<loc>https://businessmodelhub.org/</loc>` and including
`/articles/selfcheck-model-standard-revision-a/`, `/model-registry/`, and each of
the ten model pages. No `404`.

- [ ] **Step 7: Commit**

```powershell
git add render.py tests/test_render.py
git commit -m "Generate sitemap.xml from built pages"
```

---

### Task 3: `robots.txt` and the 404 page content

**Files:**
- Modify: `render.py` (add `write_robots`, call from `build()`)
- Create: `content/404.md`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

Add a test class below `SitemapTests`:

```python
class RobotsTests(unittest.TestCase):
    def test_robots_is_written_at_site_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            build(ROOT / "content", ROOT / "templates", ROOT / "assets", out)
            self.assertTrue((out / "robots.txt").exists())

    def test_robots_points_at_the_sitemap(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            build(ROOT / "content", ROOT / "templates", ROOT / "assets", out)
            robots = (out / "robots.txt").read_text(encoding="utf-8")
            self.assertIn(
                "Sitemap: %s/sitemap.xml" % SITE_URL, robots
            )
            self.assertIn("User-agent: *", robots)


class ErrorPageTests(unittest.TestCase):
    def test_404_page_is_written_at_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            build(ROOT / "content", ROOT / "templates", ROOT / "assets", out)
            self.assertTrue((out / "404.html").exists())
            self.assertFalse((out / "404" / "index.html").exists())

    def test_404_page_offers_all_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            build(ROOT / "content", ROOT / "templates", ROOT / "assets", out)
            html = (out / "404.html").read_text(encoding="utf-8")
            for href in ("/#principles", "/model-registry/", "/articles/",
                         "/#contact"):
                self.assertIn('href="%s"' % href, html)
```

`test_404_page_is_written_at_root` asserts the absence of
`404/index.html` as well, because that is the failure this whole task prevents.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_render.py" -v`

Expected: four failures — no `robots.txt`, and no `404.html`.

- [ ] **Step 3: Implement `write_robots`**

In `render.py`, add after `write_sitemap`:

```python
def write_robots(out_dir):
    """Write robots.txt at the site root pointing at the sitemap."""
    text = (
        "User-agent: *\n"
        "Sitemap: %s/sitemap.xml\n" % SITE_URL
    )
    (out_dir / "robots.txt").write_text(text, encoding="utf-8")
```

The file is generated rather than placed in `assets/` because asset copying
mirrors the source tree: `assets/robots.txt` would land at
`dist/assets/robots.txt`, while the protocol requires the site root.

- [ ] **Step 4: Call `write_robots` from `build()`**

In `build()`, change:

```python
    write_sitemap(out_dir, written)
    return sorted(written)
```

to:

```python
    write_sitemap(out_dir, written)
    write_robots(out_dir)
    return sorted(written)
```

- [ ] **Step 5: Create `content/404.md`**

```markdown
---
title: Page not found
description: The requested address does not exist on this site.
---

The address you requested does not exist on this site. It may have been moved,
or the link that brought you here may be out of date.

## Where to go instead

- [The four verification principles](/#principles) — what the consortium holds
  models to.
- [The model registry](/model-registry/) — every upstream model tracked so far,
  with architecture, scale, and licensing.
- [Articles](/articles/) — long-form writing on verification methodology,
  supply-chain post-mortems, and architecture reviews.
- [Contact](/#contact) — how to reach the foundation.

If you followed a link from elsewhere on this site, the address it pointed to
has probably changed.
```

`nav_active` is deliberately omitted: the visitor is not on any of the four
sections, so no nav item is highlighted.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: `OK`.

- [ ] **Step 7: Inspect the real output**

Run:

```powershell
py render.py | Out-Null
Get-ChildItem dist -File | Select-Object -ExpandProperty Name
Get-Content dist\robots.txt
```

Expected: `404.html`, `index.html`, `robots.txt`, `sitemap.xml` at the root of
`dist`, and robots containing `Sitemap: https://businessmodelhub.org/sitemap.xml`.

- [ ] **Step 8: Commit**

```powershell
git add render.py content/404.md tests/test_render.py
git commit -m "Add robots.txt and the 404 page"
```

---

### Task 4: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Build from clean and count**

Run:

```powershell
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
py render.py
```

Expected: 16 HTML paths printed, plus `dist/404.html`, `dist/sitemap.xml` and
`dist/robots.txt` on disk.

- [ ] **Step 2: Validate the sitemap is well-formed XML**

Run:

```powershell
try {
  [xml]$s = Get-Content dist\sitemap.xml
  "root: $($s.DocumentElement.Name)"
  "url count: $($s.urlset.url.Count)"
  "404 present: $([bool](Select-String -Path dist\sitemap.xml -Pattern '404' -Quiet))"
} catch { "XML PARSE FAILED: $_" }
```

Expected: root `urlset`, `url count` of 15, `404 present: False`.

- [ ] **Step 3: Verify every sitemap URL matches a built file**

Run:

```powershell
$root = (Get-Location).Path + "\dist"
[xml]$s = Get-Content dist\sitemap.xml
$bad = @()
foreach ($u in $s.urlset.url.loc) {
  $p = $u -replace '^https://businessmodelhub\.org', ''
  $target = if ($p -eq "/") { Join-Path $root "index.html" }
            else { Join-Path $root ($p.Trim("/").Replace("/", "\") | Join-Path -ChildPath "index.html") }
  if (-not (Test-Path $target)) { $bad += $u }
}
if ($bad) { "MISMATCH:"; $bad } else { "all sitemap URLs resolve" }
```

Expected: `all sitemap URLs resolve`.

- [ ] **Step 4: Run the full suite**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: `OK`.

- [ ] **Step 5: Serve and request a missing address**

```powershell
Start-Process -FilePath "py" -ArgumentList "-m","http.server","8000","--directory","dist" -WindowStyle Hidden
Start-Sleep -Seconds 2
foreach ($u in @("/404.html", "/sitemap.xml", "/robots.txt", "/nope/")) {
  "{0,-16} HTTP {1}" -f $u, (Invoke-WebRequest -Uri "http://localhost:8000$u" -UseBasicParsing -ErrorAction SilentlyContinue).StatusCode
}
```

Expected: the first three are 200. `/nope/` is **404 from python's server**, which
is expected — `http.server` does not serve a custom error page. Confirming the
host behaviour needs the real server; see the note below.

- [ ] **Step 6: Stop the server**

```powershell
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*http.server*8000*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId }
```

## Post-deployment checks, not runnable here

These depend on the host and must be run against `businessmodelhub.org`:

```
curl -I https://businessmodelhub.org/model-registry/
curl -I https://businessmodelhub.org/definitely-not-a-real-page/
curl -s https://businessmodelhub.org/robots.txt
curl -s https://businessmodelhub.org/sitemap.xml | head
```

- The first returns 200, confirming nginx serves directory `index.html` and the
  trailing-slash URLs resolve. A redirect to `.html` means the server config is
  non-standard.
- The second must return 404 with the custom page body, not a server default.
