import random
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

from utils.config_loader import calculate_difficulty

# 优化目标中的时间超支惩罚系数
TIME_BUDGET_PENALTY = 0.01
# 随机优化每次调整的时间步长（分钟）
ADJUST_STEP_MINUTES = 15

class MPCEngine:
    """智能计划引擎 - 负责生成最优学习计划"""
    
    def __init__(self, state_predictor, performance_predictor, params: Dict):
        self.state_predictor = state_predictor
        self.performance_predictor = performance_predictor
        
        self.horizon = params.get('optimization', {}).get('horizon_days', 7)
        self.max_iter = params.get('optimization', {}).get('max_iterations', 100)
        self.balance_new_old = params.get('time_allocation', {}).get('balance_new_old', 0.7)
        self.min_task = params.get('time_allocation', {}).get('min_task_minutes', 15)
        self.max_task = params.get('time_allocation', {}).get('max_task_minutes', 120)
        
    def update_mastery_state(self, current_state: Dict[str, float], 
                            record: Dict) -> Dict[str, float]:
        """按学习记录更新掌握度：正确率/自评 → 难度 → 增益"""
        knowledge = record.get('knowledge_point', '')
        study_time = record.get('actual_minutes', 0)
        
        accuracy = record.get('correct_count', 0) / max(record.get('question_count', 1), 1)
        self_rating = record.get('self_rating', 3) / 5

        difficulty = calculate_difficulty(accuracy, self_rating)
        
        current_mastery = current_state.get(knowledge, 0.0)
        gain = self.state_predictor.predict_learning_gain(
            current_mastery, study_time, difficulty
        )
        
        new_state = current_state.copy()
        new_state[knowledge] = min(1.0, current_mastery + gain)
        
        return new_state
        
    def simulate_forgetting(self, current_state: Dict[str, float], 
                           difficulty_map: Dict[str, float], days: int) -> Dict[str, float]:
        """模拟N天后的掌握度（考虑遗忘）"""
        new_state = {}
        for knowledge, mastery in current_state.items():
            difficulty = difficulty_map.get(knowledge, 0.5)
            new_state[knowledge] = self.state_predictor.predict_forgetting(
                mastery, difficulty, days
            )
        return new_state
        
    def calculate_objective(self, plan: List[Dict[str, int]], 
                           initial_state: Dict[str, float],
                           difficulty_map: Dict[str, float],
                           total_time_budget: int) -> float:
        """计算优化目标：预测期总掌握度提升（超时惩罚）"""
        current_state = initial_state.copy()
        total_improvement = 0
        
        for day_plan in plan:
            day_state = current_state.copy()
            
            for knowledge, time in day_plan.items():
                if time <= 0:
                    continue
                    
                difficulty = difficulty_map.get(knowledge, 0.5)
                gain = self.state_predictor.predict_learning_gain(
                    day_state.get(knowledge, 0.0), time, difficulty
                )
                day_state[knowledge] = min(1.0, day_state.get(knowledge, 0.0) + gain)
                
            day_improvement = sum(day_state.values()) - sum(current_state.values())
            total_improvement += day_improvement
            
            current_state = self.simulate_forgetting(day_state, difficulty_map, 1)
            
        time_penalty = abs(sum(sum(p.values()) for p in plan) - total_time_budget)
        return total_improvement - TIME_BUDGET_PENALTY * time_penalty
        
    def generate_heuristic_plan(self, knowledge_list: List[str],
                               current_state: Dict[str, float],
                               total_time: int) -> List[Dict[str, int]]:
        """生成启发式初始计划（贪心算法）"""
        plan = []
        daily_budget = total_time / self.horizon
        
        for day in range(self.horizon):
            day_plan = {}
            remaining_time = daily_budget
            
            sorted_knowledge = sorted(
                knowledge_list,
                key=lambda k: (1 - current_state.get(k, 0.0)) * (0.3 if k in current_state else 1.0),
                reverse=True
            )
            
            for knowledge in sorted_knowledge:
                if remaining_time <= 0:
                    break
                    
                time_allocation = min(remaining_time, self.max_task)
                if time_allocation < self.min_task:
                    continue
                    
                day_plan[knowledge] = int(time_allocation)
                remaining_time -= time_allocation
                
            plan.append(day_plan)
            
        return plan
        
    def optimize_plan(self, knowledge_list: List[str],
                     current_state: Dict[str, float],
                     difficulty_map: Dict[str, float],
                     daily_time_budget: int) -> List[Dict[str, int]]:
        """MPC 滚动优化：随机扰动迭代，保留更优计划"""
        total_budget = daily_time_budget * self.horizon
        
        initial_plan = self.generate_heuristic_plan(knowledge_list, current_state, total_budget)
        best_plan = initial_plan
        best_score = self.calculate_objective(initial_plan, current_state, 
                                              difficulty_map, total_budget)
        
        for iteration in range(self.max_iter):
            current_plan = [day.copy() for day in best_plan]
            
            day_to_modify = iteration % self.horizon
            if not current_plan[day_to_modify]:
                current_plan[day_to_modify] = {}
                
            knowledge_to_adjust = iteration % len(knowledge_list)
            knowledge = knowledge_list[knowledge_to_adjust]
            
            adjustment = random.choice([-ADJUST_STEP_MINUTES, ADJUST_STEP_MINUTES])
            current_time = current_plan[day_to_modify].get(knowledge, 0)
            new_time = max(0, min(self.max_task, current_time + adjustment))
            
            if new_time < self.min_task and new_time > 0:
                new_time = 0
            elif new_time >= self.min_task:
                current_plan[day_to_modify][knowledge] = int(new_time)
                
            current_score = self.calculate_objective(current_plan, current_state,
                                                     difficulty_map, total_budget)
            
            if current_score > best_score:
                best_plan = current_plan
                best_score = current_score
                
        return best_plan
        
    def generate_next_day_plan(self, knowledge_list: List[str],
                              current_state: Dict[str, float],
                              difficulty_map: Dict[str, float],
                              daily_time_budget: int) -> Dict[str, int]:
        """生成明日计划：取 7 天优化结果的第一天"""
        optimized_plan = self.optimize_plan(knowledge_list, current_state,
                                           difficulty_map, daily_time_budget)
        return optimized_plan[0] if optimized_plan else {}