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
