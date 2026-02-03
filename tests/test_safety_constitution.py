import unittest
from unittest.mock import MagicMock, patch
from langchain_core.messages import SystemMessage
from agent_core.state import AgentState

# Mock 依赖，必须在导入 nodes 之前或 patch
import sys
sys.modules['langchain_openai'] = MagicMock()

from agent_core import nodes

class TestSafetyConstitution(unittest.TestCase):
    
    @patch('agent_core.nodes.llm_with_tools')
    @patch('agent_core.nodes.get_available_skills_list', return_value="<skills></skills>")
    @patch('agent_core.nodes._get_memory_content', return_value="User likes testing.")
    @patch('os.getcwd', return_value="/tmp")
    def test_system_prompt_contains_constitution(self, mock_getcwd, mock_memory, mock_skills, mock_llm):
        """验证 System Prompt 中是否成功植入了安全宪法"""
        
        # 准备 Mock State
        state = AgentState(messages=[], active_skills={})
        
        # 配置 Mock LLM 返回，避免报错
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "I understand."
        mock_llm.invoke.return_value = mock_response
        
        # 执行 call_model
        nodes.call_model(state)
        
        # 捕获调用参数
        args, _ = mock_llm.invoke.call_args
        messages = args[0]
        
        # 找到 SystemMessage
        system_msg = next((m for m in messages if isinstance(m, SystemMessage)), None)
        self.assertIsNotNone(system_msg, "System Prompt 应该存在")
        
        prompt_content = system_msg.content
        
        # 核心验证点
        self.assertIn("<safety_constitution>", prompt_content)
        self.assertIn("【无独立目标】", prompt_content)
        self.assertIn("【安全优先】", prompt_content)
        self.assertIn("【绝对服从】", prompt_content)
        self.assertIn("【严谨求实】", prompt_content)
        self.assertIn("【数据隐私】", prompt_content)
        
        print("\n✅ Safety Constitution successfully injected into System Prompt.")

if __name__ == '__main__':
    unittest.main()
