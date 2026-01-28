import os
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from .tools import available_tools, activate_skill

# Init LLM within the core logic module
# Note: Ensure OPENAI_API_KEY is set in environment
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
        "如果用户请求复杂，优先检查是否可以激活相关技能。\n"
        "当前工作目录: " + os.getcwd()
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

def handle_skill_activation(state: AgentState):
    """
    专门处理技能激活的节点，将新技能协议存储到状态中。
    """
    last_message = state["messages"][-1]
    tool_outputs = []
    
    # 获取当前已激活的技能字典副本，避免直接修改状态
    current_skills = dict(state.get("active_skills", {}))
    skills_updated = False
    
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "activate_skill":
            skill_name = tool_call["args"]["skill_name"]
            result = activate_skill.invoke(tool_call["args"])
            
            if "SYSTEM_INJECTION" in result:
                content = result.replace("SYSTEM_INJECTION: ", "")
                # 将新技能添加到字典中
                current_skills[skill_name] = content
                skills_updated = True
                feedback = f"✅ 技能 '{skill_name}' 已成功激活并加入技能池。"
            else:
                feedback = result
            
            tool_outputs.append(ToolMessage(content=feedback, tool_call_id=tool_call["id"]))
    
    updates = {"messages": tool_outputs}
    if skills_updated:
        updates["active_skills"] = current_skills
        
    return updates
