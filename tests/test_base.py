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
