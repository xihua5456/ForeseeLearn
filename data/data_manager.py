import json
from typing import List, Dict, Any
import os

class DataManager:
    """数据存储层 - 管理学习记录和状态数据"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        # 数据存放在项目内的 data/cache 目录，随项目迁移
        cache_dir = os.path.join(base_path, "data", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        self.records_file = os.path.join(cache_dir, "learning_records.json")
        self.state_file = os.path.join(cache_dir, "knowledge_state.json")
        
    def load_records(self) -> List[Dict[str, Any]]:
        """读取全部历史学习记录；文件不存在时返回空列表（首次运行）"""
        try:
            with open(self.records_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('records', [])
        except FileNotFoundError:
            return []
            
    def save_record(self, record: Dict[str, Any]) -> bool:
        """追加一条学习记录（先读全部再加，避免覆盖历史）"""
        records = self.load_records()
        records.append(record)
        
        with open(self.records_file, 'w', encoding='utf-8') as f:
            json.dump({'records': records}, f, ensure_ascii=False, indent=2)
        return True
        
    def load_knowledge_state(self) -> Dict[str, Dict[str, float]]:
        """读取各知识点掌握度；首次运行（无文件）返回空字典"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_knowledge_state(self, state: Dict[str, Dict[str, float]]) -> bool:
        """整表覆盖保存掌握度状态（state 已是全量）"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return True
