#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from learning_system import LearningOptimizationSystem

def print_menu():
    """显示主菜单"""
    print("\n" + "="*50)
    print("智能学习助手")
    print("="*50)
    print("1. 记录今日学习")
    print("2. 查看今日评价")
    print("3. 生成明日计划")
    print("4. 查看知识点状态")
    print("5. 获取学习建议")
    print("6. 自动优化参数")
    print("7. 修改配置")
    print("0. 退出")
    print("="*50)

def get_user_choice():
    """获取用户选择"""
    try:
        choice = input("\n请选择功能 (0-7): ").strip()
        return int(choice) if choice.isdigit() else None
    except (EOFError, KeyboardInterrupt):
        return None

def record_learning(system):
    """记录学习"""
    print("\n--- 记录今日学习 ---")
    knowledge = input("知识点名称: ").strip()
    
    try:
        planned = int(input("计划时长(分钟): "))
        actual = int(input("实际时长(分钟): "))
        questions = int(input("题目数量: "))
        correct = int(input("正确数量: "))
        rating = int(input("自评分数(1-5): "))
    except ValueError:
        print("输入错误，请输入数字")
        return
    
    record = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'knowledge_point': knowledge,
        'planned_minutes': planned,
        'actual_minutes': actual,
        'question_count': questions,
        'correct_count': correct,
        'self_rating': rating,
        'notes': input("备注(可选): ").strip()
    }
    
    result = system.add_learning_record(record)
    print(f"\n{result['message']}")

def show_evaluation(system):
    """显示评价"""
    print("\n--- 今日学习评价 ---")
    date = input("日期(YYYY-MM-DD，留空则今日): ").strip() or None
    result = system.evaluate_daily_performance(date)
    
    if 'message' in result:
        print(result['message'])
        return
    
    print(f"\n日期: {result['date']}")
    print(f"平均得分: {result['average_score']:.3f}")
    print(f"总体评价: {result['overall_feedback']}")
    
    print("\n详细评价:")
    for detail in result['details']:
        print(f"  {detail['knowledge']}:")
        print(f"    得分: {detail['score']:.3f} | 正确率: {detail['accuracy']:.2f} | 自评: {detail['self_rating']}/5")
        print(f"    建议: {detail['feedback']}")

def generate_plan(system):
    """生成计划"""
    print("\n--- 生成明日学习计划 ---")
    try:
        time_budget = int(input("明日可用学习时间(分钟): "))
    except ValueError:
        print("输入错误，请输入数字")
        return
    
    result = system.generate_tomorrow_plan(time_budget)
    
    if 'message' in result:
        print(result['message'])
        return
    
    print(f"\n日期: {result['date']}")
    print(f"总计划时长: {result['total_planned_minutes']} 分钟")
    
    print("\n学习任务(按优先级排序):")
    for i, task in enumerate(result['tasks'], 1):
        print(f"  {i}. {task['knowledge']}")
        print(f"     时长: {task['planned_minutes']}分钟 | 掌握度: {task['current_mastery']:.2%} | 难度: {task['difficulty']:.2f}")

def show_status(system):
    """显示状态"""
    print("\n--- 知识点状态 ---")
    result = system.get_knowledge_status()
    
    print(f"\n知识点总数: {len(result['knowledge_status'])}")
    print("\n状态分布:")
    
    status_count = {}
    for item in result['knowledge_status']:
        status = item['status']
        status_count[status] = status_count.get(status, 0) + 1
    
    for status, count in status_count.items():
        print(f"  {status}: {count}个")
    
    print("\n知识点列表:")
    for item in result['knowledge_status'][:20]:
        print(f"  {item['knowledge']}: {item['mastery']:.2%} ({item['status']})")
    
    if len(result['knowledge_status']) > 20:
        print(f"  ... 还有 {len(result['knowledge_status']) - 20} 个知识点")

def show_insights(system):
    """显示建议"""
    print("\n--- 学习建议 ---")
    result = system.get_learning_insights()
    
    if 'message' in result:
        print(result['message'])
        return
    
    print(f"\n学习趋势: {result['performance_trend']['trend']}")
    print(f"预期得分: {result['performance_trend']['expected_score']:.3f}")
    print(f"一致性: {result['performance_trend']['consistency']:.3f}")
    
    print("\n薄弱知识点:")
    for item in result['weak_points']:
        print(f"  {item['knowledge']}: {item['mastery']:.2%}")
    
    print("\n优势知识点:")
    for item in result['strong_points']:
        print(f"  {item['knowledge']}: {item['mastery']:.2%}")
    
    print("\n个性化建议:")
    for i, suggestion in enumerate(result['suggestions'], 1):
        print(f"  {i}. {suggestion}")

def auto_optimize(system):
    """自动优化"""
    print("\n--- 自动优化参数 ---")
    confirm = input("确认开始自动优化？(y/n): ").strip().lower()
    
    if confirm != 'y':
        print("已取消")
        return
    
    result = system.auto_optimize_parameters()
    
    if result['success']:
        print(f"\n{result['message']}")
        print(f"平均正确率: {result['changes']['old_accuracy']:.3f}")
        print(f"新学习率: {result['changes']['new_learning_rate']:.3f}")
    else:
        print(f"\n{result['message']}")

def modify_config(system):
    """修改配置"""
    print("\n--- 修改配置 ---")
    print("1. 模型参数")
    print("2. 评价权重")
    print("3. 人性化设置")
    
    try:
        choice = int(input("选择配置类型 (1-3): "))
        config_map = {1: 'model_params', 2: 'evaluation_weights', 3: 'human_settings'}
        config_type = config_map.get(choice)
    except ValueError:
        print("输入错误")
        return
    
    if not config_type:
        print("无效选择")
        return
    
    print(f"\n当前配置 ({config_type}):")
    import json
    print(json.dumps(system.configs[config_type], indent=2, ensure_ascii=False))
    
    modify = input("\n是否修改？(y/n): ").strip().lower()
    if modify != 'y':
        return
    
    print("请输入新的JSON配置:")
    try:
        new_config = json.loads(input().strip())
        result = system.update_config(config_type, new_config)
        print(f"\n{result['message']}")
    except json.JSONDecodeError:
        print("JSON格式错误")

def main():
    """主函数"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    system = LearningOptimizationSystem(base_path)
    
    print("欢迎使用智能学习助手！")
    print("本系统使用智能算法帮您制定最优学习计划")
    
    while True:
        print_menu()
        choice = get_user_choice()
        
        if choice is None:
            print("无效输入，请重新选择")
            continue
        
        if choice == 0:
            print("感谢使用，再见！")
            break
        elif choice == 1:
            record_learning(system)
        elif choice == 2:
            show_evaluation(system)
        elif choice == 3:
            generate_plan(system)
        elif choice == 4:
            show_status(system)
        elif choice == 5:
            show_insights(system)
        elif choice == 6:
            auto_optimize(system)
        elif choice == 7:
            modify_config(system)
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()