import unittest
import os
import sys

# 确保能导入 agent_core
sys.path.append(os.getcwd())

from agent_core.tools import read_file

# 测试靶场：那个 20 页+ 的超级白皮书 (已归档至 tests/test_data)
TARGET_FILE = "tests/test_data/office_mock/2_星云科技_产品白皮书_Full.docx"

class TestIOv2Advanced(unittest.TestCase):
    
    def setUp(self):
        if not os.path.exists(TARGET_FILE):
            self.skipTest(f"测试素材缺失: {TARGET_FILE}。请确保测试数据已正确检出。")

    def test_01_outline_mode(self):
        """测试 Docx 大纲提取"""
        print("\n🧪 Testing Outline Mode...")
        
        # 1. 调用大纲模式
        result = read_file.invoke({"file_path": TARGET_FILE, "outline_only": True})
        
        # 2. 验证基本格式
        self.assertIn("--- 文档大纲 (结构化导航) ---", result)
        self.assertIn("[提示: 请使用 start_line 跳转", result)
        
        # 3. 验证关键章节
        self.assertIn("Technical Architecture", result)
        self.assertIn("Core Technology: Rust Engine", result)
        
        # 4. 验证行号解析
        # 结果应该类似: "Line 1: ...", "Line 250: ..."
        # 我们提取几行打印出来看看
        lines = result.split("\n")
        outline_lines = [l for l in lines if l.startswith("Line ")]
        print(f"    -> 提取到 {len(outline_lines)} 个标题节点")
        print(f"    -> 示例: {outline_lines[:3]}")
        
        self.assertTrue(len(outline_lines) > 5)

    def test_02_pagination_and_wrap(self):
        """测试文本折行与分页"""
        print("\n🧪 Testing Text Wrapping & Pagination...")
        
        # 1. 读取前 50 行
        result = read_file.invoke({"file_path": TARGET_FILE, "start_line": 1, "end_line": 50})
        
        # 2. 验证图片感知
        # 脚本里插入了图片，read_file 应该能感知到
        # 注意：图片感知只有在 outline_only=False 时才生效（正文模式）
        # 但如果前 50 行没有图片，可能测不到。我们的脚本在每个章节开头都有图片。
        # 让我们找一个肯定有图片的章节。
        
        # 3. 验证折行
        # 如果折行生效，result 里应该有很多行，且每行不应过长
        lines = result.split("\n")
        long_lines = [l for l in lines if len(l) > 150] # 阈值设为 150 (代码里 wrap 是 120)
        
        if long_lines:
            print(f"    ⚠️ Warning: 发现 {len(long_lines)} 行超长文本，折行逻辑可能失效。\n")
            print(f"    -> Sample: {long_lines[0][:50]}...")
        else:
            print("    ✅ 所有文本行宽正常 (<=150 chars)")
            
        self.assertEqual(len(long_lines), 0)

    def test_03_precision_jump(self):
        """测试基于行号的精准跳转"""
        print("\n🧪 Testing Precision Jump...")
        
        # 1. 先获取大纲找到 'Core Technology: AI Models' 的位置
        outline_res = read_file.invoke({"file_path": TARGET_FILE, "outline_only": True})
        
        target_line = -1
        for line in outline_res.split("\n"):
            if "Core Technology: AI Models" in line:
                # 格式: "Line 123: ..."
                try:
                    target_line = int(line.split(":")[0].replace("Line ", ""))
                except:
                    pass
                break
        
        if target_line == -1:
            self.fail("无法在大纲中找到 AI Models 章节")
            
        print(f"    -> 目标章节 'AI Models' 位于 Line {target_line}")
        
        # 2. 精准读取该章节 (假设读 100 行够了)
        content = read_file.invoke({
            "file_path": TARGET_FILE, 
            "start_line": target_line, 
            "end_line": target_line + 100
        })
        
        # 3. 验证是否读到了该章节特有的 KEY FEATURE
        # 生成脚本里写了: "KEY FEATURE: Built-in DeepSeek-V3"
        self.assertIn("Built-in DeepSeek-V3", content)
        print("    ✅ 成功读取到深层章节的关键信息！")

if __name__ == '__main__':
    unittest.main()
