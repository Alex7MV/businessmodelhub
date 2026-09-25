import shutil
from pathlib import Path

import markdown as markdown_lib
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

VALID_TEMPLATES = {"page": "page.html", "article": "article.html"}
DEFAULT_TEMPLATE = "page.html"
ARTICLE_DIR = "articles"


class _FrontMatterLoader(yaml.SafeLoader):
    pass


_FrontMatterLoader.yaml_implicit_resolvers = {
    first_char: [
        (tag, regexp)
        for tag, regexp in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]
    for first_char, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def parse_front_matter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        raise ValueError("front matter opened with '---' but never closed")

    raw_meta = "\n".join(lines[1:end])
    meta = yaml.load(raw_meta, Loader=_FrontMatterLoader)
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise ValueError("front matter must be a YAML mapping")

    body = "\n".join(lines[end + 1:])
    return meta, body


def markdown_to_html(body):
    return markdown_lib.markdown(body, extensions=["extra"])


def select_template(rel_path, meta):
    name = meta.get("template")
    if name in VALID_TEMPLATES:
        return VALID_TEMPLATES[name]
    parts = Path(rel_path).parts
    if parts and parts[0] == ARTICLE_DIR:
        return VALID_TEMPLATES["article"]
    return DEFAULT_TEMPLATE


def render_document(env, template_name, meta, body_html):
    template = env.get_template(template_name)
    return template.render(
        page=meta,
        content=body_html,
        nav_active=meta.get("nav_active"),
    )


def build(content_dir, templates_dir, assets_dir, out_dir):
    content_dir = Path(content_dir)
    templates_dir = Path(templates_dir)
    assets_dir = Path(assets_dir)
    out_dir = Path(out_dir)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    written = []
    for source in sorted(content_dir.rglob("*.md")):
        rel_path = source.relative_to(content_dir)
        meta, body = parse_front_matter(source.read_text(encoding="utf-8"))
        body_html = markdown_to_html(body)
        template_name = select_template(rel_path, meta)
        html = render_document(env, template_name, meta, body_html)
        target = out_dir / rel_path.with_suffix(".html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        written.append(target)

    shutil.copytree(assets_dir, out_dir / "assets", dirs_exist_ok=True)
    return sorted(written)
