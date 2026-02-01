---
name: knowledge_base
description: 基于 LanceDB 的本地知识库与记忆中枢。支持 Word/PDF/Excel 文档入库、语义混合检索和溯源引用。是 Agent 的"长期记忆"和"资料库"。
---

# Knowledge Base (Project Memex)

这是一个基于向量数据库 (LanceDB) 的本地知识管理系统。它赋予了 Agent 跨越对话周期的记忆能力和海量文档的检索能力。

## 核心功能

1.  **Ingest (入库)**: 将本地文档（.pdf, .docx, .md）切片并向量化存入数据库。
2.  **Search (检索)**: 基于语义搜索相关知识片段，支持混合检索（关键词+向量）。

## 依赖说明

- **Vector DB**: LanceDB (本地文件存储，无需服务器)
- **Embedding**: FastEmbed (BAAI/bge-small-zh-v1.5) - 轻量级中文 SOTA 模型
- **Storage**: `~/.agent-cli/memory/lancedb_store`

## 工具清单

### 1. `ingest_knowledge(input_path: str, collection_name: str = "documents")`
将指定文件或目录下的所有支持文档（Word/PDF/Excel/PPT）导入知识库。
- `input_path`: 文件或文件夹路径。
- `collection_name`: 集合名称（默认 "documents"）。

**⚠️ 推荐调用方式**:
`python {SKILL_DIR}/scripts/ingest.py "YOUR_PATH" "collection_name"`

### 2. `search_knowledge(query: str, collection_name: str = "documents", limit: int = 5)`
在知识库中搜索相关信息。
**⚠️ 推荐调用方式**:
`python {SKILL_DIR}/scripts/query.py "YOUR_QUERY" "collection_name"`

### 3. `manage_knowledge(command: str, args: str)`
管理知识库内容（查看清单或删除文件）。
- `command`: "list" 或 "delete"。
- `args`: 对于 list，传集合名（可选）；对于 delete，传 "filename"（必须精确匹配）。

**⚠️ 推荐调用方式**:
- 查看清单: `python {SKILL_DIR}/scripts/manage.py list`
- 删除文件: `python {SKILL_DIR}/scripts/manage.py delete "filename"`

## 使用场景示例

- **售前支持**: "把 demo_materials 里的白皮书存进去，然后帮我查查 QPS 指标。"
- **长期记忆**: "查询一下用户之前提到的 Python 偏好。" (需存入 memory 集合)
