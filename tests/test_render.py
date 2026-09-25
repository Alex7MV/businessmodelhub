import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from render import (
    markdown_to_html,
    parse_front_matter,
    render_document,
    select_template,
)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"


def make_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


class ParseFrontMatterTests(unittest.TestCase):
    def test_with_front_matter(self):
        meta, body = parse_front_matter("---\ntitle: Hello\n---\n\n# Body\n")
        self.assertEqual(meta, {"title": "Hello"})
        self.assertIn("# Body", body)
        self.assertNotIn("title: Hello", body)

    def test_without_front_matter(self):
        meta, body = parse_front_matter("# Just markdown\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "# Just markdown\n")

    def test_extra_fields(self):
        meta, body = parse_front_matter(
            "---\ntitle: T\ndate: 2026-01-01\ntemplate: article\n---\nX"
        )
        self.assertEqual(meta["date"], "2026-01-01")
        self.assertEqual(meta["template"], "article")

    def test_empty_block(self):
        meta, body = parse_front_matter("---\n---\nBody")
        self.assertEqual(meta, {})
        self.assertEqual(body, "Body")

    def test_unclosed_raises(self):
        with self.assertRaises(ValueError):
            parse_front_matter("---\ntitle: X\n")

    def test_non_mapping_raises(self):
        with self.assertRaises(ValueError):
            parse_front_matter("---\n- a\n- b\n---\nBody")


class MarkdownTests(unittest.TestCase):
    def test_heading(self):
        self.assertIn("<h1>Title</h1>", markdown_to_html("# Title"))

    def test_bold(self):
        self.assertIn("<strong>b</strong>", markdown_to_html("**b**"))

    def test_paragraph(self):
        self.assertIn("<p>text</p>", markdown_to_html("text"))


class SelectTemplateTests(unittest.TestCase):
    def test_default_page(self):
        self.assertEqual(select_template(Path("index.md"), {}), "page.html")

    def test_articles_dir(self):
        self.assertEqual(select_template(Path("articles/post.md"), {}), "article.html")

    def test_meta_overrides_dir(self):
        self.assertEqual(
            select_template(Path("articles/post.md"), {"template": "page"}),
            "page.html",
        )

    def test_meta_article_outside_dir(self):
        self.assertEqual(
            select_template(Path("about.md"), {"template": "article"}),
            "article.html",
        )

    def test_invalid_meta_falls_back(self):
        self.assertEqual(
            select_template(Path("articles/post.md"), {"template": "nope"}),
            "article.html",
        )


class RenderDocumentTests(unittest.TestCase):
    def test_page_document(self):
        html = render_document(
            make_env(), "page.html", {"title": "About"}, "<h1>About</h1>"
        )
        self.assertIn("<title>About</title>", html)
        self.assertIn("<h1>About</h1>", html)

    def test_article_document(self):
        meta = {"title": "Post", "date": "2026-02-01", "author": "Ann"}
        html = render_document(make_env(), "article.html", meta, "<p>x</p>")
        self.assertIn("<h1>Post</h1>", html)
        self.assertIn('<time datetime="2026-02-01">2026-02-01</time>', html)

    def test_nav_active(self):
        html = render_document(
            make_env(), "page.html", {"nav_active": "principles"}, ""
        )
        self.assertIn('href="/#principles" class="active"', html)


if __name__ == "__main__":
    unittest.main()
