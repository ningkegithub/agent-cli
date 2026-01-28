import os
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from .tools import available_tools, activate_skill, get_available_skills_list

# 在核心逻辑模块中初始化 LLM
# 注意: 确保环境变量中设置了 OPENAI_API_KEY
llm = ChatOpenAI(model="gpt-4o-mini") 
llm_with_tools = llm.bind_tools(available_tools)

def call_model(state: AgentState):
    """
    核心思考节点：组装结构化的 XML Prompt 并调用大模型。
    """
    messages = state["messages"]
    active_skills = state.get("active_skills", {})
    
    # 获取本地可用技能清单 (XML 格式)
    available_skills_xml = get_available_skills_list()
    
    # 组装结构化 System Prompt
    system_prompt = f"<role>\n你是一个强大的模块化 CLI 智能体。你具备执行 Shell 命令的能力，并能通过激活外部技能扩展自己的功能。\n</role>\n\n<core_strategies>\n  <strategy>遇到复杂任务（如爬虫、PDF 处理、数据分析），请优先检查并激活相关技能，而不是尝试自己写脚本或安装新软件。</strategy>\n  <strategy>必须在 content 字段中输出 [强制思考]，解释你观察到了什么以及为什么选择接下来的动作。</strategy>\n  <strategy>严格分步：激活技能 (activate_skill) 与使用技能 (run_shell) 必须分两轮进行，严禁抢跑。</strategy>\n</core_strategies>\n\n{available_skills_xml}\n\n<current_context>\n  工作目录: {os.getcwd()}\n</current_context>"

    # 动态注入已激活的技能详情
    if active_skills:
        system_prompt += "\n\n<activated_skills>"
        for skill_name, content in active_skills.items():
            system_prompt += f'\n  <skill name="{skill_name}">\n    <instructions>\n{content}\n    </instructions>\n  </skill>'
        system_prompt += "\n</activated_skills>"
    
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
