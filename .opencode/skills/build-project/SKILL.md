---
name: build-project
description: Use when building, compiling, or verifying the Business Model Hub site, before committing changes to templates/content/assets/render.py, or when asked for a full build or "собрать проект". Runs the full build (install dependencies, render dist, run tests).
---

# Build Project

Full build for the Business Model Hub static site. It installs dependencies,
renders `content/` into `dist/`, and runs the test suite. A build succeeds only
when all three steps pass.

## When to Use

- Before committing or pushing changes to `templates/`, `content/`, `assets/`, or `render.py`.
- After editing Markdown content or Jinja2 templates.
- When asked to "build", "собери проект", "полная сборка", or to verify the site.

## Steps

Run these three commands in order. Stop at the first failure and report it; do
not continue to the next step.

1. **Install dependencies**

   ```powershell
   py -m pip install -r requirements.txt
   ```

2. **Render the site**

   ```powershell
   py render.py
   ```

   Expected: prints `dist\index.html`; `dist/index.html` and `dist/assets/` exist.

3. **Run the test suite**

   ```powershell
   py -m unittest discover -s tests -p "test_*.py" -v
   ```

   Expected: `OK`, all tests pass.

## Rules

- Always use the `py` launcher. On this machine `python` and `python3` are
  Windows Store aliases that fail.
- Never skip tests. A build with failing tests is a failed build.
- `dist/` is git-ignored build output — do not commit it. Rendering overwrites
  it, which is expected.
