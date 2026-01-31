import unittest
import os
import shutil
from agent_core.tools import read_file, write_file, replace_in_file

TEST_DIR = "tests/test_data"
TEST_FILE = os.path.join(TEST_DIR, "sample.txt")

class TestNewIO(unittest.TestCase):
    
    def setUp(self):
        """每个测试前运行：创建测试目录和文件"""
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)
        os.makedirs(TEST_DIR)
        
        # 创建一个 1000 行的测试文件
        with open(TEST_FILE, "w", encoding="utf-8") as f:
            for i in range(1, 1001):
                f.write(f"Line {i}: This is content for line {i}.\n")

    def tearDown(self):
        """每个测试后运行：清理"""
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    def test_read_file_pagination(self):
        """测试分页读取"""
        print("\n🧪 Testing read_file pagination...")
        
        # 读取 10-20 行
        content = read_file.invoke({"file_path": TEST_FILE, "start_line": 10, "end_line": 20})
        
        # 验证行数
        lines = content.strip().split("\n")
        # 第一行是 [系统提示] 元数据
        self.assertTrue("系统提示" in lines[0])
        
        real_lines = lines[1:]
        # start_line=10 (Line 10), end_line=20.
        # Python slice [9:20] -> 11 items.
        # But wait, logic is lines[start_idx:end_idx].
        # start_idx = 9, end_idx = 20.
        # Line 10 (idx 9) ... Line 20 (idx 19). Total 11 lines.
        # Let's verify output content.
        
        self.assertEqual(len(real_lines), 11)
        self.assertIn("Line 10:", real_lines[0])
        self.assertIn("Line 20:", real_lines[-1])

    def test_read_file_truncation(self):
        """测试默认截断"""
        print("\n🧪 Testing read_file default truncation...")
        content = read_file.invoke({"file_path": TEST_FILE}) # 默认读 500 行
        
        self.assertIn("系统提示", content)
        self.assertIn("文件过长", content)
        
        lines = content.split("\n")
        self.assertTrue(len(lines) >= 500)

    def test_replace_in_file_success(self):
        """测试原子替换成功"""
        print("\n🧪 Testing replace_in_file success...")
        
        # 替换 Line 500
        old_str = "Line 500: This is content for line 500."
        new_str = "Line 500: MODIFIED CONTENT HERE."
        
        res = replace_in_file.invoke({"file_path": TEST_FILE, "old_string": old_str, "new_string": new_str})
        self.assertIn("成功", res)
        
        # 验证结果
        content = read_file.invoke({"file_path": TEST_FILE, "start_line": 500, "end_line": 500})
        self.assertIn("MODIFIED CONTENT HERE", content)

    def test_replace_in_file_fail_not_unique(self):
        """测试原子替换失败：内容不唯一"""
        print("\n🧪 Testing replace_in_file ambiguity check...")
        
        # 构造重复内容
        path = os.path.join(TEST_DIR, "dup.txt")
        write_file.invoke({"file_path": path, "content": "Hello\nWorld\nHello\n"})
        
        res = replace_in_file.invoke({"file_path": path, "old_string": "Hello", "new_string": "Hi"})
        self.assertIn("错误", res)
        self.assertIn("出现了多次", res)
        
        # 验证文件未被修改
        content = read_file.invoke({"file_path": path})
        self.assertEqual(content.count("Hello"), 2)

    def test_replace_in_file_fail_not_found(self):
        """测试原子替换失败：内容不存在"""
        print("\n🧪 Testing replace_in_file not found...")
        
        res = replace_in_file.invoke({"file_path": TEST_FILE, "old_string": "Line 9999", "new_string": "Whatever"})
        self.assertIn("错误", res)
        self.assertIn("未找到", res)

if __name__ == '__main__':
    unittest.main()
