import re
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from render import (
    SITE_URL,
    build,
    markdown_to_html,
    output_path,
    parse_front_matter,
    render_document,
    select_template,
    url_for_output,
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

    def test_homepage_principles_heading_carries_anchor(self):
        source = (ROOT / "content" / "index.md").read_text(encoding="utf-8")
        _, body = parse_front_matter(source)
        html = markdown_to_html(body)
        self.assertIn('id="principles"', html)


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


class BuildTests(unittest.TestCase):
    def make_content(self, tmp_path):
        content = tmp_path / "content"
        (content / "articles").mkdir(parents=True)
        (content / "index.md").write_text(
            "---\ntitle: Home\n---\n# Home\n", encoding="utf-8"
        )
        (content / "articles" / "index.md").write_text(
            "---\ntitle: Articles\ntemplate: articles\n---\nIntro.\n",
            encoding="utf-8",
        )
        (content / "articles" / "post.md").write_text(
            "---\ntitle: Post\ndate: 2026-02-01\nsummary: A post.\n---\nBody\n",
            encoding="utf-8",
        )
        return content

    def test_build_pages_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = self.make_content(tmp_path)
            out = tmp_path / "dist"

            written = build(content, ROOT / "templates", ROOT / "assets", out)

            index = out / "index.html"
            articles_index = out / "articles" / "index.html"
            post = out / "articles" / "post" / "index.html"
            self.assertTrue(index.exists())
            self.assertTrue(articles_index.exists())
            self.assertTrue(post.exists())
            self.assertIn("<title>Home</title>", index.read_text(encoding="utf-8"))
            self.assertIn("<h1>Post</h1>", post.read_text(encoding="utf-8"))
            self.assertTrue((out / "assets" / "css" / "style.css").exists())
            self.assertEqual(
                written, sorted([index, articles_index, post])
            )

    def test_articles_index_links_to_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = self.make_content(tmp_path)
            out = tmp_path / "dist"

            build(content, ROOT / "templates", ROOT / "assets", out)

            articles_index = (out / "articles" / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('href="/articles/post/"', articles_index)
            self.assertIn("A post.", articles_index)
            self.assertNotIn("/articles/index.html", articles_index)

    def test_registry_index_links_to_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = self.make_content(tmp_path)
            registry = content / "model-registry"
            registry.mkdir()
            (registry / "index.md").write_text(
                "---\ntitle: Registry\ntemplate: registry\n---\nIntro.\n",
                encoding="utf-8",
            )
            (registry / "alpha.md").write_text(
                "---\nname: Alpha\norganization: Org\n"
                "release: \"2026\"\nsummary: The alpha model.\n---\nBody\n",
                encoding="utf-8",
            )
            out = tmp_path / "dist"

            build(content, ROOT / "templates", ROOT / "assets", out)

            index = (out / "model-registry" / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('href="/model-registry/alpha/"', index)
            self.assertIn("Alpha", index)
            self.assertIn("The alpha model.", index)
            self.assertTrue((out / "model-registry" / "alpha" / "index.html").exists())

    def test_nested_page_outside_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content = self.make_content(tmp_path)
            (content / "guides").mkdir()
            (content / "guides" / "start.md").write_text(
                "---\ntitle: Start\n---\nBody\n", encoding="utf-8"
            )
            out = tmp_path / "dist"

            build(content, ROOT / "templates", ROOT / "assets", out)

            self.assertTrue((out / "guides" / "start" / "index.html").exists())


class OutputPathTests(unittest.TestCase):
    def test_index_stem_maps_to_directory_index(self):
        out = Path("dist")
        self.assertEqual(
            output_path(out, Path("index.md")), out / "index.html"
        )
        self.assertEqual(
            output_path(out, Path("articles/index.md")),
            out / "articles" / "index.html",
        )

    def test_other_stems_map_to_their_own_directory(self):
        out = Path("dist")
        self.assertEqual(
            output_path(out, Path("articles/post.md")),
            out / "articles" / "post" / "index.html",
        )

    def test_404_stem_maps_to_root_file(self):
        out = Path("dist")
        self.assertEqual(
            output_path(out, Path("404.md")), out / "404.html"
        )

    def test_site_url_has_no_trailing_slash(self):
        self.assertFalse(SITE_URL.endswith("/"))
        self.assertTrue(SITE_URL.startswith("https://"))

    def test_url_for_output_uses_trailing_slash_for_index(self):
        out = Path("dist")
        self.assertEqual(url_for_output(out, out / "index.html"), "/")
        self.assertEqual(
            url_for_output(out, out / "articles" / "index.html"), "/articles/"
        )
        self.assertEqual(
            url_for_output(out, out / "articles" / "post" / "index.html"),
            "/articles/post/",
        )

    def test_url_for_output_keeps_non_index_files(self):
        out = Path("dist")
        self.assertEqual(url_for_output(out, out / "404.html"), "/404.html")


class SitemapTests(unittest.TestCase):
    def build_site(self, tmp_path):
        content = tmp_path / "content"
        (content / "articles").mkdir(parents=True)
        (content / "index.md").write_text(
            "---\ntitle: Home\n---\n# Home\n", encoding="utf-8"
        )
        (content / "404.md").write_text(
            "---\ntitle: Not found\n---\nBody\n", encoding="utf-8"
        )
        (content / "articles" / "index.md").write_text(
            "---\ntitle: Articles\ntemplate: articles\n---\nIntro.\n",
            encoding="utf-8",
        )
        (content / "articles" / "post.md").write_text(
            "---\ntitle: Post\n---\nBody\n", encoding="utf-8"
        )
        out = tmp_path / "dist"
        build(content, ROOT / "templates", ROOT / "assets", out)
        return out

    def test_sitemap_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_site(Path(tmp))
            self.assertTrue((out / "sitemap.xml").exists())

    def test_sitemap_urls_are_absolute_and_end_in_slash(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_site(Path(tmp))
            xml = (out / "sitemap.xml").read_text(encoding="utf-8")
            for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
                self.assertTrue(loc.startswith(SITE_URL + "/"))
                self.assertTrue(loc.endswith("/"))

    def test_sitemap_lists_every_page_except_404(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_site(Path(tmp))
            xml = (out / "sitemap.xml").read_text(encoding="utf-8")
            locs = re.findall(r"<loc>([^<]+)</loc>", xml)
            self.assertEqual(
                sorted(locs),
                sorted([SITE_URL + "/", SITE_URL + "/articles/",
                        SITE_URL + "/articles/post/"]),
            )
            self.assertNotIn("404", xml)


class RobotsTests(unittest.TestCase):
    def build_real(self, tmp_path):
        out = tmp_path / "dist"
        build(ROOT / "content", ROOT / "templates", ROOT / "assets", out)
        return out

    def test_robots_is_written_at_site_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_real(Path(tmp))
            self.assertTrue((out / "robots.txt").exists())

    def test_robots_points_at_the_sitemap(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_real(Path(tmp))
            robots = (out / "robots.txt").read_text(encoding="utf-8")
            self.assertIn("Sitemap: %s/sitemap.xml" % SITE_URL, robots)
            self.assertIn("User-agent: *", robots)


class ErrorPageTests(unittest.TestCase):
    def build_real(self, tmp_path):
        out = tmp_path / "dist"
        build(ROOT / "content", ROOT / "templates", ROOT / "assets", out)
        return out

    def test_404_page_is_written_at_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_real(Path(tmp))
            self.assertTrue((out / "404.html").exists())
            self.assertFalse((out / "404" / "index.html").exists())

    def test_404_page_offers_all_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.build_real(Path(tmp))
            html = (out / "404.html").read_text(encoding="utf-8")
            for href in ("/#principles", "/model-registry/", "/articles/",
                         "/#contact"):
                self.assertIn('href="%s"' % href, html)


if __name__ == "__main__":
    unittest.main()
