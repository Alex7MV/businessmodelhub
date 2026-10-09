# Mobile Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all four navigation items reachable below 600px, without JavaScript, leaving desktop navigation unchanged.

**Architecture:** The nav links move inside a native `<details class="nav-menu">` with a `<summary>` acting as the burger control. Desktop CSS overrides the closed-`details` hiding so links stay in one row; mobile CSS turns the summary into a burger and the links into an absolutely positioned panel under the sticky bar. No JavaScript is added or changed.

**Tech Stack:** Static HTML, hand-written CSS, `unittest`. No new dependencies.

**Design spec:** `docs/superpowers/specs/2026-10-08-mobile-nav-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `templates/base.html` | Wrap the nav links in `details.nav-menu` with a `summary` burger. |
| `assets/css/style.css` | Desktop override, mobile burger + panel, `.sr-only`, nav mobile padding. |
| `tests/test_base.py` | Markup assertions for `details`, `summary`, accessible name. |
| `tests/test_assets.py` | `.nav-burger` and `.sr-only` exist; the mobile `display: none` on `.nav-links` is gone. |

`assets/js/main.js` is **not** touched.

## Commands

Use the `py` launcher — `python` and `python3` are broken Windows Store aliases here.

```powershell
py -m unittest discover -s tests -p "test_base.py" -v
py -m unittest discover -s tests -p "test_assets.py" -v
py -m unittest discover -s tests -p "test_*.py"
py render.py
```

## The one rule that cannot be unit-tested

A closed `<details>` hides its children through a user-agent rule. Overriding it
on desktop needs BOTH `display: flex` and `content-visibility: visible`, because
Chrome hides closed details with `content-visibility: hidden` rather than
`display: none`. The tests confirm both declarations exist; they cannot confirm
that a browser honours them. That check is manual — see Task 4.

---

### Task 1: Wrap the nav links in `details`

**Files:**
- Modify: `templates/base.html:19-27`
- Modify: `tests/test_base.py`

- [ ] **Step 1: Write the failing tests**

Add these two methods to `BaseTemplateTests` in `tests/test_base.py`, directly
above the `if __name__ == "__main__":` guard:

```python
    def test_nav_uses_details_disclosure(self):
        html = render("base.html")
        self.assertIn('<details class="nav-menu">', html)
        self.assertIn("<summary>", html)
        self.assertIn('class="nav-burger"', html)

    def test_nav_summary_has_accessible_name(self):
        html = render("base.html")
        self.assertIn('aria-hidden="true"', html)
        self.assertIn('<span class="sr-only">Menu</span>', html)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_base.py" -v`

Expected: FAIL. `test_nav_uses_details_disclosure` on
`'<details class="nav-menu">' not found ...`; the existing nav tests still pass,
because the four hrefs are already correct.

- [ ] **Step 3: Rewrite the nav markup**

In `templates/base.html`, replace lines 19-27:

```html
    <nav>
        <a class="logo" href="/#principles">Business Model Hub</a>
        <div class="nav-links">
            <a href="/#principles"{% if nav_active == "principles" %} class="active"{% endif %}>Principles</a>
            <a href="/model-registry/"{% if nav_active == "registry" %} class="active"{% endif %}>Registry</a>
            <a href="/articles/"{% if nav_active == "articles" %} class="active"{% endif %}>Articles</a>
            <a href="/#contact"{% if nav_active == "contact" %} class="active"{% endif %}>Contact</a>
        </div>
    </nav>
```

with:

```html
    <nav>
        <a class="logo" href="/#principles">Business Model Hub</a>
        <details class="nav-menu">
            <summary>
                <span class="nav-burger" aria-hidden="true"></span>
                <span class="sr-only">Menu</span>
            </summary>
            <div class="nav-links">
                <a href="/#principles"{% if nav_active == "principles" %} class="active"{% endif %}>Principles</a>
                <a href="/model-registry/"{% if nav_active == "registry" %} class="active"{% endif %}>Registry</a>
                <a href="/articles/"{% if nav_active == "articles" %} class="active"{% endif %}>Articles</a>
                <a href="/#contact"{% if nav_active == "contact" %} class="active"{% endif %}>Contact</a>
            </div>
        </details>
    </nav>
```

The four links and their `nav_active` conditions are copied verbatim — only
their position in the tree changes. Do not add `aria-expanded`, `role`, or
`tabindex` to the summary; the element is natively operable and announcing them
manually conflicts with the built-in semantics.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: the two new tests pass and all pre-existing nav tests still pass —
`test_nav_links`, `test_nav_active_marks_link`, `test_nav_active_marks_registry`,
`test_nav_active_marks_articles` must not regress.

Note that the site renders no usable mobile menu until Task 2, because CSS still
contains `.nav-links { display: none; }` below 600px. That is expected mid-plan.

- [ ] **Step 5: Commit**

```powershell
git add templates/base.html tests/test_base.py
git commit -m "Wrap nav links in a details disclosure"
```

---

### Task 2: Desktop override, mobile burger, and the panel

**Files:**
- Modify: `assets/css/style.css:228-245`
- Modify: `tests/test_assets.py`

- [ ] **Step 1: Write the failing tests**

Add these three methods to `AssetTests` in `tests/test_assets.py`:

```python
    def test_css_contains_burger_and_sr_only(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".nav-burger", css)
        self.assertIn(".sr-only", css)

    def test_desktop_overrides_closed_details(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        block = re.search(r"@media \(min-width: 601px\)\s*\{(.*?)\n\s{8}\}", css, re.S)
        self.assertIsNotNone(block, "no min-width 601px query in style.css")
        self.assertIn(".nav-menu > .nav-links", block.group(1))
        self.assertIn("content-visibility: visible", block.group(1))

    def test_mobile_does_not_hide_nav_links(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        block = re.search(r"@media \(max-width: 600px\)\s*\{(.*?)\n\s{8}\}", css, re.S)
        self.assertIsNotNone(block, "no max-width 600px query in style.css")
        self.assertNotIn("display: none", block.group(1))
```

`test_mobile_does_not_hide_nav_links` scopes its assertion to the 600px block
specifically, so a legitimate `display: none` elsewhere in the stylesheet does
not cause a false failure. At this point in the file `display: none` appears
exactly once in the whole stylesheet, inside that block.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_assets.py" -v`

Expected: three failures —
`test_css_contains_burger_and_sr_only` on `'.nav-burger'`,
`test_desktop_overrides_closed_details` on `no min-width 601px query`,
`test_mobile_does_not_hide_nav_links` on `display: none`.

- [ ] **Step 3: Replace the responsive block**

In `assets/css/style.css`, replace lines 228-245 — from the `/* Responsive */`
comment through the closing brace of the 600px query — with:

```css
        /* Responsive */
        @media (max-width: 900px) {
            .principles-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 600px) {
            nav {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            header {
                padding: 2rem 1rem 1.5rem;
            }
            main {
                padding: 2rem 1rem 3rem;
            }

            .nav-menu > summary {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 2.5rem;
                height: 2.5rem;
                cursor: pointer;
                list-style: none;
            }

            .nav-menu > summary::-webkit-details-marker {
                display: none;
            }

            .nav-burger {
                display: block;
                width: 1.5rem;
                height: 1.5rem;
                background-image: linear-gradient(
                    to bottom,
                    var(--muted) 0 2px,
                    transparent 2px 7px,
                    var(--muted) 7px 9px,
                    transparent 9px 14px,
                    var(--muted) 14px 16px
                );
            }

            .nav-menu[open] .nav-burger {
                background-image: linear-gradient(
                    to bottom,
                    transparent 0 7px,
                    var(--accent) 7px 9px,
                    transparent 9px 14px
                );
                transform: rotate(45deg);
            }

            .nav-menu[open] > .nav-links {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                flex-direction: column;
                gap: 0;
                background: var(--bg);
                border-bottom: 1px solid var(--border);
            }

            .nav-menu[open] > .nav-links a {
                display: block;
                padding: 0.9rem 1rem;
                border-top: 1px solid var(--border);
            }
        }
```

The `linear-gradient` stops draw the three bars; the open-state gradient draws
the cross, with `rotate(45deg)` turning one into the other. `nav` is already
`position: sticky`, so `top: 100%` anchors the panel under the bar.

- [ ] **Step 4: Add the desktop override and `.sr-only`**

Append to the end of `assets/css/style.css`:

```css
        /* Nav disclosure: keep links visible on desktop */
        @media (min-width: 601px) {
            .nav-menu > summary {
                display: none;
            }

            .nav-menu > .nav-links {
                display: flex;
                content-visibility: visible;
            }
        }

        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
```

`content-visibility: visible` is not redundant: Chrome hides the children of a
closed `<details>` with `content-visibility: hidden`, which `display: flex` alone
does not override.

The min-width query is placed after the max-width queries on purpose. Both apply
at exactly 600px, so source order decides; the later rule wins and desktop
behaviour takes precedence at the boundary.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: all pass, `OK`.

- [ ] **Step 6: Render and inspect the markup**

Run: `py render.py`

Then:

```powershell
Select-String -Path dist\index.html -Pattern '<details class="nav-menu">|<summary>|nav-burger|sr-only' -AllMatches |
  ForEach-Object { $_.Matches.Value }
```

Expected: matches for all four patterns, so the disclosure survived the build.

- [ ] **Step 7: Commit**

```powershell
git add assets/css/style.css tests/test_assets.py
git commit -m "Add burger menu for narrow viewports"
```

---

### Task 3: Confirm nothing else regressed

**Files:** none (verification only)

- [ ] **Step 1: Check `main.js` is untouched**

Run: `git diff HEAD~2 --stat -- assets/js/main.js`

Expected: no output. The mailto de-obfuscator must be unchanged.

- [ ] **Step 2: Confirm the nav still links to four live targets**

Run:

```powershell
$h = Get-Content dist\index.html -Raw
[regex]::Matches($h, 'class="nav-links">.*?</div>', 'Singleline') | ForEach-Object {
  [regex]::Matches($_.Value, 'href="([^"]+)"') | ForEach-Object { "  " + $_.Groups[1].Value }
}
```

Expected: exactly four, in order — `/#principles`, `/model-registry/`,
`/articles/`, `/#contact`.

- [ ] **Step 3: Re-run the full suite**

Run: `py -m unittest discover -s tests -p "test_*.py"`

Expected: `OK`.

---

### Task 4: Manual browser check

**Files:** none

Automated checks cannot confirm rendering. Both items below must be eyeballed.

- [ ] **Step 1: Serve the site**

```powershell
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
py render.py
Start-Process -FilePath "py" -ArgumentList "-m","http.server","8000","--directory","dist" -WindowStyle Hidden
Start-Sleep -Seconds 2
Start-Process "http://localhost:8000/"
```

- [ ] **Step 2: Verify desktop at a wide viewport**

Expected: four links in one row to the right of the logo, and no burger icon.
This is the step most likely to fail — if the links are missing, the closed
`details` override did not take effect in that browser, and the fix is confined
to the two declarations in the `min-width: 601px` query.

- [ ] **Step 3: Verify mobile at 375px**

In devtools device mode or a narrow window:

- the burger icon appears right of the logo
- tapping it opens the panel below the bar with four stacked links
- tapping again closes it
- the bar stays inset by 1rem, matching the page padding

- [ ] **Step 4: Verify keyboard operation**

Focus the summary with Tab, toggle with Enter and with Space.

Expected: it opens and closes in both cases, and the burger carries the
accessible name "Menu".

- [ ] **Step 5: Verify with JavaScript disabled**

Devtools → Settings → Debugger → Disable JavaScript, then reload.

Expected: the menu still opens. This is the reason for choosing `details` over a
JS button, and it is the one property worth confirming.

- [ ] **Step 6: Stop the server**

```powershell
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*http.server*8000*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId }
```
