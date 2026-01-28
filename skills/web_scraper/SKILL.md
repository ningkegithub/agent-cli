---
name: web_scraper
description: 从指定 URL 抓取内容，支持提取图片并下载到本地。
---

# 网页爬虫专家 (Web Scraper)

此技能赋予 Agent 访问互联网并提取数据的能力。

## 🌟 核心功能
- **图片抓取**：从网页批量下载图片到指定目录。

## 📝 执行协议 (Agent Protocol)

当用户请求“爬取网页图片”时：

1. **执行抓取**：
   直接运行技能目录下的脚本：
   ```bash
   python3 {SKILL_DIR}/scripts/scrape.py [URL] [OUTPUT_DIR]
   ```
   *示例*: `python3 {SKILL_DIR}/scripts/scrape.py https://example.com my_images`
