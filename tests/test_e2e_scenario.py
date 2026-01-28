import sys
import os
from langchain_core.messages import HumanMessage

# 动态添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core import build_graph

def run_scenario():
    print("🎬 开始多技能串联测试场景 (E2E)...")
    
    # 1. 检查 API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  错误: 未设置 OPENAI_API_KEY，无法进行真实测试。")
        return

    app = build_graph()
    chat_history = []
    active_skills = {}

    # 定义用户的复杂指令
    steps = [
        "请激活 web_scraper 和 image_to_pdf 这两个技能。",
        "现在，请帮我爬取 'https://www.python.org' 首页的所有图片，下载到 'downloaded_images' 目录，然后把它们合并成一个名为 'python_images.pdf' 的文件。"
    ]

    for step_input in steps:
        print(f"\n👤 User: {step_input}")
        inputs = {
            "messages": chat_history + [HumanMessage(content=step_input)],
            "active_skills": active_skills
        }
        
        print("🤖 Agent 运行中...")
        for event in app.stream(inputs, stream_mode="values"):
            last_msg = event["messages"][-1]
            active_skills = event.get("active_skills", active_skills)
            
            # 打印思考内容
            if last_msg.content:
                print(f"   🧠 [思考] {last_msg.content[:100]}..." if len(last_msg.content) > 100 else f"   🧠 [思考] {last_msg.content}")

            # 打印工具调用详情
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    print(f"   ⚙️  调用工具: {tc['name']} (参数: {tc['args']})")

        # 更新历史
        chat_history = event["messages"]
    
    print("\n✅ E2E 场景测试完成！")

if __name__ == "__main__":
    run_scenario()
