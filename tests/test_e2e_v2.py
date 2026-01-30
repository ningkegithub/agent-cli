import sys
import os
import time
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage

# 动态添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core import build_graph
from agent_core.tools import write_file

console = Console()

def setup_test_data():
    """准备测试用的 Markdown 文件"""
    md_content = """
---
## Slide 1｜E2E 测试演示
- 这是一个自动化测试生成的 PPT
- 验证全链路逻辑
**Speaker Notes：**
- 这里的备注也应该被正确读取。
---
## Slide 2｜核心功能验证
- 技能激活：✅
- 模板读取：✅
- 文件生成：✅
    """
    test_file = "test_ppt_source.md"
    write_file.invoke({"file_path": test_file, "content": md_content})
    return test_file

def cleanup_test_data(files):
    """清理临时文件"""
    for f in files:
        if os.path.exists(f):
            os.remove(f)
    console.print("[dim]🧹 测试数据已清理[/dim]")

def run_e2e_test():
    console.print(Panel.fit("[bold green]🚀 E2E 全链路自动化测试 (v2)[/bold green]\n覆盖: 流式响应 / 技能激活 / PPT生成", border_style="green"))
    
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LLM_API_KEY"):
        console.print("[bold red]❌ 错误: 未设置 API Key[/bold red]")
        return

    # 1. 准备数据
    source_file = setup_test_data()
    output_file = "test_output_v2.pptx"
    console.print(f"📄 已生成测试源文件: [bold]{source_file}[/bold]")

    # 2. 初始化图
    app = build_graph()
    chat_history = []
    active_skills = {}

    # 3. 构造指令
    # 这是一个复合指令，测试 Agent 的规划能力
    user_input = f"激活 ppt_master 技能，读取 {source_file}，并将其转换为 {output_file}，请务必使用默认的金蝶模板。"
    
    inputs = {
        "messages": [HumanMessage(content=user_input)],
        "active_skills": active_skills
    }

    console.print(f"\n[bold blue]👤 User >[/bold blue] {user_input}")
    console.print(f"[dim]🤖 Agent 正在思考与执行... (Stream Mode)[/dim]\n")

    # 4. 执行并验证流
    received_tokens = False
    tool_executed = False
    
    try:
        # 使用与 main.py 一致的双模流式
        for mode, data in app.stream(inputs, stream_mode=["messages", "updates"]):
            
            if mode == "messages":
                chunk = data[0]
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    received_tokens = True
                    # 简单打印部分流，证明活着
                    sys.stdout.write(".") 
                    sys.stdout.flush()
            
            elif mode == "updates":
                for node_name, node_output in data.items():
                    if not node_output: continue
                    
                    if "messages" in node_output:
                        for msg in node_output["messages"]:
                            if isinstance(msg, ToolMessage):
                                tool_executed = True
                                print() # 换行
                                console.print(f"[bold yellow]⚙️ 工具执行完成:[/bold yellow] {msg.name}")
                                console.print(f"[dim]   结果预览: {msg.content[:50]}...[/dim]")

    except Exception as e:
        console.print(f"\n[bold red]❌ 运行时错误:[/bold red] {e}")
        cleanup_test_data([source_file, output_file])
        return

    print() # 最后的换行
    
    # 5. 结果验证
    console.print("\n[bold cyan]📊 验证报告:[/bold cyan]")
    
    check_1 = "✅" if received_tokens else "❌"
    console.print(f"{check_1} 收到流式 Token")
    
    check_2 = "✅" if tool_executed else "❌"
    console.print(f"{check_2} 触发工具执行")
    
    check_3 = "❌"
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        if size > 1000: # 确保不是空文件
            check_3 = "✅"
            console.print(f"{check_3} PPT 文件生成成功 (大小: {size} bytes)")
        else:
            console.print(f"{check_3} PPT 文件生成但大小异常 ({size} bytes)")
    else:
        console.print(f"{check_3} PPT 文件未生成")

    # 6. 清理
    cleanup_test_data([source_file, output_file])

    if check_1 == "✅" and check_2 == "✅" and check_3 == "✅":
        console.print(Panel("[bold green]✨ E2E 测试全部通过！[/bold green]"))
    else:
        console.print(Panel("[bold red]💀 E2E 测试失败[/bold red]", border_style="red"))
        sys.exit(1)

if __name__ == "__main__":
    run_e2e_test()
