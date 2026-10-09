import shutil
from pathlib import Path

import markdown as markdown_lib
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

VALID_TEMPLATES = {
    "page": "page.html",
    "article": "article.html",
    "articles": "articles.html",
    "registry": "registry.html",
}
DEFAULT_TEMPLATE = "page.html"
ARTICLE_DIR = "articles"
ARTICLE_INDEX = "index.md"
REGISTRY_DIR = "model-registry"
ERROR_STEM = "404"
SITE_URL = "https://businessmodelhub.org"


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


def _sort_articles(collected):
    """Newest dated article first; undated last, then by title."""
    dated = [item for item in collected if item["date"]]
    undated = [item for item in collected if not item["date"]]
    dated.sort(key=lambda item: item["date"], reverse=True)
    undated.sort(key=lambda item: item["title"])
    return dated + undated


def collect_articles(content_dir):
    """Article metadata from content/articles/*.md, excluding index.md.

    Returns a list of dicts: {url, title, date, summary, tags}, newest
    first. Articles without a date are placed after all dated articles,
    sorted among themselves by title ascending. An article without a title
    raises ValueError.
    """
    articles_dir = Path(content_dir) / ARTICLE_DIR
    if not articles_dir.is_dir():
        return []

    collected = []
    for source in sorted(articles_dir.glob("*.md")):
        if source.name == ARTICLE_INDEX:
            continue
        meta, _ = parse_front_matter(source.read_text(encoding="utf-8"))
        title = meta.get("title")
        if not title:
            raise ValueError(
                "article %s has no 'title' in its front matter" % source.name
            )
        collected.append(
            {
                "url": "/%s/%s/" % (ARTICLE_DIR, source.stem),
                "title": title,
                "date": meta.get("date") or "",
                "summary": meta.get("summary") or "",
                "tags": meta.get("tags") or [],
            }
        )

    return _sort_articles(collected)


def collect_registry(content_dir):
    """Model metadata from content/model-registry/*.md, excluding index.md.

    Returns a list of dicts with keys url, name, organization, params,
    active_params, context_length, license, tasks, release and summary,
    sorted by organization then name, both case-insensitive. Absent
    fields become "" or []. A model without a name raises ValueError.
    """
    registry_dir = Path(content_dir) / REGISTRY_DIR
    if not registry_dir.is_dir():
        return []

    collected = []
    for source in sorted(registry_dir.glob("*.md")):
        if source.name == ARTICLE_INDEX:
            continue
        meta, _ = parse_front_matter(source.read_text(encoding="utf-8"))
        name = meta.get("name")
        if not name:
            raise ValueError(
                "model %s has no 'name' in its front matter" % source.name
            )
        collected.append(
            {
                "url": "/%s/%s/" % (REGISTRY_DIR, source.stem),
                "name": name,
                "organization": meta.get("organization") or "",
                "params": meta.get("params") or "",
                "active_params": meta.get("active_params") or "",
                "context_length": meta.get("context_length") or "",
                "license": meta.get("license") or "",
                "tasks": meta.get("tasks") or [],
                "release": meta.get("release") or "",
                "summary": meta.get("summary") or "",
            }
        )

    collected.sort(
        key=lambda item: (item["organization"].lower(), item["name"].lower())
    )
    return collected


def render_document(env, template_name, meta, body_html, articles=(), registry=()):
    template = env.get_template(template_name)
    return template.render(
        page=meta,
        content=body_html,
        nav_active=meta.get("nav_active"),
        articles=articles,
        registry=registry,
    )


def output_path(out_dir, rel_path):
    """Map a content source path to its dist location.

    index.md -> <dir>/index.html; 404.md -> <dir>/404.html;
    anything else -> <dir>/<stem>/index.html.
    """
    if rel_path.stem == "index":
        return out_dir / rel_path.parent / "index.html"
    if rel_path.stem == ERROR_STEM:
        return out_dir / rel_path.parent / (ERROR_STEM + ".html")
    return out_dir / rel_path.parent / rel_path.stem / "index.html"


def url_for_output(out_dir, path):
    """Turn a written output path into its site-root-relative URL path."""
    rel = Path(path).relative_to(out_dir).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("/index.html")] + "/"
    return "/" + rel


def write_sitemap(out_dir, written):
    """Write sitemap.xml from the pages that were actually built."""
    entries = []
    for path in written:
        if path.name == "404.html":
            continue
        url = SITE_URL + url_for_output(out_dir, path)
        entries.append(
            "  <url><loc>%s</loc></url>" % url.replace("&", "&amp;")
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    (out_dir / "sitemap.xml").write_text(xml, encoding="utf-8")


def build(content_dir, templates_dir, assets_dir, out_dir):
    content_dir = Path(content_dir)
    templates_dir = Path(templates_dir)
    assets_dir = Path(assets_dir)
    out_dir = Path(out_dir)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    articles = collect_articles(content_dir)
    registry = collect_registry(content_dir)

    written = []
    for source in sorted(content_dir.rglob("*.md")):
        rel_path = source.relative_to(content_dir)
        meta, body = parse_front_matter(source.read_text(encoding="utf-8"))
        body_html = markdown_to_html(body)
        template_name = select_template(rel_path, meta)
        html = render_document(
            env, template_name, meta, body_html, articles=articles, registry=registry
        )
        target = output_path(out_dir, rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        written.append(target)

    shutil.copytree(assets_dir, out_dir / "assets", dirs_exist_ok=True)
    write_sitemap(out_dir, written)
    return sorted(written)


def main():
    written = build("content", "templates", "assets", "dist")
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
