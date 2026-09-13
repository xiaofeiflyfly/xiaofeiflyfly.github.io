"""Build the static site.

学自 lucumr 的架构，精简为：
- 文章: content/posts/YYYY/MM-DD-slug.md（frontmatter 只有 tags/summary，标题即首个 H1）
- URL: /YYYY/M/D/slug/（去零，与 lucumr 一致）
- 输出: 首页分页、文章页、标签页、归档页、Atom feed
"""

import re
import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


from generator.config import CONFIG
from generator.markup import (
    get_pygments_css,
    plain_text_from_html,
    render_markdown,
)

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
POSTS_DIR = CONTENT / "posts"
STATIC_DIR = CONTENT / "static"
OUTPUT = ROOT / "_site"
TEMPLATES = Path(__file__).resolve().parent / "templates"


class Post:
    """一篇文章。frontmatter 只有 tags/summary，日期编码在文件名里。"""

    def __init__(self, path: Path):
        self.source_path = path
        text = path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(text)

        self.tags = frontmatter.get("tags", []) or []
        self.summary = frontmatter.get("summary")

        match = re.search(r"(\d{4})/(\d{2})-(\d{2})-(.+)\.md$", str(path))
        if not match:
            raise ValueError(f"文章路径不符合 YYYY/MM-DD-slug.md 约定: {path}")
        year, month, day, slug = match.groups()
        self.pub_date = datetime(int(year), int(month), int(day))
        self.slug = slug

        rendered = render_markdown(body)
        self.title = rendered["title"] or slug
        self.html_title = Markup(rendered["html_title"]) if rendered["html_title"] else None
        self.html = Markup(rendered["fragment"])

        if not self.summary:
            plain = plain_text_from_html(self.html)
            self.summary = plain[: CONFIG["summary_length"]] + (
                "…" if len(plain) > CONFIG["summary_length"] else ""
            )

    @staticmethod
    def _split_frontmatter(text):
        lines = text.split("\n")
        if lines and lines[0].strip() == "---":
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    frontmatter = yaml.safe_load("\n".join(lines[1:i])) or {}
                    return frontmatter, "\n".join(lines[i + 1 :])
        return {}, text

    @property
    def url(self):
        d = self.pub_date
        return f"{CONFIG['base_path']}/{d.year}/{d.month}/{d.day}/{self.slug}/"

    @property
    def absolute_url(self):
        return CONFIG["site_url"] + self.url

    @property
    def date_iso(self):
        return self.pub_date.strftime("%Y-%m-%d")

    @property
    def date_cn(self):
        return f"{self.pub_date.year} 年 {self.pub_date.month} 月 {self.pub_date.day} 日"

    @property
    def tag_urls(self):
        return [(t, f"{CONFIG['base_path']}/tags/{quote(t)}/") for t in self.tags]


class Builder:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.posts = []

    # -- 主流程 ------------------------------------------------------------

    def build(self):
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        OUTPUT.mkdir(parents=True)

        self.posts = sorted(
            (Post(p) for p in POSTS_DIR.glob("*/*.md")),
            key=lambda p: p.pub_date,
            reverse=True,
        )

        self._write_pygments_css()
        self._copy_static()
        self._write_posts()
        self._write_index_pages()
        self._write_tags()
        self._write_archive()
        self._write_feed()

        print(f"构建完成: {len(self.posts)} 篇文章 → {OUTPUT}")

    def _render(self, template, target, **ctx):
        target = OUTPUT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        html = self.env.get_template(template).render(
            config=CONFIG, posts=self.posts, **ctx
        )
        target.write_text(html, encoding="utf-8")

    # -- 各页面 ------------------------------------------------------------

    def _write_pygments_css(self):
        css = get_pygments_css()
        # 暗色模式适配：交给 CSS 变量，浅色样式即可
        target = OUTPUT / "static" / "pygments.css"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(css, encoding="utf-8")

    def _copy_static(self):
        if STATIC_DIR.exists():
            shutil.copytree(STATIC_DIR, OUTPUT / "static", dirs_exist_ok=True)

    def _write_posts(self):
        for post in self.posts:
            self._render("post.html", post.url.lstrip("/") + "index.html", post=post)

    def _write_index_pages(self):
        per_page = CONFIG["posts_per_page"]
        total_pages = max(1, -(-len(self.posts) // per_page))
        for page in range(1, total_pages + 1):
            chunk = self.posts[(page - 1) * per_page : page * per_page]
            target = "index.html" if page == 1 else f"page/{page}/index.html"
            self._render(
                "index.html",
                target,
                page_posts=chunk,
                page=page,
                total_pages=total_pages,
            )

    def _write_tags(self):
        tags = {}
        for post in self.posts:
            for tag in post.tags:
                tags.setdefault(tag, []).append(post)
        for tag, posts in tags.items():
            self._render("tag.html", f"tags/{quote(tag)}/index.html", tag=tag, tag_posts=posts)

    def _write_archive(self):
        by_year = {}
        for post in self.posts:
            by_year.setdefault(post.pub_date.year, []).append(post)
        self._render("archive.html", "archive/index.html", by_year=by_year)

    def _write_feed(self):
        self._render("feed.xml", "feed.atom", feed_posts=self.posts[: CONFIG["feed_limit"]])


def main():
    Builder().build()


if __name__ == "__main__":
    main()
