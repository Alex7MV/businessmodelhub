---
description: Run the full project build (install deps, render dist, run tests)
agent: build
---

Run the full build for Business Model Hub in this exact order, stopping at the first failure:

1. `py -m pip install -r requirements.txt`
2. `py render.py`
3. `py -m unittest discover -s tests -p "test_*.py" -v`

Report the result of each step. The build succeeds only if all three steps pass.
