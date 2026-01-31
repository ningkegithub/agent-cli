import os
import subprocess
import sys
import csv
import io
import textwrap
from langchain_core.tools import tool
from .utils import INTERNAL_SKILLS_DIR, USER_SKILLS_DIR, get_available_skills_hint, get_skill_suggestions

# 尝试导入可选依赖
try:
    import docx
    import pypdf
    import openpyxl
    HAS_OFFICE_DEPS = True
except ImportError:
    HAS_OFFICE_DEPS = False

@tool
def run_shell(command: str):
    """执行 Shell 命令。"""
    cmd_stripped = command.strip()
    if cmd_stripped.startswith("python3 ") or cmd_stripped.startswith("python "):
        parts = cmd_stripped.split(" ", 1)
        if len(parts) > 1:
            command = f"{sys.executable} {parts[1]}"
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
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
    """激活特殊技能。"""
    normalized_name = skill_name.strip()
    search_paths = [
        os.path.join(INTERNAL_SKILLS_DIR, normalized_name, "SKILL.md"),
        os.path.join(USER_SKILLS_DIR, normalized_name, "SKILL.md")
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
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            injected_content = content.replace("{SKILL_DIR}", skill_base_dir)
            return f"SYSTEM_INJECTION: {injected_content}"
        except Exception as e:
            return f"读取技能文件错误: {e}"
    else:
        suggestions = get_skill_suggestions(normalized_name)
        hint = get_available_skills_hint()
        err_msg = f"错误: 本地未找到技能 '{skill_name}'."
        if suggestions: err_msg += f"你是不是要找: {', '.join(suggestions)}."
        if hint: err_msg += f"可用技能: {hint}"
        return err_msg

def _read_docx(file_path, outline_only=False):
    doc = docx.Document(file_path)
    lines_pool = []
    outline = []
    
    # 遍历所有段落
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            # 即使是空行也要占位，确保行号对齐
            lines_pool.append("")
            continue
            
        # 记录大纲
        if para.style.name.startswith('Heading'):
            try:
                level = int(para.style.name.split()[-1])
                indent = "  " * (level - 1)
                outline.append(f"Line {len(lines_pool) + 1}: {indent}- {text}")
            except: pass

        # 文本折行：超过 120 字符拆分
        if len(text) > 120:
            wrapped = textwrap.fill(text, width=120)
            wrapped_lines = wrapped.splitlines()
            lines_pool.extend(wrapped_lines)
        else:
            lines_pool.append(text)
            
    # 图片感知
    img_count = len(doc.inline_shapes)
    if img_count > 0:
        lines_pool.append(f"\n[系统提示: 该文档包含 {img_count} 张图片]")

    if outline_only:
        if not outline: return "--- 文档大纲 ---\n[未检测到标准标题样式]\n"
        return "--- 文档大纲 (结构化导航) ---\n" + "\n".join(outline)
        
    return "\n".join(lines_pool)

def _read_pdf(file_path):
    reader = pypdf.PdfReader(file_path)
    text = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        wrapped_lines = []
        for line in page_text.splitlines():
             wrapped_lines.append(textwrap.fill(line, width=120) if len(line) > 120 else line)
        
        img_count = len(page.images)
        img_placeholder = f"\n[IMAGE_PLACEHOLDER: Page {i+1} 包含 {img_count} 张图片]\n" if img_count > 0 else ""
        text.append(f"--- Page {i+1} ---\n" + "\n".join(wrapped_lines) + img_placeholder)
    return "\n".join(text)

def _read_excel(file_path):
    wb = openpyxl.load_workbook(file_path, data_only=True)
    output = []
    for sheet_name in wb.sheetnames:
        output.append(f"--- Sheet: {sheet_name} ---")
        ws = wb[sheet_name]
        si = io.StringIO()
        writer = csv.writer(si)
        for row in ws.rows:
            writer.writerow([cell.value for cell in row])
        output.append(si.getvalue())
    return "\n".join(output)

@tool
def read_file(file_path: str, start_line: int = 1, end_line: int = -1, outline_only: bool = False):
    """
    全能文件读取器。支持读取纯文本 (.txt, .md, .py, .json) 以及办公文档 (.docx, .pdf, .xlsx)。
    1. 自动解析：对于 Office/PDF 文档，工具会自动提取文本内容及图片占位符信息。
    2. 大纲模式：设置 outline_only=True 获取 Docx 目录及行号映射，实现精准跳转。
    3. 分页功能：支持使用 start_line 和 end_line 进行按行分页读取（行号从 1 开始）。
    """
    if not os.path.exists(file_path):
        return f"错误: 未找到文件 '{file_path}'."
    
    ext = os.path.splitext(file_path)[1].lower()
    try:
        content_full = ""
        # 1. 格式分发
        if HAS_OFFICE_DEPS:
            if ext == ".docx":
                content_full = _read_docx(file_path, outline_only=outline_only)
                if outline_only: return content_full
            elif ext == ".pdf":
                content_full = _read_pdf(file_path)
            elif ext in [".xlsx", ".xls"]:
                content_full = _read_excel(file_path)
        
        # 2. 文本处理
        if not content_full:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = content_full.splitlines(keepends=True)
            
        total_lines = len(lines)
        start_idx = max(0, start_line - 1)
        
        # 默认 500 行保护
        if end_line == -1:
            end_idx = min(start_idx + 500, total_lines)
        else:
            end_idx = min(end_line, total_lines)
        
        selected_lines = lines[start_idx:end_idx]
        content_slice = "".join(selected_lines)
        
        # 3. 构造元数据头
        header = (
            f"--- 文件元数据 ---\n"
            f"路径: {file_path}\n"
            f"行数: {total_lines} | 当前范围: {start_idx+1}-{end_idx}\n"
        )
        
        footer = ""
        if end_idx < total_lines:
            footer = f"\n\n[SYSTEM WARNING]: 文件未读完，后文还有 {total_lines - end_idx} 行。请调用 read_file(..., start_line={end_idx+1})."
             
        return header + "\n" + content_slice + footer

    except Exception as e:
        return f"读取文件出错: {e}"

@tool
def write_file(file_path: str, content: str):
    """将文本内容写入指定文件（完全覆盖）。"""
    try:
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir): os.makedirs(parent_dir, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
        return f"成功写入文件: {file_path}"
    except Exception as e: return f"写入文件出错: {e}"

@tool
def replace_in_file(file_path: str, old_string: str, new_string: str):
    """精确替换文件中的字符串。old_string 必须在文件中唯一存在。"""
    if not os.path.exists(file_path): return f"错误: 未找到文件 '{file_path}'。"
    try:
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
        if old_string not in content: return "错误: 在文件中未找到 old_string。"
        if content.count(old_string) > 1: return "错误: old_string 不唯一。"
        new_content = content.replace(old_string, new_string)
        with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)
        return f"成功在 {file_path} 中完成替换。"
    except Exception as e: return f"替换出错: {e}"

@tool
def search_file(file_path: str, pattern: str, case_sensitive: bool = False):
    """
    在文件中搜索指定关键词或正则模式。支持 Office/PDF 文档。
    返回匹配的行号及上下文，帮助快速定位关键信息。
    """
    if not os.path.exists(file_path):
        return f"错误: 未找到文件 '{file_path}'。"
    
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        content_full = ""
        # 复用读取逻辑以保证行号一致
        if HAS_OFFICE_DEPS:
            if ext == ".docx":
                content_full = _read_docx(file_path)
            elif ext == ".pdf":
                content_full = _read_pdf(file_path)
            elif ext in [".xlsx", ".xls"]:
                content_full = _read_excel(file_path)
        
        if not content_full:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = content_full.splitlines()
            
        matches = []
        import re
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for i, line in enumerate(lines):
            if re.search(pattern, line, flags):
                # 记录行号 (从1开始) 和内容
                line_num = i + 1
                matches.append(f"Line {line_num}: {line.strip()}")
                
        if not matches:
            return f"未找到匹配 '{pattern}' 的内容。"
            
        # 结果截断
        count = len(matches)
        display_matches = matches[:20]
        result = f"--- 搜索结果 (共 {count} 处匹配) ---\n" + "\n".join(display_matches)
        if count > 20:
            result += f"\n... (还有 {count-20} 处匹配已隐藏)"
            
        return result

    except Exception as e:
        return f"搜索出错: {e}"

available_tools = [run_shell, activate_skill, read_file, write_file, replace_in_file, search_file]