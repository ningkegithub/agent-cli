import os
import subprocess
from langchain_core.tools import tool

# Configuration
SKILL_BASE_DIR = os.path.expanduser("~/.gemini/skills")
SKILL_MAP = {
    "imagetopdf": os.path.join(SKILL_BASE_DIR, "image-to-pdf/SKILL.md"),
    "web_scraper": os.path.join(SKILL_BASE_DIR, "web-scraper/SKILL.md"),
}

@tool
def run_shell(command: str):
    """Execute shell commands. e.g. 'ls -F', 'python3 script.py'."""
    print(f"\n💻 [Shell] Executing: {command}")
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
        return f"Error executing command: {e}"

@tool
def activate_skill(skill_name: str):
    """Activate a special skill. Available: 'imagetopdf', 'web_scraper'."""
    print(f"\n⚡️ [Tool] Activating skill: {skill_name}...")
    
    target_path = SKILL_MAP.get(skill_name)
    
    if target_path and os.path.exists(target_path):
        with open(target_path, "r") as f:
            content = f.read()
        return f"SYSTEM_INJECTION: {content}"
    elif target_path:
        return f"Error: Skill definition file not found at {target_path}"
    else:
        return f"Error: Skill '{skill_name}' is not registered locally."

# Export list for binding
available_tools = [run_shell, activate_skill]
