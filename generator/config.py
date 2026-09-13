"""Site-wide configuration."""

CONFIG = {
    # 站点信息
    "title": "小飞的博客",
    "subtitle": "记录技术与生活",
    "author": "xiaofeiflyfly",
    "language": "zh-CN",
    # 站点 URL（用于 RSS/OG 绝对链接，部署后按实际域名修改）
    "site_url": "https://xiaofeiflyfly.github.io",
    # 子路径：仓库名不是 <username>.github.io 时改为 "/<repo>"
    # 例如仓库叫 blog，则设为 "/blog"；根域名仓库设为 ""
    "base_path": "",
    # 首页每页文章数
    "posts_per_page": 10,
    # RSS 输出条数
    "feed_limit": 20,
    # 正文摘要截取长度（frontmatter 未写 summary 时）
    "summary_length": 160,
}
