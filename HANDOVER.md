# 🔄 开发者交接日志 (Developer Handover Log)

此文件用于多 Agent (Gemini, DeepSeek, Codex) 协作时的上下文同步。
**原则**：每位 Agent 在结束工作前，必须在此处更新最新进度，以确保逻辑不中断、架构不走样；条目按时间倒序排列（最新在上），同日期按追加顺序排列。

---

## 📅 2026-02-02

### 👨‍💻 交班人: Gemini (Brand Specialist)

#### ✅ 已完成工作 (Done)
1.  **记忆管理重构 (Memory Management 2.0)**：
    -   **工具合并与增强**：废弃了功能单一的 `remember` 工具，引入全能型 `manage_memory(content, action)`。
        -   `action='add'`: 写入前执行智能相似度检查（difflib > 0.85），防止记忆重复堆叠。
        -   `action='delete'`: 支持物理删除（抹除）包含特定关键词的记忆行，彻底解决“追加式遗忘”无效的问题。
    -   **策略优化**：更新 System Prompt，明确区分【长期记忆】（直接复述标签）与【情景回忆】（查向量库），并强制 Agent 在遗忘时使用删除工具。
    -   **测试覆盖**：新增 `tests/test_memory_management.py`，覆盖了增、删、去重、异常处理全链路，确保记忆操作的原子性和安全性。
2.  **品牌升级 (Rebranding)**：
    -   项目正式更名为 **ZX CLI (ZhiXing / 知行)**，Slogan 更新为 "知行合一，极致执行"。
    -   GitHub 远程仓库已更名为 `zx-cli`。
    -   更新了 `README.md`、`GEMINI.md` 及 `cli/ui.py` 中的品牌标识。
3.  **记忆清理**：
    -   移除了关于“心学文化”的旧记忆，明确了项目的纯粹工具定位。
4.  **UI 焕新**：
    -   启动横幅 (Banner) 已更新为 ZX CLI 样式，并提供了体现全栈能力的示例 Query。

#### 🧪 已运行测试 (Tests)
- `python3 tests/test_memory_management.py` (Pass) - 验证记忆增删改逻辑。
- `git status` 确认文件变更无误。
- `gh repo rename` 确认远程仓库已更名。

#### ⚠️ 注意事项 (Notes)
- **本地目录名**：由于 Agent 正在运行中，本地目录名暂仍为 `agent-cli`。建议下次冷启动前手动执行 `mv agent-cli zx-cli`。

## 📅 2026-02-02

### 👨‍💻 交班人: Codex

#### ✅ 已完成工作 (Done)
1. **会话归档稳定性增强**：
   - 增加 `atexit` + `SIGTERM/SIGHUP` 退出钩子，覆盖非优雅退出的归档场景。
   - `ingest` 失败时输出一行摘要（含 return code 与首行错误），便于排查。
2. **E2E 输出规范收敛**：
   - `tests/test_e2e_v3_full.py` 输入/输出统一迁移到 `output/e2e_v3`。
   - Prompt 明确“路径已在 output/ 下”，避免“未遵循 output/ 规范”噪音提示。
3. **测试补充**：
   - 新增 `test_archive_session_once_guard`，保证退出归档只执行一次。

#### 🧪 已运行测试 (Tests)
- `./venv/bin/python3 tests/test_memory_archiving.py` (Pass)
- `./venv/bin/python3 tests/test_e2e_v3_full.py`（因网络不可达跳过在线测试）

#### ⚠️ 注意事项 (Notes)
- `tests/test_e2e_v3_full.py` 需要可出网环境才会执行在线回归流程。

## 📅 2026-02-02

### 👨‍💻 交班人: Gemini (Full-Stack Agent Specialist)

#### ✅ 已完成工作 (Done)
1.  **依赖环境同步 (Dependencies)**：
    -   更新了 `requirements.txt`，补齐了 `lancedb`, `fastembed`, `tantivy` 等 RAG 相关库。
    -   新增 `pandas` 依赖，并已在 `venv` 中安装，为数据处理打下基础。
2.  **Excel 自动化技能 (excel_master)**：
    -   **全新技能落地**：创建了 `skills/excel_master`。
    -   **核心功能**：支持 JSON/CSV 转样式化 Excel，具备自动列宽调整、表头着色、大标题合并等功能。
    -   **目录规范**：在 `excel_ops.py` 中强制执行了 `output/` 目录规范。
3.  **多模态能力增强 (Multi-modal)**：
    -   **新增工具**：在 `agent_core/tools.py` 中添加了 `describe_image` 工具。
    -   **视觉集成**：Agent 现在可以“看见”本地图片。工具会自动读取图片并利用 `gpt-4o-mini` (或其他视觉模型) 进行内容解析。
4.  **PPT 自动化进化 (ppt_master v1.5)**：
    -   **图片插入支持**：重构了 `md2pptx.py`，现在支持识别 Markdown 中的 `![alt](path)` 语法并将其真实插入到幻灯片右侧。
    -   **智能回退**：若图片文件不存在，会自动回退到原来的“图示建议”灰色占位符模式。
5.  **稳定性验证**：
    -   **单元测试**：清理了废旧脚本，补充了模拟素材，实现了 `unittest` 全量 15 个用例 **0 Skipped, 0 Failed**。
    -   **回归测试**：创建并跑通了 `tests/test_e2e_v3_full.py`，验证了 Excel 生成与 PPT 图片插入的跨技能协作。
6.  **配置安全**：
    -   引入 `.env` 文件管理密钥，并已加入 `.gitignore`。
    -   更新 `README.md` 指导用户配置混合模型参数。

#### 🧪 已运行测试 (Tests)
- `python3 -m unittest discover tests` (All 15 Passed)
- `python3 tests/test_e2e_v3_full.py` (E2E Regression Passed)
- 手动验证：多行输入模式 (`\` 续行) 及 PPT 图片生成。

#### ⚠️ 注意事项 (Notes)
- **E2E 提示**：`tests/test_e2e_v3_full.py` 已将输入/输出全部迁移到 `output/e2e_v3` 并在 Prompt 中明确路径，避免“output/ 规范”相关提示噪音。
- **图片路径**：在 PPT 中插入图片时，建议使用相对路径或确保 Agent 能访问到的绝对路径。
- **视觉模型配置 (New)**：
    - `describe_image` 工具已解耦，不再依赖主模型的 `LLM_` 配置。
    - 请在 `.env` 中设置 `VISION_LLM_API_KEY`（必填）、`VISION_LLM_BASE_URL` 和 `VISION_LLM_MODEL_NAME`。
    - 兼容性：若未设置 `VISION_LLM_API_KEY`，系统会自动回退尝试读取 `OPENAI_API_KEY`。

#### 🗺️ 下一步建议 (Next Steps)
1.  **知识库可视化**：考虑增加一个查看已入库文档列表的 UI 或工具。
2.  **多表联动 Excel**：增强 `excel_master`，支持从多个数据源汇总生成带 Pivot Table (透视表) 的复杂 Excel。
3.  **视觉辅助 PPT**：利用 `describe_image` 获取图片描述后，自动为 PPT 的备注栏生成更丰富的演讲稿。

#### ✅ 已完成工作 (Done)
1.  **UI 交互重构 (Stream-First Architecture)**：
    -   (同前) 修复内容重复，优化工具展示面板。
2.  **文件 I/O 能力飞跃 (File I/O 2.1)**：
    -   **多格式解析**：`read_file` 现在原生支持 `.docx`, `.pdf`, `.xlsx`, `.pptx`。
        -   **PPTX**: 支持提取幻灯片正文及**演讲者备注 (Notes)**，这是获取售前方案核心亮点的关键。
        -   PDF/Word 提取文本并支持 **图片感知 (Image Placeholder)**。
        -   Excel 自动读取所有 Sheet 并转换为 CSV 格式输出。
    -   **长文档导航 (Navigation)**：
        -   **大纲模式**：`read_file(outline_only=True)` 返回带行号的文档目录，实现上帝视角。
        -   **全文搜索**：新增 `search_file` 工具，支持正则，是在海量文本中定位关键指标（如 "QPS", "价格"）的终极武器。
    -   **原子编辑能力**：新增 `replace_in_file` 工具，支持基于上下文的精准字符串替换，避免全量重写。
3.  **Project Memex (本地知识中枢)**：
    -   **架构落地**：成功构建了基于 **LanceDB** (Vector DB) + **FastEmbed** (BGE-Small-zh) 的轻量级本地 RAG 系统。
    -   **入库即归档 (Phase 1.5)**：实现 **Copy-on-Ingest** 机制。入库文件会自动加盐 Hash 并备份至 `~/.agent-cli/documents`，数据库 `source` 字段指向归档后的绝对路径，彻底解决源文件丢失导致的死链问题。
    -   **脚本自愈 (Robustness)**：优化了 `ingest.py` / `query.py` 的路径处理逻辑。脚本现在能自动识别项目根目录并加入 `sys.path`，Agent 无需再显式注入 `PYTHONPATH=.` 即可成功运行。
    -   **闭环管理**：实现了 List/Delete 功能，删除索引时会自动同步清理影子库中的物理文件。
4.  **主动记忆系统 (Active Memory - Phase 2)**：
    -   **长期记忆**：实现了基于 `MEMORY.md` 的 Prompt 注入机制。Agent 启动即知晓用户偏好。新增 `remember` 工具用于显式写入记忆。
    -   **情景记忆**：实现了会话自动归档 (`_archive_session`) 和自动入库 (Auto-Ingest)。每日对话日志会自动同步至 `episodic_memory` 向量集合。
    -   **回忆能力**：将 `search_knowledge` 升级为 Native Tool (Wrapper)，并优化 System Prompt，教会 Agent 在被问及“历史”时主动检索情景记忆。
5.  **策略优化 (Prompt Tuning)**：
    -   **反灌水策略**：System Prompt 中植入了针对长文档的“深读”指令。当 Agent 遇到重复废话时，会自动尝试向后推移读取窗口，或切换为搜索模式。
    -   **回忆策略**：引导 Agent 区分“事实查询”（长期记忆）与“历史回溯”（情景记忆）。
6.  **稳健性与测试**：
    -   新增 `tests/test_io_v2_advanced.py`，验证了大纲提取、行号绝对对齐、搜索准确性。
    -   新增 `tests/test_skill_knowledge_base.py`，验证了 RAG 的全生命周期 (Ingest->Search->Delete->Auto-Migration)。
    -   新增 `tests/test_memory_archiving.py`，验证了会话归档与自动同步流程。
    -   更新 `requirements.txt` 引入 `lancedb`, `fastembed`, `tantivy`。

#### 🧪 已运行测试 (Tests)
- `PYTHONPATH=. ./venv/bin/python3 -m unittest discover tests/` (All 12 Tests Passed)
- 手动验证：售前方案生成场景（处理 20页+ Word 和 多 Sheet Excel）。
- 用户验收：通过 CLI 对话完成知识库的增删改查，以及“讲笑话”的情景回忆。

#### ⚠️ 注意事项 (Notes)
- **记忆路径**：
    - 长期记忆: `~/.agent-cli/memory/MEMORY.md`
    - 情景日志: `~/.agent-cli/memory/logs/YYYY-MM-DD/`
    - 向量数据: `~/.agent-cli/memory/lancedb_store`
- **首次运行**：第一次调用 `knowledge_base` 时会自动下载 BGE 模型 (~300MB)，需确保网络通畅。
- **情景记忆**：已实现会话自动归档并入库到 `episodic_memory`（退出时由 `_archive_session` 调用 `skills/knowledge_base/scripts/ingest.py`）。

---

## 📅 2026-01-30

### 👨‍💻 交班人: Codex

#### ✅ 已完成工作 (Done)
1. **依赖与健壮性修复**：
   - 修正 `requirements.txt` 拼写错误（拆分 `beautifulsoup4` / `prompt_toolkit`）。
   - 修复消息去重逻辑：`msg.id` 为空时避免全量误去重。
   - `activate_skill` 读取 `SKILL.md` 强制 `utf-8`。
   - `ppt_master` 模板缺失时给出中文回退提示。
2. **技能发现与激活规范化**：
   - `<available_skills>` 输出加入 `id` 字段；系统提示要求使用 `id` 精准匹配。
   - 移除别名机制，改为 **建议提示**（difflib 近似匹配）。
   - `activate_skill` 失败时返回可用技能清单与建议。
3. **CLI 退出与稳定性**：
   - `Ctrl+C` 退出逻辑增强：任务中取消、双击退出。
   - 退出时主动关闭 LLM HTTP 客户端，减少解释器 shutdown 卡顿。
4. **UI 渲染策略收敛**：
   - 放弃“思考/回答分区”，回归单一流式 Markdown 输出。
   - 工具调用前快照固化 + 前缀裁剪，减少重复输出。
5. **测试补充与调整**：
   - 新增：`test_activate_skill_encoding.py`、`test_skill_suggestions.py`、`test_model_output_constraints.py`。
   - 删除已不适用：`test_skill_alias.py`、`test_thought_split.py`。
   - `test_basic_flow.py` / `test_e2e_v2.py` 增加网络可达预检，避免沙箱误失败。

#### 🧪 已运行测试 (Tests)
- `./venv/bin/python3 tests/test_model_output_constraints.py`
- `./venv/bin/python3 tests/test_thought_split.py`（后续已删除）
- `./venv/bin/python3 tests/test_skill_suggestions.py`
- `./venv/bin/python3 tests/test_activate_skill_encoding.py`
- `./venv/bin/python3 tests/test_skill_discovery.py`
- `./venv/bin/python3 tests/test_atomic_tools.py` / `tests/test_guardrail.py` / `tests/test_state_updater.py` / `tests/test_cli_components.py`
> 注：`test_basic_flow.py` / `test_e2e_v2.py` 在沙箱网络下因 DNS/出网限制失败，用户已在本机终端跑通。

#### ⚠️ 注意事项 (Notes)
- 当前 UI 已恢复为“单一输出流”，不再区分思考/回答；模型仍可能输出“🧠 [思考]”文本（原样展示）。
- `available_skills` 里以 `id` 为准，不再支持别名；提示会给出相近技能建议。
- 若后续恢复“分区视图”，需重新引入拆分逻辑与对应测试。

## 📅 2026-01-30

### 👨‍💻 交班人: Gemini 3 Pro (协助构建者)

#### ✅ 已完成工作 (Done)
1.  **架构升级 (v1.7)**：
    - 完成 `main.py` 的模块化重构，核心代码已拆分至 `cli/` 模块化包。
    - 确立了“职责单一”原则：`ui.py` 负责渲染，`async_worker.py` 负责逻辑，`config.py` 负责配置。
2.  **UI/UX 革命**：
    - 引入 `rich` 库，实现了 **Token 级流式 Markdown 渲染**。
    - 引入 **多线程架构**，支持动态 Spinner、实时计时器 (s) 和骚话文案。
    - 实现了 **Ctrl+C 优雅中断** 和 `exit` 彻底退出。
3.  **PPT 自动化 (ppt_master)**：
    - 实现了 Markdown 剧本 -> 2024 金蝶标准模板 PPTX 的完美渲染。
    - 增加了“图示建议”视觉占位功能。
4.  **模型中立化**：
    - 解耦了模型提供商，使本项目（Agent CLI）成功切换至 **DeepSeek (火山引擎 Ark)** 驱动。
5.  **工程化加固**：
    - 确立了 `output/` 目录规范，Agent 生成的文件强制存入该目录。
    - 完善了 `.gitignore`，清理了历史垃圾文件。
    - 测试金字塔搭建完成：包含原子工具、守卫逻辑、XML 发现、E2E v2 全链路测试。

#### 🚧 进行中/未完成 (WIP)
- **UI 细节**：目前的 `Live` 渲染在工具调用频繁时，偶尔会有微小的闪烁，但已通过“分段固化”策略降至最低。
- **PPT 图片插入**：目前的 `ppt_master` 仅支持文字填充，尚未实现真正的图片自动插入逻辑。

#### 🗺️ 下一步建议 (Next Steps)
1.  **Excel 自动化技能**：这是原定的下一个核心技能。建议 Codex 实现一个能读取 CSV/Excel 并生成统计报表的工具。
2.  **多模态增强**：探索如何让 Agent “看见”本地图片，并将其合理地排版进 PPT。
3.  **自动化验收**：Codex 开始工作前，请务必运行 `./venv/bin/python3 tests/test_e2e_v2.py` 确保环境一致。