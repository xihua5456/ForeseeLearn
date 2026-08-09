"""模糊控制器：根据学习表现偏差量，平滑调节模型参数

设计思路（对应"偏差量越大调节越多"）：
- 以目标正确率为基准（默认 0.7），算出偏差量 deviation = 实际 - 目标
- 偏差量经过 5 个三角形隶属度函数模糊化（负大/负小/零/正小/正大）
- 每条规则按隶属度触发，重心法加权合成 → 一个连续的学习率调整量
- 效果：偏差越大，调整幅度越大；偏差接近零，调整趋近零（无硬边界）
"""

from typing import Dict

# 目标正确率（学习效果基准线）
TARGET_ACCURACY = 0.7

# 学习率调整幅度（对应 5 个模糊等级的"结论"）
RATE_ADJUST = {
    'neg_big': -0.02,   # 偏差很大（学得很差）→ 大幅下调
    'neg_small': -0.008,  # 偏差较小 → 小幅下调
    'zero': 0.0,        # 接近目标 → 不动
    'pos_small': 0.008, # 略好 → 小幅上调
    'pos_big': 0.02,    # 很好 → 大幅上调
}


class FuzzyController:
    """模糊参数调节器：输入正确率/完成率，输出学习率调整量"""

    def __init__(self, target: float = TARGET_ACCURACY):
        self.target = target

    @staticmethod
    def _triangle(x: float, a: float, b: float, c: float) -> float:
        """三角形隶属度函数：返回 x 属于该等级的程度（0~1）"""
        if x <= a or x >= c:
            return 0.0
        if x <= b:
            return (x - a) / (b - a)
        return (c - x) / (c - b)

    def _fuzzify_deviation(self, deviation: float) -> Dict[str, float]:
        """把偏差量映射成 5 个模糊等级的隶属度（核心）"""
        # 偏差范围大约在 [-0.7, +0.3]（正确率 0~1，目标 0.7）
        return {
            'neg_big':   self._triangle(deviation, -1.0, -0.5, -0.15),
            'neg_small': self._triangle(deviation, -0.3, -0.1, 0.05),
            'zero':      self._triangle(deviation, -0.1, 0.0, 0.1),
            'pos_small': self._triangle(deviation, -0.05, 0.1, 0.3),
            'pos_big':   self._triangle(deviation, 0.15, 0.5, 1.0),
        }

    def tune(self, accuracy: float, completion: float = 1.0) -> Dict[str, float]:
        """计算学习率调整量（重心法去模糊化）

        输入：
            accuracy   - 近 7 天平均正确率（0~1）
            completion - 近 7 天平均完成率（0~1），用于减负
        返回：{rate_delta, task_reduction} 连续调整值
        """
        deviation = accuracy - self.target
        memberships = self._fuzzify_deviation(deviation)

        # 重心法：Σ(隶属度 × 结论) / Σ(隶属度)
        weight_sum = sum(memberships.values())
        if weight_sum <= 0:
            rate_delta = 0.0
        else:
            rate_delta = (
                sum(memberships[k] * RATE_ADJUST[k] for k in memberships) / weight_sum
            )

        # 完成率低 → 减负（缩短单任务时长），也是平滑调节
        task_reduction = 0.0
        if completion < 0.7:
            # 完成率越低减得越多：0.7 时减 0，0.4 时减 15 分钟
            task_reduction = 15.0 * (0.7 - completion) / 0.3
            task_reduction = min(task_reduction, 15.0)

        return {
            'rate_delta': round(rate_delta, 4),
            'task_reduction': round(task_reduction, 1),
        }
