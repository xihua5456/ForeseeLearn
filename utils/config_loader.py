import json
import os
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件 - 读取系统设置参数"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_all_configs(base_path: str) -> Dict[str, Dict[str, Any]]:
    """加载所有配置文件 - 读取系统所有设置"""
    config_dir = os.path.join(base_path, "config")
    
    return {
        'knowledge_structure': load_config(os.path.join(config_dir, "knowledge_structure.json")),
        'model_params': load_config(os.path.join(config_dir, "model_params.json")),
        'evaluation_weights': load_config(os.path.join(config_dir, "evaluation_weights.json")),
        'human_settings': load_config(os.path.join(config_dir, "human_settings.json"))
    }

def flatten_knowledge_structure(structure: Dict) -> list:
    """把三级知识点结构（学科→章节→知识点）摊平成叶子名单，key 用知识点名本身"""
    knowledge_list = []
    for subject, chapters in structure.items():
        for chapter, points in chapters.items():
            for point in points:
                knowledge_list.append(point)
    return knowledge_list

def calculate_difficulty(accuracy: float, self_rating: float) -> float:
    """难度 = 1 - 综合表现：正确率越高、自评越好，难度越低（唯一实现）"""
    return 1 - (accuracy * 0.7 + self_rating * 0.3)

def calculate_difficulty_map(records: list) -> Dict[str, float]:
    """汇总所有记录，算出每个知识点的平均难度表"""
    difficulty_map = {}
    
    for record in records:
        knowledge = record.get('knowledge_point', '')
        accuracy = record.get('correct_count', 0) / max(record.get('question_count', 1), 1)
        self_rating = record.get('self_rating', 3) / 5
        
        difficulty = calculate_difficulty(accuracy, self_rating)
        
        if knowledge in difficulty_map:
            difficulty_map[knowledge] = (difficulty_map[knowledge] + difficulty) / 2
        else:
            difficulty_map[knowledge] = difficulty
            
    return difficulty_map