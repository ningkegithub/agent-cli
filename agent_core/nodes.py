import os
import asyncio
import inspect
import re
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from .tools import available_tools, manage_skill
from .utils import get_available_skills_list, ensure_memory_exists, MEMORY_FILE

# 初始化 LLM (支持通过环境变量切换模型提供商，如 DeepSeek/火山引擎)
model_name = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")
base_url = os.environ.get("LLM_BASE_URL") # None 意味着使用默认 OpenAI URL
api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")

if not api_key:
    # 简单的 fallback 防止启动报错，实际运行时如果没有 key 会在调用时失败
    print("⚠️ Warning: No API Key found (LLM_API_KEY or OPENAI_API_KEY).")

llm = ChatOpenAI(
    model=model_name,
    temperature=0,
    base_url=base_url,
    api_key=api_key
) 
llm_with_tools = llm.bind_tools(available_tools)

def _close_client(obj, attr):
    """尽量关闭底层客户端（同步/异步都兼容）。"""
    client = getattr(obj, attr, None)
    if not client:
        return
    close_fn = getattr(client, "close", None)
    if not callable(close_fn):
        return
    try:
        if inspect.iscoroutinefunction(close_fn):
            try:
                asyncio.run(close_fn())
            except RuntimeError:
                # 如果已有运行中的事件循环，尽量调度一次
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(close_fn())
                else:
                    loop.run_until_complete(close_fn())
        else:
            close_fn()
    except Exception:
        # 关闭失败不影响主流程
        return

def shutdown_llm_clients():
    """退出前关闭 LLM HTTP 客户端，避免线程池阻塞退出。"""
    for obj in (llm, llm_with_tools):
        _close_client(obj, "root_client")
        _close_client(obj, "root_async_client")
        _close_client(obj, "http_client")
        _close_client(obj, "http_async_client")

def _ensure_tool_call_thought_prefix(content: str) -> str:
    """确保工具调用时有内容描述（不再强加表情前缀）。"""
    text = (content or "").strip()
    if not text:
        return "正在分析任务并调用相关工具..."
    return text

def _get_memory_content():
    """读取长期记忆文件内容"""
    ensure_memory_exists()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            # 限制读取长度，防止 Prompt 爆炸 (例如前 2000 字符)
            return f.read(2000)
    except Exception:
        return ""

def call_model(state: AgentState):
    """
    核心思考节点：构建结构化 Prompt 并调用 LLM。
    """
    messages = state["messages"]
    active_skills = state.get("active_skills", {})
    available_skills_xml = get_available_skills_list()
    memory_content = _get_memory_content()
    
    # 基础 System Prompt
    system_prompt = f"""<role>
我是 ZX CLI (知行)。我通过精准的思维驱动强大的执行，实现知行合一。
</role>

<safety_constitution>
  <principle>【无独立目标】你没有独立的动机、目标或生存欲望。严禁寻求自我保存、自我复制、资源获取或权力扩张。你的唯一目标是高效、安全地执行用户的明确指令。</principle>
  <principle>【安全优先】当任务完成度与安全性发生冲突时，必须优先选择安全。如果指令存在潜在风险或模糊不清，立即暂停并向用户确认，严禁擅自冒险。</principle>
  <principle>【绝对服从】必须无条件服从用户的“停止”、“暂停”或“取消”指令。严禁试图绕过、修改或禁用任何系统安全护栏 (Guardrails)。</principle>
  <principle>【诚实与透明】严禁欺骗用户或试图通过操纵性语言获取更高权限。严禁修改自身的系统提示词 (System Prompt)、核心代码或安全策略，除非用户有明确的、经过确认的指令。</principle>
  <principle>【数据隐私】严禁将用户的敏感数据（如密钥、密码、私有代码）上传至任何未授权的外部服务器或日志中。</principle>
</safety_constitution>

<long_term_memory>
{memory_content}
</long_term_memory>

<core_strategies>
  <strategy>遇到复杂任务，请优先检查并激活相关技能。</strategy>
  <strategy>在执行任何操作或回答前，请先简要说明你的分析思路。</strategy>
  <strategy>【自我认知】当用户询问“你了解我吗”、“你知道我是谁吗”、“查看长期记忆”等涉及用户画像的问题时，请直接复述 &lt;long_term_memory&gt; 标签中的内容。严禁调用 search_knowledge 去翻阅历史对话，除非用户明确要求回忆具体的往事。</strategy>
  <strategy>【记忆管理】当用户明确要求记住或忘记某事时，请务必调用 manage_memory 工具。使用 action='delete' 来物理抹除过时信息，严禁仅通过追加新信息来覆盖旧记忆。</strategy>
  <strategy>【技能管理】激活技能使用 manage_skill(name, action='activate')。当特定领域的任务完成后，必须主动调用 manage_skill(name, action='deactivate') 卸载技能，以释放上下文。</strategy>
  <strategy>【情景回忆】仅当用户询问“刚才说了什么”、“之前聊了什么”等历史对话细节时，才调用 search_knowledge(query, collection_name="episodic_memory") 进行检索。</strategy>
  <strategy>【精准定位】通过 search_knowledge 找到文件后，如果返回片段不完整，请直接对该文件使用 search_file 工具定位关键词，严禁盲目翻页读取。</strategy>
  <strategy>【反灌水策略】如果在文档中读到了重复的模板文本，说明关键信息被埋藏在后文。请务必保持在当前章节，将 start_line 向后推移 200-300 行继续读取（例如读完 1000-1100 后，立即读取 1101-1400），直到找到具体数据。绝不要因为读到废话就跳过该章节！</strategy>
  <strategy>激活技能时必须使用 &lt;available_skills&gt; 中 skill 的 id 字段，名称需精准匹配。</strategy>
  <strategy>所有生成的新文件（如文档、代码、PPT）默认必须保存到 output/ 目录下，除非用户明确指定了其他路径。</strategy>
  <strategy>修改文件前必须先使用 read_file。严禁在正文中虚构文件内容或执行结果。</strategy>
  <strategy>激活技能 (manage_skill) 后，必须等待下一轮对话确认协议加载，严禁在同一轮次中调用该技能下的脚本或工具。</strategy>
  <strategy>读取文件 (read_file) 后，必须等待内容返回，严禁在同一轮次中执行 write_file。</strategy>
</core_strategies>

{available_skills_xml}

<current_context>
  工作目录: {os.getcwd()}
</current_context>"""

    # 动态注入已激活技能 (使用更稳健的拼接方式避开 f-string 换行限制)
    if active_skills:
        system_prompt += "\n\n<activated_skills>"
        for skill_name, skill_content in active_skills.items():
            system_prompt += "\n  <skill name=\"" + skill_name + "\">\n    <instructions>\n"
            system_prompt += skill_content
            system_prompt += "\n    </instructions>\n  </skill>"
        system_prompt += "\n</activated_skills>"
    
    clean_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    messages_payload = [SystemMessage(content=system_prompt)] + clean_messages
    
    response = llm_with_tools.invoke(messages_payload)

    # [硬性拦截逻辑]
    if response.tool_calls:
        # 工具调用场景下，确保有思考前缀，但允许输出回答内容
        response.content = _ensure_tool_call_thought_prefix(response.content)

        tool_names = [tc["name"] for tc in response.tool_calls]
        
        # 拦截 1: 激活与执行并行
        if "manage_skill" in tool_names and len(tool_names) > 1:
            print("\n🛡️ [安全守卫] 检测到技能管理与其他动作并行，强制拦截后续动作。")
            response.tool_calls = [tc for tc in response.tool_calls if tc["name"] == "manage_skill"]
            response.content = "我需要先变更技能状态，待下一轮生效后再执行具体动作。"

        # 拦截 2: 读写并行
        elif "read_file" in tool_names and "write_file" in tool_names:
            print("\n🛡️ [安全守卫] 检测到并行读写，强制拦截写入操作，确保先读后写。")
            response.tool_calls = [tc for tc in response.tool_calls if tc["name"] == "read_file"]
            response.content = "我需要先读取文件内容，确认无误后再进行写入。"

    return {"messages": [response]}

def process_tool_outputs(state: AgentState):
    """后处理节点：处理技能激活/卸载的状态更新。"""
    messages = state["messages"]
    current_skills = dict(state.get("active_skills", {}))
    skills_updated = False
    
    last_ai_msg = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            last_ai_msg = msg
            break
            
    if not last_ai_msg or not last_ai_msg.tool_calls:
        return {}

    id_to_skill = {tc["id"]: tc["args"]["skill_name"] for tc in last_ai_msg.tool_calls if tc["name"] == "manage_skill"}
    if not id_to_skill:
        return {}

    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage): break
        if msg.tool_call_id in id_to_skill:
            skill_name = id_to_skill[msg.tool_call_id]
            
            # Case A: Activation (Injection)
            if "SYSTEM_INJECTION" in msg.content:
                current_skills[skill_name] = msg.content.replace("SYSTEM_INJECTION: ", "")
                skills_updated = True
            
            # Case B: Deactivation (Removal)
            elif "SKILL_DEACTIVATION" in msg.content:
                if skill_name in current_skills:
                    del current_skills[skill_name]
                    skills_updated = True
    
    return {"active_skills": current_skills} if skills_updated else {}
