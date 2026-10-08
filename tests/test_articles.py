import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from render import collect_articles, render_document

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"


def make_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


class CollectArticlesTests(unittest.TestCase):
    def make_content(self, files, tmp_path):
        articles_dir = tmp_path / "content" / "articles"
        articles_dir.mkdir(parents=True)
        for name, text in files.items():
            (articles_dir / name).write_text(text, encoding="utf-8")
        return tmp_path / "content"

    def test_extracts_all_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "post.md": "---\n"
                    "title: A Post\n"
                    "date: 2026-02-01\n"
                    "summary: Short summary.\n"
                    "tags: [methodology, verification]\n"
                    "---\n\nBody text.\n"
                },
                Path(tmp),
            )
            articles = collect_articles(content)
            self.assertEqual(
                articles,
                [
                    {
                        "url": "/articles/post/",
                        "title": "A Post",
                        "date": "2026-02-01",
                        "summary": "Short summary.",
                        "tags": ["methodology", "verification"],
                    }
                ],
            )

    def test_missing_date_summary_and_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {"bare.md": "---\ntitle: Bare\n---\n\nBody.\n"}, Path(tmp)
            )
            articles = collect_articles(content)
            self.assertEqual(articles[0]["date"], "")
            self.assertEqual(articles[0]["summary"], "")
            self.assertEqual(articles[0]["tags"], [])

    def test_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "old.md": "---\ntitle: Old\ndate: 2026-01-01\n---\nB\n",
                    "new.md": "---\ntitle: New\ndate: 2026-03-01\n---\nB\n",
                    "mid.md": "---\ntitle: Mid\ndate: 2026-02-01\n---\nB\n",
                },
                Path(tmp),
            )
            articles = collect_articles(content)
            self.assertEqual(
                [a["title"] for a in articles], ["New", "Mid", "Old"]
            )

    def test_undated_articles_sort_last_by_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "dated.md": "---\ntitle: Dated\ndate: 2026-01-01\n---\nB\n",
                    "zulu.md": "---\ntitle: Zulu\n---\nB\n",
                    "alpha.md": "---\ntitle: Alpha\n---\nB\n",
                },
                Path(tmp),
            )
            articles = collect_articles(content)
            self.assertEqual(
                [a["title"] for a in articles], ["Dated", "Alpha", "Zulu"]
            )

    def test_index_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "index.md": "---\ntitle: Articles\ntemplate: articles\n---\nIntro.\n",
                    "post.md": "---\ntitle: Post\ndate: 2026-02-01\n---\nB\n",
                },
                Path(tmp),
            )
            articles = collect_articles(content)
            self.assertEqual([a["title"] for a in articles], ["Post"])

    def test_missing_title_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {"bad.md": "---\ndate: 2026-02-01\n---\nB\n"}, Path(tmp)
            )
            with self.assertRaises(ValueError) as ctx:
                collect_articles(content)
            self.assertIn("bad.md", str(ctx.exception))

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content({}, Path(tmp))
            self.assertEqual(collect_articles(content), [])

    def test_no_articles_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp) / "content"
            content.mkdir()
            self.assertEqual(collect_articles(content), [])


class ArticlesTemplateTests(unittest.TestCase):
    def render_index(self, articles):
        return render_document(
            make_env(),
            "articles.html",
            {"title": "Articles", "description": "Long-form articles."},
            "<p>Intro.</p>",
            articles=articles,
        )

    def test_renders_card_per_article(self):
        html = self.render_index(
            [
                {
                    "url": "/articles/post/",
                    "title": "A Post",
                    "date": "2026-02-01",
                    "summary": "Short summary.",
                    "tags": ["methodology", "verification"],
                }
            ]
        )
        self.assertIn("<h1>Articles</h1>", html)
        self.assertIn('href="/articles/post/"', html)
        self.assertIn("A Post", html)
        self.assertIn("Short summary.", html)
        self.assertIn('<time datetime="2026-02-01">2026-02-01</time>', html)
        self.assertIn("methodology", html)
        self.assertIn("verification", html)

    def test_empty_list_renders_no_cards(self):
        html = self.render_index([])
        self.assertIn("<h1>Articles</h1>", html)
        self.assertIn("Intro.", html)
        self.assertNotIn("article-card", html)

    def test_article_without_date_or_summary(self):
        html = self.render_index(
            [
                {
                    "url": "/articles/bare/",
                    "title": "Bare",
                    "date": "",
                    "summary": "",
                    "tags": [],
                }
            ]
        )
        self.assertIn("Bare", html)
        self.assertNotIn("<time", html)

    def test_nav_active_articles(self):
        html = render_document(
            make_env(),
            "articles.html",
            {"title": "Articles", "nav_active": "articles"},
            "",
            articles=[],
        )
        self.assertIn('href="/articles/" class="active"', html)


if __name__ == "__main__":
    unittest.main()