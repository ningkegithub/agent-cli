import sys
import os

# 添加项目根目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
sys.path.append(PROJECT_ROOT)

from skills.knowledge_base.scripts.db_manager import DBManager

def search(query, collection_name="documents", limit=5):
    db = DBManager.get_instance()
    tbl = db.get_table(collection_name)
    
    if not tbl:
        return f"错误: 知识库 '{collection_name}' 不存在或为空。请先使用 ingest_knowledge 入库。"
        
    # 1. 向量化
    query_vec = db.embed_query(query)
    
    # 2. 搜索
    # LanceDB 的 search API
    results = tbl.search(query_vec).limit(limit).to_list()
    
    if not results:
        return f"未找到与 '{query}' 相关的结果。"
        
    # 3. 格式化输出
    output = [f"--- 知识库检索结果 (Query: {query}) ---"]
    for i, res in enumerate(results):
        score = 1.0 - res.get('_distance', 0) # 距离越小越相似，这里粗略转为分数
        source = res['source']
        lines = res['line_range']
        location = res.get('location', 'Unknown') # 新增
        content = res['text'].replace("\n", " ").strip()
        if len(content) > 200: content = content[:200] + "..."
        
        output.append(f"[{i+1}] {content}")
        output.append(f"    Source: {source} | Loc: {location} | Line: {lines} | Score: {score:.4f}")
        
    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query.py <query_text> [collection_name]")
        sys.exit(1)
        
    q = sys.argv[1]
    coll = sys.argv[2] if len(sys.argv) > 2 else "documents"
    print(search(q, coll))
