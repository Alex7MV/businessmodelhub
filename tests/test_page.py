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

    def test_title_falls_back_to_page_name(self):
        html = render("page.html", page={"name": "GLM-5.3-Flash"}, content="")
        self.assertIn("<title>GLM-5.3-Flash</title>", html)

    def test_title_falls_back_to_default(self):
        html = render("page.html", page={}, content="")
        self.assertIn("<title>Business Model Hub Foundation</title>", html)

    def test_extends_base(self):
        html = render("page.html", page={}, content="")
        self.assertIn("CC BY 4.0", html)


if __name__ == "__main__":
    unittest.main()
