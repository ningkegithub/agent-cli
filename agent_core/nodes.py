import os
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from .tools import available_tools, activate_skill

# 在核心逻辑模块中初始化 LLM
# 注意: 确保环境变量中设置了 OPENAI_API_KEY
llm = ChatOpenAI(model="gpt-4o-mini") 
llm_with_tools = llm.bind_tools(available_tools)

def call_model(state: AgentState):
    """
    核心思考节点：组装 Prompt 并调用大模型。
    """
    messages = state["messages"]
    # active_skills 现在是一个字典 {技能名: 协议内容}
    active_skills = state.get("active_skills", {})
    
    system_prompt = (
        "你是一个强大的 CLI 智能体，能够执行 Shell 命令。\n"
        "当前工作目录: " + os.getcwd() + "\n\n"
        "【重要策略】\n"
        "1. 遇到复杂任务（如爬虫、PDF处理、数据分析），请**优先**检查并激活相关技能，而不是尝试自己写 Shell 脚本或安装新软件。\n"
        "2. 如果需要处理图片或 PDF，请优先激活 `image_to_pdf` 技能。\n"
        "3. 如果需要抓取网页，请优先激活 `web_scraper` 技能。\n"
        "4. **[强制思考]** 绝不允许直接输出工具调用！在每一次返回 tool_calls 之前，你**必须**先在 content 字段中写下你的思考过程（Inner Monologue）。即使是连续执行任务，也要对每一步动作进行解释。\n"
        "5. **[严格串行]** 如果你需要激活一个技能（`activate_skill`），**必须单独**调用该工具，然后等待下一轮对话。严禁在同一次回复中同时调用 `activate_skill` 和该技能下的脚本（`run_shell`），因为你必须先等待系统返回技能详情（包含脚本路径）后才能知道如何执行。"
    )
    
    # 动态注入所有已激活的技能
    if active_skills:
        system_prompt += "\n\n=== 🌟 已激活技能列表 ==="
        for skill_name, content in active_skills.items():
            system_prompt += f"\n\n[技能: {skill_name}]\n{content}"
        system_prompt += "\n========================"
    
    # 过滤掉旧的系统消息，确保上下文清晰
    clean_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    messages_payload = [SystemMessage(content=system_prompt)] + clean_messages
    
    response = llm_with_tools.invoke(messages_payload)
    return {"messages": [response]}

def process_tool_outputs(state: AgentState):
    """
    后处理节点：检查工具执行结果，处理状态更新（如技能激活）。
    它在 ToolNode 之后运行。
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # 确保我们处理的是 ToolMessage 列表（因为 ToolNode 可能一次返回多个）
    # LangGraph 的 ToolNode 会将结果追加到 messages，所以我们要倒序找最近的一批 ToolMessage
    
    # 获取当前已激活的技能字典
    current_skills = dict(state.get("active_skills", {}))
    skills_updated = False
    
    # 重新设计策略：
    # 核心逻辑：通过 tool_call_id 将 ToolMessage 与 AIMessage 中的工具调用关联起来。
    
    # 1. 找到最近的一个 AIMessage (即发起工具调用的源头)
    last_ai_msg = None
    for msg in reversed(messages):
        if isinstance(msg, SystemMessage): continue # skip
        if isinstance(msg, AIMessage):
            last_ai_msg = msg
            break
            
    if not last_ai_msg or not last_ai_msg.tool_calls:
        return {}

    # 2. 建立 ID 到 skill_name 的映射表
    # 这一步是为了确保我们只处理 activate_skill 的结果，并且能拿到对应的技能名
    id_to_skill = {}
    for tc in last_ai_msg.tool_calls:
        if tc["name"] == "activate_skill":
            id_to_skill[tc["id"]] = tc["args"]["skill_name"]

    if not id_to_skill:
        return {}

    # 3. 扫描对应的 ToolMessage 并提取协议内容
    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage):
            break
        
        # 只有当消息ID匹配且包含特定的协议注入标识时，才更新状态
        if msg.tool_call_id in id_to_skill:
            skill_name = id_to_skill[msg.tool_call_id]
            if "SYSTEM_INJECTION" in msg.content:
                content = msg.content.replace("SYSTEM_INJECTION: ", "")
                current_skills[skill_name] = content
                skills_updated = True
    
    if skills_updated:
        return {"active_skills": current_skills}
    
    return {}
