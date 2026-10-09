import json
import re
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

    def test_css_contains_article_card_styles(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".article-list", css)
        self.assertIn(".article-card", css)
        self.assertIn(".article-tags", css)

    def test_css_wraps_long_code_blocks(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("pre", css)
        self.assertIn("white-space: pre-wrap", css)
        self.assertIn("overflow-wrap", css)

    def test_css_contains_registry_card_styles(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".article-card-params", css)

    def test_nav_is_constrained_to_layout_width(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        block = re.search(r"^\s*nav\s*\{(.*?)\}", css, re.S | re.M)
        self.assertIsNotNone(block, "no nav rule found in style.css")
        self.assertIn("max-width: 900px", block.group(1))

    def test_manifest_icon_paths_resolve(self):
        manifest = json.loads(
            (ROOT / "assets" / "images" / "site.webmanifest").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(manifest["icons"], "manifest declares no icons")
        for icon in manifest["icons"]:
            target = ROOT / icon["src"].lstrip("/")
            self.assertTrue(
                target.exists(), "manifest icon does not exist: %s" % icon["src"]
            )

    def test_favicon_ico_exists(self):
        self.assertTrue((ROOT / "assets" / "images" / "favicon.ico").exists())

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
        # Scoped to the .nav-links rule itself: the block legitimately contains
        # other `display: none` rules, e.g. hiding the details marker.
        hiding = re.search(
            r"\.nav-links\s*\{[^}]*display:\s*none", block.group(1), re.S
        )
        self.assertIsNone(
            hiding,
            "mobile query still hides .nav-links: %s"
            % (hiding.group(0) if hiding else ""),
        )


if __name__ == "__main__":
    unittest.main()
