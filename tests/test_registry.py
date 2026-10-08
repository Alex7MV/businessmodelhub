import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from render import collect_registry, render_document

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"


def make_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


class CollectRegistryTests(unittest.TestCase):
    def make_content(self, files, tmp_path):
        registry_dir = tmp_path / "content" / "model-registry"
        registry_dir.mkdir(parents=True)
        for name, text in files.items():
            (registry_dir / name).write_text(text, encoding="utf-8")
        return tmp_path / "content"

    def test_extracts_all_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "model.md": "---\n"
                    "name: Test Model\n"
                    "organization: Test Org\n"
                    "params: 70B (MoE)\n"
                    "active_params: 3B\n"
                    "context_length: \"128K tokens\"\n"
                    "license: MIT\n"
                    "tasks: [text-generation]\n"
                    "release: \"2026\"\n"
                    "summary: A test model.\n"
                    "---\n\nBody.\n"
                },
                Path(tmp),
            )
            self.assertEqual(
                collect_registry(content),
                [
                    {
                        "url": "/model-registry/model/",
                        "name": "Test Model",
                        "organization": "Test Org",
                        "params": "70B (MoE)",
                        "active_params": "3B",
                        "context_length": "128K tokens",
                        "license": "MIT",
                        "tasks": ["text-generation"],
                        "release": "2026",
                        "summary": "A test model.",
                    }
                ],
            )

    def test_absent_optional_fields_become_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {"bare.md": "---\nname: Bare\norganization: Org\n---\nBody\n"},
                Path(tmp),
            )
            model = collect_registry(content)[0]
            self.assertEqual(model["params"], "")
            self.assertEqual(model["active_params"], "")
            self.assertEqual(model["summary"], "")
            self.assertEqual(model["tasks"], [])
            self.assertEqual(model["release"], "")

    def test_sorted_by_organization_then_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "a.md": "---\nname: Zed\norganization: Alpha\n---\nB\n",
                    "b.md": "---\nname: Beta\norganization: alpha\n---\nB\n",
                    "c.md": "---\nname: Aaa\norganization: alpha\n---\nB\n",
                },
                Path(tmp),
            )
            order = [(m["organization"], m["name"]) for m in collect_registry(content)]
            self.assertEqual(
                order, [("alpha", "Aaa"), ("alpha", "Beta"), ("Alpha", "Zed")]
            )

    def test_index_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {
                    "index.md": "---\nname: Registry\ntemplate: registry\n---\nIntro.\n",
                    "model.md": "---\nname: Model\norganization: Org\n---\nB\n",
                },
                Path(tmp),
            )
            self.assertEqual(
                [m["name"] for m in collect_registry(content)], ["Model"]
            )

    def test_missing_name_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content(
                {"bad.md": "---\norganization: Org\n---\nB\n"}, Path(tmp)
            )
            with self.assertRaises(ValueError) as ctx:
                collect_registry(content)
            self.assertIn("bad.md", str(ctx.exception))

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = self.make_content({}, Path(tmp))
            self.assertEqual(collect_registry(content), [])

    def test_no_registry_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp) / "content"
            content.mkdir()
            self.assertEqual(collect_registry(content), [])


class RegistryTemplateTests(unittest.TestCase):
    def make_model(self, **overrides):
        model = {
            "url": "/model-registry/alpha/",
            "name": "Alpha",
            "organization": "Test Org",
            "params": "70B (MoE)",
            "active_params": "3B",
            "context_length": "128K tokens",
            "license": "MIT",
            "tasks": ["text-generation"],
            "release": "2026",
            "summary": "A test model.",
        }
        model.update(overrides)
        return model

    def render_index(self, models):
        return render_document(
            make_env(),
            "registry.html",
            {"title": "Registry", "description": "Verified models."},
            "<p>Intro.</p>",
            registry=models,
        )

    def test_renders_card_per_model(self):
        html = self.render_index([self.make_model()])
        self.assertIn("<h1>Registry</h1>", html)
        self.assertIn('href="/model-registry/alpha/"', html)
        self.assertIn("Alpha", html)
        self.assertIn("Test Org", html)
        self.assertIn("70B (MoE)", html)
        self.assertIn("3B", html)
        self.assertIn("MIT", html)
        self.assertIn("2026", html)
        self.assertIn("A test model.", html)
        self.assertIn("text-generation", html)

    def test_empty_list_renders_no_cards(self):
        html = self.render_index([])
        self.assertIn("<h1>Registry</h1>", html)
        self.assertIn("Intro.", html)
        self.assertNotIn("article-card", html)

    def test_model_without_optional_fields(self):
        html = self.render_index(
            [self.make_model(params="", active_params="", summary="", tasks=[], license="")]
        )
        self.assertIn("Alpha", html)
        self.assertNotIn("article-card-params", html)
        self.assertNotIn("article-tags", html)

    def test_nav_active_registry(self):
        html = render_document(
            make_env(),
            "registry.html",
            {"title": "Registry", "nav_active": "registry"},
            "",
            registry=[],
        )
        self.assertIn('href="/model-registry/" class="active"', html)


if __name__ == "__main__":
    unittest.main()