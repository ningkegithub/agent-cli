from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .nodes import call_model, process_tool_outputs
from .tools import available_tools

def build_graph():
    workflow = StateGraph(AgentState)

    # 1. 定义节点
    workflow.add_node("agent", call_model)
    # 使用标准 ToolNode 处理所有工具（包括 activate_skill 和 run_shell）
    workflow.add_node("tools", ToolNode(available_tools))
    # 新增状态更新节点，处理技能激活的副作用
    workflow.add_node("skill_state_updater", process_tool_outputs)

    # 2. 设置入口
    workflow.set_entry_point("agent")

    # 3. 定义路由逻辑
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        # 如果没有工具调用，结束对话
        if not last_message.tool_calls:
            return END
        # 否则去执行工具
        return "tools"

    # 4. 连接节点
    # agent -> 判断 -> tools
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    
    # tools 执行完 -> 更新技能状态
    workflow.add_edge("tools", "skill_state_updater")
    
    # 更新完状态 -> 回到 agent 继续思考
    workflow.add_edge("skill_state_updater", "agent")

    return workflow.compile()
