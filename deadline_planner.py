"""截止日期规划器：在截止日期前完成固定学习内容

算法（倒排工期）：
1. 对每个选定知识点，用 gain 模型反推"从当前掌握度到目标掌握度"所需分钟数
2. 汇总总需时间
3. 总需时间 ÷ 剩余天数 = 每天应学时长
4. 生成逐日计划：按知识点顺序 + 每日时间上限，把任务分配到每一天
5. 若每天所需超过用户预算 → 给出明确提示（无法完成/需要延后/需要减内容）
"""

from datetime import datetime, date
from typing import Dict, List, Any


class DeadlinePlanner:
    """截止日期倒排规划器"""

    def __init__(self, learning_path, configs: Dict[str, Any]):
        self.learning_path = learning_path
        self.configs = configs

    def estimate_all(self, knowledge_points: List[str]) -> Dict[str, int]:
        """估算每个知识点达标所需分钟数（复用学习路径的反推公式）"""
        state = self.learning_path.data_manager.load_knowledge_state()
        records = self.learning_path.data_manager.load_records()

        # 计算难度（简化：无历史记录默认 0.5）
        from utils.config_loader import calculate_difficulty_map
        difficulty_map = calculate_difficulty_map(records)

        estimates = {}
        for kp in knowledge_points:
            mastery = state.get(kp, 0.0)
            difficulty = difficulty_map.get(kp, 0.5)
            est = self.learning_path.estimate_time_to_target(kp, mastery, difficulty)
            estimates[kp] = est['minutes']
        return estimates

    def plan(self, deadline: str, knowledge_points: List[str],
             daily_minutes: int) -> Dict[str, Any]:
        """生成截止日期前的逐日计划

        参数：
            deadline         - 截止日期 'YYYY-MM-DD'
            knowledge_points - 要完成的知识点列表
            daily_minutes    - 每天可用学习时间（分钟）
        """
        # 1. 计算剩余天数（含今天，最少 1 天）
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'message': f'日期格式错误: {deadline}，应为 YYYY-MM-DD'}

        today = date.today()
        remaining_days = (deadline_date - today).days + 1
        if remaining_days < 1:
            return {'success': False, 'message': f'截止日期 {deadline} 已过，请重新设置'}

        # 2. 估算每个知识点所需时间
        estimates = self.estimate_all(knowledge_points)
        total_required = sum(estimates.values())

        if total_required <= 0:
            return {'success': True, 'message': '所选内容都已达标，无需规划', 'plan': []}

        # 3. 计算每天所需时长
        per_day_required = total_required / remaining_days

        # 4. 时间检查
        if per_day_required > daily_minutes:
            return {
                'success': False,
                'message': (f'时间不够：每天需要 {per_day_required:.0f} 分钟才能完成，'
                            f'但你预算只有 {daily_minutes} 分钟。\n'
                            f'建议：① 延长截止日期 {max(1, int(total_required / daily_minutes))} 天 '
                            f'② 减少知识点数量 ③ 提高每日预算'),
                'total_required': total_required,
                'per_day_required': round(per_day_required),
            }

        # 5. 生成逐日计划（按知识点顺序 + 每日上限分配）
        plan = self._distribute(estimates, knowledge_points, remaining_days, daily_minutes)

        return {
            'success': True,
            'message': f'规划完成：{len(knowledge_points)} 个知识点，共需 {total_required} 分钟，'
                       f'剩余 {remaining_days} 天，每天约 {per_day_required:.0f} 分钟',
            'total_required': total_required,
            'per_day_required': round(per_day_required),
            'remaining_days': remaining_days,
            'plan': plan,
            'estimates': estimates,
        }

    def _distribute(self, estimates: Dict[str, int], knowledge_points: List[str],
                    remaining_days: int, daily_minutes: int) -> List[Dict[str, Any]]:
        """把知识点按顺序和每日时间上限分配到每一天"""
        daily_plans = []
        current_day_idx = 0
        current_day_used = 0
        current_day_tasks = []

        for kp in knowledge_points:
            minutes = estimates.get(kp, 0)
            if minutes <= 0:
                continue

            while minutes > 0:
                # 当天剩余容量
                capacity = daily_minutes - current_day_used
                if capacity <= 0:
                    # 换下一天
                    daily_plans.append({'day': current_day_idx + 1,
                                        'date': self._day_date(current_day_idx),
                                        'tasks': current_day_tasks,
                                        'total': current_day_used})
                    current_day_idx += 1
                    current_day_used = 0
                    current_day_tasks = []
                    capacity = daily_minutes

                if minutes <= capacity:
                    current_day_tasks.append({'knowledge': kp, 'minutes': minutes})
                    current_day_used += minutes
                    minutes = 0
                else:
                    current_day_tasks.append({'knowledge': kp, 'minutes': capacity})
                    current_day_used += capacity
                    minutes -= capacity

            # 知识点可能跨天，继续处理下一个

        # 收尾：把最后一天加进去
        if current_day_tasks or daily_plans:
            daily_plans.append({'day': current_day_idx + 1,
                                'date': self._day_date(current_day_idx),
                                'tasks': current_day_tasks,
                                'total': current_day_used})

        # 截断到剩余天数
        return daily_plans[:remaining_days]

    @staticmethod
    def _day_date(day_offset: int) -> str:
        """第 N 天对应的日期字符串"""
        d = date.today()
        from datetime import timedelta
        return (d + timedelta(days=day_offset)).strftime('%Y-%m-%d')
