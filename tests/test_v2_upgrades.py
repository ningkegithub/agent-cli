import unittest
import os
import sys
import shutil

# 确保能导入 agent_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_core.tools import write_file

class TestV2Upgrades(unittest.TestCase):
    
    def test_write_file_sandboxing(self):
        """验证 write_file 的分区重定向功能"""
        print("\n🧪 测试文件分区隔离...")
        
        # 1. 尝试写一个数据文件到根目录
        result_data = write_file.invoke({"file_path": "root_data.json", "content": '{"test": 1}'})
        self.assertIn("output/root_data.json", result_data)
        self.assertIn("已触发分区隔离", result_data)
        self.assertTrue(os.path.exists("output/root_data.json"))
        
        # 2. 尝试写一个脚本文件到根目录
        result_script = write_file.invoke({"file_path": "naughty_script.py", "content": "print(1)"})
        self.assertIn("tmp/naughty_script.py", result_script)
        self.assertIn("已触发分区隔离", result_script)
        self.assertTrue(os.path.exists("tmp/naughty_script.py"))
        
        print("   ✅ 路径隔离测试通过")

    def test_excel_auto_sum(self):
        """验证 Excel 自动汇总功能"""
        print("\n🧪 测试 Excel 自动汇总...")
        
        # 准备数据
        mock_json = "tmp/mock_sales.json"
        os.makedirs("tmp", exist_ok=True)
        with open(mock_json, "w", encoding="utf-8") as f:
            f.write('[{"item": "A", "val": 100}, {"item": "B", "val": 200}]')
            
        output_xlsx = "output/test_sum.xlsx"
        if os.path.exists(output_xlsx): os.remove(output_xlsx)
        
        # 运行脚本
        import subprocess
        cmd = [sys.executable, "skills/excel_master/scripts/excel_ops.py", 
               "--input", mock_json, "--output", output_xlsx, "--calculate", "total"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 0)
        self.assertIn("正在为以下列生成总计: val", res.stdout)
        
        # 使用我们的工具读取生成的 Excel 确认内容
        from agent_core.tools import read_file
        excel_content = read_file.invoke({"file_path": output_xlsx})
        
        # 期望看到 '总计' 行
        self.assertIn("总计", excel_content)
        self.assertIn("300", excel_content) # 100 + 200
        
        print("   ✅ Excel 自动汇总测试通过")

    @classmethod
    def tearDownClass(cls):
        # 清理
        for f in ["output/root_data.json", "tmp/naughty_script.py", "tmp/mock_sales.json"]:
            if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    unittest.main()

