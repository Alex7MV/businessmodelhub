import unittest

from template_env import render


class BaseTemplateTests(unittest.TestCase):
    def test_default_title(self):
        html = render("base.html")
        self.assertIn("<title>Business Model Hub Foundation</title>", html)

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

    def test_icon_links(self):
        html = render("base.html")
        self.assertIn('href="/assets/images/favicon.ico"', html)
        self.assertIn('href="/assets/images/apple-touch-icon.png"', html)
        self.assertIn('href="/assets/images/favicon-32x32.png"', html)
        self.assertIn('href="/assets/images/favicon-16x16.png"', html)
        self.assertIn('href="/assets/images/site.webmanifest"', html)

    def test_nav_active_marks_link(self):
        html = render("base.html", nav_active="principles")
        self.assertIn('href="/#principles" class="active"', html)

    def test_nav_active_marks_registry(self):
        html = render("base.html", nav_active="registry")
        self.assertIn('href="/model-registry/" class="active"', html)

    def test_nav_active_marks_articles(self):
        html = render("base.html", nav_active="articles")
        self.assertIn('href="/articles/" class="active"', html)


if __name__ == "__main__":
    unittest.main()