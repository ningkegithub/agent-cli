import sys
import os
from langchain_core.messages import HumanMessage

sys.path.append(os.getcwd())

from agent_core import build_graph

def run_scenario():
    print("🎬 开始多技能串联测试场景...")
    
    # 1. 检查 API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  错误: 未设置 OPENAI_API_KEY，无法进行真实测试。")
        return

    app = build_graph()
    chat_history = []
    active_skills = {}

    # 定义用户的复杂指令
    # 我们分两步发指令，模拟用户交互
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
        
        print("🤖 Agent 思考中...")
        for event in app.stream(inputs, stream_mode="values"):
            last_msg = event["messages"][-1]
            active_skills = event.get("active_skills", active_skills)
            
            # 打印工具调用详情
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    print(f"   ⚙️  调用工具: {tc['name']} (参数: {tc['args']})")
            
            # 打印最终回复
            if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
                 if last_msg.content:
                    print(f"   🗣  回复: {last_msg.content}")

        # 更新历史
        chat_history = event["messages"]

if __name__ == "__main__":
    run_scenario()
