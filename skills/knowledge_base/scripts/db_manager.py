import os
import lancedb
from fastembed import TextEmbedding

# 配置常量
DB_PATH = os.path.expanduser("~/.gemini/memory/lancedb_store")
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5" # 优秀的中文模型，体积适中

class DBManager:
    _instance = None
    
    def __init__(self):
        # 确保目录存在
        if not os.path.exists(DB_PATH):
            os.makedirs(DB_PATH)
            
        self.db = lancedb.connect(DB_PATH)
        # 初始化 Embedding 模型 (会自动下载)
        print(f"🔄 [System] Loading Embedding Model: {EMBEDDING_MODEL_NAME}...")
        self.embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
        print("✅ Embedding Model Ready.")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DBManager()
        return cls._instance

    def get_table(self, table_name="documents"):
        """获取或创建表。Schema: vector, text, source, line_range, metadata"""
        # LanceDB 支持自动 Schema 推断，我们直接用 Pydantic 或者 PyArrow 定义更稳健
        # 但为了简单，我们让它自动推断 (Lazy Mode)
        try:
            return self.db.open_table(table_name)
        except:
            # 表不存在，返回 None，由调用方负责 create_table
            return None

    def check_schema_compatibility(self, table_name, sample_data):
        """检查表结构是否与新数据兼容"""
        tbl = self.get_table(table_name)
        if not tbl: return True
        
        try:
            # 获取表的第一条数据来看看 keys
            # LanceDB 0.25+ schema 获取方式
            schema = tbl.schema
            existing_fields = set(schema.names)
            new_fields = set(sample_data.keys())
            
            # 检查是否有新字段是旧表没有的
            missing_in_db = new_fields - existing_fields
            if missing_in_db:
                print(f"⚠️ [Schema Warning] Table '{table_name}' is missing fields: {missing_in_db}")
                print(f"♻️ Auto-migrating: Dropping old table to apply new schema...")
                self.db.drop_table(table_name)
                return False # Table dropped, caller should create new
            return True
        except Exception as e:
            print(f"Schema check failed: {e}")
            return True # Assume compatible to avoid accidental deletion

    def create_table(self, table_name, data):
        """创建新表"""
        # data 是一个 list of dict，包含 'vector' 字段和其他字段
        # LanceDB 0.25+ 推荐使用 pydantic mode 或者 pyarrow table
        # 这里我们使用自动推断模式
        return self.db.create_table(table_name, data=data)

    def embed_documents(self, texts: list[str]):
        """批量计算向量"""
        # FastEmbed 返回的是 generator，转为 list
        return list(self.embedding_model.embed(texts))

    def embed_query(self, text: str):
        """计算查询向量"""
        # embed 返回 list of vector，取第一个
        return list(self.embedding_model.embed([text]))[0]

    def delete_by_source(self, table_name, source_file):
        """按源文件名删除记录"""
        tbl = self.get_table(table_name)
        if not tbl: return False
        # LanceDB 删除语法
        tbl.delete(f"source = '{source_file}'")
        return True

    def list_sources(self, table_name):
        """列出所有源文件及其片段数"""
        tbl = self.get_table(table_name)
        if not tbl: return {}
        
        try:
            # 使用 to_list() 获取数据，避免 pandas 依赖
            # limit 设大一点以获取所有记录 (LanceDB 目前没有 select distinct count)
            # 或者更好的做法是 iter batches，但为了简单先 limit
            results = tbl.search().select(["source"]).limit(10000).to_list()
            
            from collections import Counter
            sources = [r['source'] for r in results]
            return dict(Counter(sources))
        except Exception as e:
            print(f"Error listing sources: {e}")
            return {}

    def reset_table(self, table_name):
        """删除整个表"""
        try:
            self.db.drop_table(table_name)
            return True
        except:
            return False
