import os
import sys
import glob

# 添加项目根目录到 path 以导入 agent_core
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
sys.path.append(PROJECT_ROOT)

from agent_core.tools import read_file
from skills.knowledge_base.scripts.db_manager import DBManager

def chunk_text_by_lines(text, chunk_size=20, overlap=5):
    """
    按行切分文本，并尝试提取语义化的位置信息（如 Slide 1, Page 2, Sheet Name）。
    返回: List[dict] -> [{'text': '...', 'lines': '10-30', 'location': 'Slide 5'}]
    """
    lines = text.splitlines()
    chunks = []
    total_lines = len(lines)
    
    # 预扫描：建立行号到位置的映射
    # line_location_map[line_index] = "Slide 1"
    line_location_map = {}
    current_location = "Unknown Location"
    
    import re
    # 匹配模式: --- Slide 1 ---, --- Page 1 ---, --- Sheet: Sheet1 ---
    loc_pattern = re.compile(r'^--- (Slide \d+|Page \d+|Sheet: .+) ---$')
    
    for i, line in enumerate(lines):
        match = loc_pattern.match(line.strip())
        if match:
            current_location = match.group(1)
        line_location_map[i] = current_location
    
    for i in range(0, total_lines, chunk_size - overlap):
        end = min(i + chunk_size, total_lines)
        chunk_lines = lines[i:end]
        chunk_content = "\n".join(chunk_lines).strip()
        
        if not chunk_content: continue
        
        # 获取当前 Chunk 对应的主要位置（取中间行的位置，或者起始行的位置）
        # 取起始行的位置通常比较准，因为 Context 覆盖了后文
        # 但如果 Chunk 跨页了怎么办？
        # 我们可以记录 range，例如 "Slide 1 - Slide 2"
        start_loc = line_location_map.get(i, "Unknown")
        end_loc = line_location_map.get(end-1, "Unknown")
        
        if start_loc == end_loc:
            location = start_loc
        else:
            location = f"{start_loc} -> {end_loc}"
            
        chunks.append({
            "text": chunk_content,
            "line_start": i + 1,
            "line_end": end,
            "location": location
        })
        
        if end == total_lines: break
        
    return chunks

def ingest_file(file_path, collection_name="documents"):
    # ... (前文读取逻辑保持不变)
    # 既然我们要修改 chunking 逻辑，我们需要把 ingest_file 的后半部分也替换掉
    # 为了稳妥，我将替换整个 ingest_file 函数的后半部分
    pass


def ingest_file(file_path, collection_name="documents"):
    print(f"📄 Processing: {file_path}")
    
    # 1. 调用 Core Tool 读取文件 (利用其强大的解析能力)
    # 不使用 outline_only，直接读全文 (利用新特性: end_line=-1)
    # 注意：read_file 内部有截断保护，但我们作为内部调用，希望读全量。
    # 我们需要绕过 read_file 的 500 行保护吗？
    # 是的。但 read_file 的实现是 end_line=-1 时默认截断。
    # 我们可以 loop 读取，或者修改 read_file 的逻辑。
    # 为了简单，我们先读前 2000 行。如果文件超大，Ingest 脚本应该实现分页循环。
    
    full_content = ""
    start_line = 1
    page_size = 1000 # 每次读 1000 行
    
    while True:
        # 调用 tool.invoke 或者是直接导入函数调用
        # 这里直接调用函数（因为我们在 python 脚本里）
        # 但 read_file 是 StructuredTool，需要 .invoke 或 .func
        # 简单起见，直接调用底层的 _read_docx 等？不，那样破坏了封装。
        # 我们用 read_file.func
        
        part = read_file.func(file_path, start_line=start_line, end_line=start_line + page_size)
        
        # 去除 Header/Footer 噪音
        # 这是一个 hack，但有效
        body = part
        if "--- 文件元数据 ---" in part:
            body = part.split("--- 文件元数据 ---")[1].split("\n", 4)[-1] # 跳过头几行
        if "[SYSTEM WARNING]" in body:
            body = body.split("[SYSTEM WARNING]")[0]
            
        full_content += body
        
        # 检查是否读完
        if "[SYSTEM WARNING]" not in part: 
            break
        start_line += page_size
        if start_line > 10000: # 安全熔断
            print("⚠️ File too large (>10k lines), stopping.")
            break

    # 2. 切片
    chunks = chunk_text_by_lines(full_content)
    print(f"   -> Split into {len(chunks)} chunks.")
    
    if not chunks: return

    # 3. 向量化 & 存储
    db = DBManager.get_instance()
    vectors = db.embed_documents([c['text'] for c in chunks])
    
    # 计算相对路径，方便 Agent 后续读取
    try:
        rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    except ValueError:
        # 如果跨盘符（Windows）或路径异常，回退到原始路径
        rel_path = file_path

    data = []
    for i, chunk in enumerate(chunks):
        data.append({
            "vector": vectors[i],
            "text": chunk['text'],
            "source": rel_path, # [修改] 存储相对路径
            "line_range": f"{chunk['line_start']}-{chunk['line_end']}",
            "location": chunk['location'], 
            "type": "document"
        })

        
    # 4. 写入 DB
    # 检查 Schema 兼容性
    is_compatible = db.check_schema_compatibility(collection_name, data[0])
    
    tbl = db.get_table(collection_name)
    if tbl and is_compatible:
        tbl.add(data)
    else:
        # 如果表不存在，或者刚才因为不兼容被删除了，这里会创建新表
        db.create_table(collection_name, data)
        
    print(f"✅ Ingested {len(data)} vectors to '{collection_name}'.")

def main(input_path, collection="documents"):
    if os.path.isfile(input_path):
        ingest_file(input_path, collection)
    elif os.path.isdir(input_path):
        # 递归查找支持的格式
        exts = ['*.docx', '*.pdf', '*.xlsx', '*.pptx', '*.md', '*.txt']
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(input_path, '**', ext), recursive=True))
            
        print(f"🔍 Found {len(files)} files in {input_path}")
        for f in files:
            try:
                ingest_file(f, collection)
            except Exception as e:
                print(f"❌ Error processing {f}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <file_or_dir> [collection_name]")
        sys.exit(1)
    
    target = sys.argv[1]
    coll = sys.argv[2] if len(sys.argv) > 2 else "documents"
    main(target, coll)
