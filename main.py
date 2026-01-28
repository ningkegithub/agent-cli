#!/usr/bin/env python3
import sys
from langchain_core.messages import HumanMessage, AIMessage
from agent_core import build_graph

def main():
    print("🤖 模块化智能体 CLI (v1.0)")
    print("---------------------------")
    print("提示：你可以试着说“把当前文件夹下的图片合并为 PDF”。")
    print("输入 'exit' 或 'quit' 退出。\n")
    
    # Check API Key
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  警告：在环境变量中未找到 OPENAI_API_KEY。")
        print("   请运行：export OPENAI_API_KEY='sk-...'")
        return

    # 初始化图
    app = build_graph()
    
    chat_history = []
    active_skills = {} # 改为字典存储多技能

    while True:
        try:
            user_input = input("用户> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            inputs = {
                "messages": chat_history + [HumanMessage(content=user_input)],
                "active_skills": active_skills
            }
            
            print("   (思考中...)")
            for event in app.stream(inputs, stream_mode="values"):
                last_msg = event["messages"][-1]
                # 从事件中获取更新后的技能池
                active_skills = event.get("active_skills", active_skills)
                
                if isinstance(last_msg, AIMessage):
                    # 1. 如果有工具调用，content 视为思考过程
                    if last_msg.tool_calls:
                        if last_msg.content:
                            print(f"🧠 [思考] {last_msg.content.strip()}")
                        for tc in last_msg.tool_calls:
                            print(f"   🤖 动作: {tc['name']}({tc['args']})")
                    # 2. 如果没有工具调用，content 视为最终回答
                    elif last_msg.content:
                        print(f"Agent> {last_msg.content.strip()}")
                
            chat_history = event["messages"]
            print("")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
