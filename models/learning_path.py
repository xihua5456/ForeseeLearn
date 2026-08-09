"""学习路径模块：定位当前单元、反推达标时间、自动推进、手动跳过

功能对应（用户设计）：
1. 复习开关 enable_review：推进时是否附带旧知识复习建议
2. 参数 → 达标时间：用 gain 模型反推"从当前掌握度到目标掌握度需要学多久"
3. 达标推进：掌握度 ≥ advance_threshold → 自动进入下一单元
4. 手动跳过：标记某单元已完成，掌握度直接设为 target_mastery，记录跳过日志
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class LearningPath:
    """学习路径推进器"""

    def __init__(self, knowledge_list: List[str], configs: Dict[str, Any],
                 data_manager, state_predictor):
        self.knowledge_list = knowledge_list
        self.configs = configs
        self.data_manager = data_manager
        self.state_predictor = state_predictor

        lp = configs.get('human_settings', {}).get('learning_path', {})
        self.enable_review = lp.get('enable_review', True)
        self.target_mastery = lp.get('target_mastery', 0.6)
        self.advance_threshold = lp.get('advance_threshold', 0.6)
        self.default_daily_minutes = lp.get('default_daily_minutes', 60)

        # 跳过日志文件（独立存储，便于统计）
        self.skipped_log_file = os.path.join(
            data_manager.base_path, 'data', 'cache', 'skipped_log.json')

    # ---------- 单元定位 ----------

    def get_current_unit(self) -> Dict[str, Any]:
        """找到当前应学习的单元：第一个未达标的（按配置顺序）"""
        state = self.data_manager.load_knowledge_state()

        for knowledge in self.knowledge_list:
            mastery = state.get(knowledge, 0.0)
            if mastery < self.advance_threshold:
                return {
                    'knowledge': knowledge,
                    'current_mastery': round(mastery, 3),
                    'target_mastery': self.target_mastery,
                    'is_done': False,
                }
        return {
            'knowledge': None,
            'current_mastery': 1.0,
            'target_mastery': self.target_mastery,
            'is_done': True,
        }

    # ---------- 达标时间反推 ----------

    def estimate_time_to_target(self, knowledge: str, current_mastery: float,
                                difficulty: float) -> Dict[str, Any]:
        """用学习增益模型反推：从当前掌握度到目标掌握度需要学多少分钟"""
        remaining = self.target_mastery - current_mastery
        if remaining <= 0:
            return {'minutes': 0, 'already_done': True}

        # gain = learn_rate * (minutes/60) * (1-mastery) * difficulty_factor
        # → minutes = gain * 60 / (learn_rate * (1-mastery) * diff_factor)
        learn_rate = self.state_predictor.learn_rate
        difficulty_factor = 1 - (difficulty - 0.5) * 0.5
        growth_rate = learn_rate * (1 - current_mastery) * difficulty_factor

        if growth_rate <= 0:
            minutes = 9999  # 无法增长（异常情况），给个大数
        else:
            minutes = remaining * 60 / growth_rate

        return {
            'minutes': round(minutes),
            'already_done': False,
            'difficulty': round(difficulty, 3),
            'growth_rate': round(growth_rate, 4),
        }

    # ---------- 复习建议 ----------

    def get_review_suggestions(self) -> List[Dict[str, Any]]:
        """复习开关开启时：找出掌握度低于阈值但高于 0 的旧单元（容易遗忘的）"""
        if not self.enable_review:
            return []

        state = self.data_manager.load_knowledge_state()
        suggestions = []
        for knowledge, mastery in state.items():
            if 0 < mastery < self.advance_threshold:
                suggestions.append({
                    'knowledge': knowledge,
                    'mastery': round(mastery, 3),
                    'reason': '掌握度未达标，建议复习',
                })
        suggestions.sort(key=lambda x: x['mastery'])
        return suggestions[:3]

    # ---------- 推进 / 跳过 ----------

    def advance(self, current: str) -> Dict[str, Any]:
        """检查当前单元是否达标，达标则推进到下一个单元"""
        state = self.data_manager.load_knowledge_state()
        mastery = state.get(current, 0.0)

        if mastery >= self.advance_threshold:
            return {
                'advanced': True,
                'from': current,
                'to': self._next_unit(current),
                'message': f'「{current}」已达标（{mastery:.2f} ≥ {self.advance_threshold}），自动推进',
            }
        return {
            'advanced': False,
            'from': current,
            'to': current,
            'message': f'「{current}」还差 {self.advance_threshold - mastery:.2f}，继续学习',
        }

    def skip(self, knowledge: str) -> Dict[str, Any]:
        """手动跳过：掌握度直接设为目标值，记录跳过日志，推进到下一单元"""
        state = self.data_manager.load_knowledge_state()
        state[knowledge] = self.target_mastery
        self.data_manager.save_knowledge_state(state)

        self._log_skip(knowledge)

        return {
            'success': True,
            'knowledge': knowledge,
            'mastery_set': self.target_mastery,
            'next': self._next_unit(knowledge),
            'message': f'已跳过「{knowledge}」，掌握度设为 {self.target_mastery}，推进到下一单元',
        }

    # ---------- 内部工具 ----------

    def _next_unit(self, current: str) -> Optional[str]:
        """返回当前单元的下一个（配置顺序），已到末尾返回 None"""
        try:
            idx = self.knowledge_list.index(current)
        except ValueError:
            return None
        if idx + 1 < len(self.knowledge_list):
            return self.knowledge_list[idx + 1]
        return None

    def _log_skip(self, knowledge: str) -> None:
        """追加一条跳过记录到 skipped_log.json"""
        try:
            with open(self.skipped_log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log = {'skips': []}

        log['skips'].append({
            'knowledge': knowledge,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'reason': 'manual_skip',
        })

        os.makedirs(os.path.dirname(self.skipped_log_file), exist_ok=True)
        with open(self.skipped_log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
