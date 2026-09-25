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
