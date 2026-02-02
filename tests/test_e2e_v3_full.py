import sys
import os
import time
import socket
import base64
from rich.console import Console
from rich.panel import Panel
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage

# 动态添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core import build_graph
from agent_core.tools import write_file

console = Console()
OUTPUT_DIR = os.path.join(project_root, "output", "e2e_v3")
OUTPUT_DIR_REL = os.path.join("output", "e2e_v3")

def can_reach_llm():
    """网络可达性检查"""
    try:
        # 简单尝试连接百度或 OpenAI 来判断出网能力
        socket.create_connection(("www.baidu.com", 80), timeout=2)
        return True
    except:
        console.print("[bold yellow]⚠️ 网络不可达，跳过在线测试。[/bold yellow]")
        return False

def create_dummy_image(filename="test_chart.png"):
    """创建一个简单的红色方块 PNG 图片，用于测试 PPT 图片插入"""
    # 1x1 Red Pixel Base64
    data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path

def setup_test_data():
    """准备测试用的数据文件和 Markdown"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Excel 源数据 (JSON)
    json_content = """[
    {"门店": "北京旗舰店", "Q1营收": 1200000, "Q2营收": 1500000},
    {"门店": "上海中心店", "Q1营收": 1100000, "Q2营收": 1350000},
    {"门店": "深圳湾店", "Q1营收": 900000, "Q2营收": 1100000}
]"""
    json_file = os.path.join(OUTPUT_DIR_REL, "test_sales_data.json")
    write_file.invoke({"file_path": json_file, "content": json_content})
    
    # 2. 图片文件
    img_path = create_dummy_image()
    img_rel = os.path.relpath(img_path, project_root)
    
    # 3. PPT 剧本 (Markdown) - 引用上面的图片
    md_content = f"""
---
## Slide 1｜季度复盘
- 数据驱动决策
- 销售业绩分析
---
## Slide 2｜业绩概览
- 核心指标增长显著
- 详情请见右侧图表
![业绩图表]({img_rel})
    """
    md_file = os.path.join(OUTPUT_DIR_REL, "test_presentation.md")
    write_file.invoke({"file_path": md_file, "content": md_content})

    return json_file, md_file, img_path

def cleanup_test_data(files):
    for f in files:
        if f and os.path.exists(f):
            try:
                os.remove(f)
            except: pass
    console.print("[dim]🧹 测试数据已清理[/dim]")
    try:
        if os.path.isdir(OUTPUT_DIR):
            os.rmdir(OUTPUT_DIR)
    except:
        pass

def run_full_regression():
    console.print(Panel.fit("[bold green]🚀 E2E v3 全量回归测试[/bold green]\n覆盖: Excel生成 / PPT图片插入 / 多技能联动", border_style="green"))
    
    if not can_reach_llm(): return

    # 1. 准备数据
    json_file, md_file, img_file = setup_test_data()
    excel_out = os.path.join(OUTPUT_DIR_REL, "test_report.xlsx")
    ppt_out = os.path.join(OUTPUT_DIR_REL, "test_slides.pptx")
    
    console.print(f"📄 测试资源就绪: [bold]{json_file}, {md_file}, {os.path.basename(img_file)}[/bold]")

    app = build_graph()
    active_skills = {}

    # 2. 构造复杂指令
    user_input = (
        f"请先激活 excel_master 技能，将 {json_file} 转换为 {excel_out}，标题设为'2026 Q1-Q2 销售报表'。"
        f"然后激活 ppt_master 技能，读取 {md_file} 生成演示文稿到 {ppt_out}。"
        "注意：PPT 中的图片请确保正确插入。"
        "所有输入/输出文件都已在 output/ 目录下，请直接使用给定路径，不要额外提示 output 规范。"
    )

    inputs = {"messages": [HumanMessage(content=user_input)], "active_skills": active_skills}
    
    console.print(f"\n[bold blue]👤 User >[/bold blue] {user_input}")
    
    tool_counts = {"excel_master": 0, "ppt_master": 0}
    
    try:
        for mode, data in app.stream(inputs, stream_mode=["updates"]):
            if mode == "updates":
                for _, node_output in data.items():
                    if not node_output: continue
                    if "messages" in node_output:
                        for msg in node_output["messages"]:
                            if isinstance(msg, ToolMessage):
                                if "excel" in msg.content or "excel" in msg.name.lower(): 
                                    tool_counts["excel_master"] += 1
                                if "ppt" in msg.content or "ppt" in msg.name.lower():
                                    tool_counts["ppt_master"] += 1
                                console.print(f"[bold yellow]⚙️ 工具执行:[/bold yellow] {msg.name}")

    except Exception as e:
        console.print(f"[bold red]❌ 错误:[/bold red] {e}")

    # 3. 验证
    console.print("\n[bold cyan]📊 回归验证报告:[/bold cyan]")
    
    # 验证 Excel
    res_excel = "❌"
    if os.path.exists(excel_out) and os.path.getsize(excel_out) > 5000: # Excel 文件通常较大
        res_excel = "✅"
    console.print(f"{res_excel} Excel 报表生成 ({excel_out})")
    
    # 验证 PPT
    res_ppt = "❌"
    if os.path.exists(ppt_out) and os.path.getsize(ppt_out) > 30000: # PPTX 带图片会比较大
        res_ppt = "✅"
    console.print(f"{res_ppt} PPT 演示文稿生成 ({ppt_out})")
    
    # 验证图片是否被脚本"吃掉"了 (PPTX 是压缩包，这里只验证文件存在且大小合理)
    
    cleanup_test_data([json_file, md_file, img_file, excel_out, ppt_out])
    
    if res_excel == "✅" and res_ppt == "✅":
        console.print(Panel("[bold green]✨ 全量回归测试通过！[/bold green]"))
    else:
        console.print(Panel("[bold red]💀 回归测试失败[/bold red]", border_style="red"))
        sys.exit(1)

if __name__ == "__main__":
    run_full_regression()
