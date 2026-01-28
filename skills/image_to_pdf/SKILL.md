---
name: imagetopdf
description: 将指定目录下的多张图像合并为一个 PDF。
---

# 图像转 PDF 专家 (Advanced Image-to-PDF Converter)

此技能专门用于将零散的图像文件汇编成专业的 PDF 文档。

## 🌟 核心功能
- **目录扫描**：支持通过 `--dir` 参数指定包含图片的文件夹。
- **智能排序**：支持按时间或文件名排序。
- **精准替换**：支持替换特定页面。

## 🛠️ 参数说明
- `output.pdf`：输出文件名。
- `--dir PATH`：包含图片的目录路径（默认当前目录）。
- `--sort {time,name}`：排序模式。
- `--replace page:file`：替换规则。

## 📝 执行协议 (Agent Protocol)

当用户提出合并图像的请求时：

1. **命令执行**：
   直接运行技能目录下的脚本。如果用户指定了文件夹（如 `images/`），请添加 `--dir` 参数：
   ```bash
   python3 {SKILL_DIR}/scripts/merge.py output.pdf --dir images/ --sort name
   ```
