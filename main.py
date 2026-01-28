#!/usr/bin/env python3
import sys
from langchain_core.messages import HumanMessage, AIMessage
from agent_core import build_graph

def main():
    print("🤖 Modular Agent CLI (v1.0)")
    print("---------------------------")
    print("Tip: Ask 'Merge images in current folder to PDF'.")
    print("Type 'exit' to quit.\n")
    
    # Check API Key
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables.")
        print("   Please run: export OPENAI_API_KEY='sk-...'")
        return

    # 初始化图
    app = build_graph()
    
    chat_history = []
    active_skills = {} # 改为字典存储多技能

    while True:
        try:
            user_input = input("User> ")
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
                    if last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            print(f"   🤖 动作: {tc['name']}({tc['args']})")
                    elif last_msg.content:
                        print(f"Agent> {last_msg.content}")
                
            chat_history = event["messages"]
            print("")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
