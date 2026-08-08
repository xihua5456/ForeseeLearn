#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_system():
    """测试系统功能（断言版）"""
    print("=== MPC学习系统功能测试 ===\n")

    # 导入系统
    from learning_system import LearningOptimizationSystem

    # 初始化系统
    base_path = os.path.dirname(os.path.abspath(__file__))
    system = LearningOptimizationSystem(base_path)

    print("1. 测试配置加载...")
    assert 'model_params' in system.configs, "model_params 配置缺失"
    assert 'evaluation_weights' in system.configs, "evaluation_weights 配置缺失"
    assert len(system.knowledge_list) > 0, "知识点列表为空"
    print(f"   模型参数: {len(system.configs['model_params'])} 个配置项")
    print(f"   评价权重: {len(system.configs['evaluation_weights'])} 个配置项")
    print(f"   知识点结构: {len(system.knowledge_list)} 个知识点")

    print("\n2. 测试知识点状态...")
    status = system.get_knowledge_status()
    assert 'knowledge_status' in status, "缺少 knowledge_status"
    assert len(status['knowledge_status']) == len(system.knowledge_list), "知识点状态数量与列表不一致"
    print(f"   知识点总数: {len(status['knowledge_status'])}")

    print("\n3. 测试添加学习记录...")
    test_record = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'knowledge_point': '一元二次方程',
        'planned_minutes': 60,
        'actual_minutes': 45,
        'question_count': 10,
        'correct_count': 8,
        'self_rating': 4,
        'notes': '测试记录'
    }

    result = system.add_learning_record(test_record)
    assert result['success'] is True, f"记录失败: {result.get('message')}"
    print(f"   记录结果: {result['message']}")

    # 验证掌握度已更新（key 一致性修复的核心验证）
    state = system.data_manager.load_knowledge_state()
    mastery = state.get('一元二次方程', 0.0)
    assert mastery > 0, f"知识点掌握度未更新，仍为 {mastery}"
    print(f"   掌握度更新: 一元二次方程 = {mastery:.3f}")

    print("\n4. 测试日评价...")
    eval_result = system.evaluate_daily_performance()
    if 'message' not in eval_result:
        assert 'average_score' in eval_result, "缺少平均得分"
        assert 0 <= eval_result['average_score'] <= 1, "得分超出范围"
        print(f"   评价结果: 平均得分 {eval_result['average_score']:.3f}")
    else:
        print(f"   评价结果: {eval_result.get('message', '正常')}")

    print("\n5. 测试生成计划...")
    plan_result = system.generate_tomorrow_plan(120)
    if 'message' not in plan_result:
        assert 'tasks' in plan_result, "缺少任务列表"
        assert plan_result['total_planned_minutes'] > 0, "计划总时长应为正数"
        print(f"   计划生成成功，总时长: {plan_result['total_planned_minutes']} 分钟")
        print(f"   任务数量: {len(plan_result['tasks'])}")
    else:
        print(f"   计划结果: {plan_result['message']}")

    print("\n6. 测试学习洞察...")
    insights = system.get_learning_insights()
    if 'message' not in insights:
        assert 'suggestions' in insights, "缺少建议列表"
        print(f"   洞察结果: {len(insights['suggestions'])} 条建议")
    else:
        print(f"   洞察结果: {insights.get('message', '正常')}")

    print("\n=== 测试通过 ===")
    return True


if __name__ == "__main__":
    try:
        test_system()
    except AssertionError as e:
        print(f"\n!!! 断言失败: {e}")
        sys.exit(1)
