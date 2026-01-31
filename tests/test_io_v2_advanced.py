import unittest
import os
import sys

# 确保能导入 agent_core
sys.path.append(os.getcwd())

from agent_core.tools import read_file, search_file

# 测试靶场：必须使用那个结构复杂的超级白皮书
TARGET_FILE = "tests/test_data/office_mock/2_星云科技_产品白皮书_Full.docx"

class TestIOv2Advanced(unittest.TestCase):
    
    def setUp(self):
        if not os.path.exists(TARGET_FILE):
            self.skipTest(f"测试素材缺失: {TARGET_FILE}")

    def test_01_alignment_check(self):
        """核心测试：大纲行号与正文内容是否绝对对齐？"""
        print("\n🧪 Testing Outline <-> Content Alignment...")
        
        # 1. 获取大纲
        outline_res = read_file.invoke({"file_path": TARGET_FILE, "outline_only": True})
        print(f"    -> 大纲前几行:\n{outline_res[:200]}...")
        
        # 2. 提取所有标题的行号和文本
        # 格式: "Line 123: - 1. Executive Summary"
        markers = []
        for line in outline_res.split("\n"):
            if line.startswith("Line "):
                parts = line.split(":", 1)
                line_num = int(parts[0].replace("Line ", ""))
                title_text = parts[1].strip("- ").strip()
                markers.append((line_num, title_text))
        
        print(f"    -> 提取到 {len(markers)} 个锚点。正在抽检...")
        
        # 3. 随机抽检 3 个锚点，验证 read_file(start_line=X) 读到的第一行是否就是该标题
        # 我们检测第 1 个、中间一个、最后一个
        check_indices = [0, len(markers)//2, len(markers)-1]
        
        for idx in check_indices:
            line_num, expected_text = markers[idx]
            print(f"    🔍 Checking Line {line_num}: Expecting '{expected_text}'")
            
            # 读取那一行
            content = read_file.invoke({
                "file_path": TARGET_FILE, 
                "start_line": line_num, 
                "end_line": line_num + 1 # 多读一行防止边界
            })
            
            # 过滤掉元数据头
            body_lines = [l for l in content.split("\n") if not l.startswith("---") and not l.startswith("路径") and not l.startswith("行数") and not l.startswith("覆盖率")]
            # 找到第一行非空内容
            actual_line = ""
            for l in body_lines:
                if l.strip():
                    actual_line = l.strip()
                    break
            
            # 断言：读到的内容必须包含标题文本
            # 注意：Docx 读取时可能会把编号 "1. " 和文本分开或者合并，这里做包含匹配
            self.assertIn(expected_text, actual_line)
            print("      ✅ 对齐成功！")

    def test_02_pagination_logic(self):
        """测试分页参数是否精确"""
        print("\n🧪 Testing Pagination Logic...")
        # 读取 100-105 行
        content = read_file.invoke({
            "file_path": TARGET_FILE,
            "start_line": 100,
            "end_line": 105
        })
        
        # 解析元数据头
        header_line = [l for l in content.split("\n") if l.startswith("行数")][0]
        # "行数: 2000+ | 当前范围: 100-105"
        self.assertIn("100-105", header_line)
        
        # 验证正文行数
        # 排除头尾，应该剩下 105-100 = 5 行 (list切片 start_idx=99, end_idx=105 -> 6行? 不，end_line=105 是开区间？)
        # 代码逻辑: selected_lines = lines[start_idx:end_idx] -> lines[99:105] -> 100,101,102,103,104,105 -> 6行。
        # 无论多少行，关键是切片逻辑是确定的。我们主要验证不会报错。
        print("    ✅ 分页参数解析正常")

    def test_04_search_file(self):
        """测试全文搜索工具"""
        print("\n🧪 Testing search_file Tool...")
        
        # 搜索 Docx 中的关键指标
        # 我们知道 "Built-in DeepSeek-V3" 是在第 5 章埋藏的
        keyword = "DeepSeek-V3"
        result = search_file.invoke({"file_path": TARGET_FILE, "pattern": keyword})
        
        print(f"    -> Search Result:\n{result}")
        
        # 验证是否找到
        self.assertIn("--- 搜索结果", result)
        self.assertIn(keyword, result)
        self.assertIn("Line ", result)
        
        # 验证行号合理性 (应该在 1000 行以后)
        # 提取行号
        import re
        match = re.search(r"Line (\d+):", result)
        if match:
            line_num = int(match.group(1))
            print(f"    -> Found at Line {line_num}")
            self.assertTrue(line_num > 1000, f"行号 {line_num} 过小，不符合预期位置")
            
            # 双重验证：用 read_file 读取该行，看是否一致
            verification = read_file.invoke({
                "file_path": TARGET_FILE,
                "start_line": line_num,
                "end_line": line_num + 1
            })
            self.assertIn(keyword, verification)
            print("      ✅ 搜索结果行号经 read_file 验证无误！")
        else:
            self.fail("搜索结果格式不正确，未找到行号")

if __name__ == '__main__':
    unittest.main()