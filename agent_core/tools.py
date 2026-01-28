import os
import subprocess
import sys
from langchain_core.tools import tool

# 配置项
# 动态计算路径，确保在任何机器上都能找到 skills 目录
CURRENT_FILE = os.path.abspath(__file__)
AGENT_CORE_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.dirname(AGENT_CORE_DIR)
INTERNAL_SKILLS_DIR = os.path.join(PROJECT_ROOT, "skills")
USER_SKILLS_DIR = os.path.expanduser("~/.gemini/skills") # 保留用户目录作为扩展

@tool
def run_shell(command: str):
    """执行 Shell 命令。例如：'ls -F', 'python3 script.py'。"""
    
    # [自动修复] 确保 Python 脚本在相同的虚拟环境 (venv) 中运行
    cmd_stripped = command.strip()
    if cmd_stripped.startswith("python3 ") or cmd_stripped.startswith("python "):
        parts = cmd_stripped.split(" ", 1)
        if len(parts) > 1:
            # 将 'python'/'python3' 替换为当前解释器的绝对路径
            original_cmd = command
            command = f"{sys.executable} {parts[1]}"
            print(f"🔄 [环境修复] 重定向至当前 Python: {sys.executable}")

    print(f"\n💻 [Shell] 执行中: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        if len(output) > 2000:
            output = output[:2000] + "...(truncated)"
        return output
    except Exception as e:
        return f"命令执行错误: {e}"

@tool
def activate_skill(skill_name: str):
    """激活特殊技能。例如：'imagetopdf', 'web_scraper'。"""
    print(f"\n⚡️ [工具] 激活技能: {skill_name}...")
    
    # 搜索优先级：项目内置技能 > 用户自定义技能
    search_paths = [
        os.path.join(INTERNAL_SKILLS_DIR, skill_name, "SKILL.md"),
        os.path.join(USER_SKILLS_DIR, skill_name, "SKILL.md")
    ]
    
    target_file = None
    skill_base_dir = None
    
    for path in search_paths:
        if os.path.exists(path):
            target_file = path
            skill_base_dir = os.path.dirname(path)
            break
            
    if target_file and skill_base_dir:
        try:
            with open(target_file, "r") as f:
                content = f.read()
            
            # [关键] 动态变量注入
            # 将 {SKILL_DIR} 替换为技能的真实绝对路径
            # 这样 Agent 无论在哪里运行，都能找到 scripts/ 下的脚本
            injected_content = content.replace("{SKILL_DIR}", skill_base_dir)
            
            return f"SYSTEM_INJECTION: {injected_content}"
        except Exception as e:
            return f"读取技能文件错误: {e}"
    else:
        return f"错误: 本地未找到技能 '{skill_name}'。"

# 导出工具列表以供绑定
available_tools = [run_shell, activate_skill]
