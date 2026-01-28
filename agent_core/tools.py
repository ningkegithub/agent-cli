import os
import subprocess
import sys
from langchain_core.tools import tool

import yaml

# 配置项
# 动态计算路径，确保在任何机器上都能找到 skills 目录
CURRENT_FILE = os.path.abspath(__file__)
AGENT_CORE_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.dirname(AGENT_CORE_DIR)
INTERNAL_SKILLS_DIR = os.path.join(PROJECT_ROOT, "skills")
USER_SKILLS_DIR = os.path.expanduser("~/.gemini/skills") # 保留用户目录作为扩展

def get_available_skills_list():
    """扫描所有可用技能并返回其名称和描述的 XML 格式字符串。"""
    search_dirs = [INTERNAL_SKILLS_DIR, USER_SKILLS_DIR]
    skills_found = []

    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
        
        # 遍历每个子目录
        for skill_dir in os.listdir(base_dir):
            skill_path = os.path.join(base_dir, skill_dir)
            if not os.path.isdir(skill_path):
                continue
            
            skill_md = os.path.join(skill_path, "SKILL.md")
            if os.path.exists(skill_md):
                try:
                    with open(skill_md, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # 简单的 YAML Frontmatter 提取
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            metadata = yaml.safe_load(parts[1])
                            name = metadata.get("name", skill_dir)
                            desc = metadata.get("description", "无描述")
                            skills_found.append({"name": name, "description": desc})
                except Exception:
                    # 忽略解析错误的技能
                    continue
    
    # 转换为 XML 格式
    if not skills_found:
        return "<available_skills>\n  <!-- 未发现本地技能 -->\n</available_skills>"
    
    xml_parts = ["<available_skills>"]
    for s in skills_found:
        xml_parts.append(f'  <skill name="{s["name"]}">{s["description"]}</skill>')
    xml_parts.append("</available_skills>")
    
    return "\n".join(xml_parts)

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
