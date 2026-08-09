from datetime import datetime
from typing import Dict, Any, List
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data_manager import DataManager
from models.predictors import KnowledgeStatePredictor, PerformancePredictor
from models.fuzzy_controller import FuzzyController
from models.learning_path import LearningPath
from engine.mpc_engine import MPCEngine
from utils.config_loader import load_all_configs, flatten_knowledge_structure, calculate_difficulty_map

# 计划优先级权重：低掌握度 + 高难度 → 高优先级
PRIORITY_NEW_CONTENT_WEIGHT = 0.3   # 未掌握内容的基础权重
PRIORITY_DIFFICULTY_WEIGHT = 0.7    # 难度的额外权重

# 自评分数范围
SELF_RATING_MIN = 1
SELF_RATING_MAX = 5

# 单日表现评分阈值
SCORE_EXCELLENT = 0.8   # ≥0.8 优秀
SCORE_GOOD = 0.6        # ≥0.6 良好
SCORE_FAIR = 0.4        # ≥0.4 一般

# 掌握度状态阈值
MASTERY_PROFICIENT = 0.8    # ≥0.8 熟练
MASTERY_MASTERED = 0.5      # ≥0.5 掌握
MASTERY_LEARNING = 0.2      # ≥0.2 学习中

# 学习洞察参数
INSIGHTS_MIN_RECORDS = 3        # 至少几天记录
INSIGHTS_RECENT_WINDOW = 14     # 查看最近 N 条
INSIGHTS_TOP_COUNT = 5          # 薄弱/优势点各取 N 个
CONSISTENCY_LOW = 0.3           # 波动大的判定线
WEAK_POINT_THRESHOLD = 0.3      # 薄弱点掌握度上限

# 自动优化参数
AUTO_OPT_MIN_RECORDS = 7        # 至少几天记录
AUTO_OPT_RECENT_WINDOW = 7      # 查看最近 N 条
LEARN_RATE_MAX = 0.25           # 学习率上限
LEARN_RATE_MIN = 0.1            # 学习率下限
BALANCE_MAX = 0.9               # 新旧平衡上限
BALANCE_MIN = 0.5               # 新旧平衡下限
BALANCE_TO_RATE_RATIO = 2.5     # 新旧平衡调整量 = 学习率调整量 × 该比例
COMPLETION_LOW = 0.7            # 完成率低 → 缩减任务
TASK_MAX_MIN = 60               # 任务时长下限
TASK_MAX_STEP = 15              # 任务时长缩减步长

class LearningOptimizationSystem:
    """学习优化系统主类 - 管理整个智能学习助手系统"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.data_manager = DataManager(base_path)
        self.configs = load_all_configs(base_path)
        
        self.knowledge_predictor = KnowledgeStatePredictor(self.configs['model_params'])
        self.performance_predictor = PerformancePredictor(self.configs['evaluation_weights'])
        self.mpc_engine = MPCEngine(
            self.knowledge_predictor,
            self.performance_predictor,
            self.configs['model_params']
        )
        
        self.knowledge_list = flatten_knowledge_structure(self.configs['knowledge_structure'])
        self.learning_path = LearningPath(
            self.knowledge_list, self.configs, self.data_manager, self.knowledge_predictor
        )
        
    def add_learning_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """添加学习记录 - 返回 {success, message}"""
        required_fields = ['date', 'knowledge_point', 'planned_minutes', 
                          'actual_minutes', 'question_count', 'correct_count', 'self_rating']
        
        for field in required_fields:
            if field not in record:
                return {'success': False, 'message': f'缺少字段: {field}'}
        
        if record['self_rating'] < SELF_RATING_MIN or record['self_rating'] > SELF_RATING_MAX:
            return {'success': False, 'message': f'自评分数必须在{SELF_RATING_MIN}-{SELF_RATING_MAX}之间'}
            
        self.data_manager.save_record(record)
        self._update_knowledge_state(record)
        return {'success': True, 'message': '记录已保存'}
            
    def _update_knowledge_state(self, record: Dict[str, Any]):
        """更新知识点掌握状态 - 根据学习记录调整进度"""
        current_state = self.data_manager.load_knowledge_state()
        new_state = self.mpc_engine.update_mastery_state(current_state, record)
        self.data_manager.save_knowledge_state(new_state)
        
    def evaluate_daily_performance(self, date: str = None) -> Dict[str, Any]:
        """评估单日表现 - 当天无记录时返回 {date, message}"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        all_records = self.data_manager.load_records()
        day_records = [r for r in all_records if r['date'] == date]
        
        if not day_records:
            return {'date': date, 'message': '当天无学习记录'}
            
        total_score = 0
        details = []
        
        for record in day_records:
            score, feedback = self.performance_predictor.evaluate_day(record)
            total_score += score
            details.append({
                'knowledge': record['knowledge_point'],
                'score': score,
                'feedback': feedback,
                'accuracy': record['correct_count'] / record['question_count'],
                'self_rating': record['self_rating']
            })
            
        avg_score = total_score / len(day_records)
        
        if avg_score >= SCORE_EXCELLENT:
            overall_feedback = "整体表现优秀！继续保持"
        elif avg_score >= SCORE_GOOD:
            overall_feedback = "整体表现良好，可以适当提升难度"
        elif avg_score >= SCORE_FAIR:
            overall_feedback = "整体表现一般，建议调整学习策略"
        else:
            overall_feedback = "整体需要改进，建议重新规划学习"
            
        return {
            'date': date,
            'average_score': round(avg_score, 3),
            'overall_feedback': overall_feedback,
            'details': details
        }
        
    def generate_tomorrow_plan(self, daily_time_budget: int) -> Dict[str, Any]:
        """生成明日计划 - 用 MPC 引擎按优先级排任务"""
        current_state = self.data_manager.load_knowledge_state()
        records = self.data_manager.load_records()
        difficulty_map = calculate_difficulty_map(records)
        
        plan = self.mpc_engine.generate_next_day_plan(
            self.knowledge_list,
            current_state,
            difficulty_map,
            daily_time_budget
        )
        
        if not plan:
            return {'message': '无法生成计划，请检查配置和数据'}
            
        total_time = sum(plan.values())
        
        plan_details = []
        for knowledge, time in plan.items():
            current_mastery = current_state.get(knowledge, 0.0)
            difficulty = difficulty_map.get(knowledge, 0.5)
            priority = (1 - current_mastery) * (PRIORITY_NEW_CONTENT_WEIGHT + PRIORITY_DIFFICULTY_WEIGHT * difficulty)
            
            plan_details.append({
                'knowledge': knowledge,
                'planned_minutes': time,
                'current_mastery': round(current_mastery, 3),
                'difficulty': round(difficulty, 3),
                'priority': round(priority, 3)
            })
            
        plan_details.sort(key=lambda x: x['priority'], reverse=True)
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_planned_minutes': total_time,
            'tasks': plan_details
        }
        
    def get_knowledge_status(self) -> Dict[str, Any]:
        """获取所有知识点状态 - 掌握度映射为 未开始/学习中/掌握/熟练"""
        state = self.data_manager.load_knowledge_state()
        
        status_list = []
        for knowledge in self.knowledge_list:
            mastery = state.get(knowledge, 0.0)
            status = '未开始'
            if mastery >= MASTERY_PROFICIENT:
                status = '熟练'
            elif mastery >= MASTERY_MASTERED:
                status = '掌握'
            elif mastery >= MASTERY_LEARNING:
                status = '学习中'
                
            status_list.append({
                'knowledge': knowledge,
                'mastery': round(mastery, 3),
                'status': status
            })
            
        return {'knowledge_status': status_list}
        
    def update_config(self, config_type: str, new_config: Dict) -> Dict[str, Any]:
        """更新配置 - 返回 {success, message}"""
        valid_configs = ['model_params', 'evaluation_weights', 'human_settings']
        
        if config_type not in valid_configs:
            return {'success': False, 'message': f'无效的配置类型: {config_type}'}
            
        config_path = os.path.join(self.base_path, 'config', f'{config_type}.json')
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            
            self.configs[config_type] = new_config
            
            if config_type == 'model_params':
                self.knowledge_predictor = KnowledgeStatePredictor(new_config)
                self.mpc_engine = MPCEngine(
                    self.knowledge_predictor,
                    self.performance_predictor,
                    new_config
                )
            elif config_type == 'evaluation_weights':
                self.performance_predictor = PerformancePredictor(new_config)
                
            return {'success': True, 'message': f'{config_type} 配置已更新'}
        except Exception as e:
            return {'success': False, 'message': f'更新失败: {str(e)}'}
            
    def get_learning_insights(self) -> Dict[str, Any]:
        """学习洞察：趋势判断 + 薄弱/优势点 + 个性化建议"""
        records = self.data_manager.load_records()
        state = self.data_manager.load_knowledge_state()
        
        if len(records) < INSIGHTS_MIN_RECORDS:
            return {'message': f'数据不足，需要至少{INSIGHTS_MIN_RECORDS}天的学习记录'}
            
        recent_scores = []
        for record in records[-INSIGHTS_RECENT_WINDOW:]:
            score, _ = self.performance_predictor.evaluate_day(record)
            recent_scores.append(score)
            
        performance = self.performance_predictor.predict_future_performance(recent_scores)
        
        weak_points = sorted(
            state.items(),
            key=lambda x: x[1]
        )[:INSIGHTS_TOP_COUNT]
        
        strong_points = sorted(
            state.items(),
            key=lambda x: x[1],
            reverse=True
        )[:INSIGHTS_TOP_COUNT]
        
        suggestions = []
        
        if performance['trend'] == 'improving':
            suggestions.append("学习效果在提升，继续保持当前节奏")
        elif performance['trend'] == 'declining':
            suggestions.append("学习效果下降，建议调整学习方法和时间分配")
        else:
            suggestions.append("学习效果稳定，可以尝试增加难度或学习新内容")
            
        if performance['consistency'] < CONSISTENCY_LOW:
            suggestions.append("学习波动较大，建议制定更规律的作息")
            
        if weak_points and weak_points[0][1] < WEAK_POINT_THRESHOLD:
            suggestions.append(f"重点关注薄弱知识点：{weak_points[0][0]}")
            
        return {
            'performance_trend': performance,
            'weak_points': [{'knowledge': k, 'mastery': v} for k, v in weak_points],
            'strong_points': [{'knowledge': k, 'mastery': v} for k, v in strong_points],
            'suggestions': suggestions
        }
        
    def auto_optimize_parameters(self) -> Dict[str, Any]:
        """自动优化模型参数 - 模糊控制器根据表现偏差量平滑调节"""
        records = self.data_manager.load_records()
        
        if len(records) < AUTO_OPT_MIN_RECORDS:
            return {'success': False, 'message': f'数据不足，需要至少{AUTO_OPT_MIN_RECORDS}天的学习记录'}
            
        recent_records = records[-AUTO_OPT_RECENT_WINDOW:]
        
        avg_accuracy = sum(r['correct_count'] / r['question_count'] for r in recent_records) / len(recent_records)
        avg_completion = sum(min(r['actual_minutes'] / r['planned_minutes'], 1) for r in recent_records) / len(recent_records)
        
        new_params = self.configs['model_params'].copy()
        
        # 模糊控制器：偏差量越大调节越多，无硬边界
        fuzzy = FuzzyController()
        adjustment = fuzzy.tune(avg_accuracy, avg_completion)
        rate_delta = adjustment['rate_delta']
        task_reduction = adjustment['task_reduction']
        
        # 学习率：按模糊偏差量平滑调整，并夹在上下限内
        base_rate = new_params['learning_efficiency']['base_rate']
        new_params['learning_efficiency']['base_rate'] = min(
            LEARN_RATE_MAX, max(LEARN_RATE_MIN, base_rate + rate_delta)
        )
        
        # 新旧平衡：学得好多学新内容（与学习率同向小幅调整）
        balance = new_params['time_allocation']['balance_new_old']
        balance_delta = rate_delta * BALANCE_TO_RATE_RATIO
        new_params['time_allocation']['balance_new_old'] = min(
            BALANCE_MAX, max(BALANCE_MIN, balance + balance_delta)
        )
        
        # 完成率低 → 减负（平滑缩短单任务时长）
        new_params['time_allocation']['max_task_minutes'] = max(
            TASK_MAX_MIN,
            new_params['time_allocation']['max_task_minutes'] - task_reduction
        )
            
        result = self.update_config('model_params', new_params)
        
        return {
            **result,
            'changes': {
                'old_accuracy': round(avg_accuracy, 3),
                'old_learning_rate': round(base_rate, 4),
                'new_learning_rate': round(new_params['learning_efficiency']['base_rate'], 4),
                'rate_delta': rate_delta,
            }
        }
        
    # ---------- 学习路径模式 ----------
        
    def get_learning_path_status(self) -> Dict[str, Any]:
        """查看当前学习单元 + 达标所需时间 + 复习建议"""
        unit = self.learning_path.get_current_unit()
        if unit['is_done']:
            return {'message': '所有单元都已达标，学习完成！'}
            
        # 计算难度（用该知识点的历史难度，无则默认 0.5）
        records = self.data_manager.load_records()
        difficulty_map = calculate_difficulty_map(records)
        difficulty = difficulty_map.get(unit['knowledge'], 0.5)
        
        estimate = self.learning_path.estimate_time_to_target(
            unit['knowledge'], unit['current_mastery'], difficulty
        )
        reviews = self.learning_path.get_review_suggestions()
        
        return {
            'current_unit': unit['knowledge'],
            'current_mastery': unit['current_mastery'],
            'target_mastery': unit['target_mastery'],
            'estimated_minutes': estimate['minutes'],
            'difficulty': difficulty,
            'review_suggestions': reviews,
        }
        
    def advance_learning_path(self) -> Dict[str, Any]:
        """检查当前单元是否达标，达标则自动推进"""
        unit = self.learning_path.get_current_unit()
        if unit['is_done']:
            return {'message': '所有单元都已达标，无需推进'}
        return self.learning_path.advance(unit['knowledge'])
        
    def skip_learning_unit(self, knowledge: str) -> Dict[str, Any]:
        """手动跳过某单元：掌握度设为目标值，推进到下一单元"""
        return self.learning_path.skip(knowledge)