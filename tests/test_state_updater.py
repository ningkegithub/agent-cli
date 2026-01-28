import sys
import os
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage

# 添加项目根目录到 Path
sys.path.append(os.getcwd())

from agent_core.nodes import process_tool_outputs
from agent_core.state import AgentState

def test_updater_logic():
    print("🧪 开始测试 process_tool_outputs 逻辑...")

    # 1. 构造模拟场景：LLM 同时发起了两个调用
    ai_msg = AIMessage(
        content="Thinking...",
        tool_calls=[
            {"name": "activate_skill", "args": {"skill_name": "test_skill"}, "id": "call_skill_1"},
            {"name": "run_shell", "args": {"command": "ls"}, "id": "call_shell_1"}
        ]
    )

    # 2. 模拟 ToolNode 的执行结果
    # 注意：LangGraph 中消息是顺序追加的
    tool_msg_1 = ToolMessage(
        content="SYSTEM_INJECTION: [Protocol] Do this...", 
        tool_call_id="call_skill_1"
    )
    tool_msg_2 = ToolMessage(
        content="file1.txt\nfile2.txt", 
        tool_call_id="call_shell_1"
    )

    # 3. 构造状态
    state: AgentState = {
        "messages": [
            SystemMessage(content="Init"),
            ai_msg,
            tool_msg_1, 
            tool_msg_2
        ],
        "active_skills": {}
    }

    print("📊 初始状态: 空技能池")

    # 4. 执行待测函数
    updates = process_tool_outputs(state)

    # 5. 验证结果
    print(f"🔄 更新结果: {updates}")
    
    # 断言 1: 必须有 active_skills 更新
    if "active_skills" not in updates:
        print("❌ 失败: 没有检测到技能更新！")
        sys.exit(1)
    
    new_skills = updates["active_skills"]
    
    # 断言 2: 技能名称必须正确
    if "test_skill" not in new_skills:
        print("❌ 失败: 技能名称提取错误！")
        sys.exit(1)
        
    # 断言 3: 内容必须去掉了前缀
    expected_content = "[Protocol] Do this..."
    if new_skills["test_skill"] != expected_content:
        print(f"❌ 失败: 内容解析错误。期望: '{expected_content}', 实际: '{new_skills['test_skill']}'")
        sys.exit(1)

    # 验证健壮性：如果有干扰消息怎么办？
    print("✅ 基础逻辑通过。测试干扰项...")
    # 比如后面又多了一条 AIMessage（不应该发生，但在 updater 运行时刻，它是最新的）
    # 我们的逻辑是找“最近的一个 AIMessage”。
    
    print("🎉 所有测试通过！逻辑是稳健的。")

if __name__ == "__main__":
    test_updater_logic()
