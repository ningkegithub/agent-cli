import os
import sys

# 模拟 agent_core/tools.py 中的路径逻辑
CURRENT_FILE = os.path.abspath("agent_core/tools.py") # 假设我们在根目录运行
AGENT_CORE_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.dirname(AGENT_CORE_DIR)
INTERNAL_SKILLS_DIR = os.path.join(PROJECT_ROOT, "skills")
USER_SKILLS_DIR = os.path.expanduser("~/.gemini/skills")

print(f"Current Working Dir: {os.getcwd()}")
print(f"Calculated Project Root: {PROJECT_ROOT}")
print(f"Internal Skills Dir: {INTERNAL_SKILLS_DIR}")

# Check if skills exist
skills = ["imagetopdf", "web_scraper"]
for skill in skills:
    path = os.path.join(INTERNAL_SKILLS_DIR, skill, "SKILL.md")
    print(f"Checking {skill}: {path} -> Exists? {os.path.exists(path)}")
