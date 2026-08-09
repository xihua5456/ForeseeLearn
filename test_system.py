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

    print("\n7. 测试模糊控制器...")
    from models.fuzzy_controller import FuzzyController
    fuzzy = FuzzyController()

    # 7.1 偏差量越大，调节幅度越大（你要求的核心特性）
    r_terrible = fuzzy.tune(0.2, 1.0)['rate_delta']   # 严重低于目标 → 大幅下调
    r_bad      = fuzzy.tune(0.55, 1.0)['rate_delta']  # 略低 → 小幅下调
    r_ok       = fuzzy.tune(0.7, 1.0)['rate_delta']   # 正好目标 → 几乎不动
    r_good     = fuzzy.tune(0.85, 1.0)['rate_delta']  # 略高 → 小幅上调
    r_excellent = fuzzy.tune(0.95, 1.0)['rate_delta'] # 很高 → 大幅上调

    assert r_terrible <= r_bad <= r_ok <= r_good <= r_excellent, \
        f"调节幅度应随偏差单调变化: {r_terrible} {r_bad} {r_ok} {r_good} {r_excellent}"
    assert abs(r_ok) < 0.005, f"目标点附近应几乎不动: {r_ok}"
    assert r_excellent > 0.01, f"大幅偏差应大幅调节: {r_excellent}"
    print(f"   偏差调节验证: 差0.2→{r_terrible} 差0.55→{r_bad} 目标→{r_ok} 好0.85→{r_good} 好0.95→{r_excellent}")

    # 7.2 平滑性：边界两侧调节量应接近（无硬跳变）
    a = fuzzy.tune(0.69, 1.0)['rate_delta']
    b = fuzzy.tune(0.71, 1.0)['rate_delta']
    assert abs(a - b) < 0.005, f"边界两侧应平滑过渡: {a} vs {b}"
    print(f"   平滑性验证: 0.69→{a}  0.71→{b}（差异 {abs(a-b):.4f} < 0.005）")

    # 7.3 完成率低 → 减负
    task_red = fuzzy.tune(0.7, 0.5)['task_reduction']
    assert task_red >= 10, f"完成率低应明显减负: {task_red}"
    print(f"   减负验证: 完成率0.5 → 任务减 {task_red} 分钟")

    print("\n8. 测试学习路径...")
    # 8.1 定位当前单元（第一个未达标的）
    status = system.get_learning_path_status()
    assert 'current_unit' in status, "应返回当前单元"
    assert status['estimated_minutes'] > 0, "达标时间应为正数"
    print(f"   当前单元: {status['current_unit']} 掌握度 {status['current_mastery']} 需 {status['estimated_minutes']} 分钟")

    # 8.2 手动跳过 → 掌握度设为目标值并推进
    skip_result = system.skip_learning_unit(status['current_unit'])
    assert skip_result['success'] is True, "跳过应成功"
    assert skip_result['mastery_set'] == 0.6, f"跳过应设掌握度为0.6: {skip_result['mastery_set']}"
    state = system.data_manager.load_knowledge_state()
    assert state.get(status['current_unit'], 0) >= 0.6, "跳过单元掌握度应达标"
    print(f"   跳过验证: {skip_result['message']}")

    # 8.3 推进逻辑：已达标单元应推进
    adv = system.advance_learning_path()
    print(f"   推进验证: {adv['message']}")

    # 8.4 跳过日志已记录
    import json as _json
    log_file = system.data_manager.base_path + "/data/cache/skipped_log.json"
    assert os.path.exists(log_file), "跳过日志应存在"
    with open(log_file, encoding='utf-8') as f:
        log = _json.load(f)
    assert len(log['skips']) >= 1, "应至少有一条跳过记录"
    print(f"   日志验证: 已记录 {len(log['skips'])} 条跳过记录")

    print("\n=== 测试通过 ===")
    return True


if __name__ == "__main__":
    try:
        test_system()
    except AssertionError as e:
        print(f"\n!!! 断言失败: {e}")
        sys.exit(1)
