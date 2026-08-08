import math
from typing import Dict, Tuple

# 学习增益模型常量
MID_DIFFICULTY = 0.5        # 难度中位线，作为难度调整的基准
DIFFICULTY_SLOPE = 0.5      # 难度影响斜率：偏离中位线 1 分 → 效率降 0.5
MINUTES_PER_HOUR = 60       # 分钟转小时的换算
SELF_RATING_MAX_SCALE = 5   # 自评满分（1-5 分制）

# 单日评分阈值
SCORE_EXCELLENT = 0.8   # ≥0.8 优秀
SCORE_GOOD = 0.6        # ≥0.6 良好
SCORE_FAIR = 0.4        # ≥0.4 一般

# 趋势预测参数
TREND_MIN_RECORDS = 3       # 至少 N 条才预测
TREND_RECENT_WINDOW = 3     # 近期窗口
TREND_OVERALL_WINDOW = 7    # 整体窗口
TREND_CHANGE_THRESHOLD = 0.05   # 波动超过 ±0.05 判为上升/下降

class KnowledgeStatePredictor:
    """知识点状态预测模型 - 预测学习效果和遗忘情况"""
    
    def __init__(self, params: Dict):
        self.forget_base = params.get('forgetting_curve', {}).get('base_decay', 0.1)
        self.forget_diff = params.get('forgetting_curve', {}).get('difficulty_multiplier', 0.2)
        self.learn_rate = params.get('learning_efficiency', {}).get('base_rate', 0.15)
        self.fatigue_decay = params.get('learning_efficiency', {}).get('fatigue_decay', 0.05)
        
    def predict_forgetting(self, current_mastery: float, difficulty: float, days: int) -> float:
        """预测遗忘后的掌握度"""
        decay = self.forget_base + (self.forget_diff * difficulty)
        decayed_mastery = current_mastery * math.exp(-decay * days)
        return max(0, min(1, decayed_mastery))
        
    def predict_learning_gain(self, current_mastery: float, study_time: float, 
                             difficulty: float, fatigue: float = 0) -> float:
        """预测学习收益"""
        effective_time = study_time * (1 - fatigue * self.fatigue_decay)
        difficulty_factor = 1 - (difficulty - MID_DIFFICULTY) * DIFFICULTY_SLOPE  # 难度调整
        learning_potential = (1 - current_mastery) * difficulty_factor
        
        gain = self.learn_rate * effective_time / MINUTES_PER_HOUR * learning_potential
        return max(0, min(1 - current_mastery, gain))

class PerformancePredictor:
    """学习表现预测模型 - 评估学习效果并给出反馈"""
    
    def __init__(self, params: Dict):
        self.accuracy_weight = params.get('daily_assessment', {}).get('accuracy_weight', 0.6)
        self.self_rating_weight = params.get('daily_assessment', {}).get('self_rating_weight', 0.3)
        self.completion_weight = params.get('daily_assessment', {}).get('completion_weight', 0.1)
        
    def evaluate_day(self, record: Dict) -> Tuple[float, str]:
        """评估单日学习效果 - 计算得分和反馈"""
        accuracy = record.get('correct_count', 0) / max(record.get('question_count', 1), 1)
        self_rating = record.get('self_rating', 3) / SELF_RATING_MAX_SCALE
        completion = min(record.get('actual_minutes', 0) / max(record.get('planned_minutes', 1), 1), 1)
        
        score = (accuracy * self.accuracy_weight + 
                self_rating * self.self_rating_weight + 
                completion * self.completion_weight)
        
        if score >= SCORE_EXCELLENT:
            feedback = "优秀！保持这个节奏"
        elif score >= SCORE_GOOD:
            feedback = "良好，继续加油"
        elif score >= SCORE_FAIR:
            feedback = "一般，需要改进"
        else:
            feedback = "较差，建议重新学习"
            
        return score, feedback
        
    def predict_future_performance(self, historical_scores: list) -> Dict[str, float]:
        """预测未来表现趋势"""
        if len(historical_scores) < TREND_MIN_RECORDS:
            return {'trend': 'data_insufficient', 'expected_score': 0.5}
            
        recent_trend = sum(historical_scores[-TREND_RECENT_WINDOW:]) / TREND_RECENT_WINDOW
        overall_trend = sum(historical_scores[-TREND_OVERALL_WINDOW:]) / min(TREND_OVERALL_WINDOW, len(historical_scores))
        
        trend = 'stable'
        if recent_trend > overall_trend + TREND_CHANGE_THRESHOLD:
            trend = 'improving'
        elif recent_trend < overall_trend - TREND_CHANGE_THRESHOLD:
            trend = 'declining'
            
        return {
            'trend': trend,
            'expected_score': recent_trend,
            'consistency': 1 - (max(historical_scores[-TREND_OVERALL_WINDOW:]) - min(historical_scores[-TREND_OVERALL_WINDOW:]))
        }