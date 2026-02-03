import sys
import os

# 动态添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core.tools import manage_skill

def test_manage_skill_lifecycle():
    print("🧪 测试技能生命周期管理 (manage_skill)...")
    
    # 1. 测试激活 (Activate)
    print("   [1/2] 测试激活 (action='activate')...")
    result_activate = manage_skill.invoke({"skill_name": "ppt_master", "action": "activate"})
    
    if "SYSTEM_INJECTION" not in result_activate:
        print(f"❌ 激活失败: 未返回 SYSTEM_INJECTION。\n返回: {result_activate}")
        sys.exit(1)
    
    if "PPT 渲染大师" not in result_activate:
        print("❌ 激活失败: 中文内容疑似未正确读取或被破坏。")
        sys.exit(1)
    print("   ✅ 激活测试通过")

    # 2. 测试卸载 (Deactivate)
    print("   [2/2] 测试卸载 (action='deactivate')...")
    result_deactivate = manage_skill.invoke({"skill_name": "ppt_master", "action": "deactivate"})
    
    if "SKILL_DEACTIVATION: ppt_master" not in result_deactivate:
        print(f"❌ 卸载失败: 未返回预期的卸载信号。\n返回: {result_deactivate}")
        sys.exit(1)
    print("   ✅ 卸载测试通过")

    print("\n✅ 所有技能管理测试通过！")

if __name__ == "__main__":
    test_manage_skill_lifecycle()