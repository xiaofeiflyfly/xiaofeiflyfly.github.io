# 小飞的博客

基于自研静态生成器的中文博客，架构参考 [lucumr.pocoo.org](https://lucumr.pocoo.org)（Armin Ronacher 的博客），为中文排版做了专门适配。

## 特性

- **极简写作**：文章放在 `content/posts/YYYY/MM-DD-slug.md`，frontmatter 只有可选的 `tags` 和 `summary`，标题即正文第一个 H1，日期编码在文件名里
- **中文排版**：中英文之间自动加空格、行高 1.9、两端对齐 + 标点规则、代码字体中文回退
- **零前端框架**：纯静态 HTML + 一份手写 CSS（约 300 行），无 JS 依赖，支持暗色模式
- **生成器仅约 500 行 Python**：marko（Markdown）+ Jinja2（模板）+ Pygments（高亮）+ watchdog（热重载）

## 项目结构

```
├── content/
│   ├── posts/          # 文章（YYYY/MM-DD-slug.md）
│   └── static/         # 样式等静态资源
├── generator/
│   ├── builder.py      # 构建：文章/首页分页/标签/归档/RSS
│   ├── markup.py       # Markdown 渲染 + Pygments + 中文排版
│   ├── serve.py        # 开发服务器（变更自动重建）
│   └── templates/      # Jinja2 模板
├── .github/workflows/  # GitHub Pages 自动部署
└── Makefile
```

## 本地开发

```bash
make serve    # http://127.0.0.1:8000 ，内容/模板变更自动重建
make build    # 构建到 _site/
```

依赖 [uv](https://docs.astral.sh/uv/) 管理，首次运行自动安装。

## 写作

新建文章：

```bash
mkdir -p content/posts/$(date +%Y)
cat > content/posts/$(date +%Y)/$(date +%m-%d)-my-post.md <<'EOF'
---
tags: [随笔]
---

# 我的第一篇文章

正文从这里开始……
EOF
```

## 部署（GitHub Pages）

1. push 到 `main` 分支后 Actions 自动构建部署
2. 首次使用需在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**
3. 若仓库名不是 `<username>.github.io`，把 `generator/config.py` 里的 `base_path` 改为 `"/<仓库名>"`

## License

内容版权归作者所有，代码部分以 MIT 许可发布。
